"""Randomised scripts that use every command and every kind of operand.

The shipped scripts only use about two thirds of the language. Here programs are built at
random from the language table so that every command, every INT_ variable, every keyword,
out-of-range attribute values, division by zero, 32-bit overflow, random numbers on the
short-circuit side of a condition and DO PARTIAL_BUILDING_COUNT all occur.

Each program is checked four ways:
  1. printed in Bullfrog syntax and parsed back: same tree
  2. printed in World Editor syntax and parsed back: same tree (so the two parsers agree)
  3. converted from each text and run against the interpreter model (differential test)
  4. every command in the table appears in at least one program

Usage: python tests/synthetic.py <game root> [--programs N] [--turns N] [--seed N]
"""
import argparse
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

import differential as D                                          # noqa: E402
from popscript_upgrader import printer, source                     # noqa: E402
from popscript_upgrader.model import (Assign, Block, Do, Every, If, Logic, MulDiv, Script, ScriptError,  # noqa: E402
                                      Test, Value, structure)
from popscript_upgrader.tables import ALACN, BULLFROG, language    # noqa: E402

LANG = language()
INTERESTING = (0, 0, 1, 1, 2, 3, 5, 7, 12, 64, 100, 255, 256, 300, 1000, 65536, 2147483647, -1, -2, -300, -2147483648)


class Maker:
    def __init__(self, rng, commands, alacn_safe):
        self.rng = rng
        self.alacn_safe = alacn_safe
        self.nvars = rng.randint(3, 12)
        self.vars = ['USER_V%d' % i for i in range(self.nvars)]
        self.commands = commands
        self.attrs = [e for e in LANG.internals if e['kind'] == 'attr']
        self.reads = [e for e in LANG.internals if e['kind'] != 'attr' and self.ok_internal(e)]

    def ok_internal(self, e):
        return not (self.alacn_safe and e['name'] in ('INT_RECONVERSION', 'INT_R_BUILDING_WALL_PIECE'))

    def const(self):
        r = self.rng
        return Value('const', value=r.choice(INTERESTING) if r.random() < 0.6 else r.randint(-50, 400))

    def user(self):
        i = self.rng.randrange(self.nvars)
        return Value('user', name=self.vars[i], slot=i)

    def internal(self):
        r = self.rng
        if r.random() < 0.12:
            return Value('internal', entry=LANG.internal('INT_RANDOM_100', BULLFROG))
        return Value('internal', entry=r.choice(self.reads if r.random() < 0.7 else self.attrs))

    def value(self, allow_const=True):
        r = self.rng.random()
        if allow_const and r < 0.4:
            return self.const()
        return self.user() if r < 0.7 else self.internal()

    def keyword(self, kinds):
        return Value('keyword', entry=self.rng.choice([k for k in LANG.keywords if k['kind'] in kinds]))

    def arg(self, param):
        kind = param['kind']
        if kind == 'onoff':
            return self.keyword(('onoff',))
        if kind in ('tribe', 'tribe_wild'):
            if self.rng.random() < 0.6:
                return self.keyword(('tribe', 'wild') if kind == 'tribe_wild' else ('tribe',))
            return Value('const', value=self.rng.randint(0, 3)) if self.rng.random() < 0.5 else self.user()
        if kind == 'var':
            return self.user()
        if kind in ('target_type', 'attack_type', 'guard_type', 'oneshot_type', 'vehicle_type'):
            return self.keyword((kind,))
        return self.value()

    def target(self):
        if self.rng.random() < 0.6:
            return self.user()
        return Value('internal', entry=self.rng.choice(self.attrs))

    def test(self):
        ops = ('>', '<', '==', '!=', '>=', '<=')
        return Test(self.rng.choice(ops), self.value(allow_const=False), self.value())

    def cond(self, depth=0):
        r = self.rng.random()
        if depth >= 2 or r < 0.45:
            return self.test()
        op = self.rng.choice(('AND', 'OR'))
        if self.alacn_safe:                      # the World Editor can only chain to the right
            return Logic(op, self.test(), self.cond(depth + 1))
        return Logic(op, self.cond(depth + 1), self.cond(depth + 1))

    def do(self, cmd=None):
        cmd = cmd or self.rng.choice(self.commands)
        if cmd.get('special') in ('give', 'remove'):
            tribe = self.arg(cmd['params'][0])
            thing = self.internal() if self.rng.random() < 0.8 else self.value()
            return Do(command=cmd, args=[tribe, thing])
        return Do(command=cmd, args=[self.arg(p) for p in cmd['params']])

    def statement(self, depth):
        r = self.rng.random()
        if r < 0.50:
            return self.do()
        if r < 0.66:
            return Assign(op=self.rng.choice(('SET', 'INCREMENT', 'DECREMENT')), target=self.target(), value=self.value())
        if r < 0.76:
            return MulDiv(op=self.rng.choice(('MULTIPLY', 'DIVIDE')), target=self.target(), a=self.value(), b=self.value())
        if depth >= 3:
            return self.do()
        if r < 0.90:
            return If(cond=self.cond(), then=self.block(depth + 1),
                      orelse=self.block(depth + 1) if self.rng.random() < 0.5 else None)
        period = self.rng.choice((2, 4, 8, 16, 64, 256, 1024))
        offset = None if self.rng.random() < 0.4 else self.rng.choice((0, 1, 2, 3, 17, 133, 1000, 20052))
        return Every(period=period, offset=offset, body=self.block(depth + 1))

    def block(self, depth, forced=()):
        stmts = [self.do(c) for c in forced]
        stmts += [self.statement(depth) for _ in range(self.rng.randint(1, 5 if depth else 12))]
        self.rng.shuffle(stmts)
        return Block(statements=stmts)

    def script(self, forced):
        # Bullfrog creates a variable where it is first assigned, so assign them all up front.
        init = [Assign(op='SET', target=Value('user', name=n, slot=i), value=Value('const', value=0))
                for i, n in enumerate(self.vars)]
        guard = If(cond=Test('==', Value('internal', entry=LANG.internal('INT_GAME_TURN', BULLFROG)), Value('const', value=0)),
                   then=Block(statements=init), orelse=None)
        body = self.block(0, forced)
        body.statements.insert(0, guard)
        return Script(dialect=BULLFROG, source_name='synthetic', player_number=1, body=body, variables=list(self.vars))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('game_root')
    ap.add_argument('--programs', type=int, default=120)
    ap.add_argument('--turns', type=int, default=260)
    ap.add_argument('--seed', type=int, default=1998)
    a = ap.parse_args()
    std_path = D.find_std(a.game_root)
    turns = D.turn_schedule(a.turns)
    usable = [c for c in LANG.commands if c.get('special') != 'unsupported']
    both = [c for c in usable if c.get('alacn')]
    pending = list(usable)
    seen = set()
    failures = 0
    calls = 0
    for n in range(a.programs):
        rng = random.Random(a.seed * 1000 + n)
        alacn_safe = n % 2 == 0
        pool = both if alacn_safe else usable
        forced = [c for c in pending if c in pool][:6]
        for c in forced:
            pending.remove(c)
        script = Maker(rng, pool, alacn_safe).script(forced)
        from popscript_upgrader.model import walk
        seen.update(s.command['name'] for s in walk(script.body) if isinstance(s, Do))
        want = structure(script)
        variants = [(BULLFROG, printer.to_text(script, BULLFROG))]
        if alacn_safe:
            variants.append((ALACN, printer.to_text(script, ALACN)))
        for dialect, text in variants:
            label = 'program %d (%s)' % (n, dialect)
            try:
                parsed = source.parse(text, source_name='synthetic')
            except ScriptError as e:
                failures += 1
                print('%s: does not parse back: %s' % (label, e))
                continue
            if parsed.dialect != dialect:
                failures += 1
                print('%s: detected as %s' % (label, parsed.dialect))
                continue
            if structure(parsed) != want:
                failures += 1
                print('%s: parses back to a different program' % label)
                continue
            d = D.compare(parsed, 1 + n % 3, std_path, turns, seed=n)
            if d is not None:
                failures += 1
                print('%s: %s' % (label, d))
            else:
                calls += D.compare.last_calls
    missing = sorted(c['name'] for c in usable if c['name'] not in seen)
    print('%d program(s), %d engine calls compared, %d failure(s)' % (a.programs, calls, failures))
    print('commands exercised: %d of %d%s' % (len(usable) - len(missing), len(usable),
                                             '' if not missing else '; never generated: ' + ', '.join(missing)))
    return 1 if failures or missing else 0


if __name__ == '__main__':
    sys.exit(main())

"""Does the differential test notice mistakes?  Break the generator on purpose and see.

Each mutant changes one behaviour of the Lua generator or of the runtime library. The
differential test must report a difference for every one of them on at least one shipped
script; a mutant that survives means the test is blind to that kind of error.

Usage: python tests/mutation.py <game root> [--turns N]
"""
import argparse
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

import differential as D                               # noqa: E402
from oracle import index_sources                       # noqa: E402
from popscript_upgrader import luagen                  # noqa: E402
from popscript_upgrader.model import Assign, Every, If, Logic, MulDiv, ScriptError  # noqa: E402
from refinterp import RefInterp                         # noqa: E402

G = luagen.Generator
ORIG = {name: getattr(G, name) for name in ('cond', 'statement', 'value', 'fill', 'needs_full_evaluation')}


def restore():
    for name, fn in ORIG.items():
        setattr(G, name, fn)


def m_short_circuit():
    G.needs_full_evaluation = lambda self, c: False


def m_swap_and_or():
    def cond(self, c, full=False, top=True):
        text = ORIG['cond'](self, c, full, top)
        return text.replace(' and ', ' or ', 1) if isinstance(c, Logic) and not full else text
    G.cond = cond


def m_flip_comparison():
    def cond(self, c, full=False, top=True):
        return ORIG['cond'](self, c, full, top).replace(' >= ', ' > ', 1).replace(' ~= ', ' == ', 1)
    G.cond = cond


def m_increment_as_set():
    def statement(self, depth, s):
        if isinstance(s, Assign) and s.op == 'INCREMENT':
            s = Assign(op='SET', target=s.target, value=s.value, line=s.line, leading=s.leading)
        return ORIG['statement'](self, depth, s)
    G.statement = statement


def m_every_drops_offset():
    def statement(self, depth, s):
        if isinstance(s, Every) and s.offset is not None:
            s = Every(period=s.period, offset=None, body=s.body, line=s.line, leading=s.leading)
        return ORIG['statement'](self, depth, s)
    G.statement = statement


def m_else_dropped():
    def statement(self, depth, s):
        if isinstance(s, If) and s.orelse is not None and s.orelse.statements:
            s = If(cond=s.cond, then=s.then, orelse=None, line=s.line, leading=s.leading)
        return ORIG['statement'](self, depth, s)
    G.statement = statement


def m_swap_two_arguments():
    def fill(self, template, s):
        text = ORIG['fill'](self, template, s)
        if s.command['name'] == 'SET_MARKER_ENTRY':
            head, rest = text.split('(', 1)
            args = rest[:-1].split(', ')
            args[2], args[3] = args[3], args[2]
            text = head + '(' + ', '.join(args) + ')'
        return text
    G.fill = fill


def m_tribe_constant_wrong():
    def value(self, v, kind='value'):
        text = ORIG['value'](self, v, kind)
        return 'TRIBE_RED' if text == 'TRIBE_BLUE' else text
    G.value = value


def m_multiply_as_divide():
    def statement(self, depth, s):
        if isinstance(s, MulDiv) and s.op == 'MULTIPLY':
            s = MulDiv(op='DIVIDE', target=s.target, a=s.a, b=s.b, line=s.line, leading=s.leading)
        return ORIG['statement'](self, depth, s)
    G.statement = statement


GENERATOR_MUTANTS = [m_swap_and_or, m_flip_comparison, m_increment_as_set, m_every_drops_offset, m_else_dropped,
                     m_swap_two_arguments, m_tribe_constant_wrong, m_multiply_as_divide, m_short_circuit]

# Mutants of the runtime library: text replaced in a temporary copy of cpscript.lua.
LIBRARY_MUTANTS = [
    ('every_ignores_tribe', 'return ((getTurn() + self.tribe + shift) & (period - 1)) == 0',
     'return ((getTurn() + shift) & (period - 1)) == 0'),
    ('every_offset_off_by_one', 'if offset ~= nil then shift = offset - 1 end', 'if offset ~= nil then shift = offset end'),
    ('attribute_not_a_byte', 'WRITE_CP_ATTRIB(tribe, index(name), value % 256)',
     'WRITE_CP_ATTRIB(tribe, index(name), value)'),
    ('flag_keeps_raw_value', 'if x == nil or x == false or x == 0 then return 0 end\n  return 1',
     'if x == nil or x == false or x == 0 then return 0 end\n  if x == true then return 1 end\n  return x'),
    ('slots_start_at_one', 'slot_of[name] = i - 1', 'slot_of[name] = i'),
]


def survey(scripts, std_path, turns):
    """Number of scripts on which the differential test reports a difference."""
    hits = 0
    for num, script in scripts:
        try:
            if D.compare(script, 1, std_path, turns, seed=num * 10 + 1) is not None:
                hits += 1
        except Exception:                               # noqa: BLE001 - a crash is a detection too
            hits += 1
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('game_root')
    ap.add_argument('--turns', type=int, default=700)
    a = ap.parse_args()
    std_path = D.find_std(a.game_root)
    turns = D.turn_schedule(a.turns)
    sources = index_sources(os.path.join(a.game_root, 'CpScript'))

    def load_all():
        out = []
        for num in sorted(sources):
            try:
                out.append((num, D.load_script(sources[num][0], os.path.join(a.game_root, 'levels', 'cpscr%03d.dat' % num))))
            except ScriptError:
                pass
        # plus random programs, which reach the parts of the language the shipped scripts do not
        import random
        import synthetic
        usable = [c for c in synthetic.LANG.commands if c.get('special') != 'unsupported']
        for n in range(60):
            out.append((9000 + n, synthetic.Maker(random.Random(n), usable, False).script([])))
        return out

    base = survey(load_all(), std_path, turns)
    print('unmodified converter: %d script(s) differ (must be 0)' % base)
    survived = 0
    for m in GENERATOR_MUTANTS:
        m()
        try:
            hits = survey(load_all(), std_path, turns)
        finally:
            restore()
        print('%-28s detected on %2d script(s)%s' % (m.__name__[2:], hits, '' if hits else '   <-- SURVIVED'))
        survived += not hits
    lib = open(std_path, encoding='utf-8').read()
    for name, old, new in LIBRARY_MUTANTS:
        assert lib.count(old) == 1, 'library text for mutant %s not found' % name
        with tempfile.NamedTemporaryFile('w', suffix='.lua', delete=False, encoding='utf-8') as f:
            f.write(lib.replace(old, new))
        try:
            hits = survey(load_all(), f.name, turns)
        finally:
            os.unlink(f.name)
        print('%-28s detected on %2d script(s)%s' % (name, hits, '' if hits else '   <-- SURVIVED'))
        survived += not hits
    # the interpreter model must also disagree with itself when its own EVERY rule is changed
    print('\n%d mutant(s) survived' % survived)
    return 1 if survived or base else 0


if __name__ == '__main__':
    sys.exit(main())

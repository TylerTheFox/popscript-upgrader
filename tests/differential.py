"""Differential test: generated Lua versus a model of the bytecode interpreter.

For each script:
  1. build the tree (from text, or from text reconciled with the compiled .DAT)
  2. generate the Lua
  3. run the Lua in a real Lua 5.3 (the engine's version) against a mock engine, using the
     real std/cpscript.lua from the standard library
  4. run tests/refinterp.py (the interpreter model) on the same tree against an identical
     mock engine
  5. after every turn compare: the ordered list of state-changing engine calls with their
     arguments, the 64 script variables and the 48 attributes

The mock engine also rejects any call to a function that is not in the engine's API, any
call with the wrong number of arguments and any non-integer argument, so this doubles as a
check that the output only uses real Script4 functions correctly.

Usage:
  python tests/differential.py <game root> [--turns N] [--only NUM] [-v]
  python tests/differential.py --file script.scr [--tribe N]

Requires: pip install lupa
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

from popscript_upgrader import compiled, luagen, source          # noqa: E402
from popscript_upgrader.model import ScriptError                  # noqa: E402
from popscript_upgrader.reconcile import reconcile                # noqa: E402
from popscript_upgrader.tables import language                    # noqa: E402
from refinterp import RefInterp, World, uses_partial              # noqa: E402

try:
    from lupa import lua53 as lupa
except ImportError:                                               # pragma: no cover
    lupa = None

API = json.load(open(os.path.join(HERE, 'engine_api.json'), encoding='utf-8'))
LANG = language()


def find_std(game_root):
    for cand in (os.path.join(game_root or '', 'Scripts', 'std', 'v0.0.1', 'cpscript.lua'),
                 os.path.join(ROOT, 'std', 'cpscript.lua')):
        if os.path.isfile(cand):
            return cand
    raise SystemExit('std/v0.0.1/cpscript.lua not found; pass the game root')


def pure_read_names():
    names = set()
    for e in LANG.internals:
        if e['kind'] == 'read' and not e.get('side_effect'):
            names.update(re.findall(r'\b([A-Za-z_][A-Za-z0-9_]*)\(', e['lua']))
    names.discard('GET_INTERNAL_VARIABLE')
    return names


PURE = pure_read_names()


def make_world(seed, tribe, partial):
    w = World(API, seed, tribe, partial)
    w.internal_names = LANG.internal_by_index
    w.pure_reads = PURE
    return w


class LuaSide:
    """The generated script running in Lua 5.3 on top of the real std.cpscript."""

    def __init__(self, lua_text, world, std_path):
        self.world = world
        self.rt = lupa.LuaRuntime(unpack_returned_tuples=True)
        g = self.rt.globals()
        self.handlers = {}

        def on(event, fn):
            self.handlers.setdefault(event, []).append(fn)
            return len(self.handlers[event])

        # Minimal std: the pieces cpscript.lua and the generated file touch.
        self.rt.execute('std = { cpscript = nil }; function include() end; function log() end')
        g.std.install = lambda *a: None
        g.std.on = on
        for name in API['functions']:
            if name in ('include', 'log'):
                continue
            g[name] = self.binding(name)
        for name, value in API['constants'].items():
            if value is not None:
                g[name] = value
        g['WILD'] = 8
        # Any other global is a mistake in the generated code.
        self.rt.execute('''
            setmetatable(_G, { __index = function(_, k) error("undefined global '" .. tostring(k) .. "'", 2) end })
        ''')
        self.rt.execute(open(std_path, encoding='utf-8').read())
        self.rt.execute(lua_text)
        for fn in self.handlers.get('OnLevelInit', []):
            fn(1)

    def binding(self, name):
        world = self.world

        def call(*args):
            fixed = []
            for a in args:
                if isinstance(a, float) and a == int(a):
                    raise AssertionError('%s received a float argument %r' % (name, a))
                fixed.append(tuple(a.values()) if lupa.lua_type(a) == 'table' else a)
            if name == 'getPlayer':
                return self.rt.table_from(['player', fixed[0]])
            return world.call(name, *fixed)
        return call

    def run_turn(self):
        for fn in self.handlers['OnComputerPlayerScript']:
            fn(self.world.tribe)


def lua_table_to_tuple(t):
    return tuple(t.values())


def compare(script, tribe, std_path, turns, seed=1, verbose=False):
    """Run both sides for `turns` turns. Returns None if identical, else a description."""
    partial = uses_partial(script)
    text, _ = luagen.generate(script, tribe)
    w_lua, w_ref = make_world(seed, tribe, partial), make_world(seed, tribe, partial)
    try:
        lua = LuaSide(text, w_lua, std_path)
    except Exception as e:                        # noqa: BLE001
        return 'the generated Lua does not load: %s' % e
    # muting the original script is the only call made at level start
    if w_lua.trace != [('script_set_up_empty_script', tribe)]:
        return 'level start: expected the original script to be muted once, got %r' % (w_lua.trace,)
    w_ref.version = w_lua.version
    ref = RefInterp(script, tribe, w_ref, LANG, API['constants'])
    calls = 0
    for turn in turns:
        w_lua.start_turn(turn)
        w_ref.start_turn(turn)
        try:
            ref.run_turn()
        except AssertionError as e:
            return 'turn %d: interpreter model: %s' % (turn, e)
        try:
            lua.run_turn()
        except Exception as e:                    # noqa: BLE001 - report whatever Lua raised
            return 'turn %d: Lua: %s' % (turn, e)
        calls += len(w_ref.trace)
        if w_lua.trace != w_ref.trace:
            for i, (a, b) in enumerate(zip(w_lua.trace, w_ref.trace)):
                if a != b:
                    return 'turn %d: call %d differs:\n    Lua        %r\n    interpreter %r' % (turn, i, a, b)
            return 'turn %d: %d call(s) from Lua, %d from the interpreter; first extra: %r' % (
                turn, len(w_lua.trace), len(w_ref.trace),
                (w_lua.trace + w_ref.trace)[min(len(w_lua.trace), len(w_ref.trace))])
        if w_lua.user_vars != w_ref.user_vars:
            d = [(i, a, b) for i, (a, b) in enumerate(zip(w_lua.user_vars, w_ref.user_vars)) if a != b][0]
            return 'turn %d: variable %s (slot %d) is %d in Lua, %d in the interpreter' % (
                turn, script.variables[d[0]] if d[0] < len(script.variables) else '?', d[0], d[1], d[2])
        if w_lua.attribs != w_ref.attribs:
            d = [(i, a, b) for i, (a, b) in enumerate(zip(w_lua.attribs, w_ref.attribs)) if a != b][0]
            return 'turn %d: attribute %d is %d in Lua, %d in the interpreter' % (turn, d[0], d[1], d[2])
        if w_lua.version != w_ref.version:
            return 'turn %d: engine state versions differ' % turn
    compare.last_calls = calls
    return None


def turn_schedule(n):
    """The first turns one by one (initialisation, low EVERY periods), then strides that hit
    every residue of the larger periods."""
    turns = list(range(0, min(n, 600)))
    t = 600
    step = 1
    while len(turns) < n:
        turns.append(t)
        t += step
        step = step % 97 + 1
    return turns


def load_script(src_path, dat_path=None):
    if dat_path and os.path.isfile(dat_path):
        dat = compiled.decode_file(dat_path)
        src = source.parse_file(src_path, recover=True)
        script, _ = reconcile(src, dat)
        return script
    return source.parse_file(src_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('game_root', nargs='?')
    ap.add_argument('--file')
    ap.add_argument('--dats', help='folder of compiled CPSCRnnn.DAT files to test (a mod without sources)')
    ap.add_argument('--tribe', type=int, default=1)
    ap.add_argument('--turns', type=int, default=3000)
    ap.add_argument('--only', type=int)
    ap.add_argument('-v', action='store_true')
    a = ap.parse_args()
    if lupa is None:
        raise SystemExit('this test needs Lua 5.3: pip install lupa')
    std_path = find_std(a.game_root)
    turns = turn_schedule(a.turns)
    if a.file:
        d = compare(load_script(a.file), a.tribe, std_path, turns, verbose=a.v)
        print('IDENTICAL' if d is None else 'DIFFERENT: ' + d)
        return 0 if d is None else 1
    if a.dats:
        ok = bad = skipped = 0
        total = 0
        for fn in sorted(os.listdir(a.dats)):
            if not re.match(r'cpscr.*\.dat$', fn, re.I):
                continue
            try:
                script = compiled.decode_file(os.path.join(a.dats, fn))
            except ScriptError as e:
                skipped += 1
                print('skipped    %-18s %s' % (fn, e.message))
                continue
            worst = None
            for tribe in (1, 2, 3):
                d = compare(script, tribe, std_path, turns, seed=len(fn) * 7 + tribe)
                if d is not None:
                    worst = 'tribe %d: %s' % (tribe, d)
                    break
                total += compare.last_calls
            ok += worst is None
            bad += worst is not None
            if worst:
                print('DIFFERENT  %-18s %s' % (fn, worst))
        print('%d compiled script(s) identical over %d turns x 3 tribes (%d engine calls compared), %d different, '
              '%d not loadable' % (ok, len(turns), total, bad, skipped))
        return 1 if bad else 0
    from oracle import index_sources
    sources = index_sources(os.path.join(a.game_root, 'CpScript'))
    levels = os.path.join(a.game_root, 'levels')
    ok = bad = skipped = 0
    total_calls = 0
    for num in sorted(sources):
        if a.only is not None and num != a.only:
            continue
        dat_path = os.path.join(levels, 'cpscr%03d.dat' % num)
        for path in sources[num]:
            name = os.path.basename(path)
            try:
                script = load_script(path, dat_path)
            except ScriptError as e:
                skipped += 1
                if a.v:
                    print('skipped    %-14s %s' % (name, e))
                continue
            worst = None
            for tribe in (1, 2, 3):
                d = compare(script, tribe, std_path, turns, seed=num * 10 + tribe, verbose=a.v)
                if d is not None:
                    worst = 'tribe %d: %s' % (tribe, d)
                    break
                total_calls += compare.last_calls
            if worst is None:
                ok += 1
                if a.v:
                    print('identical  %-14s' % name)
            else:
                bad += 1
                print('DIFFERENT  %-14s %s' % (name, worst))
    print('\n%d script(s) identical over %d turns x 3 tribes (%d engine calls compared), %d different, '
          '%d not convertible' % (ok, len(turns), total_calls, bad, skipped))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())

"""A model of the game's bytecode interpreter, and a mock engine, for differential testing.

RefInterp executes a script tree the way Source/Script.cpp does:

  * EVERY     runs its block when ((turn + player + stored offset) & stored period) == 0,
              where the compiler stored (period - 1) and (offset - 1); no offset means 0
  * IF        evaluates every test of the condition, left to right, then combines them
  * SET / INCREMENT / DECREMENT / MULTIPLY / DIVIDE  32-bit signed arithmetic; DIVIDE rounds
              toward zero and gives 0 on division by zero; an INT_ATTR_ target keeps one byte
  * DO        performs the engine call for the command and stores a result if it has one

World is a stand-in for the engine. It answers every Script4 function with a deterministic
pseudo-random value and records every call that changes something, in order. The same World
class backs the Lua side of the test, so "the converted Lua behaves like the bytecode" becomes
"both produce the same list of engine calls and leave the same variables, turn after turn".

The interpreter evaluates the language table's call templates with its own small evaluator;
it shares no code with the Lua generator.
"""
import hashlib
import re

from popscript_upgrader.model import Assign, Do, Every, If, Junk, Logic, MulDiv, Test, walk

MASK32 = 0xFFFFFFFF


def int32(x):
    x &= MASK32
    return x - 0x100000000 if x & 0x80000000 else x


def c_div(a, b):
    if b == 0:
        return 0
    q = abs(a) // abs(b)
    return int32(-q if (a < 0) != (b < 0) else q)


# Functions that only read. Their answers depend on the engine state, which changes when a
# state-changing call happens; reading twice in a row gives the same answer.
BOOL_RESULT = {'I_HAVE_ONE_SHOT', 'HAS_TIMER_REACHED_ZERO', 'IS_PLAYER_IN_WORLD_VIEW'}
FLAG_RESULT = {'HAS_HOUSE_INFO_BEEN_SHOWN', 'OH_LOOK_PLAYER_HAS_JUST_KILLED_HIS_FIRST_GHOST'}
SAMPLE = (0, 0, 1, 1, 2, 3, 4, 5, 6, 8, 10, 13, 20, 33, 50, 75, 100, 150, 400, 1000, 5000, -1)


class World:
    def __init__(self, api, seed, tribe, partial_mode):
        self.api = api
        self.seed = seed
        self.tribe = tribe
        self.partial_mode = partial_mode
        self.turn = 0
        self.version = 0
        self.user_vars = [0] * 64
        self.attribs = [0] * 48
        self.attack_slot = 0
        self.trace = []
        self.internal_names = {}
        self.pure_reads = set()

    def rnd(self, *key):
        h = hashlib.md5(repr((self.seed,) + key).encode()).digest()
        return int.from_bytes(h[:4], 'little')

    def start_turn(self, turn):
        self.turn = turn
        self.trace = []
        # The engine writes attack results into the script's attack variable between turns.
        if self.rnd('attack-write', turn) % 5 == 0:
            self.user_vars[self.attack_slot] = (0, 1, 2, 3, 4, 5, 6, 7, 51, 52)[self.rnd('attack-value', turn) % 10]
        self.version += 1

    def is_pure(self, name, args):
        if name in ('GET_USER_VARIABLE_VALUE', 'READ_CP_ATTRIB', 'getTurn', 'GET_TURNS_PER_SECOND', 'getPlayer'):
            return True
        if name == 'GET_INTERNAL_VARIABLE':
            e = self.internal_names.get(args[1])
            if e is None:
                raise AssertionError('GET_INTERNAL_VARIABLE called with unknown index %r' % (args[1],))
            return not (e.get('side_effect') or (self.partial_mode and e.get('building_count')))
        return name in self.pure_reads

    def call(self, name, *args):
        """Every Script4 function goes through here, from either side of the test."""
        expected = self.api['functions'].get(name)
        if expected is None:
            raise AssertionError('%s is not a Script4 function' % name)
        if len(args) != expected:
            raise AssertionError('%s called with %d argument(s), the engine takes %d' % (name, len(args), expected))
        for a in args:
            if not isinstance(a, int) or isinstance(a, bool):
                if not (name == 'computer_build_at_xz' and a == ('player', self.tribe)):
                    raise AssertionError('%s called with a non-integer argument %r' % (name, a))
        if name == 'getTurn':
            return self.turn
        if name == 'getPlayer':
            return ('player', args[0])
        if name == 'GET_TURNS_PER_SECOND':
            return 12
        if name == 'GET_USER_VARIABLE_VALUE':
            assert args[0] == self.tribe
            return self.user_vars[args[1]]
        if name == 'SET_USER_VARIABLE_VALUE':
            assert args[0] == self.tribe
            assert -0x80000000 <= args[2] <= 0x7FFFFFFF, 'value out of 32-bit range reached the engine'
            self.user_vars[args[1]] = args[2]
            return None
        if name == 'READ_CP_ATTRIB':
            assert args[0] == self.tribe
            return self.attribs[args[1]]
        if name == 'WRITE_CP_ATTRIB':
            assert args[0] == self.tribe
            assert 0 <= args[2] <= 255, 'attribute value out of byte range reached the engine'
            self.attribs[args[1]] = args[2]
            return None
        if self.is_pure(name, args):
            return self.answer(name, args)
        self.trace.append((name,) + tuple(args))
        value = self.answer(name, args)
        self.version += 1
        if name == 'SET_ATTACK_VARIABLE':
            self.attack_slot = args[1]
        elif name == 'ATTACK':
            self.user_vars[self.attack_slot] = self.rnd('attack-now', self.version) % 4
        return value

    def answer(self, name, args):
        r = self.rnd(name, args, self.version)
        if name in BOOL_RESULT:
            return bool(r & 1)
        if name in FLAG_RESULT:
            return 0x4000 if r & 1 else 0
        if name == 'G_RANDOM':
            return r % max(1, args[0])
        if name == 'GET_INTERNAL_VARIABLE' and self.internal_names[args[1]]['name'] == 'INT_RANDOM_100':
            return r % 100
        if name == 'CHECK_IF_PERSON_PREACHED_TO':
            return -1 if r & 1 else (r >> 8) & 0xFFFF
        return SAMPLE[r % len(SAMPLE)]


class RefInterp:
    def __init__(self, script, tribe, world, lang, constants):
        self.script, self.tribe, self.world, self.lang = script, tribe, world, lang
        self.constants = constants
        self.partial = world.partial_mode

    # --------------------------------------------------- template evaluator
    def const(self, name):
        if name == 'cp.TARGET_SHAMAN':
            return 999
        v = self.constants.get(name)
        if v is None:
            raise AssertionError('constant %s has no known value' % name)
        return v

    def eval_text(self, text, args=None, params=None):
        """Evaluate a call template: NAME(arg, ...), nested calls, {me}, {n}, numbers, constants."""
        pos = [0]
        s = text

        def skip():
            while pos[0] < len(s) and s[pos[0]] == ' ':
                pos[0] += 1

        def expr():
            skip()
            m = re.compile(r'\{(?:([a-z]+):)?(\d+|me)\}').match(s, pos[0])
            if m:
                pos[0] = m.end()
                if m.group(2) == 'me':
                    return self.tribe
                v = self.value(args[int(m.group(2)) - 1])
                if m.group(1) == 'tooltip':
                    return {0: 1, 1: 2}.get(v, v)
                if m.group(1) == 'seconds':
                    return int32(v * self.world.call('GET_TURNS_PER_SECOND'))
                return v
            m = re.compile(r'-?\d+').match(s, pos[0])
            if m:
                pos[0] = m.end()
                return int(m.group(0))
            m = re.compile(r'[A-Za-z_][A-Za-z0-9_.]*').match(s, pos[0])
            if not m:
                raise AssertionError('cannot evaluate template %r at %d' % (s, pos[0]))
            name = m.group(0)
            pos[0] = m.end()
            skip()
            if pos[0] < len(s) and s[pos[0]] == '(':
                pos[0] += 1
                call_args = []
                skip()
                if s[pos[0]] == ')':
                    pos[0] += 1
                else:
                    while True:
                        call_args.append(expr())
                        skip()
                        ch = s[pos[0]]
                        pos[0] += 1
                        if ch == ')':
                            break
                        assert ch == ',', (s, pos[0])
                return self.world.call(name, *call_args)
            return self.const(name)
        v = expr()
        skip()
        assert pos[0] == len(s), 'trailing text in template %r' % s
        return v

    # ------------------------------------------------------------- values
    def value(self, v):
        if v.kind == 'const':
            return v.value
        if v.kind == 'user':
            return self.world.user_vars[v.slot]
        if v.kind == 'keyword':
            return v.entry['value']
        e = v.entry
        if e['kind'] == 'attr':
            return self.world.attribs[e['index'] - 1000]
        if e['kind'] == 'const':
            return e['value']
        if self.partial and e.get('building_count'):
            return self.world.call('GET_INTERNAL_VARIABLE', self.tribe, e['index'])
        return self.eval_text(e['lua'])

    def store(self, target, value):
        if target.kind == 'user':
            self.world.user_vars[target.slot] = int32(value)
        elif target.entry['kind'] != 'attr':
            pass                                  # the interpreter stores nothing (Script.cpp, "bugger 6")
        else:
            self.world.attribs[target.entry['index'] - 1000] = value & 0xFF

    def cond(self, c):
        if isinstance(c, Test):
            a = self.value(c.a)
            b = self.value(c.b)
            return {'>': a > b, '<': a < b, '==': a == b, '!=': a != b, '>=': a >= b, '<=': a <= b}[c.op]
        left = self.cond(c.left)          # both sides, always
        right = self.cond(c.right)
        return (left and right) if c.op == 'AND' else (left or right)

    # --------------------------------------------------------- statements
    def do(self, s):
        cmd = s.command
        special = cmd.get('special')
        if special == 'noop':
            for a in s.args:                      # SET_CONVERT_MARKER reads its operand and drops it
                self.value(a)
            return
        if special == 'attack_var':
            self.world.call('SET_ATTACK_VARIABLE', self.tribe, s.args[0].slot)
            return
        if special in ('give', 'remove'):
            from popscript_upgrader.luagen import _GIVE_BUILDINGS, _GIVE_SPELLS
            tribe, thing = s.args
            pn = self.value(tribe)
            model = self.value(thing)
            if thing.kind == 'internal' and thing.entry['name'] in _GIVE_SPELLS:
                self.world.call('set_player_can_cast' if special == 'give' else 'set_player_cannot_cast', model, pn)
            elif thing.kind == 'internal' and thing.entry['name'] in _GIVE_BUILDINGS:
                self.world.call('set_player_can_build' if special == 'give' else 'set_player_cannot_build', model, pn)
            return
        if special == 'preached':
            pos = self.world.call('CHECK_IF_PERSON_PREACHED_TO', 0)
            if pos != -1:
                self.store(s.args[0], 1)
                self.store(s.args[1], pos & 0xFF)
                self.store(s.args[2], pos >> 8)
            else:
                self.store(s.args[0], 0)
            return
        if 'set' in cmd:
            result = self.eval_text(cmd['expr'], s.args)
            if cmd.get('norm'):
                result = 1 if result else 0
            self.store(s.args[cmd['set'] - 1], result)
            return
        if cmd.get('ignored'):
            # operands are read in order before the call; an ignored one is read and dropped
            from popscript_upgrader.model import Value
            vals = [Value('const', value=self.value(a)) for a in s.args]
            self.eval_text(cmd['call'], vals)
            return
        self.eval_text(cmd['call'], s.args)

    def block(self, block):
        w = self.world
        for s in block.statements:
            if isinstance(s, Junk):
                continue
            if isinstance(s, Do):
                self.do(s)
            elif isinstance(s, Assign):
                value = self.value(s.value)
                if s.op == 'SET':
                    self.store(s.target, value)
                elif s.target.kind == 'internal' and s.target.entry['kind'] != 'attr':
                    pass
                else:
                    old = self.value(s.target)
                    self.store(s.target, old + value if s.op == 'INCREMENT' else old - value)
            elif isinstance(s, MulDiv):
                a = self.value(s.a)
                b = self.value(s.b)
                self.store(s.target, int32(a * b) if s.op == 'MULTIPLY' else c_div(a, b))
            elif isinstance(s, Every):
                stored_period = s.period - 1
                stored_offset = 0 if s.offset is None else s.offset - 1
                if ((w.turn + self.tribe + stored_offset) & MASK32 & stored_period) == 0:
                    self.block(s.body)
            elif isinstance(s, If):
                if self.cond(s.cond):
                    self.block(s.then)
                elif s.orelse is not None:
                    self.block(s.orelse)

    def run_turn(self):
        self.block(self.script.body)


def uses_partial(script):
    return any(isinstance(s, Do) and s.command.get('flag') == 'partial_count' for s in walk(script.body))

"""Read a compiled script (levels/CPSCRnnn.DAT) back into the syntax tree.

A .DAT file is the engine's ScriptInfo structure written to disk:

    UWORD  Codes[4096]              the program
    struct { ULONG Type; SLONG Value; } Fields[512]
    SLONG  UserVars[64]
    (two pointers, unused on disk)

A code below 1000 is an index into Fields; anything else is a token. Field types are
0 = constant, 1 = script variable (Value is its slot), 2 = internal variable (Value is its
INT_ index), 3 = unused.

This is used two ways: to convert a level that only ships compiled scripts, and to prove the
text parser right (parsing CPSCRnnn.SCR must give the same tree as decoding CPSCRnnn.DAT).
"""
import struct

from .model import Assign, Block, Do, Every, If, Logic, MulDiv, Script, ScriptError, Test, Value
from .tables import COMPILED, language

NUM_CODES, NUM_FIELDS, NUM_VARS = 4096, 512, 64
MIN_SIZE = NUM_CODES * 2 + NUM_FIELDS * 8

_REL = {1012: '>', 1013: '<', 1014: '==', 1015: '!=', 1016: '>=', 1017: '<='}
_SETS = {1007: 'SET', 1008: 'INCREMENT', 1009: 'DECREMENT'}
_MULDIV = {1025: 'MULTIPLY', 1026: 'DIVIDE'}
IF, ELSE, ENDIF, BEGIN, END, EVERY, DO, SCRIPT_END, AND, OR = 1000, 1001, 1002, 1003, 1004, 1005, 1006, 1019, 1020, 1021


def looks_compiled(data):
    """A .DAT starts with the script version (12) then BEGIN, as 16-bit words."""
    return len(data) >= MIN_SIZE and struct.unpack_from('<HH', data, 0) == (12, BEGIN)


class Decoder:
    def __init__(self, data, source_name=''):
        if len(data) < MIN_SIZE:
            raise ScriptError('not a compiled script: %d bytes, expected at least %d' % (len(data), MIN_SIZE), 0, source_name)
        self.lang = language()
        self.source_name = source_name
        self.codes = struct.unpack_from('<%dH' % NUM_CODES, data, 0)
        self.fields = [struct.unpack_from('<Ii', data, NUM_CODES * 2 + i * 8) for i in range(NUM_FIELDS)]
        self.pc = 0
        self.max_slot = -1

    def err(self, msg):
        raise ScriptError('%s (at code %d)' % (msg, self.pc), 0, self.source_name)

    def code(self):
        if self.pc >= NUM_CODES:
            self.err('ran past the end of the program')
        return self.codes[self.pc]

    def take(self):
        c = self.code()
        self.pc += 1
        return c

    def expect(self, token, what):
        c = self.take()
        if c != token:
            self.pc -= 1
            self.err('expected %s but found code %d' % (what, c))

    def field(self):
        c = self.take()
        if c >= NUM_FIELDS:
            self.pc -= 1
            self.err('expected a value but found code %d' % c)
        ftype, fval = self.fields[c]
        if ftype == 0:
            return Value('const', value=fval)
        if ftype == 1:
            if not 0 <= fval < NUM_VARS:
                self.err('variable slot %d is out of range' % fval)
            self.max_slot = max(self.max_slot, fval)
            return Value('user', name='USER_%d' % fval, slot=fval)
        if ftype == 2:
            e = self.lang.internal_by_index.get(fval)
            if e is None:
                self.err('unknown internal variable %d' % fval)
            return Value('internal', entry=e)
        self.err('field %d is marked unused' % c)

    def operand(self, param):
        c = self.code()
        if c >= 1000:
            k = self.lang.keyword_by_token.get(c)
            if k is None:
                self.err('expected an operand but found token %d' % c)
            self.pc += 1
            return Value('keyword', entry=k)
        return self.field()

    def cond(self):
        c = self.take()
        if c in (AND, OR):
            left = self.cond()
            right = self.cond()
            return Logic('AND' if c == AND else 'OR', left, right)
        if c in _REL:
            a = self.field()
            b = self.field()
            return Test(_REL[c], a, b)
        self.pc -= 1
        self.err('expected a condition but found code %d' % c)

    def block(self):
        self.expect(BEGIN, 'BEGIN')
        b = Block()
        while self.code() != END:
            b.statements.append(self.statement())
        self.pc += 1
        return b

    def statement(self):
        c = self.take()
        if c == DO:
            tok = self.take()
            cmd = self.lang.command_by_token.get(tok)
            if cmd is None:
                self.pc -= 1
                self.err('unknown command token %d' % tok)
            return Do(command=cmd, args=[self.operand(p) for p in cmd['params']])
        if c in _SETS:
            target = self.field()
            return Assign(op=_SETS[c], target=target, value=self.field())
        if c in _MULDIV:
            target = self.field()
            a = self.field()
            return MulDiv(op=_MULDIV[c], target=target, a=a, b=self.field())
        if c == EVERY:
            period = self.field()
            offset = None
            if self.code() != BEGIN:
                offset = self.field()
            if period.kind != 'const' or (offset is not None and offset.kind != 'const'):
                self.err('EVERY operands must be constants')
            return Every(period=period.value + 1, offset=None if offset is None else offset.value + 1, body=self.block())
        if c == IF:
            cond = self.cond()
            then = self.block()
            orelse = None
            if self.code() == ELSE:
                self.pc += 1
                orelse = self.block()
            self.expect(ENDIF, 'ENDIF')
            return If(cond=cond, then=then, orelse=orelse)
        self.pc -= 1
        self.err('expected a statement but found code %d' % c)

    def decode(self):
        version = self.take()
        if version != self.lang.script_version:
            self.err('script version is %d, expected %d' % (version, self.lang.script_version))
        script = Script(dialect=COMPILED, source_name=self.source_name)
        script.body = self.block()
        self.expect(SCRIPT_END, 'SCRIPT_END')
        script.variables = ['USER_%d' % i for i in range(self.max_slot + 1)]
        return script


def decode(data, source_name=''):
    return Decoder(data, source_name).decode()


def decode_file(path):
    import os
    with open(path, 'rb') as f:
        return decode(f.read(), os.path.basename(path))

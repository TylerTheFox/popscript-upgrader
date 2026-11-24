"""Write a script tree back out as script text, in either syntax.

Useful on its own (turn a compiled CPSCRnnn.DAT into readable text, or translate between the
Bullfrog and World Editor syntaxes) and as a test: text printed here must parse back to the
same tree.
"""
from .model import Assign, Do, Every, If, Junk, Logic, MulDiv, ScriptError, Test
from .tables import ALACN, BULLFROG


class Printer:
    def __init__(self, script, dialect):
        self.script, self.dialect = script, dialect
        self.open, self.close = ('BEGIN', 'END') if dialect == BULLFROG else ('{', '}')
        self.tab = '\t' if dialect == BULLFROG else '  '
        self.out = []

    def emit(self, depth, text=''):
        self.out.append((self.tab * depth + text).rstrip())

    def comment(self, depth, c):
        self.emit(depth, '// ' + c.text if c.text else '//')

    def value(self, v):
        if v.kind == 'const':
            return str(v.value)
        if v.kind == 'user':
            return ('$' + v.name) if self.dialect == ALACN else v.name
        e = v.entry
        if v.kind == 'keyword':
            return e['alacn'] if self.dialect == ALACN else e['name']
        if self.dialect == ALACN:
            return e.get('alacn') or e['name']
        return e['name']

    def cond(self, c, top=True):
        if isinstance(c, Test):
            text = '%s %s %s' % (self.value(c.a), c.op, self.value(c.b))
            return '( %s )' % text if self.dialect == BULLFROG else text
        op = '&&' if c.op == 'AND' else '||'
        if self.dialect == BULLFROG:
            return '( %s %s %s )' % (self.cond(c.left, False), op, self.cond(c.right, False))
        if isinstance(c.left, Logic):
            raise ScriptError('this condition groups to the left, which the World Editor syntax cannot express')
        return '%s %s %s' % (self.cond(c.left, False), op, self.cond(c.right, False))

    def block(self, depth, b):
        self.emit(depth, self.open)
        for s in b.statements:
            self.statement(depth + 1, s)
        for c in b.tail:
            self.comment(depth + 1, c)
        self.emit(depth, self.close)

    def statement(self, depth, s):
        if s.blank_before:
            self.emit(0)
        for c in s.leading:
            self.comment(depth, c)
        tail = ('  // ' + s.trailing.text) if s.trailing is not None and s.trailing.text else ''
        if isinstance(s, Junk):
            for line in s.text:
                self.emit(depth, '// ' + line)
        elif isinstance(s, Do):
            cmd = s.command
            if self.dialect == ALACN and not cmd.get('alacn'):
                raise ScriptError('DO %s does not exist in the World Editor syntax' % cmd['name'], s.line)
            name = cmd['alacn'] if self.dialect == ALACN else cmd['name']
            self.emit(depth, ' '.join(['DO', name] + [self.value(a) for a in s.args]) + tail)
        elif isinstance(s, Assign):
            self.emit(depth, '%s %s %s' % (s.op, self.value(s.target), self.value(s.value)) + tail)
        elif isinstance(s, MulDiv):
            self.emit(depth, '%s %s %s %s' % (s.op, self.value(s.target), self.value(s.a), self.value(s.b)) + tail)
        elif isinstance(s, Every):
            self.emit(depth, 'EVERY %d' % s.period + ('' if s.offset is None else ' %d' % s.offset) + tail)
            self.block(depth, s.body)
        elif isinstance(s, If):
            c = self.cond(s.cond)
            self.emit(depth, 'IF ' + (c if self.dialect == BULLFROG else '( %s )' % c) + tail)
            self.block(depth, s.then)
            if s.orelse is not None:
                self.emit(depth, 'ELSE')
                self.block(depth, s.orelse)
            self.emit(depth, 'ENDIF')

    def text(self):
        sc = self.script
        for c in sc.header:
            self.comment(0, c)
        if self.dialect == BULLFROG:
            self.emit(0, 'COMPUTER_PLAYER %d' % (sc.player_number if sc.player_number is not None else 0))
        self.block(0, sc.body)
        self.emit(0, 'SCRIPT_END')
        for c in sc.footer:
            self.comment(0, c)
        return '\n'.join(self.out) + '\n'


def to_text(script, dialect=BULLFROG):
    """Script text in the given syntax ('bullfrog' or 'alacn')."""
    return Printer(script, dialect).text()

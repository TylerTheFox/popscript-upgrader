"""Syntax tree shared by every input format (Bullfrog text, World Editor text, compiled .DAT)."""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Comment:
    text: str                    # without the comment marker
    line: int
    blank_before: bool = False   # an empty line preceded it in the source


@dataclass
class Value:
    """One operand.

    kind: 'const'    value = integer
          'user'     name  = variable name, slot = index in the engine's array
          'internal' entry = row of the language table (INT_ name)
          'keyword'  entry = row of the keyword table (BLUE, ON, MARKER ...)
    """
    kind: str
    line: int = 0
    value: int = 0
    name: str = ''
    slot: int = -1
    entry: Optional[dict] = None

    def key(self):
        """Identity that does not depend on spelling (used to compare trees)."""
        if self.kind == 'const':
            return ('const', self.value)
        if self.kind == 'user':
            return ('user', self.slot)
        if self.kind == 'internal':
            return ('internal', self.entry['index'])
        return ('keyword', self.entry['token'])


@dataclass
class Statement:
    line: int = 0
    leading: List[Comment] = field(default_factory=list)   # comment lines above it
    trailing: Optional[Comment] = None                     # comment on the same line
    blank_before: bool = False
    end_line: int = 0
    notes: List[str] = field(default_factory=list)         # converter remarks, emitted as comments


@dataclass
class Block:
    statements: List[Statement] = field(default_factory=list)
    tail: List[Comment] = field(default_factory=list)       # comments before the closing END


@dataclass
class Junk(Statement):
    """Source text that is not part of the program (kept so it can be shown as a comment)."""
    text: List[str] = field(default_factory=list)
    why: str = ''


@dataclass
class Do(Statement):
    command: dict = None
    args: List[Value] = field(default_factory=list)


@dataclass
class Assign(Statement):
    op: str = 'SET'               # SET | INCREMENT | DECREMENT
    target: Value = None
    value: Value = None


@dataclass
class MulDiv(Statement):
    op: str = 'MULTIPLY'          # MULTIPLY | DIVIDE
    target: Value = None
    a: Value = None
    b: Value = None


@dataclass
class Test:
    op: str                       # > < == != >= <=
    a: Value
    b: Value


@dataclass
class Logic:
    op: str                       # AND | OR
    left: object
    right: object


@dataclass
class If(Statement):
    cond: object = None           # Test | Logic
    then: Block = None
    orelse: Optional[Block] = None


@dataclass
class Every(Statement):
    period: int = 0               # as written in the source (the bytecode stores period - 1)
    offset: Optional[int] = None  # as written in the source (the bytecode stores offset - 1)
    body: Block = None


@dataclass
class Script:
    dialect: str                  # 'bullfrog' | 'alacn' | 'compiled'
    source_name: str = ''
    player_number: Optional[int] = None    # COMPUTER_PLAYER n (informational)
    header: List[Comment] = field(default_factory=list)    # comments before the first BEGIN
    body: Block = None
    footer: List[Comment] = field(default_factory=list)    # comments after the last END
    variables: List[str] = field(default_factory=list)     # names by slot
    lines: List[str] = field(default_factory=list)         # the source text, for quoting
    warnings: List[str] = field(default_factory=list)


class ScriptError(Exception):
    def __init__(self, message, line=0, source=''):
        self.message, self.line, self.source = message, line, source
        where = source or 'script'
        super().__init__('%s:%d: %s' % (where, line, message) if line else '%s: %s' % (where, message))


# ---------------------------------------------------------------- comparison

def _cond_key(c):
    if isinstance(c, Test):
        return ('test', c.op, c.a.key(), c.b.key())
    return ('logic', c.op, _cond_key(c.left), _cond_key(c.right))


def _block_key(b):
    return tuple(_stmt_key(s) for s in b.statements if not isinstance(s, Junk))


def _stmt_key(s):
    if isinstance(s, Do):
        return ('do', s.command['token'], tuple(a.key() for a in s.args))
    if isinstance(s, Assign):
        return (s.op, s.target.key(), s.value.key())
    if isinstance(s, MulDiv):
        return (s.op, s.target.key(), s.a.key(), s.b.key())
    if isinstance(s, If):
        return ('if', _cond_key(s.cond), _block_key(s.then), _block_key(s.orelse) if s.orelse is not None else None)
    if isinstance(s, Every):
        return ('every', s.period, s.offset, _block_key(s.body))
    raise TypeError(s)


def structure(script):
    """A spelling-independent form of the whole program; equal structures run identically."""
    return _block_key(script.body)


def walk(block):
    """Every statement in a block, depth first, in source order."""
    for s in block.statements:
        if isinstance(s, Junk):
            continue
        yield s
        if isinstance(s, If):
            yield from walk(s.then)
            if s.orelse is not None:
                yield from walk(s.orelse)
        elif isinstance(s, Every):
            yield from walk(s.body)


def values_of(stmt):
    """Operands of one statement in the order the interpreter evaluates them (conditions included)."""
    if isinstance(stmt, Do):
        return list(stmt.args)
    if isinstance(stmt, Assign):
        return [stmt.target, stmt.value]
    if isinstance(stmt, MulDiv):
        return [stmt.target, stmt.a, stmt.b]
    if isinstance(stmt, If):
        out = []

        def go(c):
            if isinstance(c, Test):
                out.extend([c.a, c.b])
            else:
                go(c.left); go(c.right)
        go(stmt.cond)
        return out
    return []

"""Read a computer-player script written as text.

Two syntaxes compile to the same bytecode and are both accepted:

  Bullfrog (the 1998 compiler, CPSCRnnn.SCR)        World Editor (ALACN)
  ------------------------------------------        ----------------------------------
  COMPUTER_PLAYER 10                                 (no header)
  BEGIN ... END                                      { ... }
  IF (( A == 1 ) && ( B > 2 ))                       IF ( $a == 1 && $b > 2 )
  USER_NAME   (any word that is not INT_)            $name
  // comment                                         // comment   and   /* comment */
  case sensitive                                     not case sensitive
  WILD, MARKER, BUILDING, PERSON                     COUNT_WILD, ATTACK_MARKER, ...
  INT_MEDICINE_MAN, INT_TEPEE, ...                   INT_SHAMAN, INT_SMALL_HUT, ...

The parser is strict on purpose. Anything it does not understand is an error with a line
number, never a guess: a silently skipped token would change what the script does.
"""
import re

from .model import (Assign, Block, Comment, Do, Every, If, Junk, Logic, MulDiv, Script, ScriptError,
                    Test, Value)
from .tables import ALACN, BULLFROG, language

_INT = re.compile(r'^[+-]?\d+$')
_OPS = ('&&', '||', '==', '!=', '>=', '<=', '>', '<')
_RELOPS = ('>', '<', '==', '!=', '>=', '<=')
_SPLIT_OPS = re.compile(r'(&&|\|\||==|!=|>=|<=|>|<)')


class Tok:
    __slots__ = ('text', 'line', 'pre', 'blank_before')

    def __init__(self, text, line):
        self.text, self.line = text, line
        self.pre = []            # comments between the previous token and this one
        self.blank_before = False

    def __repr__(self):
        return '%r@%d' % (self.text, self.line)


def detect_dialect(text):
    """Tell the two syntaxes apart from the first meaningful word, then by their markers."""
    stripped = re.sub(r'/\*.*?\*/', ' ', text, flags=re.S)
    stripped = re.sub(r'//[^\n]*', ' ', stripped)
    words = stripped.split()
    if not words:
        raise ScriptError('the script is empty')
    if words[0] == '{':
        return ALACN
    if words[0] == 'COMPUTER_PLAYER':
        return BULLFROG
    bull = sum(1 for w in words if w in ('BEGIN', 'END', 'COMPUTER_PLAYER'))
    alac = sum(1 for w in words if w in ('{', '}') or w.startswith('$'))
    if bull and not alac:
        return BULLFROG
    if alac and not bull:
        return ALACN
    raise ScriptError('cannot tell which syntax this is: expected a script that starts with '
                      'COMPUTER_PLAYER (Bullfrog) or { (World Editor)')


def tokenize(text, dialect):
    """Split into tokens. Comments are kept, attached to the token that follows them."""
    toks = []
    pending = []                 # comments waiting for the next token
    in_block = False
    last_content_line = 0        # last line that held a token or a comment
    eof_blank = False

    def note_blank(lineno):
        return last_content_line and lineno - last_content_line > 1

    lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    for lineno, raw in enumerate(lines, 1):
        raw = raw.replace('\x1a', '')        # DOS end-of-file marker
        i, n = 0, len(raw)
        while i < n:
            if in_block:
                j = raw.find('*/', i)
                body = raw[i:] if j < 0 else raw[i:j]
                if body.strip():
                    pending.append(Comment(body.strip(), lineno, note_blank(lineno)))
                    last_content_line = lineno
                if j < 0:
                    i = n
                else:
                    in_block = False
                    i = j + 2
                continue
            ch = raw[i]
            if ch in ' \t\f\v':
                i += 1
                continue
            if raw.startswith('//', i):
                pending.append(Comment(raw[i + 2:].strip().expandtabs(4), lineno, note_blank(lineno)))
                last_content_line = lineno
                i = n
                continue
            if dialect == ALACN and raw.startswith('/*', i):
                in_block = True
                i += 2
                continue
            if ch in '()':
                word, i = ch, i + 1
            else:
                j = i
                while j < n and raw[j] not in ' \t\f\v()':
                    if raw.startswith('//', j) and (dialect == BULLFROG or j == i):
                        break
                    j += 1
                word, i = raw[i:j], j
            parts = [word]
            if dialect == BULLFROG and word not in '()':
                parts = [p for p in _SPLIT_OPS.split(word) if p]
            for p in parts:
                t = Tok(p, lineno)
                t.pre, pending = pending, []
                t.blank_before = bool(note_blank(lineno)) if not t.pre else t.pre[0].blank_before
                toks.append(t)
                last_content_line = lineno
    if in_block:
        raise ScriptError('a /* comment is never closed', len(lines))
    end = Tok('<end of file>', len(lines))
    end.pre = pending
    toks.append(end)
    return toks


class Parser:
    def __init__(self, text, dialect=None, source_name='', recover=False):
        self.lang = language()
        self.source_name = source_name
        # recover: keep going past text the compiler would have ignored or rejected. Only used
        # when a compiled script is at hand to say what the program really is.
        self.recover = recover
        self.lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
        try:
            self.dialect = dialect or detect_dialect(text)
            self.toks = tokenize(text, self.dialect)
        except ScriptError as e:
            raise ScriptError(e.message, e.line, source_name)
        self.pos = 0
        self.open, self.close = ('BEGIN', 'END') if self.dialect == BULLFROG else ('{', '}')
        self.slots = {}          # variable key -> slot
        self.names = []          # slot -> name as first written
        self.late = []           # variables read before any assignment (Bullfrog)
        self.warnings = []
        self.carry = []          # comments waiting to be attached to the next statement

    # ------------------------------------------------------------ helpers
    def err(self, msg, tok=None):
        tok = tok or self.peek()
        raise ScriptError(msg, tok.line, self.source_name)

    def peek(self):
        return self.toks[self.pos]

    def norm(self, text):
        return text.upper() if self.dialect == ALACN else text

    def next(self):
        t = self.toks[self.pos]
        if self.pos < len(self.toks) - 1:
            self.pos += 1
        return t

    def at(self, word):
        return self.norm(self.peek().text) == word

    def expect(self, word, what=None):
        t = self.peek()
        if self.norm(t.text) != word:
            self.err('expected %s but found %s' % (what or word, t.text), t)
        return self.next()

    def take_pre(self, tok):
        """Comments in front of `tok` (plus any carried over) become leading comments."""
        out = self.carry + tok.pre
        self.carry, tok.pre = [], []
        return out

    def split_trailing(self, last_tok):
        """A comment on the last line of a statement belongs to that statement."""
        nxt = self.peek()
        if nxt.pre and nxt.pre[0].line == last_tok.line:
            return nxt.pre.pop(0)
        return None

    # ------------------------------------------------------------- values
    def variable(self, tok, define):
        text = tok.text
        if self.dialect == ALACN:
            if not text.startswith('$') or len(text) < 2:
                self.err('expected a number, an INT_ variable or a $variable but found %s' % text, tok)
            if len(text) - 1 > 33:
                self.err('variable name %s is longer than 33 characters' % text, tok)
            key = text[1:].upper()
            shown = text[1:]
        else:
            if not (text[0].isalpha() or text[0] == '_'):
                self.err('expected a number or a variable but found %s' % text, tok)
            if self.lang.keyword(text, self.dialect) or text in self.lang.tokens or text in ('ON', 'OFF'):
                self.err('%s is a keyword and cannot be used as a value here' % text, tok)
            key = shown = text
        slot = self.slots.get(key)
        if slot is None:
            if self.dialect == BULLFROG and not define:
                # The 1998 compiler only creates a variable when it is first assigned.
                self.late.append((key, shown, tok.line))
                return Value('user', tok.line, name=shown, slot=-1)
            slot = len(self.names)
            self.slots[key] = slot
            self.names.append(shown)
        return Value('user', tok.line, name=self.names[slot], slot=slot)

    def value(self, define=False):
        tok = self.next()
        text = tok.text
        if tok.text == '<end of file>':
            self.err('the script ends in the middle of a statement', tok)
        if _INT.match(text):
            v = int(text)
            if not -2147483648 <= v <= 2147483647:
                self.err('number %s does not fit in 32 bits' % text, tok)
            return Value('const', tok.line, value=v)
        if self.norm(text).startswith('INT_'):
            e = self.lang.internal(text, self.dialect)
            if e is None:
                hint = self.lang.other_dialect_hint(text, self.dialect)
                self.err('unknown internal variable %s%s' % (text, ' (%s)' % hint if hint else ''), tok)
            return Value('internal', tok.line, entry=e)
        return self.variable(tok, define)

    def target(self):
        """First operand of SET / INCREMENT / DECREMENT / MULTIPLY / DIVIDE."""
        tok = self.peek()
        v = self.value(define=True)
        if v.kind == 'const':
            self.err('cannot assign to the number %s' % tok.text, tok)
        if v.kind == 'internal' and v.entry.get('kind') != 'attr':
            self.err('%s cannot be assigned: only INT_ATTR_ variables and script variables can' % tok.text, tok)
        return v

    def keyword_arg(self, kinds, what):
        tok = self.peek()
        k = self.lang.keyword(tok.text, self.dialect)
        if k is None or k['kind'] not in kinds:
            return None
        self.next()
        return Value('keyword', tok.line, entry=k)

    def argument(self, param, cmd):
        kind = param['kind']
        tok = self.peek()
        label = param.get('label') or kind
        if tok.text == '<end of file>' or self.norm(tok.text) in (self.close, 'DO', 'IF', 'SET', 'EVERY', 'ENDIF'):
            self.err('%s needs %d operand(s); "%s" is missing' % (cmd['name'], len(cmd['params']), label), tok)
        if kind == 'onoff':
            v = self.keyword_arg(('onoff',), 'ON or OFF')
            if v is None:
                self.err('%s needs ON or OFF here but found %s' % (cmd['name'], tok.text), tok)
            return v
        if kind in ('tribe', 'tribe_wild'):
            v = self.keyword_arg(('tribe', 'wild') if kind == 'tribe_wild' else ('tribe',), 'tribe')
            return v if v is not None else self.value()
        if kind in ('target_type', 'attack_type', 'guard_type', 'oneshot_type', 'vehicle_type'):
            v = self.keyword_arg((kind,), label)
            if v is None:
                names = [k['name'] if self.dialect == BULLFROG else k['alacn']
                         for k in self.lang.keywords if k['kind'] == kind]
                self.err('%s needs one of %s for "%s" but found %s' % (cmd['name'], ', '.join(names), label, tok.text), tok)
            return v
        if kind == 'var':
            v = self.value(define=True)
            if v.kind != 'user':
                self.err('%s stores its result in a script variable; %s is not one' % (cmd['name'], tok.text), tok)
            return v
        return self.value()

    # --------------------------------------------------------- conditions
    def relop(self):
        tok = self.next()
        if tok.text not in _RELOPS:
            self.err('expected a comparison (> < == != >= <=) but found %s' % tok.text, tok)
        return tok.text

    def test(self):
        first = self.peek()
        a = self.value()
        op = self.relop()
        b = self.value()
        if self.dialect == BULLFROG and a.kind == 'const':
            self.err('a comparison cannot start with a number (%s): the 1998 compiler drops the '
                     'right-hand side of such a test' % first.text, first)
        return Test(op, a, b)

    def logic_op(self):
        t = self.peek().text
        if t == '&&':
            self.next(); return 'AND'
        if t == '||':
            self.next(); return 'OR'
        return None

    def cond_bullfrog(self):
        """( value op value )  or  ( (cond) && (cond) )."""
        self.expect('(')
        if self.at('('):
            left = self.cond_bullfrog()
            op = self.logic_op()
            if op is not None:
                right = self.cond_bullfrog()
                extra = self.peek()
                if extra.text in ('&&', '||'):
                    self.err('three conditions are joined without brackets; write ((A && B) && C) or '
                             '(A && (B && C)) so the grouping is explicit', extra)
                left = Logic(op, left, right)
        else:
            left = self.test()
        self.expect(')')
        return left

    def cond_alacn(self):
        """( test { &&|| test } ), grouped to the right: A && B || C is A && (B || C)."""
        self.expect('(')
        tests, ops = [self.test()], []
        while True:
            op = self.logic_op()
            if op is None:
                break
            ops.append(op)
            tests.append(self.test())
        self.expect(')')
        node = tests[-1]
        for i in range(len(ops) - 1, -1, -1):
            node = Logic(ops[i], tests[i], node)
        return node

    # --------------------------------------------------------- statements
    def block(self):
        opener = self.expect(self.open)
        self.carry += opener.pre
        opener.pre = []
        b = Block()
        while True:
            t = self.peek()
            if self.norm(t.text) == self.close:
                b.tail = self.take_pre(t)
                self.next()
                return b
            if t.text == '<end of file>':
                if self.recover:
                    b.tail = self.take_pre(t)
                    return b
                self.err('%s is missing: the block opened on line %d is never closed' % (self.close, opener.line), t)
            if not self.recover:
                b.statements.append(self.statement())
                continue
            start = self.pos
            saved = (dict(self.slots), list(self.names), list(self.late), list(self.carry), list(t.pre))
            try:
                b.statements.append(self.statement())
            except ScriptError as e:
                self.pos = start
                self.slots, self.names, self.late, self.carry, t.pre = saved
                b.statements.append(self.junk(e.message))

    _STARTERS = ('DO', 'IF', 'SET', 'EVERY', 'INCREMENT', 'DECREMENT', 'MULTIPLY', 'DIVIDE')

    def junk(self, why):
        """Skip to the next thing that can start or end a statement; keep the text."""
        first = self.next()
        leading = self.take_pre(first)
        last = first
        while True:
            t = self.peek()
            w = self.norm(t.text)
            if t.text == '<end of file>' or w in self._STARTERS or w == self.close:
                break
            if w == self.open:                 # a stray block: skip it whole
                depth = 0
                while True:
                    t = self.peek()
                    w = self.norm(t.text)
                    if t.text == '<end of file>':
                        break
                    last = self.next()
                    if w == self.open:
                        depth += 1
                    elif w == self.close:
                        depth -= 1
                        if depth == 0:
                            break
                continue
            last = self.next()
        j = Junk(text=[l.strip() for l in self.lines[first.line - 1:last.line] if l.strip()], why=why)
        j.line, j.end_line, j.leading = first.line, last.line, leading
        j.blank_before = leading[0].blank_before if leading else first.blank_before
        return j

    def finish(self, stmt, first, leading):
        stmt.line = first.line
        stmt.end_line = self.toks[self.pos - 1].line
        stmt.leading = leading
        stmt.blank_before = leading[0].blank_before if leading else first.blank_before
        return stmt

    def statement(self):
        first = self.next()
        leading = self.take_pre(first)
        word = self.norm(first.text)

        if word == 'DO':
            name = self.next()
            cmd = self.lang.command(name.text, self.dialect)
            if cmd is None:
                hint = self.lang.other_dialect_hint(name.text, self.dialect)
                self.err('unknown command %s%s' % (name.text, ' (%s)' % hint if hint else ''), name)
            args = [self.argument(p, cmd) for p in cmd['params']]
            s = self.finish(Do(command=cmd, args=args), first, leading)
            s.trailing = self.split_trailing(self.toks[self.pos - 1])
            self.no_leftovers(cmd['name'])
            return s

        if word in ('SET', 'INCREMENT', 'DECREMENT'):
            target = self.target()
            value = self.value()
            s = self.finish(Assign(op=word, target=target, value=value), first, leading)
            s.trailing = self.split_trailing(self.toks[self.pos - 1])
            self.no_leftovers(word)
            return s

        if word in ('MULTIPLY', 'DIVIDE'):
            target = self.target()
            a = self.value()
            b = self.value()
            s = self.finish(MulDiv(op=word, target=target, a=a, b=b), first, leading)
            s.trailing = self.split_trailing(self.toks[self.pos - 1])
            self.no_leftovers(word)
            return s

        if word == 'EVERY':
            ptok = self.next()
            if not _INT.match(ptok.text):
                self.err('EVERY needs a number of turns but found %s' % ptok.text, ptok)
            period = int(ptok.text)
            if period < 2 or period & (period - 1):
                self.err('EVERY %d: the period must be a power of two (2, 4, 8 ... 8192)' % period, ptok)
            offset = None
            if _INT.match(self.peek().text):
                offset = int(self.next().text)
            s = self.finish(Every(period=period, offset=offset), first, leading)
            s.trailing = self.split_trailing(self.toks[self.pos - 1])
            s.body = self.block()
            return s

        if word == 'IF':
            cond = self.cond_bullfrog() if self.dialect == BULLFROG else self.cond_alacn()
            s = self.finish(If(cond=cond), first, leading)
            s.trailing = self.split_trailing(self.toks[self.pos - 1])
            s.then = self.block()
            if self.at('ELSE'):
                e = self.next()
                self.carry += e.pre
                e.pre = []
                s.orelse = self.block()
            end = self.expect('ENDIF', 'ENDIF to close the IF on line %d' % first.line)
            self.carry += end.pre
            end.pre = []
            return s

        hint = self.lang.other_dialect_hint(first.text, self.dialect)
        self.err('expected a statement (DO, IF, EVERY, SET, INCREMENT, DECREMENT, MULTIPLY, DIVIDE) '
                 'but found %s%s' % (first.text, ' (%s)' % hint if hint else ''), first)

    def no_leftovers(self, what):
        """Operands left over after a statement would be silently ignored by the engine."""
        t = self.peek()
        w = self.norm(t.text)
        stop = (self.close, 'DO', 'IF', 'SET', 'EVERY', 'INCREMENT', 'DECREMENT', 'MULTIPLY', 'DIVIDE', 'ELSE', 'ENDIF')
        if t.text == '<end of file>' or w in stop:
            return
        if not self.recover:
            self.err('%s has too many operands: %s is not expected here' % (what, t.text), t)
        # The 1998 compiler ignored words left over after a statement.
        extra = []
        while self.peek().text != '<end of file>' and self.norm(self.peek().text) not in stop:
            extra.append(self.next().text)
        self.warnings.append('line %d: ignored after %s: %s' % (t.line, what, ' '.join(extra)))

    # ------------------------------------------------------------- script
    def parse(self):
        script = Script(dialect=self.dialect, source_name=self.source_name)
        first = self.peek()
        script.header = self.take_pre(first)
        if self.dialect == BULLFROG:
            if self.at('COMPUTER_PLAYER'):
                self.next()
                n = self.next()
                if not _INT.match(n.text):
                    self.err('COMPUTER_PLAYER needs a number but found %s' % n.text, n)
                script.player_number = int(n.text)
                script.header += self.take_pre(self.peek())
        elif self.norm(first.text) == 'COMPUTER_PLAYER':
            self.err('COMPUTER_PLAYER is not part of the World Editor syntax; the script starts with {')
        script.body = self.block()
        t = self.peek()
        if self.at('SCRIPT_END'):
            script.footer = self.take_pre(t)
            self.next()
            script.footer += self.peek().pre
        elif t.text == '<end of file>':
            script.footer = self.take_pre(t)
            self.warnings.append('SCRIPT_END is missing at the end of the script')
        elif self.recover:
            self.warnings.append('line %d: text after the end of the program was ignored' % t.line)
            self.pos = len(self.toks) - 1
        else:
            self.err('expected SCRIPT_END after the last %s but found %s' % (self.close, t.text), t)
        # Bullfrog: variables that are read but never assigned get the slots after the assigned ones.
        if self.late:
            for key, shown, line in self.late:
                if key not in self.slots:
                    self.slots[key] = len(self.names)
                    self.names.append(shown)
                    self.warnings.append('line %d: variable %s is read but never assigned; it stays 0 '
                                         'unless the engine writes it' % (line, shown))
            self._resolve(script.body)
        if len(self.names) > 64:
            self.err('the script uses %d variables; the engine has room for 64' % len(self.names), self.toks[-1])
        script.variables = list(self.names)
        script.warnings = self.warnings
        script.lines = self.lines
        return script

    def _resolve(self, block):
        from .model import values_of, walk
        for s in walk(block):
            for v in values_of(s):
                if v.kind == 'user' and v.slot < 0:
                    v.slot = self.slots[v.name if self.dialect == BULLFROG else v.name.upper()]
                    v.name = self.names[v.slot]


def parse(text, dialect=None, source_name='', recover=False):
    return Parser(text, dialect, source_name, recover).parse()


def read_text(path):
    with open(path, 'rb') as f:
        raw = f.read()
    return raw.decode('utf-8-sig') if raw.startswith(b'\xef\xbb\xbf') else raw.decode('latin-1')


def parse_file(path, dialect=None, recover=False):
    import os
    return parse(read_text(path), dialect, os.path.basename(path), recover)

"""Make a parsed source script agree with the compiled script the game actually runs.

The text of a CPSCRnnn.SCR and the CPSCRnnn.DAT that ships with a level do not always say
the same thing:

  * The 1998 compiler did not terminate the buffer it converted numbers in, so some numbers
    picked up a stray extra digit (EVERY 2048 1088 was compiled as EVERY 2048 10881).
  * Words it did not recognise were silently dropped (a misspelt MULTPLY never ran).
  * Some sources were edited after the last compile.

The game runs the .DAT, so the .DAT decides what the program is. The source decides what it
is called: variable names, comments and layout come from the text. reconcile() walks both
trees together and returns the source tree changed to match the compiled one, with a note
on every statement that had to change. The result always has exactly the structure of the
compiled script; that is checked before it is returned.
"""
from difflib import SequenceMatcher

from .model import (Assign, Block, Do, Every, If, Junk, Logic, MulDiv, Script, ScriptError, Test,
                    structure, values_of, walk)


def _sig(s):
    """What a statement is, ignoring its operands (used to line the two programs up)."""
    if isinstance(s, Do):
        return ('do', s.command['token'])
    if isinstance(s, (Assign, MulDiv)):
        return (s.op, s.target.kind, s.target.entry['index'] if s.target.kind == 'internal' else None)
    if isinstance(s, If):
        return ('if',)
    if isinstance(s, Every):
        return ('every',)
    return ('junk', id(s))


def _show(v):
    if v.kind == 'const':
        return str(v.value)
    if v.kind == 'user':
        return v.name
    return v.entry['name']


class Reconciler:
    def __init__(self, src, dat):
        self.src, self.dat = src, dat
        self.name_of = {}        # compiled slot -> source name
        self.slot_of = {}        # source name -> compiled slot
        self.report = []         # human readable list of differences

    def note(self, stmt, line, text):
        stmt.notes.append(text)
        self.report.append('line %d: %s' % (line, text) if line else text)

    # ------------------------------------------------------------- values
    def value(self, sv, dv, stmt, line, what):
        """Return the operand to use: the compiled one, with the source's spelling if it agrees."""
        if sv.kind == 'user' and dv.kind == 'user':
            known = self.name_of.get(dv.slot)
            if known is None and sv.name not in self.slot_of:
                self.name_of[dv.slot] = sv.name
                self.slot_of[sv.name] = dv.slot
            elif known != sv.name:
                self.note(stmt, line, '%s: the compiled script uses a different variable here than the '
                                      'source (%s)' % (what, sv.name))
            return dv
        if sv.key() == dv.key():
            dv.line = sv.line
            return dv
        if sv.kind == 'const' and dv.kind == 'const':
            extra = ''
            if str(dv.value).startswith(str(sv.value)) and len(str(dv.value)) == len(str(sv.value)) + 1:
                extra = ' (the 1998 compiler appended a stray digit)'
            self.note(stmt, line, '%s: the source says %d; the compiled script, which is what the game '
                                  'runs, has %d%s' % (what, sv.value, dv.value, extra))
        else:
            self.note(stmt, line, '%s: the source says %s; the compiled script has %s' % (what, _show(sv), _show(dv)))
        return dv

    def cond(self, sc, dc, stmt, line):
        if isinstance(sc, Test) and isinstance(dc, Test) and sc.op == dc.op:
            dc.a = self.value(sc.a, dc.a, stmt, line, 'condition')
            dc.b = self.value(sc.b, dc.b, stmt, line, 'condition')
        elif isinstance(sc, Logic) and isinstance(dc, Logic) and sc.op == dc.op:
            self.cond(sc.left, dc.left, stmt, line)
            self.cond(sc.right, dc.right, stmt, line)
        else:
            self.note(stmt, line, 'the condition in the compiled script is not the one in the source')
        return dc

    # --------------------------------------------------------- statements
    def statement(self, s, d):
        """s and d have the same signature. Returns s, changed to mean what d means."""
        line = s.line
        if isinstance(s, Do):
            labels = [p.get('label') or p['kind'] for p in s.command['params']]
            s.args = [self.value(a, b, s, line, '%s "%s"' % (s.command['name'], labels[i]))
                      for i, (a, b) in enumerate(zip(s.args, d.args))]
        elif isinstance(s, Assign):
            s.target = self.value(s.target, d.target, s, line, s.op)
            s.value = self.value(s.value, d.value, s, line, s.op)
        elif isinstance(s, MulDiv):
            s.target = self.value(s.target, d.target, s, line, s.op)
            s.a = self.value(s.a, d.a, s, line, s.op)
            s.b = self.value(s.b, d.b, s, line, s.op)
        elif isinstance(s, Every):
            if (s.period, s.offset) != (d.period, d.offset):
                def fmt(e):
                    return 'EVERY %d' % e.period + ('' if e.offset is None else ' %d' % e.offset)
                extra = ''
                if s.offset is not None and d.offset is not None and str(d.offset).startswith(str(s.offset)):
                    extra = ' (the 1998 compiler appended a stray digit)'
                self.note(s, line, 'the source says %s; the compiled script, which is what the game runs, '
                                   'has %s%s' % (fmt(s), fmt(d), extra))
                s.period, s.offset = d.period, d.offset
            s.body = self.block(s.body, d.body)
        elif isinstance(s, If):
            s.cond = self.cond(s.cond, d.cond, s, line)
            s.then = self.block(s.then, d.then)
            if d.orelse is None:
                if s.orelse is not None and s.orelse.statements:
                    self.note(s, line, 'the ELSE block in the source is not in the compiled script')
                s.orelse = None
            elif s.orelse is None:
                self.note(s, line, 'the compiled script has an ELSE block that the source does not')
                s.orelse = d.orelse
            else:
                s.orelse = self.block(s.orelse, d.orelse)
        return s

    def only_in_source(self, s):
        """A source statement the compiled script does not contain: keep its text as a comment."""
        if isinstance(s, Junk):
            return s
        text = [l.strip() for l in self.src.lines[s.line - 1:max(s.end_line, s.line)] if l.strip()]
        if isinstance(s, (If, Every)):
            text = text[:1] + ['...']
        j = Junk(text=text, why='in the source but not in the compiled script')
        j.line, j.leading, j.trailing, j.blank_before = s.line, s.leading, s.trailing, s.blank_before
        self.report.append('line %d: not in the compiled script: %s' % (s.line, text[0] if text else ''))
        return j

    def only_in_compiled(self, d):
        d.notes.append('this statement is in the compiled script but not in the source text')
        self.report.append('a %s statement exists only in the compiled script' %
                           (d.command['name'] if isinstance(d, Do) else type(d).__name__.upper()))
        return d

    def block(self, sb, db):
        out = Block(tail=sb.tail)
        ss = sb.statements
        real = [s for s in ss if not isinstance(s, Junk)]
        sm = SequenceMatcher(a=[_sig(s) for s in real], b=[_sig(d) for d in db.statements], autojunk=False)
        merged = {}              # id(source statement) -> list of statements replacing it
        inserts = {}             # index in `real` -> compiled-only statements to put before it
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == 'equal':
                for k in range(i2 - i1):
                    merged[id(real[i1 + k])] = [self.statement(real[i1 + k], db.statements[j1 + k])]
            else:
                for k in range(i1, i2):
                    merged[id(real[k])] = [self.only_in_source(real[k])]
                if j2 > j1:
                    inserts.setdefault(i1, []).extend(self.only_in_compiled(d) for d in db.statements[j1:j2])
        idx = 0
        for s in ss:
            if isinstance(s, Junk):
                out.statements.append(s)
                continue
            out.statements.extend(inserts.pop(idx, []))
            out.statements.extend(merged[id(s)])
            idx += 1
        for k in sorted(inserts):
            out.statements.extend(inserts[k])
        return out

    # ------------------------------------------------------------- script
    def run(self):
        src, dat = self.src, self.dat
        body = self.block(src.body, dat.body)
        nslots = len(dat.variables)
        names, used = [], set()
        for slot in range(nslots):
            name = self.name_of.get(slot) or 'USER_%d' % slot
            while name in used:
                name += '_'
            used.add(name)
            names.append(name)
        out = Script(dialect=src.dialect, source_name=src.source_name, player_number=src.player_number,
                     header=src.header, body=body, footer=src.footer, variables=names, lines=src.lines)
        out.warnings = list(src.warnings)
        for s in walk(out.body):
            for v in values_of(s):
                if v.kind == 'user':
                    v.name = names[v.slot]
        if structure(out) != structure(dat):
            raise ScriptError('internal error: the reconciled script does not match the compiled one',
                              0, src.source_name)
        return out, self.report


def reconcile(src, dat):
    """(script, report): `src` rewritten to run exactly as the compiled `dat` does."""
    return Reconciler(src, dat).run()

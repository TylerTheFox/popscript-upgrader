"""Turn a script tree into Script4 Lua that uses the standard library (std.cpscript).

The output is one function per script, statement for statement in source order, so it runs
the way the bytecode did:

    IF / ELSE / ENDIF         if ... then ... else ... end
    EVERY 256 16              if ai:every(256, 16) then ... end
    SET / INCREMENT / ...     v.NAME = ...        (script variables, kept in the engine)
                              attr.NAME = ...     (INT_ATTR_ attributes)
    DO COMMAND a b c          the Script4 function for that command, arguments in its order
    INT_ values               the Script4 constant or getter with the same value

Things that need care to stay identical to the original are handled here, not left to the
reader of the output:

  * && and || evaluated both sides. Lua's `and` / `or` stop early, so a condition whose
    skipped side would have drawn a random number is written with cp.all / cp.any instead.
  * DIVIDE rounds toward zero and gives 0 when dividing by zero: cp.div.
  * Commands that stored exactly 1 or 0 keep doing so (cp.flag) where the Lua function
    returns a boolean or a flag bit.
  * After DO PARTIAL_BUILDING_COUNT the next building count includes buildings under
    construction. Scripts that use it read building counts through the engine's own
    evaluator (GET_INTERNAL_VARIABLE) so that rule stays with the engine.
"""
import re

from .model import Assign, Do, Every, If, Junk, Logic, MulDiv, ScriptError, Test, values_of, walk

VERSION = '2.0.0'
INDENT = '    '
WIDTH = 100

_LUA_KEYWORDS = {'and', 'break', 'do', 'else', 'elseif', 'end', 'false', 'for', 'function', 'goto', 'if', 'in',
                 'local', 'nil', 'not', 'or', 'repeat', 'return', 'then', 'true', 'until', 'while'}
_IDENT = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
_TRIBES = {0: 'TRIBE_BLUE', 1: 'TRIBE_RED', 2: 'TRIBE_YELLOW', 3: 'TRIBE_GREEN',
           4: 'TRIBE_CYAN', 5: 'TRIBE_PINK', 6: 'TRIBE_BLACK', 7: 'TRIBE_ORANGE'}
_TRIBE_WORD = {0: 'Blue', 1: 'Red (Dakini)', 2: 'Yellow (Chumara)', 3: 'Green (Matak)',
               4: 'Cyan', 5: 'Pink', 6: 'Black', 7: 'Orange'}
_LUA_REL = {'>': '>', '<': '<', '==': '==', '!=': '~=', '>=': '>=', '<=': '<='}

# DO GIVE_PLAYER_SPELL / REMOVE_PLAYER_THING look at which INT_ name was written.
_GIVE_SPELLS = {'INT_BURN', 'INT_BLAST', 'INT_LIGHTNING_BOLT', 'INT_WHIRLWIND', 'INT_INSECT_PLAGUE',
                'INT_INVISIBILITY', 'INT_HYPNOTISM', 'INT_FIRESTORM', 'INT_GHOST_ARMY', 'INT_EROSION', 'INT_SWAMP',
                'INT_LAND_BRIDGE', 'INT_ANGEL_OF_DEATH', 'INT_EARTHQUAKE', 'INT_FLATTEN', 'INT_VOLCANO',
                'INT_WRATH_OF_GOD', 'INT_SHIELD', 'INT_CONVERT', 'INT_TELEPORT', 'INT_BLOODLUST'}
_GIVE_BUILDINGS = {'INT_TEPEE', 'INT_HUT', 'INT_FARM', 'INT_DRUM_TOWER', 'INT_TEMPLE', 'INT_SPY_TRAIN',
                   'INT_WARRIOR_TRAIN', 'INT_SUPER_TRAIN', 'INT_BOAT_HUT_1', 'INT_AIRSHIP_HUT_1'}


def lua_string(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


def comment_text(text):
    """Comment text on one line; runs of tabs (column alignment in the source) become one space."""
    return re.sub(r'[ ]*\t+[ \t]*', ' ', text.replace('\r', ' ')).rstrip()


class Generator:
    def __init__(self, script, tribe, title=None, source_label=None, notes=()):
        self.script = script
        self.tribe = tribe
        self.title = title
        self.source_label = source_label or script.source_name or 'script'
        self.extra_notes = list(notes)
        self.out = []
        self.warnings = list(script.warnings)
        # A script that asks for partial building counts reads every building count through
        # the engine's evaluator, which applies and clears the one-shot flag.
        self.partial = any(isinstance(s, Do) and s.command.get('flag') == 'partial_count' for s in walk(script.body))

    # ------------------------------------------------------------- output
    def emit(self, depth, text=''):
        self.out.append((INDENT * depth + text).rstrip())

    def blank(self):
        # no blank line at the top of a block
        if self.out and self.out[-1] != '' and not self.out[-1].rstrip().endswith((' then', 'else', 'function()')):
            self.out.append('')

    def comments(self, depth, comments, allow_blank=True):
        for c in comments:
            if c.blank_before and allow_blank:
                self.blank()
            self.emit(depth, ('-- ' + comment_text(c.text)) if c.text else '--')

    # ------------------------------------------------------------- values
    def var(self, name):
        if _IDENT.match(name) and name not in _LUA_KEYWORDS:
            return 'v.' + name
        return 'v[%s]' % lua_string(name)

    def discarded(self, s):
        """Indexes of operands the interpreter evaluates but the Lua call does not use."""
        cmd = s.command
        special = cmd.get('special')
        if special == 'noop':
            return set(range(len(s.args)))
        if special in ('give', 'remove'):
            thing = s.args[1]
            if thing.kind != 'internal' or thing.entry['name'] not in (_GIVE_SPELLS | _GIVE_BUILDINGS):
                return {0, 1}
            return set()
        return set(i - 1 for i in cmd.get('ignored', []))

    def side_effect(self, v):
        if v.kind != 'internal':
            return False
        e = v.entry
        return bool(e.get('side_effect')) or (self.partial and e.get('building_count'))

    def value(self, v, kind='value'):
        if v.kind == 'local':
            return v.name
        if v.kind == 'const':
            if kind in ('tribe', 'tribe_wild') and v.value in _TRIBES:
                return _TRIBES[v.value]
            return str(v.value)
        if v.kind == 'user':
            return self.var(v.name)
        if v.kind == 'keyword':
            return v.entry['lua']
        e = v.entry
        if e['kind'] == 'attr':
            return 'attr.' + e['lua'][len('ATTR_'):]
        if e['kind'] == 'const':
            return e['lua']
        if self.partial and e.get('building_count'):
            return 'GET_INTERNAL_VARIABLE(me, %s)' % e['name']
        return e['lua'].replace('{me}', 'me')

    def target(self, v):
        if v.kind == 'user':
            return self.var(v.name)
        return 'attr.' + v.entry['lua'][len('ATTR_'):]

    # --------------------------------------------------------- conditions
    def test(self, t):
        return '%s %s %s' % (self.value(t.a), _LUA_REL[t.op], self.value(t.b))

    def cond_has_side_effect(self, c):
        if isinstance(c, Test):
            return self.side_effect(c.a) or self.side_effect(c.b)
        return self.cond_has_side_effect(c.left) or self.cond_has_side_effect(c.right)

    def needs_full_evaluation(self, c):
        """True if Lua's short-circuit could skip (or reorder) a read that has a side effect."""
        if isinstance(c, Test):
            return False
        if self.cond_has_side_effect(c.right):
            return True
        return self.needs_full_evaluation(c.left)

    def cond(self, c, full=False, top=True):
        if isinstance(c, Test):
            return self.test(c)
        if full:
            # cp.all / cp.any receive finished values: every test is evaluated, left to right.
            fn = 'cp.all' if c.op == 'AND' else 'cp.any'
            return '%s(%s, %s)' % (fn, self.cond(c.left, True, False), self.cond(c.right, True, False))
        word = 'and' if c.op == 'AND' else 'or'
        parts = []
        for child in (c.left, c.right):
            text = self.cond(child, False, False)
            if isinstance(child, Logic) and child.op != c.op:
                text = '(' + text + ')'
            parts.append(text)
        return '%s %s %s' % (parts[0], word, parts[1])

    # ----------------------------------------------------------- commands
    def call(self, depth, text):
        """Emit a call, wrapping long argument lists under the opening bracket."""
        line = INDENT * depth + text
        if len(line) <= WIDTH or '(' not in text:
            self.emit(depth, text)
            return
        head, rest = text.split('(', 1)
        # split top-level arguments
        args, cur, level = [], '', 0
        body, tail = rest.rsplit(')', 1)
        for ch in body:
            if ch == '(':
                level += 1
            elif ch == ')':
                level -= 1
            if ch == ',' and level == 0:
                args.append(cur.strip()); cur = ''
            else:
                cur += ch
        args.append(cur.strip())
        pad = ' ' * (len(head) + 1)
        cur = head + '('
        first = True
        for i, a in enumerate(args):
            piece = a + (', ' if i < len(args) - 1 else ')' + tail)
            if not first and len(INDENT * depth + cur + piece.rstrip()) > WIDTH:
                self.emit(depth, cur.rstrip())
                cur = pad
            cur += piece
            first = False
        self.emit(depth, cur)

    def fill(self, template, s):
        params = s.command['params']

        def repl(m):
            mode, n = m.group(1), int(m.group(2))
            arg, kind = s.args[n - 1], params[n - 1]['kind']
            text = self.value(arg, kind)
            if mode == 'tooltip':
                if arg.kind == 'const':
                    return str({0: 1, 1: 2}.get(arg.value, arg.value))
                return 'cp.tooltip_code(%s)' % text
            if mode == 'seconds':
                if arg.kind == 'const' and abs(arg.value) < (1 << 23):
                    return '%s * GET_TURNS_PER_SECOND()' % text
                # the interpreter multiplied in 32 bits
                return 'cp.int32(%s * GET_TURNS_PER_SECOND())' % text
            return text
        text = template.replace('{me}', 'me')
        return re.sub(r'\{(?:([a-z]+):)?(\d+)\}', repl, text)

    def do(self, depth, s):
        cmd = s.command
        name = cmd['name']
        special = cmd.get('special')
        if special == 'unsupported':
            raise ScriptError('DO %s cannot be converted: %s' % (name, cmd['why']), s.line, self.script.source_name)
        if special == 'noop':
            self.emit(depth, '-- DO %s: %s' % (name, cmd['why']))
            return
        if special == 'attack_var':
            self.emit(depth, 'SET_ATTACK_VARIABLE(me, ai:slot(%s))' % lua_string(s.args[0].name))
            return
        if special in ('give', 'remove'):
            tribe, thing = s.args
            if thing.kind != 'internal' or thing.entry['name'] not in (_GIVE_SPELLS | _GIVE_BUILDINGS):
                # The interpreter only acts on spell and building names; anything else does nothing.
                self.emit(depth, '-- DO %s: the original engine ignores a second operand that is not a spell '
                                 'or building name' % name)
                return
            is_spell = thing.entry['name'] in _GIVE_SPELLS
            fn = {('give', True): 'set_player_can_cast', ('give', False): 'set_player_can_build',
                  ('remove', True): 'set_player_cannot_cast', ('remove', False): 'set_player_cannot_build'}[(special, is_spell)]
            self.emit(depth, '%s(%s, %s)' % (fn, self.value(thing), self.value(tribe, 'tribe')))
            return
        if special == 'preached':
            flag, x, z = (self.var(a.name) for a in s.args)
            self.emit(depth, 'do')
            self.emit(depth + 1, 'local pos = CHECK_IF_PERSON_PREACHED_TO(TRIBE_BLUE)')
            self.emit(depth + 1, 'if pos ~= -1 then')
            # one store at a time, in the original order (the same variable may be named twice)
            self.emit(depth + 2, '%s = 1' % flag)
            self.emit(depth + 2, '%s = pos %% 256' % x)
            self.emit(depth + 2, '%s = pos // 256' % z)
            self.emit(depth + 1, 'else')
            self.emit(depth + 2, '%s = 0' % flag)
            self.emit(depth + 1, 'end')
            self.emit(depth, 'end')
            return
        if 'set' in cmd:
            expr = self.fill(cmd['expr'], s)
            if cmd.get('norm'):
                expr = 'cp.flag(%s)' % expr
            self.call(depth, '%s = %s' % (self.var(s.args[cmd['set'] - 1].name), expr))
            return
        self.call(depth, self.fill(cmd['call'], s))

    # --------------------------------------------------------- statements
    def statement(self, depth, s):
        if s.blank_before:
            self.blank()
        self.comments(depth, s.leading, allow_blank=False)
        if isinstance(s, (Do, MulDiv)):
            self.check_order(s)
        for n in s.notes:
            self.emit(depth, '-- NOTE: ' + n)
        start = len(self.out)

        if isinstance(s, Junk):
            self.emit(depth, '-- Not part of the program (%s):' % s.why)
            for line in s.text:
                self.emit(depth, '--   ' + comment_text(line.expandtabs(4)))
        elif isinstance(s, Do):
            if any(self.side_effect(s.args[i]) for i in self.discarded(s)):
                # An operand with a side effect (a random number, a one-shot count) is evaluated
                # by the interpreter and then not used. Evaluate every such operand here, in
                # the original order, so the same numbers are drawn.
                from .model import Value
                self.emit(depth, 'do')
                args, n = [], 0
                for i, a in enumerate(s.args):
                    if self.side_effect(a):
                        n += 1
                        note = '  -- evaluated and not used, as in the original' if i in self.discarded(s) else ''
                        self.emit(depth + 1, 'local r%d = %s%s' % (n, self.value(a), note))
                        a = Value('local', a.line, name='r%d' % n)
                    args.append(a)
                self.do(depth + 1, Do(command=s.command, args=args, line=s.line))
                self.emit(depth, 'end')
            else:
                self.do(depth, s)
        elif isinstance(s, (Assign, MulDiv)) and s.target.kind == 'internal' and s.target.entry['kind'] != 'attr':
            # Only script variables and INT_ATTR_ attributes can be written. The interpreter
            # evaluates the operands of such a statement and then stores nothing.
            self.emit(depth, '-- %s %s: the engine ignores assignments to this variable' % (s.op, s.target.entry['name']))
            for v in ([s.value] if isinstance(s, Assign) else [s.a, s.b]):
                if self.side_effect(v):
                    self.emit(depth, 'local _ = %s  -- still evaluated, as the original did' % self.value(v))
        elif isinstance(s, Assign):
            t = self.target(s.target)
            val = self.value(s.value)
            if s.op == 'SET':
                self.emit(depth, '%s = %s' % (t, val))
            else:
                self.emit(depth, '%s = %s %s %s' % (t, t, '+' if s.op == 'INCREMENT' else '-', val))
        elif isinstance(s, MulDiv):
            t = self.target(s.target)
            a, b = self.value(s.a), self.value(s.b)
            if s.op == 'MULTIPLY':
                self.emit(depth, '%s = %s * %s' % (t, a, b))
            else:
                self.emit(depth, '%s = cp.div(%s, %s)' % (t, a, b))
        elif isinstance(s, Every):
            args = str(s.period) if s.offset is None else '%d, %d' % (s.period, s.offset)
            self.emit(depth, 'if ai:every(%s) then' % args)
            self.attach_trailing(s, start)
            self.block(depth + 1, s.body)
            self.emit(depth, 'end')
            return
        elif isinstance(s, If):
            full = self.needs_full_evaluation(s.cond)
            self.emit(depth, 'if %s then' % self.cond(s.cond, full))
            self.attach_trailing(s, start)
            self.block(depth + 1, s.then)
            node = s
            while node.orelse is not None:
                inner = self.sole_if(node.orelse)
                if inner is None:
                    self.emit(depth, 'else')
                    self.block(depth + 1, node.orelse)
                    break
                # ELSE BEGIN IF ... ENDIF END is the same program as elseif
                at = len(self.out)
                self.emit(depth, 'elseif %s then' % self.cond(inner.cond, self.needs_full_evaluation(inner.cond)))
                self.attach_trailing(inner, at)
                self.block(depth + 1, inner.then)
                node = inner
            self.emit(depth, 'end')
            return
        self.attach_trailing(s, start)

    @staticmethod
    def sole_if(block):
        """The IF that is the whole of an ELSE block, if nothing else (not even a comment) is in it."""
        if len(block.statements) != 1 or block.tail:
            return None
        s = block.statements[0]
        if not isinstance(s, If) or s.leading or s.notes:
            return None
        return s

    def check_order(self, s):
        """Two side-effecting reads in one statement: Lua evaluates arguments left to right,
        which is the interpreter's order too, but say so in the output."""
        if sum(1 for v in values_of(s) if self.side_effect(v)) > 1:
            s.notes.append('more than one random or one-shot value is read here; they are read left to right, '
                           'as the original did')

    def attach_trailing(self, s, start):
        if s.trailing is not None and s.trailing.text and start < len(self.out):
            self.out[start] += '  -- ' + comment_text(s.trailing.text)

    def block(self, depth, block):
        before = len(self.out)
        for s in block.statements:
            self.statement(depth, s)
        self.comments(depth, block.tail)
        if len(self.out) == before:
            return

    # ------------------------------------------------------------- script
    def generate(self):
        script = self.script
        tribe = self.tribe
        tribe_const = _TRIBES.get(tribe, str(tribe))
        dialect = {'bullfrog': 'Bullfrog script', 'alacn': 'World Editor script', 'compiled': 'compiled script'}[script.dialect]
        self.emit(0, '--[[')
        if self.title:
            self.emit(0, '  ' + self.title)
        self.emit(0, '  Computer player script for the %s tribe.' % _TRIBE_WORD.get(tribe, 'tribe %d' % tribe))
        self.emit(0, '')
        self.emit(0, '  Converted from %s (%s) by popscript-upgrader %s.' % (self.source_label, dialect, VERSION))
        self.emit(0, '  It runs once per game turn, top to bottom, exactly as the original did.')
        for n in self.extra_notes:
            self.emit(0, '')
            for line in n.split('\n'):
                self.emit(0, '  ' + line)
        self.emit(0, ']]')
        self.emit(0)
        self.emit(0, 'include("std/v0.0.1/init.lua")')
        self.emit(0, 'std.install()')
        self.emit(0)
        self.emit(0, 'local cp = std.cpscript')
        if script.variables:
            self.emit(0, 'local ai = cp.new(%s, {' % tribe_const)
            self.emit(1, 'source = %s,' % lua_string(script.source_name or self.source_label))
            self.emit(1, 'vars = {')
            line = ''
            for name in script.variables:
                piece = lua_string(name) + ', '
                if len(INDENT * 2 + line + piece) > WIDTH:
                    self.emit(2, line.rstrip())
                    line = ''
                line += piece
            if line:
                self.emit(2, line.rstrip())
            self.emit(1, '},')
            self.emit(0, '})')
        else:
            self.emit(0, 'local ai = cp.new(%s, { source = %s })' % (tribe_const, lua_string(script.source_name or self.source_label)))
        used_attr = any(v.kind == 'internal' and v.entry['kind'] == 'attr' for s in walk(script.body) for v in values_of(s))
        names = ['me']
        exprs = ['ai.tribe']
        if script.variables:
            names.append('v'); exprs.append('ai.vars')
        if used_attr:
            names.append('attr'); exprs.append('ai.attr')
        self.emit(0, 'local %s = %s' % (', '.join(names), ', '.join(exprs)))
        self.emit(0)
        if script.header:
            self.comments(0, script.header)
            self.emit(0)
        self.emit(0, 'ai:run(function()')
        self.block(1, script.body)
        self.emit(0, 'end)')
        if script.footer:
            self.emit(0)
            self.comments(0, script.footer)
        return '\n'.join(self.out) + '\n'


def generate(script, tribe, title=None, source_label=None, notes=()):
    """Lua source for `script` driving tribe number `tribe`."""
    g = Generator(script, tribe, title, source_label, notes)
    text = g.generate()
    return text, g.warnings

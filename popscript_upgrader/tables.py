"""The language table: every command, internal variable and keyword of the 1998 script
language, with its bytecode value and its Script4 (Lua) equivalent.

data/language.json is the single source of truth. Each Lua call in it was checked against the
engine source: the interpreter's handler for the command (Source/Script.cpp) and the body of
the Lua binding (Source/Script4_PopScript.cpp). tools/verify_tables.py re-checks the argument
counts against an engine checkout.
"""
import json
import os

_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'language.json')

BULLFROG = 'bullfrog'
ALACN = 'alacn'
COMPILED = 'compiled'


class Language:
    def __init__(self, path=_PATH):
        with open(path, encoding='utf-8') as f:
            d = json.load(f)
        self.tokens = d['tokens']
        self.script_version = d['script_version']
        self.commands = d['commands']
        self.internals = d['internals']
        self.keywords = d['keywords']

        self.command_by_token = {c['token']: c for c in self.commands}
        self.internal_by_index = {i['index']: i for i in self.internals}
        self.keyword_by_token = {k['token']: k for k in self.keywords}

        # Bullfrog names are case sensitive; the World Editor compares without case.
        self._cmd = {BULLFROG: {c['name']: c for c in self.commands}, ALACN: {}}
        self._int = {BULLFROG: {i['name']: i for i in self.internals}, ALACN: {}}
        self._kw = {BULLFROG: {k['name']: k for k in self.keywords}, ALACN: {}}
        for c in self.commands:
            self._cmd[ALACN][c['name'].upper()] = c
            if c.get('alacn'):
                self._cmd[ALACN][c['alacn'].upper()] = c
        for i in self.internals:
            self._int[ALACN].setdefault(i['name'].upper(), i)
        for i in self.internals:                      # World Editor spellings win in that dialect
            if i.get('alacn'):
                self._int[ALACN][i['alacn'].upper()] = i
        for k in self.keywords:
            self._kw[ALACN][k['name'].upper()] = k
            self._kw[ALACN][k['alacn'].upper()] = k

    def command(self, name, dialect):
        return self._cmd[dialect].get(name.upper() if dialect == ALACN else name)

    def internal(self, name, dialect):
        return self._int[dialect].get(name.upper() if dialect == ALACN else name)

    def keyword(self, name, dialect):
        return self._kw[dialect].get(name.upper() if dialect == ALACN else name)

    def other_dialect_hint(self, name, dialect):
        """If `name` is a spelling from the other dialect, say what it is called here."""
        other = ALACN if dialect == BULLFROG else BULLFROG
        for table, field in ((self._cmd, 'command'), (self._int, 'variable'), (self._kw, 'keyword')):
            e = table[other].get(name.upper() if other == ALACN else name)
            if e:
                here = e['name'] if dialect == BULLFROG else (e.get('alacn') or e['name'])
                return '%s is the %s spelling; this file is in %s syntax, where it is %s' % (
                    name, 'World Editor' if other == ALACN else 'Bullfrog',
                    'World Editor' if dialect == ALACN else 'Bullfrog', here)
        return None


_default = None


def language():
    global _default
    if _default is None:
        _default = Language()
    return _default

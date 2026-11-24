"""Command line for popscript-upgrader.

  convert   one script (text and/or compiled) -> one Lua file
  level     every computer tribe of the given level(s) of a game or mod folder
  all       every level of a game or mod folder
  custom    a level described by a pasted or custom header plus your own scripts
  check     read a script and report problems without writing anything
  text      write a script out as script text (decompile a .DAT, or change syntax)
"""
import argparse
import os
import sys

from . import luagen
from .level import LevelHeader, find_level_header, level_names, read_header
from .model import ScriptError
from .project import build_script, convert_game, convert_level
from .tables import ALACN, BULLFROG

SYNTAX = {'bullfrog': BULLFROG, 'worldeditor': ALACN, 'alacn': ALACN, 'auto': None}


def parse_levels(text):
    out = []
    for part in text.split(','):
        if '-' in part:
            a, b = part.split('-', 1)
            out.extend(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return out


def split_inputs(paths):
    """Sort the given files into (source, compiled) by looking at their contents."""
    from .compiled import looks_compiled
    src = dat = None
    for p in paths:
        with open(p, 'rb') as f:
            head = f.read(12552)
        if looks_compiled(head):
            dat = p
        else:
            src = p
    return src, dat


def cmd_convert(a):
    src, dat = split_inputs(a.script + ([a.dat] if a.dat else []))
    script, report = build_script(src, dat, SYNTAX[a.syntax])
    notes = []
    if src and dat and report:
        notes.append('The source text and the compiled script differ in %d place(s).\n'
                     'This file follows the compiled script; each place is marked NOTE below.' % len(report))
    text, warnings = luagen.generate(script, a.tribe, title=a.title, notes=notes,
                                     source_label=' + '.join(os.path.basename(p) for p in (src, dat) if p))
    if a.output:
        with open(a.output, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
        print('wrote %s (%d lines, %d variable(s))' % (a.output, text.count('\n'), len(script.variables)))
    else:
        sys.stdout.write(text)
    out = sys.stderr if not a.output else sys.stdout
    for r in report:
        print('difference: ' + r, file=out)
    for w in warnings:
        print('warning: ' + w, file=out)
    return 0


def cmd_check(a):
    src, dat = split_inputs(a.script)
    script, report = build_script(src, dat, SYNTAX[a.syntax])
    luagen.generate(script, 1)
    kinds = {'bullfrog': 'Bullfrog', 'alacn': 'World Editor', 'compiled': 'compiled'}
    print('%s: %s syntax, %d variable(s), converts cleanly' % (script.source_name, kinds[script.dialect], len(script.variables)))
    for r in report:
        print('difference: ' + r)
    for w in script.warnings:
        print('warning: ' + w)
    return 0


def cmd_text(a):
    from .printer import to_text
    src, dat = split_inputs(a.script)
    script, report = build_script(src, dat, SYNTAX[a.syntax])
    text = to_text(script, ALACN if a.to in ('worldeditor', 'alacn') else BULLFROG)
    if a.output:
        with open(a.output, 'w', encoding='utf-8', newline='\r\n') as f:
            f.write(text)
        print('wrote %s' % a.output)
    else:
        sys.stdout.write(text)
    for r in report:
        print('difference: ' + r, file=sys.stderr)
    return 0


def summarise(results):
    levels = sum(1 for r in results if r['tribes'])
    files = sum(len(r['tribes']) for r in results)
    problems = sum(len(r['problems']) for r in results)
    print('\n%d level(s), %d script file(s) written, %d problem(s)' % (levels, files, problems))
    return 1 if problems else 0


def cmd_level(a):
    return summarise(convert_game(a.game, a.output, parse_levels(a.levels), a.scripts, a.scripts_root))


def cmd_all(a):
    return summarise(convert_game(a.game, a.output, None, a.scripts, a.scripts_root))


def cmd_custom(a):
    if a.header:
        header = read_header(a.header)
    else:
        if not a.tribe:
            raise ScriptError('give --header, or one or more --tribe N=SCRIPT')
        header = LevelHeader(bytes(88) + bytes([4, 0, 0, 0]) + bytes(8), 'command line')
    for item in a.tribe or []:
        tribe, _, script_no = item.partition('=')
        tribe, script_no = int(tribe), int(script_no)
        if not 1 <= tribe <= 3:
            raise ScriptError('--tribe %s: the game runs scripts for tribes 1, 2 and 3 only' % item)
        header.script_index[tribe - 1] = script_no
        header.num_players = max(header.num_players, tribe + 1)
    name = a.name or header.name or None
    print('header: %d player(s), scripts for tribes 1-3: %s' % (header.num_players, header.script_index))
    r = convert_level(a.number, header, a.game or a.scripts, a.output, name, a.scripts, a.scripts_root)
    for t in r['tribes']:
        print('tribe %d <- CPSCR%03d -> %s%s' % (t['tribe'], t['script'], os.path.join(r['folder'], t['file']),
                                                 '   [%d difference(s) from source]' % len(t['differences']) if t['differences'] else ''))
    for p in r['problems']:
        print('! ' + p)
    return 1 if r['problems'] and not r['tribes'] else 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog='popscript-upgrader', description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--version', action='version', version='popscript-upgrader ' + luagen.VERSION)
    sub = ap.add_subparsers(dest='command', required=True)

    def common(p):
        p.add_argument('--syntax', choices=sorted(SYNTAX), default='auto',
                       help='syntax of the script text (default: detect)')

    p = sub.add_parser('convert', help='convert one script')
    p.add_argument('script', nargs='+', help='CPSCRnnn.SCR and/or CPSCRnnn.DAT (give both to check the text against the compiled script)')
    p.add_argument('--dat', help='compiled script to check the text against')
    p.add_argument('--tribe', type=int, default=1, help='tribe number the script drives (1 red, 2 yellow, 3 green; default 1)')
    p.add_argument('--title', help='first line of the header comment')
    p.add_argument('-o', '--output', help='output file (default: standard output)')
    common(p)
    p.set_defaults(fn=cmd_convert)

    p = sub.add_parser('check', help='read a script and report problems')
    p.add_argument('script', nargs='+')
    common(p)
    p.set_defaults(fn=cmd_check)

    p = sub.add_parser('text', help='write a script as text: decompile a .DAT or change syntax')
    p.add_argument('script', nargs='+')
    p.add_argument('--to', choices=['bullfrog', 'worldeditor'], default='bullfrog', help='syntax to write (default bullfrog)')
    p.add_argument('-o', '--output')
    common(p)
    p.set_defaults(fn=cmd_text)

    def game_args(p):
        p.add_argument('--game', required=True, help='game or mod folder (the one that holds levels/)')
        p.add_argument('--scripts', help='folder with CPSCRnnn.SCR sources (default: <game>/CpScript)')
        p.add_argument('-o', '--output', required=True, help='folder to write the level folders into')
        p.add_argument('--scripts-root', help="the game's Scripts folder, if the output is not inside one")

    p = sub.add_parser('level', help='convert the scripts of one or more levels')
    p.add_argument('levels', help='level numbers, e.g. 1 or 1-25 or 3,7,12')
    game_args(p)
    p.set_defaults(fn=cmd_level)

    p = sub.add_parser('all', help='convert every level of a game or mod folder')
    game_args(p)
    p.set_defaults(fn=cmd_all)

    p = sub.add_parser('custom', help='convert a custom level from its header and your scripts')
    p.add_argument('--header', help='level header: a .HDR or .DAT file, a text file with a pasted hex dump or base64, or - to paste on standard input')
    p.add_argument('--tribe', action='append', metavar='N=SCRIPT', help='say which script a tribe runs, e.g. --tribe 1=10 (overrides the header)')
    p.add_argument('--scripts', required=True, help='folder with your CPSCRnnn.SCR and/or CPSCRnnn.DAT files')
    p.add_argument('--game', help='game folder to fall back on for scripts not in --scripts')
    p.add_argument('--number', type=int, default=1, help='level number, used for the folder name and the run command')
    p.add_argument('--name', help='level name (default: the name in the header)')
    p.add_argument('-o', '--output', required=True)
    p.add_argument('--scripts-root')
    p.set_defaults(fn=cmd_custom)

    a = ap.parse_args(argv)
    try:
        return a.fn(a)
    except ScriptError as e:
        print('error: %s' % e, file=sys.stderr)
        return 2
    except FileNotFoundError as e:
        print('error: %s' % e, file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())

"""Convert whole levels: one folder per level, one Lua file per computer tribe.

    <out>/lvl01_the_journey_begins/
        ai_p1.lua       the script for tribe 1 (red)
        harness.lua     loads the files above; point the game at this one

which is the layout of Scripts/std/v0.0.1/test/sp_campaign in the game.
"""
import os
import re

from . import compiled, luagen, source
from .level import find_level_header, find_script_files, level_names, list_levels
from .model import ScriptError
from .reconcile import reconcile

TRIBE_NAMES = {1: 'Red', 2: 'Yellow', 3: 'Green'}


def build_script(src_path=None, dat_path=None, dialect=None):
    """(script, report) from a source file, a compiled file, or both.

    With both, the compiled file decides what the program is and the source supplies names
    and comments (see reconcile.py). `report` lists every place the two disagreed.
    """
    dat = None
    report = []
    if dat_path:
        try:
            dat = compiled.decode_file(dat_path)
        except ScriptError as e:
            if not src_path:
                raise
            report.append('the compiled file was not used: %s' % e.message)
    if src_path and dat is not None:
        try:
            src = source.parse_file(src_path, dialect, recover=True)
        except ScriptError as e:
            report.append('the source text could not be read (%s); converted from the compiled script alone' % e)
            return dat, report
        script, diffs = reconcile(src, dat)
        return script, report + diffs
    if src_path:
        return source.parse_file(src_path, dialect), report
    if dat is None:
        raise ScriptError('no script given')
    return dat, report


def slug(text):
    s = re.sub(r'[^a-z0-9]+', '_', text.lower()).strip('_')
    return s[:48].rstrip('_')


def level_folder(number, name):
    base = 'lvl%02d' % number
    s = slug(name or '')
    return base + ('_' + s if s else '')


def include_prefix(out_dir, scripts_root=None):
    """Path of out_dir relative to the game's Scripts folder, as include() wants it."""
    out_dir = os.path.abspath(out_dir)
    if scripts_root:
        rel = os.path.relpath(out_dir, os.path.abspath(scripts_root))
        if not rel.startswith('..'):
            return '' if rel == '.' else rel.replace('\\', '/')
    parts = out_dir.replace('\\', '/').split('/')
    for i in range(len(parts) - 1, -1, -1):
        if parts[i].lower() == 'scripts':
            return '/'.join(parts[i + 1:])
    return None


def describe(src_path, dat_path):
    if src_path and dat_path:
        return '%s, checked against %s' % (os.path.basename(src_path), os.path.basename(dat_path))
    return os.path.basename(src_path or dat_path)


def convert_level(number, header, game_root, out_root, name=None, scripts_dir=None, scripts_root=None, log=print):
    """Write the folder for one level. Returns a dict describing what was written."""
    title = 'Level %d' % number + (': %s' % name if name else '')
    folder = os.path.join(out_root, level_folder(number, name))
    result = {'level': number, 'name': name, 'folder': folder, 'tribes': [], 'problems': [], 'absent': [], 'differences': 0}
    written = []
    for tribe, script_no in header.tribes():
        src_paths, dat_path = find_script_files(game_root, script_no, scripts_dir)
        if not src_paths and not dat_path:
            result['absent'].append('tribe %d: the header names script %d but CPSCR%03d is not there; the game runs '
                                    'no script for this tribe' % (tribe, script_no, script_no))
            continue
        src_path = src_paths[0] if src_paths else None
        try:
            script, report = build_script(src_path, dat_path)
            for other in src_paths[1:]:              # several sources: keep the one closest to the compiled script
                if not report:
                    break
                try:
                    s2, r2 = build_script(other, dat_path)
                except ScriptError:
                    continue
                if len(r2) < len(report):
                    script, report, src_path = s2, r2, other
            notes = []
            if src_path and dat_path and report:
                notes.append('The source text and the compiled script the game runs differ in %d place(s).\n'
                             'This file follows the compiled script; each place is marked NOTE below.' % len(report))
            elif dat_path and not src_path:
                notes.append('Only the compiled script exists, so variables are named by slot (USER_0, USER_1 ...)\n'
                             'and there are no comments.')
            text, warnings = luagen.generate(script, tribe, title=title, source_label=describe(src_path, dat_path), notes=notes)
        except ScriptError as e:
            result['problems'].append('tribe %d: %s' % (tribe, e))
            continue
        os.makedirs(folder, exist_ok=True)
        fn = 'ai_p%d.lua' % tribe
        with open(os.path.join(folder, fn), 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
        written.append((tribe, fn, script_no, describe(src_path, dat_path)))
        result['tribes'].append({'tribe': tribe, 'file': fn, 'script': script_no, 'differences': report, 'warnings': warnings})
        result['differences'] += len(report)
    if written:
        prefix = include_prefix(folder, scripts_root)
        if prefix is None:
            prefix = level_folder(number, name)
            result['problems'].append('the output is not inside a Scripts folder: harness.lua assumes this level folder '
                                      'is copied directly into Scripts/ (use --scripts-root to say otherwise)')
        lines = ['--[[', '  ' + title, '  Loads the converted computer-player scripts for this level:']
        for tribe, fn, script_no, desc in written:
            lines.append('    tribe %d (%s)  %s  <- %s' % (tribe, TRIBE_NAMES.get(tribe, '?'), fn, desc))
        lines += ['', '  Run it with:  pop3.exe /level %d /dscript %s/harness.lua' % (number, prefix),
                  '  Each script switches off the original CPSCR script of its tribe when the level starts.',
                  '  Generated by popscript-upgrader %s.' % luagen.VERSION, ']]', '',
                  'include("std/v0.0.1/init.lua")', 'std.install()', '']
        for tribe, fn, _, _ in written:
            lines.append('include("%s/%s")' % (prefix, fn))
        with open(os.path.join(folder, 'harness.lua'), 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(lines) + '\n')
    return result


def convert_game(game_root, out_root, levels=None, scripts_dir=None, scripts_root=None, log=print):
    """Convert every level of a game or mod folder (or the listed ones)."""
    levels_dir = os.path.join(game_root, 'levels')
    if not os.path.isdir(levels_dir):
        raise ScriptError('%s has no levels folder' % game_root)
    names = level_names(game_root)
    results = []
    for number in (levels or list_levels(levels_dir)):
        header = find_level_header(levels_dir, number)
        if header is None:
            log('level %d: no header (LEVL2%03d.HDR) found' % (number, number))
            continue
        if not header.tribes():
            continue
        name = names.get(number) or header.name or None
        r = convert_level(number, header, game_root, out_root, name, scripts_dir, scripts_root, log)
        results.append(r)
        done = ', '.join('tribe %d <- CPSCR%03d' % (t['tribe'], t['script']) for t in r['tribes'])
        log('level %3d  %-28s %s%s' % (number, (name or '')[:28], done or 'nothing converted',
                                       '   [%d difference(s) from source]' % r['differences'] if r['differences'] else ''))
        for p in r['problems']:
            log('           ! ' + p)
        for p in r['absent']:
            log('             ' + p)
    return results

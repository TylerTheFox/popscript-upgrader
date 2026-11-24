"""Parser check against the game's own compiled scripts.

For every levels/CPSCRnnn.DAT in a game checkout, find CpScript/CPSCRnnn.SCR, parse it, and
compare the syntax tree with the one decoded from the .DAT. Equal trees mean the parser reads
the text exactly as the 1998 compiler did.

Usage: python tests/oracle.py <game root> [-v]
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from popscript_upgrader import compiled, source          # noqa: E402
from popscript_upgrader.model import ScriptError, structure  # noqa: E402


def index_sources(folder):
    out = {}
    for fn in os.listdir(folder):
        m = re.match(r'^cpscr0*(\d+)\.scr$', fn, re.I)
        if m:
            out.setdefault(int(m.group(1)), []).append(os.path.join(folder, fn))
    return out


def first_difference(a, b, path='body'):
    if type(a) != type(b):
        return '%s: %r vs %r' % (path, a, b)
    if isinstance(a, tuple):
        if len(a) != len(b):
            for i, (x, y) in enumerate(zip(a, b)):
                d = first_difference(x, y, '%s[%d]' % (path, i))
                if d:
                    return d
            return '%s: %d items vs %d' % (path, len(a), len(b))
        for i, (x, y) in enumerate(zip(a, b)):
            d = first_difference(x, y, '%s[%d]' % (path, i))
            if d:
                return d
        return None
    return None if a == b else '%s: %r vs %r' % (path, a, b)


def main():
    root = sys.argv[1]
    verbose = '-v' in sys.argv
    sources = index_sources(os.path.join(root, 'CpScript'))
    levels = os.path.join(root, 'levels')
    same = differ = nosrc = bad = 0
    for fn in sorted(os.listdir(levels)):
        m = re.match(r'^cpscr(\d+)\.dat$', fn, re.I)
        if not m:
            continue
        num = int(m.group(1))
        try:
            dat = compiled.decode_file(os.path.join(levels, fn))
        except ScriptError as e:
            bad += 1
            print('DECODE FAIL %s: %s' % (fn, e))
            continue
        if num not in sources:
            nosrc += 1
            if verbose:
                print('no source   %s' % fn)
            continue
        results = []
        for path in sources[num]:
            try:
                src = source.parse_file(path)
            except ScriptError as e:
                results.append((os.path.basename(path), 'PARSE FAIL: %s' % e))
                continue
            d = first_difference(structure(src), structure(dat))
            results.append((os.path.basename(path), d))
        if any(d is None for _, d in results):
            same += 1
            if verbose:
                print('identical   %s == %s' % (fn, [n for n, d in results if d is None][0]))
        else:
            differ += 1
            for n, d in results:
                print('DIFFERENT   %s vs %s: %s' % (fn, n, d))
    print('\n%d identical, %d different, %d without source, %d undecodable' % (same, differ, nosrc, bad))
    return 0 if not differ and not bad else 1


if __name__ == '__main__':
    sys.exit(main())

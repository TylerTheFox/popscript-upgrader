"""Reconcile every shipped source script with its compiled form and list what differed.

Usage: python tests/oracle_reconcile.py <game root> [-v]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from oracle import index_sources                      # noqa: E402
from popscript_upgrader import compiled, source        # noqa: E402
from popscript_upgrader.model import ScriptError, structure  # noqa: E402
from popscript_upgrader.reconcile import reconcile     # noqa: E402
import re                                              # noqa: E402


def main():
    root = sys.argv[1]
    verbose = '-v' in sys.argv
    sources = index_sources(os.path.join(root, 'CpScript'))
    levels = os.path.join(root, 'levels')
    clean = changed = failed = 0
    for fn in sorted(os.listdir(levels)):
        m = re.match(r'^cpscr(\d+)\.dat$', fn, re.I)
        if not m or int(m.group(1)) not in sources:
            continue
        try:
            dat = compiled.decode_file(os.path.join(levels, fn))
        except ScriptError:
            continue
        best = None
        for path in sources[int(m.group(1))]:
            try:
                dat = compiled.decode_file(os.path.join(levels, fn))
                src = source.parse_file(path, recover=True)
                out, report = reconcile(src, dat)
                assert structure(out) == structure(compiled.decode_file(os.path.join(levels, fn)))
            except (ScriptError, AssertionError) as e:
                report, out = ['FAILED: %s' % e], None
            if best is None or len(report) < len(best[1]):
                best = (os.path.basename(path), report, out)
        name, report, out = best
        if out is None:
            failed += 1
        elif report:
            changed += 1
        else:
            clean += 1
        if report and (verbose or out is None):
            print('%s <- %s: %d difference(s)' % (fn, name, len(report)))
            for r in report[:12 if not verbose else 1000]:
                print('    ' + r[:230])
        elif report:
            print('%s <- %s: %d difference(s)' % (fn, name, len(report)))
    print('\n%d clean, %d reconciled with differences, %d failed' % (clean, changed, failed))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())

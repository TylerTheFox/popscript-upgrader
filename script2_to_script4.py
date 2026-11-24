#!/usr/bin/env python3
"""Old entry point, kept so existing command lines still work.

    python script2_to_script4.py -f INPUT.SCR OUTPUT.lua [--tribe N]
    python script2_to_script4.py -b INPUT_DIR OUTPUT_DIR [--tribe N]

The converter itself is the popscript_upgrader package; see README.md, or run

    python -m popscript_upgrader --help
"""
import argparse
import os
import sys

from popscript_upgrader.cli import main as cli_main


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('-f', '--file', nargs='+', metavar='PATH', help='INPUT OUTPUT [ignored...]')
    ap.add_argument('-b', '--batch', nargs='+', metavar='DIR', help='INPUT_DIR OUTPUT_DIR [ignored...]')
    ap.add_argument('--tribe', default='1')
    a = ap.parse_args()
    if a.file and len(a.file) >= 2:
        return cli_main(['convert', a.file[0], '-o', a.file[1], '--tribe', str(a.tribe)])
    if a.batch and len(a.batch) >= 2:
        src, dst = a.batch[0], a.batch[1]
        os.makedirs(dst, exist_ok=True)
        worst = 0
        for fn in sorted(os.listdir(src)):
            if fn.lower().endswith(('.scr', '.dat', '.txt')):
                out = os.path.join(dst, os.path.splitext(fn)[0] + '.lua')
                worst = max(worst, cli_main(['convert', os.path.join(src, fn), '-o', out, '--tribe', str(a.tribe)]))
        return worst
    ap.print_help()
    return 2


if __name__ == '__main__':
    sys.exit(main())

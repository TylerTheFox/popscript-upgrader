"""Level headers: which script drives which tribe.

A level names its computer-player scripts by number in its header:

    LEVL2nnn.HDR  (616 bytes)             LEVL2nnn.DAT in the newer single-file format
    offset 56  Name[32]                    "LEVL3" + the same 616 bytes + extra fields
    offset 88  NumPlayers (human included)
    offset 89  ComputerPlayerIndex[3]      script numbers for tribes 1, 2 and 3

Tribe n (1 = red, 2 = yellow, 3 = green) runs levels/CPSCRnnn.DAT where nnn is
ComputerPlayerIndex[n - 1]. The game loads a script only for tribes 1 .. NumPlayers - 1, and
an index of 0 (or a missing file) means "no script".

A header can also be given as text: a hex dump or base64, pasted into a file or on standard
input. That is what --header reads.
"""
import base64
import binascii
import os
import re
import struct

from .model import ScriptError

HEADER_SIZE = 616
_NAME, _NUM_PLAYERS, _CP_INDEX = 56, 88, 89


class LevelHeader:
    def __init__(self, data, origin=''):
        if data[:5] == b'LEVL3':
            data = data[5:]
        if len(data) < _CP_INDEX + 3:
            raise ScriptError('level header is too short (%d bytes, need at least %d)' % (len(data), _CP_INDEX + 3), 0, origin)
        self.origin = origin
        self.name = data[_NAME:_NAME + 32].split(b'\0')[0].decode('latin-1').strip()
        self.num_players = data[_NUM_PLAYERS]
        self.script_index = list(struct.unpack_from('3B', data, _CP_INDEX))
        if not 1 <= self.num_players <= 8:
            raise ScriptError('level header says %d players; this does not look like a level header' % self.num_players, 0, origin)

    def tribes(self):
        """[(tribe, script number)] for the tribes the game gives a script to."""
        out = []
        for tribe in range(1, min(self.num_players, 4)):
            idx = self.script_index[tribe - 1]
            if idx:
                out.append((tribe, idx))
        return out


def bytes_from_text(text):
    """Bytes from pasted text: a hex dump (with or without offsets and an ASCII column) or base64."""
    t = text.strip()
    compact = re.sub(r'\s+', '', t)
    if re.fullmatch(r'(?:0[xX])?[0-9a-fA-F]+', compact) and len(compact) % 2 == 0 and len(compact) >= 200:
        return binascii.unhexlify(compact[2:] if compact[:2].lower() == '0x' else compact)
    # hex dump lines: optional "00000010:" offset, byte pairs, optional "|ascii|" column
    out = bytearray()
    dump = True
    for line in t.splitlines():
        line = line.split('|')[0]
        line = re.sub(r'^\s*[0-9a-fA-F]{4,8}\s*[: ]\s*', '', line + ' ')
        pairs = re.findall(r'\b[0-9a-fA-F]{2}\b', line)
        rest = re.sub(r'\b[0-9a-fA-F]{2}\b', '', line).strip()
        if rest and not pairs:
            dump = False
            break
        out.extend(int(p, 16) for p in pairs)
    if dump and len(out) >= _CP_INDEX + 3:
        return bytes(out)
    try:
        return base64.b64decode(compact, validate=True)
    except (binascii.Error, ValueError):
        raise ScriptError('could not read the pasted header: expected a hex dump or base64 text')


def read_header(path_or_dash, stdin=None):
    """A LevelHeader from a .HDR / .DAT file, a text file holding a pasted dump, or '-' (stdin)."""
    if path_or_dash == '-':
        import sys
        raw = (stdin or sys.stdin.buffer).read()
        origin = 'standard input'
    else:
        with open(path_or_dash, 'rb') as f:
            raw = f.read()
        origin = os.path.basename(path_or_dash)
    looks_binary = raw[:5] == b'LEVL3' or (len(raw) >= HEADER_SIZE and b'\0' in raw[:HEADER_SIZE])
    if not looks_binary:
        raw = bytes_from_text(raw.decode('latin-1'))
    return LevelHeader(raw, origin)


def find_level_header(levels_dir, number):
    """The header for level `number`: LEVL2nnn.HDR, or a single-file LEVL3 LEVL2nnn.DAT."""
    found = {}
    for fn in os.listdir(levels_dir):
        m = re.fullmatch(r'levl2(\d{3})\.(hdr|dat)', fn, re.I)
        if m and int(m.group(1)) == number:
            found[m.group(2).lower()] = os.path.join(levels_dir, fn)
    if 'dat' in found:
        with open(found['dat'], 'rb') as f:
            if f.read(5) == b'LEVL3':
                return read_header(found['dat'])      # the game prefers the single-file format
    if 'hdr' in found:
        return read_header(found['hdr'])
    return None


def list_levels(levels_dir):
    nums = set()
    for fn in os.listdir(levels_dir):
        m = re.fullmatch(r'levl2(\d{3})\.(hdr|dat)', fn, re.I)
        if m:
            nums.add(int(m.group(1)))
    return sorted(nums)


def level_names(game_root):
    """{level number: name} from the game's English string table, when it is there."""
    names = {}
    path = os.path.join(game_root, 'language', 'lang00.txt')
    if os.path.isfile(path):
        with open(path, encoding='latin-1') as f:
            for line in f:
                m = re.match(r'\s*STR_LEVEL_(\d+)_NAME\s*=\s*(.+?)\s*$', line)
                if m:
                    names[int(m.group(1))] = m.group(2).strip().strip('"')
    return names


def find_script_files(game_root, number, scripts_dir=None):
    """(list of source paths, compiled path or None) for script `number`.

    More than one source can exist (CPSCR013.SCR next to CPSCR13.SCR); the caller picks the
    one that agrees best with the compiled script.
    """
    srcs, dat = [], None
    for folder in ([scripts_dir] if scripts_dir else []) + [os.path.join(game_root, 'CpScript'), os.path.join(game_root, 'levels')]:
        if not folder or not os.path.isdir(folder):
            continue
        for fn in sorted(os.listdir(folder)):
            m = re.fullmatch(r'cpscr0*(\d+)\.(scr|txt|dat)', fn, re.I)
            if not m or int(m.group(1)) != number:
                continue
            if m.group(2).lower() == 'dat':
                dat = dat or os.path.join(folder, fn)
            else:
                srcs.append(os.path.join(folder, fn))
    return srcs, dat

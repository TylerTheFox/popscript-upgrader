"""Extract every PopScript Lua binding signature from an engine checkout.

Usage: python tools/extract_bindings.py <engine Source dir> [out.json]

Reads Source/Script4_PopScript.cpp and writes, for each registered function, the C++
parameter list exactly as declared (default output: tests/bindings.json). Nothing is
interpreted: this is what the engine registers, so it is the reference for argument counts.
"""
import json, os, re, sys

SRC = sys.argv[1]
text = open(os.path.join(SRC, 'Script4_PopScript.cpp'), encoding='utf-8', errors='replace').read()


def split_params(s):
    s = s.strip()
    if not s or s == 'void':
        return []
    out, depth, cur = [], 0, ''
    for ch in s:
        if ch in '<([':
            depth += 1
        elif ch in '>)]':
            depth -= 1
        if ch == ',' and depth == 0:
            out.append(cur); cur = ''
        else:
            cur += ch
    out.append(cur)
    res = []
    for p in out:
        p = ' '.join(p.split())
        m = re.match(r'^(.*?)([A-Za-z_][A-Za-z0-9_]*)$', p)
        res.append([m.group(1).strip(), m.group(2)] if m else [p, ''])
    return res


def balanced(s, i, open_ch, close_ch):
    """index just past the bracket that closes the one at s[i]"""
    depth = 0
    j = i
    while j < len(s):
        c = s[j]
        if c == '"':
            j += 1
            while j < len(s) and s[j] != '"':
                j += 2 if s[j] == '\\' else 1
        elif c == open_ch:
            depth += 1
        elif c == close_ch:
            depth -= 1
            if depth == 0:
                return j + 1
        j += 1
    return len(s)


bindings = {}
for m in re.finditer(r'ENGINE_ADD_LAMBDA\(\s*"([A-Za-z0-9_]+)"\s*,\s*\[[^\]]*\]\s*', text):
    name = m.group(1)
    i = m.end()
    line = text.count('\n', 0, m.start()) + 1
    params = []
    if text[i] == '(':
        j = balanced(text, i, '(', ')')
        params = split_params(text[i + 1:j - 1])
        i = j
    b = text.index('{', i)
    e = balanced(text, b, '{', '}')
    body = ' '.join(text[b:e].split())
    if name in bindings:
        bindings[name].setdefault('duplicates', []).append(line)
        continue
    bindings[name] = {'params': params, 'line': line, 'kind': 'lambda', 'body': body}

consts = re.findall(r'ENGINE_ADD_GLOBAL_CONST_EASY\(\s*([A-Za-z0-9_]+)\s*\)', text) + re.findall(r'ENGINE_ADD_GLOBAL_CONST\(\s*"([A-Za-z0-9_]+)"', text)
print('constants registered in this module:', len(set(consts)))

# plain C functions registered by name: find their definition anywhere in Source
func_names = re.findall(r'ENGINE_ADD_FUNC_EASY\(\s*([A-Za-z0-9_]+)\s*\)', text)
func_named = [(lua, c) for c, lua in re.findall(r'ENGINE_ADD_FUNC_R\(\s*([A-Za-z0-9_:]+)\s*,\s*"([A-Za-z0-9_]+)"\s*\)', text)]
all_src = {}
for fn in os.listdir(SRC):
    if fn.lower().endswith(('.cpp', '.h')):
        try:
            all_src[fn] = open(os.path.join(SRC, fn), encoding='utf-8', errors='replace').read()
        except OSError:
            pass


def find_def(cname):
    pat = re.compile(r'^[A-Za-z_][A-Za-z0-9_ \*&:<>]*?\b' + re.escape(cname) + r'\s*\(([^;{}]*?)\)\s*(?:\{|;)', re.M)
    best = None
    for fn, src in all_src.items():
        for mm in pat.finditer(src):
            cand = (fn, src.count('\n', 0, mm.start()) + 1, mm.group(1))
            if best is None or (fn.lower().endswith('.cpp') and '{' in src[mm.end() - 1:mm.end()]):
                best = cand
    return best


for lua_name, cname in [(n, n) for n in func_names] + func_named:
    line = text.count('\n', 0, text.index(cname)) + 1
    d = find_def(cname.split('::')[-1])
    bindings.setdefault(lua_name, {
        'params': split_params(d[2]) if d else None, 'line': line, 'kind': 'func',
        'body': ('%s:%d' % (d[0], d[1])) if d else 'DEFINITION NOT FOUND', 'c_name': cname})

out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tests', 'bindings.json')
slim = {k: {'params': v['params'], 'line': v['line']} for k, v in sorted(bindings.items())}
json.dump({'functions': slim, 'constants': sorted(set(consts))}, open(out, 'w', newline=chr(10)), indent=0)
print('bindings extracted:', len(bindings), '(lambda %d, func %d)' % (
    sum(1 for b in bindings.values() if b['kind'] == 'lambda'), sum(1 for b in bindings.values() if b['kind'] == 'func')))
print('unresolved funcs:', [k for k, b in bindings.items() if b['params'] is None])

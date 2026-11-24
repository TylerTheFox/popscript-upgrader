"""Build tests/engine_api.json from a Script4 spec, and check the language table against it.

The spec is the engine's own description of its Lua API (functions with their parameters,
constants with their values). Generate it from an engine checkout with

    python Source/script4_doc_hybrid.py --output script4_spec.json

then run

    python tools/extract_bindings.py <engine>/Source
    python tools/build_engine_api.py script4_spec.json

Argument counts come from tests/bindings.json (read from the C++ by extract_bindings.py);
the spec supplies the remaining function names and the values of the constants.

Checks made here (any failure is listed and the exit code is 1):
  * every function the converter can emit exists and takes the number of arguments passed
  * every constant the converter can emit exists
  * keyword constants have the value the bytecode interpreter gives the keyword
  * ATTR_x == INT_ATTR_x - 1000, CP_AT_TYPE_x == command token - 1028
  * spell, building and person constants have the value the interpreter substitutes
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def to_int(v):
    try:
        return int(str(v), 0)
    except (TypeError, ValueError):
        return None


def main():
    spec = json.load(open(sys.argv[1], encoding='utf-8'))
    functions, constants = {}, {}
    for m in spec['modules']:
        for f in m.get('functions', []):
            params = [p for p in (f.get('parameters') or []) if p.strip() != 'void']
            functions[f['name']] = len(params)
        for e in m.get('enums', []):
            constants[e['name']] = to_int(e.get('value'))
    b = json.load(open(os.path.join(ROOT, 'tests', 'bindings.json'), encoding='utf-8'))
    for name, info in b['functions'].items():
        functions[name] = len(info['params'])       # the C++ is the authority on arity
    for name in b['constants']:
        constants.setdefault(name, None)
    lang = json.load(open(os.path.join(ROOT, 'popscript_upgrader', 'data', 'language.json'), encoding='utf-8'))
    problems = []

    def need_const(name, where, value=None):
        if name.startswith('cp.') or re.match(r'^-?\d+$', name):
            return
        if name not in constants:
            problems.append('%s: constant %s is not in the spec' % (where, name))
        elif value is not None and constants[name] is not None and constants[name] != value:
            problems.append('%s: %s is %s in the engine, the interpreter uses %s' % (where, name, constants[name], value))

    def check_expr(text, where):
        flat = re.sub(r'\{[^}]*\}', '0', text)
        for fn, args in re.findall(r'\b([A-Za-z_][A-Za-z0-9_]*)\(([^()]*(?:\([^()]*\)[^()]*)*)\)', flat):
            if fn not in functions:
                problems.append('%s: function %s is not in the spec' % (where, fn))
                continue
            argc = 0 if not args.strip() else len(re.sub(r'\([^()]*\)', '', args).split(','))
            if argc != functions[fn]:
                problems.append('%s: %s takes %d argument(s), %d passed' % (where, fn, functions[fn], argc))
        for ident in re.findall(r'\b([A-Z][A-Z0-9_]{2,})\b(?!\()', flat):
            need_const(ident, where)

    for k in lang['keywords']:
        need_const(k['lua'], 'keyword %s' % k['name'], k['value'])
    for c in lang['commands']:
        for key in ('call', 'expr'):
            if key in c:
                check_expr(c[key], 'command %s' % c['name'])
        m = re.search(r'CP_AT_TYPE_[A-Z_]+', c.get('call', ''))
        if m and c['name'].startswith('STATE_') and 'STATE_SET' in c['call']:
            need_const(m.group(0), 'command %s' % c['name'], c['token'] - 1028)
    for i in lang['internals']:
        where = 'variable %s' % i['name']
        if i.get('exact_reader') or i.get('building_count'):
            need_const(i['name'], where, i['index'])
        if i['kind'] == 'attr':
            need_const(i['lua'], where, i['index'] - 1000)
        elif i['kind'] == 'const':
            need_const(i['lua'], where, i.get('value'))
        else:
            check_expr(i['lua'], where)
    for fn in ('getTurn', 'GET_USER_VARIABLE_VALUE', 'SET_USER_VARIABLE_VALUE', 'READ_CP_ATTRIB', 'WRITE_CP_ATTRIB',
               'script_set_up_empty_script', 'GET_INTERNAL_VARIABLE', 'GET_TURNS_PER_SECOND', 'SET_ATTACK_VARIABLE',
               'set_player_can_cast', 'set_player_cannot_cast', 'set_player_can_build', 'set_player_cannot_build',
               'CHECK_IF_PERSON_PREACHED_TO', 'log', 'include'):
        if fn not in functions:
            problems.append('runtime: function %s is not in the spec' % fn)
    for t in range(8):
        name = ['TRIBE_BLUE', 'TRIBE_RED', 'TRIBE_YELLOW', 'TRIBE_GREEN', 'TRIBE_CYAN', 'TRIBE_PINK', 'TRIBE_BLACK', 'TRIBE_ORANGE'][t]
        need_const(name, 'tribes', t)

    out = os.path.join(ROOT, 'tests', 'engine_api.json')
    json.dump({'generated_from': spec.get('generation_time'), 'functions': functions, 'constants': constants},
              open(out, 'w', encoding='utf-8', newline='\n'), indent=0, sort_keys=True)
    print('%d functions, %d constants -> %s' % (len(functions), len(constants), out))
    print('%d problem(s)' % len(problems))
    for p in problems:
        print('  ' + p)
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())

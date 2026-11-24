"""The hand-writing helpers of std.cpscript make the engine calls they claim to.

Runs a small hand-written script in Lua 5.3 against the mock engine (which rejects unknown
functions and wrong argument counts) and compares the calls with what the equivalent 1998
script would have made.

Usage: python tests/stdlib_helpers.py <game root>
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

import differential as D          # noqa: E402

SCRIPT = '''
local cp = std.cpscript
local ai = cp.new(TRIBE_YELLOW, { source = "hand written", vars = { "USER_ATTACK", "USER_COUNT" } })
local me, v, attr = ai.tribe, ai.vars, ai.attr
ai:run(function()
    if getTurn() == 0 then
        ai:state("BUILD_WALLS", ON)
        ai:states{ FETCH_WOOD = true }
        ai:attributes{ EXPANSION = 300 }
        ai:spell_buckets{ [M_SPELL_BLAST] = 8 }
        ai:marker_entry(2, { from = 12, to = 13, warriors = 3, preachers = 1 })
        ai:spell_entry(1, { spell = M_SPELL_BLAST, mana = 500, every = 64, people = 3, at_base = true })
        ai:attack_result_in("USER_COUNT")
        ai:attack{ target = TRIBE_BLUE, people = 12, building = M_BUILDING_DRUM_TOWER }
        ai:attack{ target = TRIBE_RED, people = 8, person = cp.TARGET_SHAMAN,
                   spells = { M_SPELL_LIGHTNING_BOLT, M_SPELL_BLAST }, by = ATTACK_BY_BOAT, via = { 4, 5 }, direction = 2 }
        ai:attack{ target = TRIBE_GREEN, people = 5, marker = 20, damage = 100, bring_back_vehicles = 1 }
        v.USER_ATTACK = cp.div(-7, 2)
    end
end)
'''


def main():
    std_path = D.find_std(sys.argv[1])
    c = D.API['constants']
    w = D.make_world(1, 2, False)
    lua = D.LuaSide(SCRIPT, w, std_path)
    w.start_turn(0)
    lua.run_turn()
    want = [
        ('STATE_SET', 2, 1, c['CP_AT_TYPE_REPAIR_BLDGS']),
        ('STATE_SET', 2, 1, c['CP_AT_TYPE_FETCH_WOOD']),
        ('SET_BUCKET_COUNT_FOR_SPELL', 2, c['M_SPELL_BLAST'], 8),
        ('SET_MARKER_ENTRY', 2, 2, 12, 13, 0, 3, 0, 1),
        ('SET_SPELL_ENTRY', 2, 1, c['M_SPELL_BLAST'], 500, 64, 3, 1),
        ('SET_ATTACK_VARIABLE', 2, 1),
        ('ATTACK', 2, 0, 12, c['ATTACK_BUILDING'], c['M_BUILDING_DRUM_TOWER'], 999, 0, 0, 0, c['ATTACK_NORMAL'], 0, -1, -1, -1),
        ('ATTACK', 2, 1, 8, c['ATTACK_PERSON'], 999, 999, c['M_SPELL_LIGHTNING_BOLT'], c['M_SPELL_BLAST'], 0,
         c['ATTACK_BY_BOAT'], 0, 4, 5, 2),
        ('ATTACK', 2, 3, 5, c['ATTACK_MARKER'], 20, 100, 0, 0, 0, c['ATTACK_NORMAL'], 1, -1, -1, -1),
    ]
    ok = w.trace == want
    for i, (a, b) in enumerate(zip(w.trace, want)):
        if a != b:
            print('call %d:\n  got  %r\n  want %r' % (i, a, b))
    if len(w.trace) != len(want):
        print('%d call(s), expected %d' % (len(w.trace), len(want)))
    ok = ok and w.attribs[c['ATTR_EXPANSION']] == 300 % 256 and w.user_vars[0] == -3
    print('std.cpscript helpers: %s' % ('OK' if ok else 'FAILED'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())

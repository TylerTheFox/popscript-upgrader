--[[
  Example computer player
  Computer player script for the Red (Dakini) tribe.

  Converted from tutorial.scr (Bullfrog script) by popscript-upgrader 2.0.0.
  It runs once per game turn, top to bottom, exactly as the original did.
]]

include("std/v0.0.1/init.lua")
std.install()

local cp = std.cpscript
local ai = cp.new(TRIBE_RED, {
    source = "tutorial.scr",
    vars = {
        "USER_ATTACKS", "USER_RESULT",
    },
})
local me, v, attr = ai.tribe, ai.vars, ai.attr

-- A small computer player in Bullfrog syntax.

ai:run(function()
    if getTurn() == 0 then
        -- Things the tribe does on its own
        STATE_SET(me, ON, CP_AT_TYPE_CONSTRUCT_BUILDING)
        STATE_SET(me, ON, CP_AT_TYPE_FETCH_WOOD)
        STATE_SET(me, ON, CP_AT_TYPE_TRAIN_PEOPLE)
        attr.EXPANSION = 12
        attr.HOUSE_PERCENTAGE = 60
        v.USER_ATTACKS = 0
        v.USER_RESULT = 0
        SET_ATTACK_VARIABLE(me, ai:slot("USER_RESULT"))
    end

    -- Every 512 turns: attack blue if there are enough warriors
    if ai:every(512, 64) then
        if cp.all(PLAYERS_PEOPLE_OF_TYPE(me, M_PERSON_WARRIOR) > 5, G_RANDOM(100) < 70) then
            ATTACK(me, TRIBE_BLUE, 6, ATTACK_BUILDING, M_BUILDING_DRUM_TOWER, 999, M_SPELL_BLAST,
                   M_SPELL_NONE, M_SPELL_NONE, ATTACK_NORMAL, 0, -1, -1, -1)
            v.USER_ATTACKS = v.USER_ATTACKS + 1
        else
            TRAIN_PEOPLE_NOW(me, 2, M_PERSON_WARRIOR)  -- not enough yet
        end
    end
end)

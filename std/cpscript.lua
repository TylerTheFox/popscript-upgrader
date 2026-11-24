--[[============================================================================
  std/v0.0.1/cpscript.lua
  Runtime for computer-player scripts converted from the 1998 script language
  (CPSCRnnn.SCR, in Bullfrog or World Editor syntax) by popscript-upgrader.

  A converted script is one function that runs once per game turn for one
  tribe, top to bottom, the way the bytecode did:

      include("std/v0.0.1/init.lua")
      std.install()

      local cp = std.cpscript
      local ai = cp.new(TRIBE_RED, { source = "CPSCR010.SCR", vars = { "USER_ATTACK" } })
      local me, v, attr = ai.tribe, ai.vars, ai.attr

      ai:run(function()
          if getTurn() == 0 then
              STATE_SET(me, ON, CP_AT_TYPE_FETCH_WOOD)
              attr.EXPANSION = 12
          end
          if ai:every(256, 16) then
              v.USER_ATTACK = v.USER_ATTACK + 1
          end
      end)

  What this module guarantees, so the converted script behaves like the
  original one:

  * Timing. The function is called from OnComputerPlayerScript, which the
    engine fires at the point of the turn where the tribe's bytecode ran:
    tribes in ascending order, each one before its own decision pass. On an
    engine without that callback the script falls back to OnTurn (all tribes
    after every decision pass) and says so in the log once.
  * The original script is switched off for the tribe, so the two never run
    together. That normally happens when the level starts. If the Lua arrives
    later (it was loaded mid-game, or the level was restored before the
    scripts were), the bytecode has already run for the current turn: it is
    switched off then, and the Lua takes over from the next turn. Either way
    every turn is run exactly once, by one of the two.
  * ai.vars lives in the engine's own user-variable array, in the original
    slot order. The engine writes attack results into that array, and it is
    part of every saved game, so nothing here needs saving.
  * ai.attr reads and writes the tribe's attributes (one byte each).
  * ai:every(period, offset) is the original EVERY test, staggered by tribe.
============================================================================]]

std = std or {}
std.cpscript = std.cpscript or {}

local C = std.cpscript

-- "Attack the shaman" as the target model of ATTACK(..., ATTACK_PERSON, ...).
C.TARGET_SHAMAN = 999

C._scripts   = C._scripts or {}    -- tribe -> script object
C._installed = C._installed or false

-- True when the engine can run a script at the original point of the turn.
function C.exact_timing()
  return rawget(_G, "GET_INTERNAL_VARIABLE") ~= nil
end

local function say(msg)
  if type(log) == "function" then log("[std.cpscript] " .. msg) end
end

--------------------------------------------------------------------------------
-- Arithmetic the way the bytecode interpreter did it
--------------------------------------------------------------------------------

-- Wrap to a signed 32-bit integer (the width of a user variable).
function C.int32(x)
  x = x & 0xFFFFFFFF
  if x >= 0x80000000 then x = x - 0x100000000 end
  return x
end

-- DIVIDE: integer division that rounds toward zero; dividing by zero gives 0.
function C.div(a, b)
  if b == 0 then return 0 end
  local q = a // b
  if (a % b ~= 0) and ((a < 0) ~= (b < 0)) then q = q + 1 end
  return q
end

-- 1 or 0 from anything a binding returns as a truth value (true/false, a flag
-- bit, a count). The original commands stored exactly 1 or 0.
function C.flag(x)
  if x == nil or x == false or x == 0 then return 0 end
  return 1
end

-- Conditions in the original language evaluated both sides of && and ||.
-- Lua's `and` / `or` stop early, which matters when a side draws a random
-- number. cp.all / cp.any take already-evaluated values, so nothing is skipped.
function C.all(...)
  local n = select("#", ...)
  for i = 1, n do
    if not select(i, ...) then return false end
  end
  return true
end

function C.any(...)
  local n = select("#", ...)
  for i = 1, n do
    if select(i, ...) then return true end
  end
  return false
end

-- FORCE_TOOLTIP / FLYBY_SET_EVENT_TOOLTIP: the script wrote 0 for a stone head
-- and 1 for a building; the engine calls those 1 and 2.
function C.tooltip_code(code)
  if code == 0 then return 1 end
  if code == 1 then return 2 end
  return code
end

--------------------------------------------------------------------------------
-- Script object
--------------------------------------------------------------------------------

local Script = {}
Script.__index = Script

local function make_vars(tribe, names)
  local slot_of = {}
  for i, name in ipairs(names) do slot_of[name] = i - 1 end
  local proxy = setmetatable({}, {
    __index = function(_, name)
      local slot = slot_of[name]
      if slot == nil then error("unknown script variable '" .. tostring(name) .. "'", 2) end
      return GET_USER_VARIABLE_VALUE(tribe, slot)
    end,
    __newindex = function(_, name, value)
      local slot = slot_of[name]
      if slot == nil then error("unknown script variable '" .. tostring(name) .. "'", 2) end
      SET_USER_VARIABLE_VALUE(tribe, slot, C.int32(value))
    end,
  })
  return proxy, slot_of
end

local function make_attr(tribe)
  local index_of = {}
  local function index(name)
    local idx = index_of[name]
    if idx == nil then
      idx = rawget(_G, "ATTR_" .. tostring(name))
      if idx == nil then error("unknown attribute '" .. tostring(name) .. "'", 3) end
      index_of[name] = idx
    end
    return idx
  end
  return setmetatable({}, {
    __index = function(_, name)
      return READ_CP_ATTRIB(tribe, index(name))
    end,
    -- An attribute is one byte; a larger value keeps its low byte, as it did
    -- when the bytecode wrote it.
    __newindex = function(_, name, value)
      WRITE_CP_ATTRIB(tribe, index(name), value % 256)
    end,
  })
end

-- Create the script object for one tribe.
--   opts.vars    list of variable names, in the original slot order
--   opts.source  name of the script this was converted from (for the log)
function C.new(tribe, opts)
  assert(type(tribe) == "number", "std.cpscript.new: tribe must be a number")
  opts = opts or {}
  local self = setmetatable({}, Script)
  self.tribe  = tribe
  self.source = opts.source or "?"
  self.vars, self._slot_of = make_vars(tribe, opts.vars or {})
  self.attr   = make_attr(tribe)
  return self
end

-- Slot number of a variable in the engine's array (for SET_ATTACK_VARIABLE).
function Script:slot(name)
  local slot = self._slot_of[name]
  if slot == nil then error("unknown script variable '" .. tostring(name) .. "'", 2) end
  return slot
end

-- EVERY period [offset]. True on the turns the original block ran: the turn
-- counter is staggered by tribe number so the tribes do not all act at once.
-- `period` should be a power of two, as the original compiler required.
function Script:every(period, offset)
  local shift = 0
  if offset ~= nil then shift = offset - 1 end
  return ((getTurn() + self.tribe + shift) & (period - 1)) == 0
end

-- Register the script body. It replaces the tribe's original script.
function Script:run(fn)
  assert(type(fn) == "function", "std.cpscript: run() needs a function")
  self._fn = fn
  C._scripts[self.tribe] = self
  C._install()
  return self
end

--------------------------------------------------------------------------------
-- Shorthand for scripts written by hand
--
-- The converter never emits these: it keeps one Lua statement per original
-- statement. They are for people writing a new computer player (or tidying a
-- converted one) who would rather say what they mean in one table.
--------------------------------------------------------------------------------

local function on_off(x)
  if x == true or x == 1 then return 1 end
  if x == false or x == 0 or x == nil then return 0 end
  error("expected ON, OFF, true or false, got " .. tostring(x), 3)
end

-- Names the 1998 scripts used that differ from the engine's constant.
local STATE_ALIAS = {
  BUILD_WALLS = "REPAIR_BLDGS",
}

local function state_flag(name)
  local key = STATE_ALIAS[name] or name
  local flag = rawget(_G, "CP_AT_TYPE_" .. tostring(key))
  if flag == nil then error("unknown state '" .. tostring(name) .. "'", 3) end
  return flag
end

-- Switch one state on or off:  ai:state("FETCH_WOOD", ON)
function Script:state(name, on)
  STATE_SET(self.tribe, on_off(on), state_flag(name))
  return self
end

-- Switch several states at once. The states are independent of each other, so
-- the order they are applied in does not matter.
--   ai:states{ CONSTRUCT_BUILDING = ON, FETCH_WOOD = ON, SEND_GHOSTS = OFF }
function Script:states(t)
  for name, on in pairs(t) do
    STATE_SET(self.tribe, on_off(on), state_flag(name))
  end
  return self
end

-- Set several attributes at once.
--   ai:attributes{ EXPANSION = 12, HOUSE_PERCENTAGE = 60, MAX_ATTACKS = 3 }
function Script:attributes(t)
  for name, value in pairs(t) do
    self.attr[name] = value
  end
  return self
end

-- Spell bucket sizes, the table every late-game script sets on a timer.
--   ai:spell_buckets{ [M_SPELL_BLAST] = 8, [M_SPELL_LIGHTNING_BOLT] = 24 }
function Script:spell_buckets(t)
  for spell, count in pairs(t) do
    SET_BUCKET_COUNT_FOR_SPELL(self.tribe, spell, count)
  end
  return self
end

-- A guard entry: who stands between two markers.
--   ai:marker_entry(0, { from = 12, to = 13, braves = 0, warriors = 3, firewarriors = 2, preachers = 1 })
function Script:marker_entry(entry, o)
  SET_MARKER_ENTRY(self.tribe, entry, o.from, o.to or -1,
                   o.braves or 0, o.warriors or 0, o.firewarriors or 0, o.preachers or 0)
  return self
end

-- A spell the shaman casts on her own.
--   ai:spell_entry(0, { spell = M_SPELL_BLAST, mana = 25000, every = 64, people = 3, at_base = true })
-- `every` must be a power of two.
function Script:spell_entry(entry, o)
  SET_SPELL_ENTRY(self.tribe, entry, o.spell, o.mana or PLAYERS_SPELL_COST(o.spell, self.tribe),
                  o.every or 64, o.people or 1, on_off(o.at_base))
  return self
end

-- Launch an attack. Only `target`, `people` and what to aim at are needed:
--   ai:attack{ target = TRIBE_BLUE, people = 12, building = M_BUILDING_DRUM_TOWER }
--   ai:attack{ target = TRIBE_BLUE, people = 8,  person = cp.TARGET_SHAMAN,
--              spells = { M_SPELL_LIGHTNING_BOLT, M_SPELL_BLAST }, by = ATTACK_BY_BOAT }
--   ai:attack{ target = TRIBE_BLUE, people = 5,  marker = 20, damage = 100 }
-- Options: damage (default 999), spells (up to three), by (ATTACK_NORMAL, ATTACK_BY_BOAT,
-- ATTACK_BY_BALLOON), bring_back_vehicles, via (one or two markers to pass through),
-- direction. The result arrives in the variable named with SET_ATTACK_VARIABLE.
function Script:attack(o)
  local kind, model
  if o.marker ~= nil then kind, model = ATTACK_MARKER, o.marker
  elseif o.building ~= nil then kind, model = ATTACK_BUILDING, o.building
  elseif o.person ~= nil then kind, model = ATTACK_PERSON, o.person
  else error("ai:attack needs marker=, building= or person=", 2) end
  local spells = o.spells or {}
  local via = o.via or {}
  if type(via) ~= "table" then via = { via } end
  return ATTACK(self.tribe, o.target, o.people, kind, model, o.damage or 999,
                spells[1] or M_SPELL_NONE, spells[2] or M_SPELL_NONE, spells[3] or M_SPELL_NONE,
                o.by or ATTACK_NORMAL, o.bring_back_vehicles or 0,
                via[1] or -1, via[2] or -1, o.direction or -1)
end

-- Put the result of this tribe's attacks into the named variable.
--   ai:attack_result_in("USER_ATTACK")   ...   if v.USER_ATTACK == cp.ATTACK_NO_TARGET then
function Script:attack_result_in(name)
  SET_ATTACK_VARIABLE(self.tribe, self:slot(name))
  return self
end

-- Values the engine writes into the attack variable.
C.ATTACK_NOT_YET             = 0
C.ATTACK_TOO_MANY            = 1
C.ATTACK_NO_SPACE            = 2
C.ATTACK_NO_TARGET           = 3
C.ATTACK_NO_SPARE_PEOPLE     = 4
C.ATTACK_DONT_KNOW           = 5
C.ATTACK_NOT_ENOUGH_VEHICLES = 6
C.ATTACK_NAV_FAILURE         = 7
C.ATTACK_EVERYONE_DEAD       = 51
C.ATTACK_SENT_HOME           = 52

--------------------------------------------------------------------------------
-- Engine hooks
--------------------------------------------------------------------------------

local MAX_TRIBES = 8

local function mute_originals()
  for tribe = 1, MAX_TRIBES - 1 do          -- never the human in slot 0
    local s = C._scripts[tribe]
    if s then
      script_set_up_empty_script(tribe)
      s._live = true
      say(("tribe %d runs %s"):format(tribe, s.source))
    end
  end
end

-- Called where the tribe's bytecode has just run (or done nothing, if it is
-- already switched off). Returns true if the Lua script should run this turn.
local function take_over(s, tribe)
  if s._live then return true end
  s._live = true
  if tribe == 0 or script_is_empty(tribe) then return true end
  script_set_up_empty_script(tribe)
  say(("tribe %d runs %s from the next turn (the original script ran turn %d)"):format(tribe, s.source, getTurn()))
  return false
end

function C._install()
  if C._installed then return end
  C._installed = true

  std.on("OnLevelInit", mute_originals)

  if C.exact_timing() then
    std.on("OnComputerPlayerScript", function(tribe)
      local s = C._scripts[tribe]
      if s and take_over(s, tribe) then s._fn() end
    end)
  else
    say("this engine has no OnComputerPlayerScript callback; scripts run from OnTurn, " ..
        "one decision pass later than the originals")
    std.on("OnTurn", function()
      for tribe = 0, MAX_TRIBES - 1 do
        local s = C._scripts[tribe]
        if s then
          local ok, err = pcall(s._fn)
          if not ok then say(("tribe %d: %s"):format(tribe, tostring(err))) end
        end
      end
    end)
  end
end

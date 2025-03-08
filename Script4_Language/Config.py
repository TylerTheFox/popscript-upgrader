"""
Script4_Language/Config.py
Configuration constants and settings for the Script2 to Script4 converter
"""

USER_PREFIX = "USER_"
SC2_USR_PREFIX = "SC2_USR_"
STR_INT_PREFIX = "INT_"

TRIBE_PREFIX = "TRIBE_"

BLUE = 'BLUE'
RED = 'RED'
GREEN = 'GREEN'
YELLOW = 'YELLOW'

# Tribe name constants
TRIBE_BLUE = TRIBE_PREFIX + BLUE
TRIBE_RED = TRIBE_PREFIX + RED
TRIBE_GREEN = TRIBE_PREFIX + GREEN
TRIBE_YELLOW = TRIBE_PREFIX + YELLOW
MY_TRIBE = "MY_TRIBE"  # Default tribe reference

# Constants for structure components
SCRIPT_START = "-- Script4 Generated Script"
SCRIPT_END = "-- End of Generated Script"
COMMENT_PREFIX = "--"
INDENT_SIZE = 4
INDENT_CHAR = " "
SCRIPT_LOOP_START = "local script_continuing = true\nwhile script_continuing do"
SCRIPT_LOOP_END = "if EveryPow2Seconds(1024) then script_continuing = false end\nSLEEP(30)\nend"
SINGLE_RETURN = "ONE_OFF_RETURN\n"
FUNCTION_PREFIX = "function "
FUNCTION_SUFFIX = "end\n"

# Statement type constants
COMMAND_STMT = "COMMAND"
EVERY_STMT = "EVERY"
IF_STMT = "IF"
IF_ELSE_STMT = "IF_ELSE"
BEGIN_ACTIVE_STMT = "BEGIN_ACTIVE"
END_ACTIVE_STMT = "END_ACTIVE"
COMMENT_STMT = "COMMENT"
COMMENT_BLOCK_STMT = "COMMENT_BLOCK"
SET_TIMER_STMT = "SET_TIMER"
SET_TIMER_GOING_STMT = "SET_TIMER_GOING"
SET_LEVEL_COMPLETE_STMT = "SET_LEVEL_COMPLETE"

# Command types
CMD_COMMENT = "COMMENT"

# Game state constants
OFF = 0
ON = 1

# Constants for command parameters
PARAM_INDEX_COMMAND = 0
PARAM_INDEX_FIRST_ARG = 1
PARAM_INDEX_SECOND_ARG = 2
PARAM_INDEX_THIRD_ARG = 3
PARAM_INDEX_FOURTH_ARG = 4
PARAM_INDEX_FIFTH_ARG = 5 

# Constants for common script concepts
MARKER = "MARKER"
SPELL = "SPELL"
BUILDING = "BUILDING"
PERSON = "PERSON"
VEHICLE = "VEHICLE"
TYPE = "TYPE"
RADIUS = "RADIUS"
ANGLE = "ANGLE"
COUNT = "COUNT"
CELL_RADIUS = "CELLS"

# Constants for variable prefixes and access paths
ACCESS_PATH_SEPARATOR = "."
GSI_PREFIX = "_gsi"
GNSI_PREFIX = "_gnsi"
PLAYERS_PATH = f"{GSI_PREFIX}.Players"
NUM_PEOPLE_ATTR = "NumPeople"
NUM_PEOPLE_TYPE_PATH = "NumPeopleOfType"

SPELL_PREFIX = "M_SPELL_"
ATTACK_PREFIX = "ATTACK_"
NO_SPECIFIC_SPELL = "M_SPELL_NONE"
SPELL_TYPE_SPELL = "T_SPELL"
SPELL_TYPE_BUILDING = "T_BUILDING"
ATTACK_NORMAL = "ATTACK_NORMAL"
INT_NO_SPECIFIC_SPELL = 'INT_NO_SPECIFIC_SPELL'

# Constants for variable mapping functions
PLAYER_TRIBE_FMT = f"{PLAYERS_PATH}[{{0}}]"
NUM_PEOPLE_FMT = f"{PLAYER_TRIBE_FMT}{ACCESS_PATH_SEPARATOR}{NUM_PEOPLE_ATTR}"
NUM_PEOPLE_TYPE_FMT = f"{PLAYER_TRIBE_FMT}{ACCESS_PATH_SEPARATOR}{NUM_PEOPLE_TYPE_PATH}[{{1}}]"
FREE_ENTRIES_FMT = "FREE_ENTRIES({0})"
WILD_PEOPLE_PATH = f"{GNSI_PREFIX}.NumWildPeople"

# Constants for building access
BUILDING_TYPE_FMT = "PLAYERS_BUILDING_OF_TYPE({0}, {1})"
BUILDING_PREFIX = "M_BUILDING_"
SPELL_PREFIX = "M_SPELL_"
PERSON_PREFIX = "M_PERSON_"

# Operator mapping dictionary for converting conditions
# Add or update these in your Config.py or where you define OPERATOR_MAP
OPERATOR_MAP = {
    "GREATER_THAN": ">",
    "LESS_THAN": "<",
    "EQUAL_TO": "==",
    "GREATER_THAN_EQUAL_TO": ">=",
    "LESS_THAN_EQUAL_TO": "<=",
    "DOESNT_EQUAL": "~=",
    "!=": "~=",
    "AND": "and",
    "OR": "or",
    "&&": "and",
    "||": "or",
    "<": "<",
    ">": ">",
    "==": "==",
    ">=": ">=",
    "<=": "<="
}

# State to Computer Player Action Type mapping
STATE_CP_MAP = {
    "STATE_BRING_NEW_PEOPLE_BACK": "CP_AT_TYPE_BRING_NEW_PEOPLE_BACK",
    "STATE_TRAIN_PEOPLE": "CP_AT_TYPE_TRAIN_PEOPLE",
    "STATE_MED_MAN_GET_WILD_PEEPS": "CP_AT_TYPE_MED_MAN_GET_WILD_PEEPS",
    "STATE_CONSTRUCT_BUILDING": "CP_AT_TYPE_CONSTRUCT_BUILDING",
    "STATE_FETCH_WOOD": "CP_AT_TYPE_FETCH_WOOD",
    "STATE_SEND_GHOSTS": "CP_AT_TYPE_SEND_GHOSTS",
    "STATE_FETCH_LOST_PEOPLE": "CP_AT_TYPE_FETCH_LOST_PEOPLE",
    "STATE_FETCH_FAR_VEHICLE": "CP_AT_TYPE_FETCH_FAR_VEHICLE",
    "STATE_FETCH_LOST_VEHICLE": "CP_AT_TYPE_FETCH_LOST_VEHICLE",
    "STATE_DEFEND": "CP_AT_TYPE_DEFEND",
    "STATE_DEFEND_BASE": "CP_AT_TYPE_DEFEND_BASE",
    "STATE_HOUSE_A_PERSON": "CP_AT_TYPE_HOUSE_A_PERSON",
    "STATE_AUTO_ATTACK": "CP_AT_TYPE_AUTO_ATTACK",
    "STATE_POPULATE_DRUM_TOWER": "CP_AT_TYPE_POPULATE_DRUM_TOWER",
    "STATE_BUILD_VEHICLE": "CP_AT_TYPE_BUILD_VEHICLE",
    "STATE_PREACH": "CP_AT_TYPE_PREACH",
    "STATE_SPELL_DEFENSE": "CP_AT_TYPE_SPELL_DEFENSE",
    "STATE_BUILD_WALLS": "CP_AT_TYPE_BUILD_WALLS",
    "STATE_SABOTAGE": "CP_AT_TYPE_SABOTAGE",
    "STATE_SPELL_OFFENSIVE": "CP_AT_TYPE_SPELL_OFFENSIVE",
    "STATE_SUPER_DEFEND": "CP_AT_TYPE_SUPER_DEFEND",
    "STATE_MED_MAN_DEFEND": "CP_AT_TYPE_MED_MAN_DEFEND",
    "STATE_FLATTEN_BASE": "CP_AT_TYPE_FLATTEN_BASE",
    "STATE_BUILD_OUTER_DEFENCES": "CP_AT_TYPE_BUILD_OUTER_DEFENCES",
    "STATE_GUARD_AT_MARKER": "CP_AT_TYPE_GUARD_AT_MARKER",
    "STATE_SEND_ALL_TO_MARKER": "CP_AT_TYPE_SEND_ALL_TO_MARKER",
    "STATE_PRAY_AT_HEAD": "CP_AT_TYPE_PRAY_AT_HEAD",
    "STATE_BOAT_PATROL": "CP_AT_TYPE_BOAT_PATROL",
    "STATE_DEFEND_SHAMEN": "CP_AT_TYPE_DEFEND_SHAMEN",
    "STATE_DESTROY_BUILDING": "CP_AT_TYPE_DESTROY_BUILDING"
}

STATE_ATTR_MAP = {
    "INT_ATTR_EXPANSION": "ATTR_EXPANSION",
    "INT_ATTR_PREF_SPY_TRAINS": "ATTR_PREF_SPY_TRAINS",
    "INT_ATTR_PREF_RELIGIOUS_TRAINS": "ATTR_PREF_RELIGIOUS_TRAINS",
    "INT_ATTR_PREF_WARRIOR_TRAINS": "ATTR_PREF_WARRIOR_TRAINS",
    "INT_ATTR_PREF_SUPER_WARRIOR_TRAINS": "ATTR_PREF_SUPER_WARRIOR_TRAINS",
    "INT_ATTR_PREF_SPY_PEOPLE": "ATTR_PREF_SPY_PEOPLE",
    "INT_ATTR_PREF_RELIGIOUS_PEOPLE": "ATTR_PREF_RELIGIOUS_PEOPLE",
    "INT_ATTR_PREF_WARRIOR_PEOPLE": "ATTR_PREF_WARRIOR_PEOPLE",
    "INT_ATTR_PREF_SUPER_WARRIOR_PEOPLE": "ATTR_PREF_SUPER_WARRIOR_PEOPLE",
    "INT_ATTR_MAX_BUILDINGS_ON_GO": "ATTR_MAX_BUILDINGS_ON_GO",
    "INT_ATTR_HOUSE_PERCENTAGE": "ATTR_HOUSE_PERCENTAGE",
    "INT_ATTR_AWAY_BRAVE": "ATTR_AWAY_BRAVE",
    "INT_ATTR_AWAY_WARRIOR": "ATTR_AWAY_WARRIOR",
    "INT_ATTR_AWAY_RELIGIOUS": "ATTR_AWAY_RELIGIOUS",
    "INT_ATTR_DEFENSE_RAD_INCR": "ATTR_DEFENSE_RAD_INCR",
    "INT_ATTR_MAX_DEFENSIVE_ACTIONS": "ATTR_MAX_DEFENSIVE_ACTIONS",
    "INT_ATTR_AWAY_SPY": "ATTR_AWAY_SPY",
    "INT_ATTR_AWAY_SUPER_WARRIOR": "ATTR_AWAY_SUPER_WARRIOR",
    "INT_ATTR_ATTACK_PERCENTAGE": "ATTR_ATTACK_PERCENTAGE",
    "INT_ATTR_AWAY_MEDICINE_MAN": "ATTR_AWAY_MEDICINE_MAN",
    "INT_ATTR_PEOPLE_PER_BOAT": "ATTR_PEOPLE_PER_BOAT",
    "INT_ATTR_PEOPLE_PER_BALLOON": "ATTR_PEOPLE_PER_BALLOON",
    "INT_ATTR_MAX_SPY_ATTACKS": "ATTR_MAX_SPY_ATTACKS",
    "INT_ATTR_ENEMY_SPY_MAX_STAND": "ATTR_ENEMY_SPY_MAX_STAND",
    "INT_ATTR_MAX_ATTACKS": "ATTR_MAX_ATTACKS",
    "INT_ATTR_SPY_CHECK_FREQUENCY": "ATTR_SPY_CHECK_FREQUENCY",
    "INT_ATTR_RETREAT_VALUE": "ATTR_RETREAT_VALUE",
    "INT_ATTR_SHAMEN_BLAST": "ATTR_SHAMEN_BLAST",
    "INT_ATTR_MAX_TRAIN_AT_ONCE": "ATTR_MAX_TRAIN_AT_ONCE",
    "INT_ATTR_GROUP_OPTION": "ATTR_GROUP_OPTION",
    "INT_ATTR_PREF_BOAT_HUTS": "ATTR_PREF_BOAT_HUTS",
    "INT_ATTR_PREF_BALLOON_HUTS": "ATTR_PREF_BALLOON_HUTS",
    "INT_ATTR_PREF_BOAT_DRIVERS": "ATTR_PREF_BOAT_DRIVERS",
    "INT_ATTR_PREF_BALLOON_DRIVERS": "ATTR_PREF_BALLOON_DRIVERS",
    "INT_ATTR_FIGHT_STOP_DISTANCE": "ATTR_FIGHT_STOP_DISTANCE",
    "INT_ATTR_SPY_DISCOVER_CHANCE": "ATTR_SPY_DISCOVER_CHANCE",
    "INT_ATTR_COUNT_PREACH_DAMAGE": "ATTR_COUNT_PREACH_DAMAGE",
    "INT_ATTR_USE_PREACHER_FOR_DEFENCE": "ATTR_USE_PREACHER_FOR_DEFENCE",
    "INT_ATTR_RANDOM_BUILD_SIDE": "ATTR_RANDOM_BUILD_SIDE",
    "INT_ATTR_BASE_UNDER_ATTACK_RETREAT": "ATTR_BASE_UNDER_ATTACK_RETREAT",
    "INT_ATTR_EMPTY_AT_WAYPOINT": "ATTR_EMPTY_AT_WAYPOINT",
    "INT_ATTR_DONT_USE_BOATS": "ATTR_DONT_USE_BOATS",
    "INT_ATTR_DONT_GROUP_AT_DT": "ATTR_DONT_GROUP_AT_DT",
    "INT_ATTR_SPELL_DELAY": "ATTR_SPELL_DELAY",
    "INT_ATTR_DONT_DELETE_USELESS_BOAT_HOUSE": "ATTR_DONT_DELETE_USELESS_BOAT_HOUSE",
    "INT_ATTR_BOAT_HOUSE_BROKEN": "ATTR_BOAT_HOUSE_BROKEN",
    "INT_ATTR_DONT_AUTO_TRAIN_PREACHERS": "ATTR_DONT_AUTO_TRAIN_PREACHERS"
}

# Special mappings that don't follow standard patterns
SPECIAL_MAPPINGS = {
    "INT_NO_SPECIFIC_SPELL": "M_SPELL_NONE",
    "BUILDING": "ATTACK_BUILDING",
    "MARKER": "ATTACK_MARKER",
    "INT_WRATH_OF_GOD": "M_SPELL_ARMAGEDDON",
    "INT_CONVERT": "M_SPELL_CONVERT_WILD",
    "CONVERT": "M_SPELL_CONVERT_WILD",
    "INT_TARGET_MEDICINE_MAN": "ATTACK_TARGET_MEDICINE_MAN",
}

# People and population mappings
PEOPLE_MAPPINGS = {
    "INT_MY_NUM_PEOPLE": "_gsi.Players[MY_TRIBE].NumPeople",
    "INT_BLUE_PEOPLE": "_gsi.Players[TRIBE_BLUE].NumPeople",
    "INT_RED_PEOPLE": "_gsi.Players[TRIBE_RED].NumPeople",
    "INT_YELLOW_PEOPLE": "_gsi.Players[TRIBE_YELLOW].NumPeople",
    "INT_GREEN_PEOPLE": "_gsi.Players[TRIBE_GREEN].NumPeople",
    "INT_WILD_PEOPLE": "_gnsi.NumWildPeople",
    "INT_CP_FREE_ENTRIES": "FREE_ENTRIES(MY_TRIBE)"
}

# Tribe mapping for person counts
TRIBE_MAP = {
    "B": "TRIBE_BLUE",
    "R": "TRIBE_RED",
    "Y": "TRIBE_YELLOW", 
    "G": "TRIBE_GREEN",
    "M": "MY_TRIBE"
}

# Lists of spell names for conversions
SPELL_NAMES = [
    "BLAST", "BURN", "LIGHTNING_BOLT", "WHIRLWIND", "INSECT_PLAGUE", 
    "INVISIBILITY", "HYPNOTISM", "FIRESTORM", "GHOST_ARMY", "EROSION", 
    "SWAMP", "LAND_BRIDGE", "ANGEL_OF_DEATH", "EARTHQUAKE", "FLATTEN", 
    "VOLCANO", "SHIELD", "TELEPORT", "BLOODLUST", "CONVERT", "ARMAGEDDON"
]

# Lists of building types for conversions
BUILDING_TYPES = [
    "TEPEE", "HUT", "FARM", "DRUM_TOWER", "TEMPLE", "SPY_TRAIN", 
    "WARRIOR_TRAIN", "SUPER_TRAIN", "WALL_PIECE", "GATE",
    "BOAT_HUT_1", "BOAT_HUT_2", "AIRSHIP_HUT_1", "AIRSHIP_HUT_2"
]

# List of person types for conversions
PERSON_TYPES = [
    "BRAVE", "WARRIOR", "RELIGIOUS", "SPY", "SUPER_WARRIOR", "MEDICINE_MAN"
]

# Constants for conversion status and file handling
SUCCESS = 0
FAILURE = 1

# Constants for common file extensions
SCRIPT2_EXT = ".SCR"
SCRIPT4_EXT = ".lua"

# Constants for script structure components
INDENT_SIZE = 4
INDENT_CHAR = " "
COMMENT_PREFIX = "--"
SCRIPT_HEADER_TEMPLATE = """-- {output_file}
-- Generated from {input_file} by script2_to_script4 converter
"""

# Import modules for standard header
STANDARD_IMPORTS = [
    "import(Module_DataTypes)",
    "import(Module_PopScript)",
    "import(Module_Globals)",
    "import(Module_Helpers)",
    "import(Module_Players)",
    "import(Module_Defines)",
    "import(Module_Objects)",
    "import(Module_System)",
    "import(Module_String)",
    "import(Module_Bit32)",
    "import(Module_Game)",
    "import(Module_Math)",
    "import(Module_Map)"
]

# Default user variables to ensure are always present
DEFAULT_USER_VARS = []

# Configure script conversion settings
CONVERSION_SETTINGS = {
    "prefix_user_vars": True,   # Whether to prefix USER_ with SC2_USR_
    "include_save_logic": True, # Whether to include OnSave/OnLoad functions
    "debug_mode": False,        # Enable additional debug logging in scripts
    "default_tribe": TRIBE_BLUE # Default tribe to use if not specified
}

AUTO_SAVE = '''function OnSave(state)
    -- Save all user variables to the state object
    for varName, value in pairs(_G) do
        -- Check if this is a user variable
        if type(varName) == "string" and #tostring(varName) > 8 and varName:sub(1, 8) == "SC2_USR_" then
            if type(value) == "number" then
                state:push_int(value)
                log("Saving number: " .. varName .. " = " .. tostring(value))
            elseif type(value) == "boolean" then
                state:push_bool(value)
                log("Saving boolean: " .. varName .. " = " .. tostring(value))
            elseif type(value) == "string" then
                state:push_string(value)
                log("Saving string: " .. varName .. " = " .. tostring(value))
            end
            -- Record the variable name so we know the order for loading
            state:push_string(varName)
        end
    end
    
    -- Store the count of variables saved
    local varCount = 0
    for k, _ in pairs(_G) do
        if type(k) == "string" and k:sub(1, 8) == "SC2_USR_" then
            varCount = varCount + 1
        end
    end
    state:push_int(varCount)
    log("OnSave: Saved " .. varCount .. " variables")
end


function OnLoad(state)
    -- Get the number of variables to restore
    local varCount = state:pop_int()
    log("OnLoad: Restoring " .. varCount .. " variables")
    
    -- Restore variables in reverse order of saving
    for i = 1, varCount do
        local varName = state:pop_string()
        
        -- Check the type of the next value and load appropriately
        -- This requires knowing the type in advance or having a type marker
        if type(_G[varName]) == "number" then
            _G[varName] = state:pop_int()
            log("Loading number: " .. varName .. " = " .. tostring(_G[varName]))
        elseif type(_G[varName]) == "boolean" then
            _G[varName] = state:pop_bool()
            log("Loading boolean: " .. varName .. " = " .. tostring(_G[varName]))
        elseif type(_G[varName]) == "string" then
            _G[varName] = state:pop_string()
            log("Loading string: " .. varName .. " = " .. tostring(_G[varName]))
        end
    end
end'''
import argparse
import json
import sys
import os
from Script2_Language.Script2_Parser import *

def parse_arguments():
    """Parse command line arguments"""
    par = argparse.ArgumentParser(description='Convert PopScript to Lua')
    par.add_argument('input_file', help='Input script file (e.g. cpscr10.scr)')
    par.add_argument('output_file', help='Output Lua file (e.g. Level1_Blue.lua)')
    par.add_argument('system_spec', help='System specification JSON file')
    par.add_argument('--tribe', default='TRIBE_BLUE', 
                       choices=['TRIBE_BLUE', 'TRIBE_RED', 'TRIBE_YELLOW', 'TRIBE_GREEN'],
                       help='Default tribe for commands (default: TRIBE_BLUE)')
    return par.parse_args()

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
    "STATE_AUTO_ATTACK": "CP_AT_TYPE_AUTO_ATTACK"
}

# First, define a centralized function for INT_ conversions

def convert_int_constant(int_value):
    """
    Central function to convert INT_ constants to their Script4 equivalents
    """
    # Handle non-string values or empty values
    if not isinstance(int_value, str) or not int_value:
        return int_value
        
    # Special mappings that don't follow the standard pattern
    special_mappings = {
        "INT_NO_SPECIFIC_SPELL": "M_SPELL_NONE",
        "INT_NO_SPECIFIC_BUILDING": "0",
        "INT_NO_SPECIFIC_PERSON": "0",
        "INT_WRATH_OF_GOD": "M_SPELL_ARMAGEDDON",
        "INT_CONVERT": "M_SPELL_CONVERT_WILD",
        "INT_TARGET_MEDICINE_MAN": "ATTACK_TARGET_MEDICINE_MAN",
    }
    
    if int_value in special_mappings:
        return special_mappings[int_value]
    
    # People access - convert to GSI paths when needed
    people_mappings = {
        "INT_MY_NUM_PEOPLE": "_gsi.Players[MY_TRIBE].NumPeople",
        "INT_BLUE_PEOPLE": "_gsi.Players[TRIBE_BLUE].NumPeople",
        "INT_RED_PEOPLE": "_gsi.Players[TRIBE_RED].NumPeople",
        "INT_YELLOW_PEOPLE": "_gsi.Players[TRIBE_YELLOW].NumPeople",
        "INT_GREEN_PEOPLE": "_gsi.Players[TRIBE_GREEN].NumPeople",
        "INT_WILD_PEOPLE": "_gnsi.NumWildPeople",
    }
    
    if int_value in people_mappings:
        return people_mappings[int_value]
    
    # Tribe-specific person counts
    if int_value.startswith("INT_") and ("_PERSON_" in int_value):
        parts = int_value.split("_PERSON_")
        if len(parts) == 2:
            tribe_prefix = parts[0][-1]  # Get B, R, Y, G or M
            person_type = parts[1]
            tribe_map = {
                "B": "TRIBE_BLUE",
                "R": "TRIBE_RED",
                "Y": "TRIBE_YELLOW", 
                "G": "TRIBE_GREEN",
                "M": "MY_TRIBE"
            }
            tribe = tribe_map.get(tribe_prefix, "MY_TRIBE")
            return f"_gsi.Players[{tribe}].NumPeopleOfType[M_PERSON_{person_type}]"
    
    # Standard spell mappings
    spell_names = [
        "BLAST", "BURN", "LIGHTNING_BOLT", "WHIRLWIND", "INSECT_PLAGUE", 
        "INVISIBILITY", "HYPNOTISM", "FIRESTORM", "GHOST_ARMY", "EROSION", 
        "SWAMP", "LAND_BRIDGE", "ANGEL_OF_DEATH", "EARTHQUAKE", "FLATTEN", 
        "VOLCANO", "SHIELD", "TELEPORT", "BLOODLUST"
    ]
    
    if int_value.startswith("INT_") and any(spell in int_value for spell in spell_names):
        return int_value.replace("INT_", "M_SPELL_")
    
    # Building type mappings
    building_types = [
        "TEPEE", "HUT", "FARM", "DRUM_TOWER", "TEMPLE", "SPY_TRAIN", 
        "WARRIOR_TRAIN", "SUPER_TRAIN", "WALL_PIECE", "GATE",
        "BOAT_HUT_1", "BOAT_HUT_2", "AIRSHIP_HUT_1", "AIRSHIP_HUT_2"
    ]
    
    if int_value.startswith("INT_") and any(building in int_value for building in building_types):
        for building in building_types:
            if building in int_value and not "_BUILDING_" in int_value:
                return int_value.replace(f"INT_{building}", f"M_BUILDING_{building}")
        return int_value.replace("INT_", "M_BUILDING_")
    
    # Person type mappings without tribe prefix (INT_WARRIOR etc.)
    person_types = ["BRAVE", "WARRIOR", "RELIGIOUS", "SPY", "SUPER_WARRIOR", "MEDICINE_MAN"]
    if int_value in [f"INT_{t}" for t in person_types]:
        return int_value.replace("INT_", "M_PERSON_")
    
    # Player-specific prefixes
    for prefix in ["INT_M_", "INT_B_", "INT_R_", "INT_Y_", "INT_G_"]:
        if int_value.startswith(prefix):
            return int_value.replace(prefix, "M_")
    
    # Default case - just remove the INT_ prefix
    if int_value.startswith("INT_"):
        return int_value[4:]
    
    return int_value

def convert_user_var_name(var_name):
    """Convert USER_ variable names to SC2_USR_ format"""
    if isinstance(var_name, str) and var_name.startswith('USER_'):
        return var_name.replace('USER_', 'SC2_USR_')
    return var_name

# Then update the command map functions to use this helper
def build_command_map(tribe):
    command_map = {
        "GET_SPELLS_CAST": lambda p: f"{convert_user_var_name(p[4])} = GET_SPELLS_CAST(TRIBE_{p[2]}, {p[3].replace('INT_', 'M_SPELL_')})",
        "GET_HEIGHT_AT_POS": lambda p: f"{convert_user_var_name(p[3])} = GET_HEIGHT_AT_POS({p[2]})",
        "GET_HEAD_TRIGGER_COUNT": lambda p: f"{convert_user_var_name(p[4])} = GET_HEAD_TRIGGER_COUNT({p[2]}, {p[3]})",
        "GET_NUM_ONE_OFF_SPELLS": lambda p: f"{convert_user_var_name(p[4])} = GET_NUM_ONE_OFF_SPELLS(TRIBE_BLUE, {p[3].replace('INT_', 'M_SPELL_')})",
        "COUNT_PEOPLE_IN_MARKER": lambda p: f"{convert_user_var_name(p[5])} = COUNT_PEOPLE_IN_MARKER(TRIBE_{p[2]}, {p[3]}, {p[4]})",
        
        # Core commands
        "SET_REINCARNATION": lambda p: f"SET_REINCARNATION({p[2]}, MY_TRIBE)",
        "DELAY_MAIN_DRUM_TOWER": lambda p: f"DELAY_MAIN_DRUM_TOWER(ON, MY_TRIBE)",
        "SET_ATTACK_VARIABLE": lambda p: f"SET_ATTACK_VARIABLE(MY_TRIBE, {p[2]})",
        "DISABLE_USER_INPUTS": lambda p: f"DISABLE_USER_INPUTS()",
        "ENABLE_USER_INPUTS": lambda p: f"ENABLE_USER_INPUTS()",
        
        # State commands - using STATE_SET instead of SET_STATE
        "STATE_BRING_NEW_PEOPLE_BACK": lambda p: f"STATE_SET(MY_TRIBE, {STATE_CP_MAP['STATE_BRING_NEW_PEOPLE_BACK']}, {p[2]})",
        "STATE_TRAIN_PEOPLE": lambda p: f"STATE_SET(MY_TRIBE, {STATE_CP_MAP['STATE_TRAIN_PEOPLE']}, {p[2]})",
        "STATE_MED_MAN_GET_WILD_PEEPS": lambda p: f"STATE_SET(MY_TRIBE, {STATE_CP_MAP['STATE_MED_MAN_GET_WILD_PEEPS']}, {p[2]})",
        "STATE_CONSTRUCT_BUILDING": lambda p: f"STATE_SET(MY_TRIBE, {STATE_CP_MAP['STATE_CONSTRUCT_BUILDING']}, {p[2]})",
        "STATE_FETCH_WOOD": lambda p: f"STATE_SET(MY_TRIBE, {STATE_CP_MAP['STATE_FETCH_WOOD']}, {p[2]})",
        "STATE_SEND_GHOSTS": lambda p: f"STATE_SET(MY_TRIBE, {STATE_CP_MAP['STATE_SEND_GHOSTS']}, {p[2]})",
        "STATE_FETCH_LOST_PEOPLE": lambda p: f"STATE_SET(MY_TRIBE, {STATE_CP_MAP['STATE_FETCH_LOST_PEOPLE']}, {p[2]})",
        "STATE_FETCH_FAR_VEHICLE": lambda p: f"STATE_SET(MY_TRIBE, {STATE_CP_MAP['STATE_FETCH_FAR_VEHICLE']}, {p[2]})",
        "STATE_FETCH_LOST_VEHICLE": lambda p: f"STATE_SET(MY_TRIBE, {STATE_CP_MAP['STATE_FETCH_LOST_VEHICLE']}, {p[2]})",
        "STATE_DEFEND": lambda p: f"STATE_SET(MY_TRIBE, {STATE_CP_MAP['STATE_DEFEND']}, {p[2]})",
        "STATE_DEFEND_BASE": lambda p: f"STATE_SET(MY_TRIBE, {STATE_CP_MAP['STATE_DEFEND_BASE']}, {p[2]})",
        "STATE_HOUSE_A_PERSON": lambda p: f"STATE_SET(MY_TRIBE, {STATE_CP_MAP['STATE_HOUSE_A_PERSON']}, {p[2]})",
        "STATE_AUTO_ATTACK": lambda p: f"STATE_SET(MY_TRIBE, {STATE_CP_MAP['STATE_AUTO_ATTACK']}, {p[2]})",
        "STATE_SPELL_DEFENCE": lambda p: f"SHAMAN_DEFEND(MY_TRIBE, {p[2]}, {p[3]}, {p[4]})",

        # Marker and defense commands
        "SET_DEFENCE_RADIUS": lambda p: f"SET_DEFENCE_RADIUS(MY_TRIBE, {p[2]})",
        "SET_MARKER_ENTRY": lambda p: f"SET_MARKER_ENTRY(MY_TRIBE, {p[2]}, {p[3]}, {p[4]}, {p[5]}, {p[6]}, {p[7]}, {p[8]})",
        "ONLY_STAND_AT_MARKERS": lambda p: f"ONLY_STAND_AT_MARKERS(MY_TRIBE)",
        "MARKER_ENTRIES": lambda p: f"MARKER_ENTRIES(MY_TRIBE, {p[2]}, {p[3]}, {p[4]}, {p[5]})",
        
        # Spell related commands - removed invalid functions
        
        "SET_SPELL_ENTRY": map_set_spell_entry,        
        "SET_BUCKET_COUNT_FOR_SPELL": lambda p: f"SET_BUCKET_COUNT_FOR_SPELL(MY_TRIBE, {convert_int_constant(p[2])}, {p[3]})",
        
        # Flyby commands 
        "FLYBY_CREATE_NEW": lambda p: "FLYBY_CREATE_NEW()",
        "FLYBY_ALLOW_INTERRUPT": lambda p: f"FLYBY_ALLOW_INTERRUPT({p[2]})",
        "FLYBY_SET_EVENT_POS": lambda p: f"FLYBY_SET_EVENT_POS({p[2]}, {p[3]}, {p[4]}, {p[5]})",
        "FLYBY_SET_EVENT_ANGLE": lambda p: f"FLYBY_SET_EVENT_ANGLE({p[2]}, {p[3]}, {p[4]})",
        "FLYBY_SET_EVENT_ZOOM": lambda p: f"FLYBY_SET_EVENT_ZOOM({p[2]}, {p[3]}, {p[4]})",
        "FLYBY_SET_EVENT_TOOLTIP": lambda p: f"FLYBY_SET_EVENT_TOOLTIP({p[2]}, {p[3]}, {p[4]}, {p[5]}, {p[6]})",
        "FLYBY_SET_END_TARGET": lambda p: f"FLYBY_SET_END_TARGET({p[2]}, {p[3]}, {p[4]}, {p[5]})",
        "FLYBY_START": lambda p: "FLYBY_START()",

        # Message commands
        "CREATE_MSG_INFORMATION": lambda p: f"CREATE_MSG_INFORMATION({p[2]})",
        "SET_MSG_AUTO_OPEN_DLG": lambda p: "SET_MSG_AUTO_OPEN_DLG()",
        "SET_MSG_DELETE_ON_OK": lambda p: "SET_MSG_DELETE_ON_OK()",

        # Utility commands
        "PARTIAL_BUILDING_COUNT": lambda p: f"PARTIAL_BUILDING_COUNT(MY_TRIBE)",
        "TRIGGER_THING": lambda p: f"TRIGGER_THING({p[2]})",
        "REMOVE_HEAD_AT_POS": lambda p: f"REMOVE_HEAD_AT_POS({p[2]}, {p[3]})",
        "DEFEND_SHAMEN": lambda p: f"DEFEND_SHAMEN(MY_TRIBE, _gsi.Players[MY_TRIBE].NumPeople)",
        "TRAIN_PEOPLE_NOW": lambda p: f"TRAIN_PEOPLE_NOW(MY_TRIBE, {p[2]}, {p[3].replace('INT_', 'M_PERSON_')})",

        # Turn commands
        "TURN_PUSH": lambda p: f"TURN_PUSH({p[2]})",
        "SET_BUCKET_USAGE": lambda p: f"SET_BUCKET_USAGE(MY_TRIBE, {p[2]})",
        "ATTACK": map_attack_command,
    }
    return command_map

def map_set_spell_entry(p):
    """Helper function for SET_SPELL_ENTRY command mapping"""
    spell_idx = p[2]  # The spell slot index
    spell_type = p[3]  # The spell type (INT_BLAST, 0, etc.)
    
    # For the spell parameter in the function
    if spell_type.startswith('INT_'):
        spell_param = spell_type.replace('INT_', 'M_SPELL_')
    else:
        spell_param = spell_type
    
    # For the spell cost parameter
    if spell_type == '0':
        # Special case: spell type 0 maps to BLAST for cost
        cost_spell = 'M_SPELL_BLAST'
    elif spell_type.startswith('INT_'):
        cost_spell = 'M_SPELL_' + spell_type.replace('INT_', '')
    else:
        cost_spell = 'M_SPELL_' + spell_type
    
    return f"SET_SPELL_ENTRY(MY_TRIBE, {spell_idx}, {spell_param}, PLAYERS_SPELL_COST(MY_TRIBE, {cost_spell}), {p[5]}, {p[6]}, {p[7]})"

def build_variable_map(tribe):
    return {
        "INT_MY_NUM_PEOPLE": lambda: f"_gsi.Players[MY_TRIBE].NumPeople",
        "INT_MY_NUM_BUILDINGS": lambda: f"GetPlayerBuildings(MY_TRIBE)",
        "INT_GAME_TURN": lambda: "getTurn()",
        "INT_MY_NUM_KILLED_BY_BLUE": lambda: f"_gsi.Players[TRIBE_BLUE].PeopleKilled[MY_TRIBE]",
        "INT_BLUE_PEOPLE": lambda: "GET_NUM_PEOPLE(TRIBE_BLUE)",
        
        # Building and person types
        "INT_M_PERSON_WARRIOR": lambda: f"_gsi.Players[MY_TRIBE].NumPeopleOfType[M_PERSON_WARRIOR]",
        "INT_B_PERSON_WARRIOR": lambda: "_gsi.Players[TRIBE_BLUE].NumPeopleOfType[M_PERSON_WARRIOR]",
        "INT_M_BUILDING_TEPEE": lambda: f"PLAYERS_BUILDING_OF_TYPE(MY_TRIBE, M_BUILDING_TEPEE)",
        "INT_B_BUILDING_TEPEE": lambda: "PLAYERS_BUILDING_OF_TYPE(TRIBE_BLUE, M_BUILDING_TEPEE)",
        "INT_B_BUILDING_HUT": lambda: "PLAYERS_BUILDING_OF_TYPE(TRIBE_BLUE, M_BUILDING_HUT)",
        "INT_B_BUILDING_FARM": lambda: "PLAYERS_BUILDING_OF_TYPE(TRIBE_BLUE, M_BUILDING_FARM)",
        "INT_B_BUILDING_WARRIOR_TRAIN": lambda: "PLAYERS_BUILDING_OF_TYPE(TRIBE_BLUE, M_BUILDING_WARRIOR_TRAIN)",
        "INT_WARRIOR": lambda: "M_PERSON_WARRIOR",
    }

# Add operator mapping dictionary
OPERATOR_MAP = {
    "GREATER_THAN": ">",
    "LESS_THAN": "<",
    "EQUAL_TO": "==",
    "GREATER_THAN_EQUAL_TO": ">=",
    "LESS_THAN_EQUAL_TO": "<=",
    "DOESNT_EQUAL": "~=",
    "!=": "~=",  # Add explicit mapping for !=
    "AND": "and",
    "OR": "or"
}

def load_system_spec(filepath):
    """Loads the system specification from JSON file"""
    with open(filepath, 'r') as f:
        return json.load(f)

def validate_command_map(command_map, system_spec):
    """
    Validates command mappings against the system specification
    Returns tuple of (valid_commands, invalid_commands)
    """
    valid_commands = {}
    invalid_commands = {}
    
    # Extract all available functions and their parameter counts from modules
    available_functions = {}  # Changed to dict to store function info
    for module in system_spec.get('modules', []):
        for func in module.get('functions', []):
            if not func.get('deprecated', False):
                name = func.get('name', '')
                params = func.get('parameters', [])
                return_type = func.get('return', None)
                
                # Handle void parameter functions
                if isinstance(params, list) and len(params) == 1 and (
                    (isinstance(params[0], dict) and params[0].get('type') == 'void') or 
                    (isinstance(params[0], str) and params[0].lower() == 'void')
                ):
                    param_count = 0
                else:
                    param_count = len(params)
                
                available_functions[name] = {
                    'params': param_count,
                    'return_type': return_type
                }
    
    # Validate each command mapping
    for cmd_name, cmd_func in command_map.items():
        try:
            # Create dummy params list with enough elements
            test_params = ['DO', cmd_name] + ['0'] * 15
            result = cmd_func(test_params)
            
            # Extract function name and parameter count from the result
            # Handle cases with assignment (e.g., 'USER_0 = GET_SPELLS_CAST(...)')
            if '=' in result:
                func_call = result.split('=')[1].strip()
            else:
                func_call = result

            # Helper function to count parameters while handling nested functions
            def count_params(func_str):
                # Handle empty parameter case
                if not '(' in func_str or not ')' in func_str:
                    return 0
                    
                params_str = func_str[func_str.find('(')+1:func_str.rfind(')')]
                if not params_str.strip():
                    return 0
                
                param_count = 0
                paren_count = 0
                current_param = ''
                
                for char in params_str:
                    if char == '(' and paren_count == 0:
                        paren_count += 1
                    elif char == '(' and paren_count > 0:
                        paren_count += 1
                        current_param += char
                    elif char == ')' and paren_count > 1:
                        paren_count -= 1
                        current_param += char
                    elif char == ')' and paren_count == 1:
                        paren_count -= 1
                    elif char == ',' and paren_count == 0:
                        param_count += 1
                        current_param = ''
                    else:
                        current_param += char
                        
                # Count the last parameter if exists
                if current_param.strip():
                    param_count += 1
                    
                return param_count

            # Extract base function name and count parameters
            func_parts = func_call.split('(')
            base_func = func_parts[0].strip()
            param_count = count_params(func_call)
            
            # Check if the function is assigning to a return value
            has_return_assignment = '=' in result and result.split('=')[0].strip()
            
            if base_func in available_functions:
                func_info = available_functions[base_func]
                expected_params = func_info['params']
                has_return_type = func_info['return_type'] is not None and func_info['return_type'] != 'void'
                
                # Validate parameter count
                if param_count != expected_params:
                    invalid_commands[cmd_name] = (
                        f"Parameter count mismatch for {base_func}: "
                        f"got {param_count}, expected {expected_params}"
                    )
                # Validate return value assignment
                elif has_return_type and not has_return_assignment:
                    invalid_commands[cmd_name] = (
                        f"Function {base_func} requires return value assignment"
                    )
                elif not has_return_type and has_return_assignment:
                    invalid_commands[cmd_name] = (
                        f"Function {base_func} does not return a value but assignment found"
                    )
                else:
                    valid_commands[cmd_name] = cmd_func
            else:
                invalid_commands[cmd_name] = f"Function {base_func} not found in system spec"
        except Exception as e:
            invalid_commands[cmd_name] = f"Error processing command: {str(e)}"

    return valid_commands, invalid_commands

def convert_script(input_file, output_file, system_spec, tribe, command_map, variable_map):
    """
    Converts a Script2 format file to Script4 (Lua) format
    
    Args:
        input_file: Path to the input Script2 file
        output_file: Path to save the output Lua file
        system_spec: JSON system specification
        tribe: The target tribe for the script
        command_map: Command mapping dictionary
        variable_map: Variable mapping dictionary
    """
    # Read the input script
    with open(input_file, 'r') as f:
        script_content = f.read()
        
    parsed_script = Parse_Script2(script_content)
    
    # Generate Lua output
    lua_output = []
    
    # Add standard header
    lua_output.append('-- ' + output_file)
    lua_output.append('-- Generated from ' + input_file + ' by script2_to_script4 converter')
    lua_output.append('import(Module_DataTypes)')
    lua_output.append('import(Module_PopScript)')
    lua_output.append('import(Module_Globals)')
    lua_output.append('import(Module_Helpers)')
    lua_output.append('import(Module_Players)')
    lua_output.append('import(Module_Defines)')
    lua_output.append('import(Module_Objects)')
    lua_output.append('import(Module_System)')
    lua_output.append('import(Module_String)')
    lua_output.append('import(Module_Bit32)')
    lua_output.append('import(Module_Game)')
    lua_output.append('import(Module_Map)')
    lua_output.append('')
    
    # Add script description
    lua_output.append('-- ' + os.path.basename(input_file) + ' converted to Script4')
    lua_output.append('-- This script was automatically converted from Script2 format to Script4 format')
    lua_output.append('')

    # Define global constants
    lua_output.append('-- SCRIPT CONFIG')
    lua_output.append(f'MY_TRIBE = {tribe}')
    lua_output.append('')
    
    # Define global constants
    lua_output.append('-- GLOBAL CONSTANTS')
    lua_output.append('OFF = 0')
    lua_output.append('ON = 1')
    lua_output.append('')
    
    # Extract user variables from parsed script and define them
    user_vars = extract_user_variables(parsed_script)
    if user_vars:
        lua_output.append('-- USER VARIABLES')
        for var_name in sorted(user_vars):
            # Replace USER_ with SC2_USR_ in variable definitions
            new_var_name = var_name.replace('USER_', 'SC2_USR_')
            lua_output.append(f'{new_var_name} = 0')
        lua_output.append('')
    
    # Add GSI reference
    lua_output.append('-- Capture the global save items into a local variable')
    lua_output.append('_gsi = gsi()')
    lua_output.append('_gnsi = gnsi()')
    lua_output.append('')
    
    # Add after GSI reference in convert_script function
    lua_output.append('-- Initialize Computer Player')
    lua_output.append(f'computer_init_player(getPlayer(MY_TRIBE))')
    lua_output.append('')
    
    # Extract spells and buildings to enable
    spells, buildings = extract_spells_and_buildings(parsed_script)
    
    #if spells:
    #    lua_output.append('-- AI spells')
    #    lua_output.append('_bot_spells = { ' + ', '.join(spells) + ' }')
    
    #if buildings:
    #    lua_output.append('-- AI buildings')
    #    lua_output.append('_bot_buildings = { ' + ', '.join(buildings) + ' }')
    
    lua_output.append('')
    
    # Add OnTurn function
    lua_output.append('function OnTurn()')
    
    # Process the entire script structure and convert it
    converted_code = convert_script_structure(parsed_script, tribe, command_map, variable_map)
    lua_output.extend(['    ' + line for line in converted_code])
    
    # Close the OnTurn function
    lua_output.append('end')

    lua_output.append(
    '''
function OnSave(state)
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
end
    ''')

    # Write the output file
    with open(output_file, 'w') as f:
        f.write('\n'.join(lua_output))
    
    print(f"Converted {input_file} to {output_file}")

def extract_user_variables(parsed_script):
    """Extract user variables from the parsed script"""
    user_vars = set()
    
    # Function to recursively scan for variables in the AST
    def scan_for_variables(node):
        if isinstance(node, tuple):
            if len(node) >= 2:
                # Check if this is a SET operation for a user variable
                if node[0] == 'set' and isinstance(node[1], str) and node[1].startswith('USER_'):
                    user_vars.add(node[1])
                # Check each element in the tuple
                for item in node:
                    scan_for_variables(item)
        elif isinstance(node, list):
            for item in node:
                scan_for_variables(item)
    
    # Start scanning from the script node
    if isinstance(parsed_script, tuple) and parsed_script[0] == 'script':
        # The script structure is ('script', id, statements)
        statements = parsed_script[2]
        scan_for_variables(statements)
    
    return user_vars

def extract_spells_and_buildings(parsed_script):
    """
    Extract spells and buildings used in the script
    
    Returns:
        tuple: (spells, buildings) where each is a list of spell/building constants
    """
    # Default essential spells and buildings
    spells = ["M_SPELL_BLAST", "M_SPELL_CONVERT"]
    buildings = ["M_BUILDING_TEPEE", "M_BUILDING_DRUM_TOWER"]
    
    # Add any detectable spells and buildings from the script
    # This would involve analyzing the parsed script for specific spell/building references
    # For now, we'll just include common ones
    
    # For warrior training
    if "INT_WARRIOR" in str(parsed_script):
        buildings.append("M_BUILDING_WARRIOR_TRAIN")
    
    # For specific spells
    if "INT_BLAST" in str(parsed_script) or "BLAST" in str(parsed_script):
        if "M_SPELL_BLAST" not in spells:
            spells.append("M_SPELL_BLAST")
    
    if "INT_LAND_BRIDGE" in str(parsed_script) or "LAND_BRIDGE" in str(parsed_script):
        spells.append("M_SPELL_LAND_BRIDGE")
    
    if "INT_LIGHTNING_BOLT" in str(parsed_script) or "LIGHTNING" in str(parsed_script):
        spells.append("M_SPELL_LIGHTNING_BOLT")
    
    return spells, buildings

def convert_script_structure(parsed_script, tribe, command_map, variable_map):
    """
    Convert the parsed script structure to Lua code
    
    Args:
        parsed_script: The parsed Script2 structure
        tribe: The target tribe
        command_map: Command mapping dictionary
        variable_map: Variable mapping dictionary
        
    Returns:
        list: Lines of converted Lua code
    """
    result = []
    
    # Extract the main statements from the script
    if isinstance(parsed_script, tuple) and parsed_script[0] == 'script':
        # The script structure is ('script', id, statements)
        statements = parsed_script[2]
        
        # Convert the statements
        if isinstance(statements, tuple) and statements[0] == 'statements':
            converted = convert_statements(statements[1], tribe, command_map, variable_map)
            result.extend(converted)
    
    return result

def convert_statements(statements, tribe, command_map, variable_map):
    """Convert a list of statements to Lua"""
    result = []
    
    for stmt in statements:
        converted = convert_statement(stmt, tribe, command_map, variable_map)
        if converted:
            result.extend(converted)
    
    return result

def convert_statement(stmt, tribe, command_map, variable_map, indent=0):
    """Convert a single statement to Lua"""
    result = []
    indent_str = '    ' * indent
    
    if isinstance(stmt, tuple):
        stmt_type = stmt[0]
        
        # Handle different statement types
        if stmt_type == 'if-else':
            # Format: ('if-else', condition, if_body, else_body)
            condition = convert_condition(stmt[1], variable_map)
            result.append(f"{indent_str}if {condition} then")
            
            # Convert if body
            if_body = convert_statements(stmt[2], tribe, command_map, variable_map)
            result.extend([f"{indent_str}    {line}" for line in if_body])
            
            # Check if there's an else body
            if len(stmt) > 3 and stmt[3]:
                result.append(f"{indent_str}else")
                else_body = convert_statements(stmt[3], tribe, command_map, variable_map)
                result.extend([f"{indent_str}    {line}" for line in else_body])
            
            result.append(f"{indent_str}end")
            
        elif stmt_type == 'if':
            # Format: ('if', condition, body)
            condition = convert_condition(stmt[1], variable_map)
            result.append(f"{indent_str}if {condition} then")
            
            # Convert body
            body = convert_statements(stmt[2], tribe, command_map, variable_map)
            result.extend([f"{indent_str}    {line}" for line in body])
            
            result.append(f"{indent_str}end")
            
        elif stmt_type == 'every':
            # Format: ('every', period, offset, body)
            period = stmt[1]
            offset = stmt[2]
            
            # Check if period is a power of 2
            if period == None:
                # It's a power of 2, determine the power
                power = 0
                period_int = int(period)
                while period_int > 1:
                    period_int >>= 1
                    power += 1
                result.append(f"{indent_str}if EVERY_2POW_TURNS({power}) then")
            elif offset == None:
                result.append(f"{indent_str}if EVERY_2POW_TURNS({int(period)}) then")
            else:
                result.append(f"{indent_str}if ((getTurn() + MY_TRIBE + {offset}) % {period} == 0) then")
            
            # Convert body
            body = convert_statements(stmt[3], tribe, command_map, variable_map)
            result.extend([f"{indent_str}    {line}" for line in body])
            
            result.append(f"{indent_str}end")
            
        elif stmt_type == 'do':
            # Format: ('do', command, arg1, arg2, ...)
            # Handle the special case where there's a missing command (just a variable)
            if len(stmt) == 2 and isinstance(stmt[1], str) and stmt[1].startswith('USER_'):
                # Convert USER_ to SC2_USR_ for standalone variables
                new_var_name = stmt[1].replace('USER_', 'SC2_USR_')
                # This is just a user variable with no command - log a warning
                result.append(f"{indent_str}-- WARNING: Standalone user variable '{new_var_name}' with no command")
                return result
            
            cmd = stmt[1]
            args = stmt[2:] if len(stmt) > 2 else []
            
            # Try to map the command using the command_map
            if cmd in command_map:
                converted_cmd = command_map[cmd](list(['DO'] + [cmd] + list(args)))
                result.append(f"{indent_str}{converted_cmd}")
            else:
                # For unmapped commands, create a default conversion
                args_str = ', '.join(convert_arg(arg, variable_map) for arg in args)
                result.append(f"{indent_str}{cmd}({args_str})")
            
        elif stmt_type == 'set':
            var = convert_variable(stmt[1], variable_map, tribe)
            value = convert_value(stmt[2], variable_map)
            
            if stmt[1].startswith('INT_ATTR_'):
                # Handle attribute settings specially
                attr_name = stmt[1][9:]  # Remove 'INT_ATTR_' prefix
                result.append(f"{indent_str}WRITE_CP_ATTRIB(MY_TRIBE, ATTR_{attr_name}, {value})")
            else:
                # Regular variable assignment
                result.append(f"{indent_str}{var} = {value}")
                
        elif stmt_type == 'increment':
            # Format: ('increment', variable, value)
            value = convert_value(stmt[2], variable_map)
            
            if stmt[1].startswith('INT_ATTR_'):
                # Handle attribute increments specially
                attr_name = stmt[1][9:]  # Remove 'INT_ATTR_' prefix
                result.append(f"{indent_str}WRITE_CP_ATTRIB(MY_TRIBE, ATTR_{attr_name}, READ_CP_ATTRIB(MY_TRIBE, ATTR_{attr_name}) + {value})")
            else:
                # Regular variable increment
                var = convert_variable(stmt[1], variable_map, tribe)
                result.append(f"{indent_str}{var} = {var} + {value}")
                
        elif stmt_type == 'decrement':
            # Format: ('decrement', variable, value)
            value = convert_value(stmt[2], variable_map)
            
            if stmt[1].startswith('INT_ATTR_'):
                # Handle attribute decrements specially
                attr_name = stmt[1][9:]  # Remove 'INT_ATTR_' prefix
                result.append(f"{indent_str}WRITE_CP_ATTRIB(MY_TRIBE, ATTR_{attr_name}, READ_CP_ATTRIB(MY_TRIBE, ATTR_{attr_name}) - {value})")
            else:
                # Regular variable decrement
                var = convert_variable(stmt[1], variable_map, tribe)
                result.append(f"{indent_str}{var} = {var} - {value}")
                
        elif stmt_type == 'multiply':
            # Format: ('multiply', result_var, var1, var2)
            var1 = convert_value(stmt[2], variable_map)
            var2 = convert_value(stmt[3], variable_map)
            
            if stmt[1].startswith('INT_ATTR_'):
                # Handle attribute multiplication specially
                attr_name = stmt[1][9:]  # Remove 'INT_ATTR_' prefix
                result.append(f"{indent_str}WRITE_CP_ATTRIB(MY_TRIBE, ATTR_{attr_name}, {var1} * {var2})")
            else:
                # Regular variable multiplication
                result_var = convert_variable(stmt[1], variable_map, tribe)
                result.append(f"{indent_str}{result_var} = {var1} * {var2}")
            
    return result

def convert_condition(condition, variable_map):
    """Convert a condition to Lua syntax"""
    if isinstance(condition, tuple):
        if len(condition) == 3:
            # Binary operator: (op, left, right)
            op = condition[0]
            
            # Map operators
            op_map = {
                '==': '==',
                '!=': '~=',
                '<': '<',
                '>': '>',
                '<=': '<=',
                '>=': '>=',
                'AND': 'and',
                'OR': 'or',
                'EQUAL_TO': '==',
                'NOT_EQUAL_TO': '~=',
                'GREATER_THAN': '>',
                'LESS_THAN': '<',
                'GREATER_THAN_EQUAL_TO': '>=',
                'LESS_THAN_EQUAL_TO': '<=',
                'DOESNT_EQUAL': '~=',
                '&&': 'and',
                '||': 'or'
            }
            
            lua_op = op_map.get(op, op)
            
            # Special handling for logical operators that might have nested conditions
            if op in ('&&', '||', 'AND', 'OR'):
                left = convert_condition(condition[1], variable_map)
                right = convert_condition(condition[2], variable_map)
                return f"({left} {lua_op} {right})"
            else:
                # Check if left or right are attribute accesses
                if isinstance(condition[1], str) and condition[1].startswith('INT_ATTR_'):
                    attr_name = condition[1][9:]  # Remove 'INT_ATTR_' prefix
                    left = f"READ_CP_ATTRIB(MY_TRIBE, ATTR_{attr_name})"
                else:
                    left = convert_value(condition[1], variable_map)
                
                if isinstance(condition[2], str) and condition[2].startswith('INT_ATTR_'):
                    attr_name = condition[2][9:]  # Remove 'INT_ATTR_' prefix
                    right = f"READ_CP_ATTRIB(MY_TRIBE, ATTR_{attr_name})"
                else:
                    right = convert_value(condition[2], variable_map)
                
                return f"{left} {lua_op} {right}"
    
    # For simple conditions
    if isinstance(condition, str) and condition.startswith('INT_ATTR_'):
        attr_name = condition[9:]  # Remove 'INT_ATTR_' prefix
        return f"READ_CP_ATTRIB(MY_TRIBE, ATTR_{attr_name})"
    else:
        return convert_value(condition, variable_map)

def convert_variable(var, variable_map, tribe):
    """Convert a variable name to Lua syntax"""
    if var in variable_map:
        return variable_map[var]()
    elif var.startswith('USER_'):
        # Replace USER_ with SC2_USR_ in variable references
        return var.replace('USER_', 'SC2_USR_')
    elif var.startswith('INT_'):
        if var.startswith('INT_ATTR_'):
            # Handle attribute settings specially
            attr_name = var[9:]  # Remove 'INT_ATTR_' prefix
            return f"READ_CP_ATTRIB(MY_TRIBE, ATTR_{attr_name})"  # Use READ_CP_ATTRIB
        elif var.startswith('INT_B_BUILDING_'):
            building_type = var.replace('INT_B_BUILDING_', '')
            return f"PLAYERS_BUILDING_OF_TYPE(TRIBE_BLUE, M_BUILDING_{building_type})"
        elif var.startswith('INT_B_PERSON_'):
            person_type = var.replace('INT_B_PERSON_', '')
            return f"_gsi.Players[TRIBE_BLUE].NumPeopleOfType[M_PERSON_{person_type}]"
        elif var == 'INT_GAME_TURN':
            return "getTurn()"
        elif var.startswith('INT_MY_'):
            var_name = var[7:]  # Remove 'INT_MY_' prefix
            return f"_gsi.Players[MY_TRIBE].{var_name}"
        elif var.startswith('INT_NO_SPECIFIC_'):
            return "M_SPELL_NONE"
        elif var == 'INT_WARRIOR':
            return 'M_PERSON_WARRIOR'
        else:
            # Default variable handling
            return var.replace('INT_', 'M_SPELL_')
    else:
        return var

def convert_value(value, variable_map):
    """Convert a value to Lua syntax"""
    if isinstance(value, str):
        # Check if it's a variable
        if value in variable_map:
            return variable_map[value]()
        elif value.startswith('USER_'):
            # Replace USER_ with SC2_USR_ in variable values
            return value.replace('USER_', 'SC2_USR_')
        elif value.startswith('INT_'):
            # Handle built-in constants/variables
            if value == 'INT_NO_SPECIFIC_SPELL':
                return 'M_SPELL_NONE'
            elif value == 'INT_NO_SPECIFIC_BUILDING':
                return 'ATTACK_BUILDING'
            elif value.startswith('INT_M_SPELL_'):
                return value.replace('INT_M_SPELL_', 'M_SPELL_')
            elif value.startswith('INT_M_'):
                return value.replace('INT_M_', 'M_')
            elif value.startswith('INT_B_'):
                return value.replace('INT_B_', 'B_')
            else:
                return value.replace('INT_', '')
        elif value == 'ATTACK_NORMAL':
            return 'ATTACK_NORMAL'
        elif value in ('ON', 'OFF', 'TRUE', 'FALSE'):
            return value
        elif value in ('BLUE', 'RED', 'GREEN', 'YELLOW'):
            return f'TRIBE_{value}'
        elif value.isdigit() or value == '-1':
            return value
        else:
            # For other string values
            return value
    else:
        # For non-string values
        return str(value)

def convert_arg(arg, variable_map):
    """Convert a command argument to Lua syntax"""
    return convert_value(arg, variable_map)

def map_attack_command(p):
    """Helper function for ATTACK command with variable parameters"""
    # Target tribe - always present
    target_tribe = f"TRIBE_{p[2]}"
    
    # Number of attackers - use the centralized function for INT_ constants
    num_attackers = p[3]
    if isinstance(num_attackers, str) and num_attackers.startswith("INT_"):
        # Special handling for person type counts
        if num_attackers in ["INT_BRAVE", "INT_WARRIOR", "INT_RELIGIOUS", "INT_SPY", "INT_SUPER_WARRIOR"]:
            person_type = convert_int_constant(num_attackers)
            num_attackers = f"_gsi.Players[MY_TRIBE].NumPeopleOfType[{person_type}]"
        else:
            num_attackers = convert_int_constant(num_attackers)
    
    # Attack type 
    attack_type = p[4]
    if isinstance(attack_type, str):
        if not attack_type.startswith("ATTACK_"):
            if attack_type.startswith("INT_"):
                attack_type = convert_int_constant(attack_type)
            if attack_type != "ATTACK_NORMAL":  # Avoid ATTACK_ATTACK_NORMAL
                attack_type = f"ATTACK_{attack_type}"
    
    # Target building/marker
    target = convert_int_constant(p[5])
    
    # Distance
    distance = p[6]
    
    # Spell types - use the centralized function
    spell1 = convert_int_constant(p[7] if len(p) > 7 else "INT_NO_SPECIFIC_SPELL")
    spell2 = convert_int_constant(p[8] if len(p) > 8 else "INT_NO_SPECIFIC_SPELL")
    spell3 = convert_int_constant(p[9] if len(p) > 9 else "INT_NO_SPECIFIC_SPELL")
    
    # Remaining parameters
    attack_mode = p[10] if len(p) > 10 else "ATTACK_NORMAL"
    param1 = p[11] if len(p) > 11 else "0"
    param2 = p[12] if len(p) > 12 else "-1"
    param3 = p[13] if len(p) > 13 else "-1"
    param4 = p[14] if len(p) > 14 else "-1"
    
    return f"ATTK_RST = ATTACK(MY_TRIBE, {target_tribe}, {num_attackers}, {attack_type}, {target}, {distance}, {spell1}, {spell2}, {spell3}, {attack_mode}, {param1}, {param2}, {param3}, {param4})"

# Extend the main function to use this converter
def main():
    """Main function with command line argument support"""
    args = parse_arguments()

    # Load system specification
    system_spec = load_system_spec(args.system_spec)

    # Build command map with tribe parameter
    # Build command map for each command and display function parameters
    command_map = build_command_map(args.tribe)
    
    print("\nCommand Map Function Parameters:")
    print("-" * 50)
    
    # Test each command with dummy parameters to see output format
    test_params = ['DO', 'CMD', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0']
    
    for cmd_name, cmd_func in sorted(command_map.items()):
        try:
            result = cmd_func(test_params)
            func_name = result.split('(')[0]
            params = result.split('(')[1].rstrip(')')
            print(f"{cmd_name}:")
            print(f"  {func_name}({params})")
            print()
        except Exception as e:
            print(f"{cmd_name}: Error analyzing parameters - {str(e)}\n")
    
    command_map = build_command_map(args.tribe)
    variable_map = build_variable_map(args.tribe)

    # Validate command mappings
    valid_commands, invalid_commands = validate_command_map(command_map, system_spec)

    # Report any invalid commands
    if invalid_commands:
        print("WARNING: Some commands are not valid in the system specification:")
        for cmd, reason in invalid_commands.items():
            print(f"  {cmd}: {reason}")

    # Convert the script
    convert_script(args.input_file, args.output_file, system_spec, args.tribe, valid_commands, variable_map)
    
if __name__ == "__main__":
    main()
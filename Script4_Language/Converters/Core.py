import os
import logging
import json
import re
from pathlib import Path
from Script2_Language.Script2_Parser import Parse_Script2
from Script4_Language.Converters.Statements import convert_statements
from Script4_Language.Config import *

"""
Script4_Language/Converters/Core.py
Core conversion logic and utilities for Script2 to Script4 conversion
"""

def convert_script_file(input_file, output_file, tribe, command_map, variable_map):
    """
    Converts a single Script2 file to Script4 format
    
    Args:
        input_file: Path to the input Script2 file
        output_file: Path to save the output Lua file
        tribe: The target tribe for the script
        command_map: Command mapping dictionary
        variable_map: Variable mapping dictionary
        
    Returns:
        SUCCESS or FAILURE
    """
    try:
        # Read the input script
        with open(input_file, 'r') as f:
            script_content = f.read()
        
        # Parse and convert the script
        
        parsed_script = Parse_Script2(script_content)
        if not parsed_script:
            logging.error(f"Failed to parse {input_file}")
            return FAILURE
        
        # Extract user variables
        user_variables = extract_user_variables(parsed_script)
        
        # Generate Lua output
        lua_output = convert_script(
            parsed_script,  
            input_file,
            output_file, 
            tribe, 
            command_map, 
            variable_map
        )
        
        # Write output to file
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            f.write('\n'.join(lua_output))
        
        logging.info(f"Successfully converted {input_file} to {output_file}")
        return SUCCESS
        
    except Exception as e:
        logging.error(f"Error converting {input_file}: {str(e)}")
        return FAILURE


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
    
    # Return a dictionary with the user variables as keys and default values
    return {var: 0 for var in user_vars}


def extract_variables_from_condition(condition):
    """
    Extract user variables from condition expressions
    
    Args:
        condition: The condition structure
        
    Returns:
        Dictionary of user variables
    """
    user_vars = {}
    
    if isinstance(condition, str) and condition.startswith("USER_"):
        user_vars[condition] = 0
    elif isinstance(condition, (list, tuple)) and len(condition) > 1:
        # Process each part of the condition
        for part in condition:
            if isinstance(part, str) and part.startswith("USER_"):
                user_vars[part] = 0
            elif isinstance(part, (list, tuple)):
                # Recursive call for nested conditions
                user_vars.update(extract_variables_from_condition(part))
    
    return user_vars


def convert_script(parsed_script, input_file, output_file, tribe, command_map, variable_map):
    """
    Converts a Script2 format file to Script4 (Lua) format
    
    Args:
        parsed_script: Path to the input Script2 file
        output_file: Path to save the output Lua file
        tribe: The target tribe for the script
        command_map: Command mapping dictionary
        variable_map: Variable mapping dictionary
    """
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
    lua_output.append('import(Module_Math)')
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
    try:
        user_vars = extract_user_variables(parsed_script)
        if user_vars:
            lua_output.append('-- USER VARIABLES')
            if isinstance(user_vars, dict):
                for var_name in sorted(user_vars.keys()):
                    # Replace USER_ with SC2_USR_ in variable definitions
                    new_var_name = var_name.replace('USER_', 'SC2_USR_')
                    lua_output.append(f'{new_var_name} = 0')
            lua_output.append('')
    except Exception as e:
        logging.error(f"Error processing user variables: {e}")
        lua_output.append('-- Error processing user variables')
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
    # spells, buildings = extract_spells_and_buildings(parsed_script)
    
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
    converted_code = convert_statements(parsed_script, tribe, command_map, variable_map)
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

    return lua_output


def convert_user_var_name(var_name):
    """
    Convert USER_ variable names to SC2_USR_ format
    
    Args:
        var_name: The variable name to convert
        
    Returns:
        The converted variable name with SC2_USR_ prefix instead of USER_
    """
    
    if isinstance(var_name, str) and var_name.startswith(USER_PREFIX):
        return var_name.replace(USER_PREFIX, SC2_USR_PREFIX, 1)
    return var_name


def load_system_spec(filepath):
    """Loads the system specification from JSON file"""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading system spec: {str(e)}")
        return None


def validate_command_map(command_map, system_spec, variable_map):
    """
    Validates command mappings against the system specification
    Returns tuple of (valid_commands, invalid_commands)
    """
    valid_commands = {}
    invalid_commands = {}
    
    # Extract all available functions and their parameter counts from modules
    available_functions = {}
    for module in system_spec.get('modules', []):
        module_name = module.get('name')
        for function in module.get('functions', []):
            func_name = function.get('name')
            param_count = len(function.get('parameters', []))
            available_functions[func_name] = {
                'module': module_name,
                'param_count': param_count
            }
    
    # Validate each command mapping
    for cmd_name, cmd_func in command_map.items():
        # Test the function with dummy parameters
        try:
            # Create a test call with the expected number of parameters
            test_params = [f"param{i}" for i in range(10)]  # Create 10 dummy parameters
            result = cmd_func(test_params, variable_map)
            
            # Extract function name from the result
            func_match = re.search(r'^(\w+)\(', result)
            if not func_match:
                invalid_commands[cmd_name] = f"Invalid format: {result}"
                continue
            
            func_name = func_match.group(1)
            
            # Check if function exists in system spec
            if func_name not in available_functions:
                invalid_commands[cmd_name] = f"Unknown function: {func_name}"
                continue
            
            # Add to valid commands
            valid_commands[cmd_name] = result
            
        except Exception as e:
            invalid_commands[cmd_name] = str(e)
    
    return valid_commands, invalid_commands
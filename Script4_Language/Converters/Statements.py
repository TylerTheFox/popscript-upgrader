import sys
import logging
from Script4_Language.Config import *

"""
Script4_Language/Converters/Statements.py
Functions for converting specific Script2 statements to Script4 format
"""

from Script4_Language.Converters.Expressions import (
    convert_condition, convert_variable, convert_value, 
    convert_int_constant, convert_user_var_name
)

def convert_statement(stmt, tribe, command_map, variable_map, indent=0):
    """
    Convert a single Script2 statement to Script4 format
    
    Args:
        stmt: The Script2 statement structure
        tribe: The target tribe for the script
        command_map: Command mapping dictionary
        variable_map: Variable mapping dictionary
        indent: The current indentation level
        
    Returns:
        String or List containing the converted Script4 statement(s)
    """
    indent_str = INDENT_CHAR * (indent * INDENT_SIZE)
    
    # Handle different statement types
    if not stmt:
        return f"{indent_str}-- Empty statement"
    
    stmt_type = stmt[0]
    
    # Handle command statements (both COMMAND_STMT and 'do')
    if stmt_type == COMMAND_STMT or stmt_type == "do":
        command = stmt[1]
        
        # Skip comments in commands
        if command == CMD_COMMENT:
            comment_text = stmt[2]
            return f"{indent_str}{COMMENT_PREFIX} {comment_text}"
        
        if command in command_map:
            try:
                my_func = command_map[command]
                return f"{indent_str}{my_func(stmt, variable_map)}"
            except Exception as e:
                logging.error(f"Error converting command {command}: {e}")
                return f"{indent_str}-- ERROR: Failed to convert {command}: {e}"
        else:
            return f"{indent_str}-- UNSUPPORTED: {command} {', '.join(str(arg) for arg in stmt[2:])}"
    
    # Handle variable assignment statements (set)
    elif stmt_type == "set":
        if len(stmt) >= 3:
            # Check for INT_ATTR_ variables using STATE_ATTR_MAP
            if isinstance(stmt[1], str) and stmt[1] in STATE_ATTR_MAP:
                attr_name = STATE_ATTR_MAP[stmt[1]]
                
                # Special handling for operations where the attribute appears on both sides
                if isinstance(stmt[2], (list, tuple)) and len(stmt[2]) == 3:
                    op = stmt[2][0]
                    left = stmt[2][1]
                    right = stmt[2][2]
                    
                    # Check if we're operating on the same attribute
                    if left == stmt[1] and op in ['+', '-', '*', '/', '%']:
                        right_val = convert_value(right, variable_map)
                        return f"{indent_str}WRITE_CP_ATTRIB(MY_TRIBE, {attr_name}, READ_CP_ATTRIB(MY_TRIBE, {attr_name}) {op} {right_val})"
                
                # If right side references another attribute, read it
                if isinstance(stmt[2], str) and stmt[2] in STATE_ATTR_MAP:
                    right_attr_name = STATE_ATTR_MAP[stmt[2]]
                    return f"{indent_str}WRITE_CP_ATTRIB(MY_TRIBE, {attr_name}, READ_CP_ATTRIB(MY_TRIBE, {right_attr_name}))"
                    
                # Standard case - just assigning a value
                value = convert_value(stmt[2], variable_map)
                return f"{indent_str}WRITE_CP_ATTRIB(MY_TRIBE, {attr_name}, {value})"
            else:
                # Handle regular variable assignments
                var_name = convert_user_var_name(stmt[1])
                
                # Check if right side is an attribute that needs to be read
                if isinstance(stmt[2], str) and stmt[2] in STATE_ATTR_MAP:
                    right_attr_name = STATE_ATTR_MAP[stmt[2]]
                    return f"{indent_str}{var_name} = READ_CP_ATTRIB(MY_TRIBE, {right_attr_name})"
                
                value = convert_value(stmt[2], variable_map)
                return f"{indent_str}{var_name} = {value}"
        else:
            return f"{indent_str}-- ERROR: Invalid set statement format: {stmt}"
    
    # Handle EVERY statement - check condition periodically
    elif stmt_type == EVERY_STMT or stmt_type == "every":
        # Extract seconds and condition
        period  = convert_value(stmt[1], variable_map) if len(stmt) > 1 else 1
        offset  = convert_value(stmt[2], variable_map)
        if offset  == 'nil':
            offset  = 0

        condition = "true"
        
        # Some every statements have a random offset (position 2)
        # The actual statements are in position 3
        statements_pos = 3 if len(stmt) > 3 else 2
        
        # Check if we have at least the required parts
        if len(stmt) <= statements_pos:
            return f"{indent_str}-- ERROR: Invalid every statement format: {stmt}"
            
        # Convert the inner statements
        inner_statements = convert_statements(stmt[statements_pos], tribe, command_map, variable_map)
        
        output = [f"{indent_str}if ((getTurn() + MY_TRIBE + {offset}) % {period} == 0) then"]
        
        for inner in inner_statements:
            output.append(f"{indent_str}{INDENT_CHAR * INDENT_SIZE}{inner}")
        
        output.append(f"{indent_str}end")
        return output
    
    # Handle basic IF statement
    elif stmt_type == IF_STMT or stmt_type == "if":
        condition = convert_condition(stmt[1], variable_map)
        inner_statements = convert_statements(stmt[2], tribe, command_map, variable_map)
        
        output = [f"{indent_str}if {condition} then"]
        
        for inner in inner_statements:
            output.append(f"{indent_str}{INDENT_CHAR * INDENT_SIZE}{inner}")
        
        output.append(f"{indent_str}end")
        
        return output
    
    # Handle IF-ELSE statement - handle both 'IF_ELSE' (constant) and 'if-else' (string from parser)
    elif stmt_type == IF_ELSE_STMT or stmt_type == "if-else":
        condition = convert_condition(stmt[1], variable_map)
        if_statements = convert_statements(stmt[2], tribe, command_map, variable_map)
        else_statements = convert_statements(stmt[3], tribe, command_map, variable_map)
        
        output = [f"{indent_str}if {condition} then"]
        
        for inner in if_statements:
            output.append(f"{indent_str}{INDENT_CHAR * INDENT_SIZE}{inner}")
        
        output.append(f"{indent_str}else")
        
        for inner in else_statements:
            output.append(f"{indent_str}{INDENT_CHAR * INDENT_SIZE}{inner}")
        
        output.append(f"{indent_str}end")
        
        return output

    # Handle BEGIN_ACTIVE and END_ACTIVE
    elif stmt_type in [BEGIN_ACTIVE_STMT, END_ACTIVE_STMT]:
        # No direct equivalent in Script4, but we can comment for documentation
        return f"{indent_str}-- {stmt_type} (not needed in Script4)"
    
    # Handle single-line comments
    elif stmt_type == COMMENT_STMT:
        return f"{indent_str}{COMMENT_PREFIX} {stmt[1]}"
    
    # Handle multi-line comments
    elif stmt_type == COMMENT_BLOCK_STMT:
        return convert_comment_block(stmt, indent_str)
    
    # Handle SET_TIMER and SET_TIMER_GOING
    elif stmt_type == SET_TIMER_STMT:
        timer_id = convert_value(stmt[1], variable_map)
        timer_value = convert_value(stmt[2], variable_map)
        return f"{indent_str}SET_TIMER({timer_id}, {timer_value})"
    
    elif stmt_type == SET_TIMER_GOING_STMT:
        timer_id = convert_value(stmt[1], variable_map)
        going_state = convert_value(stmt[2], variable_map)
        return f"{indent_str}SET_TIMER_GOING({timer_id}, {going_state})"
    
    # Handle SET_CELL_SCRIPT_LEVEL
    elif stmt_type == SET_LEVEL_COMPLETE_STMT:
        return f"{indent_str}SET_LEVEL_COMPLETE({convert_value(stmt[1], variable_map)})"
    
    elif stmt_type == "divide":
        if len(stmt) >= 4:
            if isinstance(stmt[1], str) and stmt[1] in STATE_ATTR_MAP:
                attr_name = STATE_ATTR_MAP[stmt[1]]
                
                # Check if dividend is an attribute that needs to be read
                if isinstance(stmt[2], str) and stmt[2] in STATE_ATTR_MAP:
                    dividend_attr = STATE_ATTR_MAP[stmt[2]]
                    dividend = f"READ_CP_ATTRIB(MY_TRIBE, {dividend_attr})"
                else:
                    dividend = convert_value(stmt[2], variable_map)
                    
                # Check if divisor is an attribute that needs to be read
                if isinstance(stmt[3], str) and stmt[3] in STATE_ATTR_MAP:
                    divisor_attr = STATE_ATTR_MAP[stmt[3]]
                    divisor = f"READ_CP_ATTRIB(MY_TRIBE, {divisor_attr})"
                else:
                    divisor = convert_value(stmt[3], variable_map)
                    
                return f"{indent_str}WRITE_CP_ATTRIB(MY_TRIBE, {attr_name}, math.floor({dividend} / {divisor}))"
            else:
                var_name = convert_user_var_name(stmt[1])
                
                # Check if dividend is an attribute that needs to be read
                if isinstance(stmt[2], str) and stmt[2] in STATE_ATTR_MAP:
                    dividend_attr = STATE_ATTR_MAP[stmt[2]]
                    dividend = f"READ_CP_ATTRIB(MY_TRIBE, {dividend_attr})"
                else:
                    dividend = convert_value(stmt[2], variable_map)
                    
                # Check if divisor is an attribute that needs to be read
                if isinstance(stmt[3], str) and stmt[3] in STATE_ATTR_MAP:
                    divisor_attr = STATE_ATTR_MAP[stmt[3]]
                    divisor = f"READ_CP_ATTRIB(MY_TRIBE, {divisor_attr})"
                else:
                    divisor = convert_value(stmt[3], variable_map)
                    
                return f"{indent_str}{var_name} = math.floor({dividend} / {divisor})"
        else:
            return f"{indent_str}-- ERROR: Invalid divide statement format: {stmt}"
            
    elif stmt_type == "multiply":
        if len(stmt) >= 4:
            if isinstance(stmt[1], str) and stmt[1] in STATE_ATTR_MAP:
                attr_name = STATE_ATTR_MAP[stmt[1]]
                
                # Check if factors are attributes that need to be read
                if isinstance(stmt[2], str) and stmt[2] in STATE_ATTR_MAP:
                    factor1_attr = STATE_ATTR_MAP[stmt[2]]
                    factor1 = f"READ_CP_ATTRIB(MY_TRIBE, {factor1_attr})"
                else:
                    factor1 = convert_value(stmt[2], variable_map)
                    
                if isinstance(stmt[3], str) and stmt[3] in STATE_ATTR_MAP:
                    factor2_attr = STATE_ATTR_MAP[stmt[3]]
                    factor2 = f"READ_CP_ATTRIB(MY_TRIBE, {factor2_attr})"
                else:
                    factor2 = convert_value(stmt[3], variable_map)
                    
                return f"{indent_str}WRITE_CP_ATTRIB(MY_TRIBE, {attr_name}, {factor1} * {factor2})"
            else:
                var_name = convert_user_var_name(stmt[1])
                
                # Check if factors are attributes that need to be read
                if isinstance(stmt[2], str) and stmt[2] in STATE_ATTR_MAP:
                    factor1_attr = STATE_ATTR_MAP[stmt[2]]
                    factor1 = f"READ_CP_ATTRIB(MY_TRIBE, {factor1_attr})"
                else:
                    factor1 = convert_value(stmt[2], variable_map)
                    
                if isinstance(stmt[3], str) and stmt[3] in STATE_ATTR_MAP:
                    factor2_attr = STATE_ATTR_MAP[stmt[3]]
                    factor2 = f"READ_CP_ATTRIB(MY_TRIBE, {factor2_attr})"
                else:
                    factor2 = convert_value(stmt[3], variable_map)
                    
                return f"{indent_str}{var_name} = {factor1} * {factor2}"
        else:
            return f"{indent_str}-- ERROR: Invalid multiply statement format: {stmt}"
    
    
    elif stmt_type == "increment":
        if len(stmt) >= 3:
            # Check if we're incrementing an INT_ATTR_ variable
            if isinstance(stmt[1], str) and stmt[1] in STATE_ATTR_MAP:
                attr_name = STATE_ATTR_MAP[stmt[1]]
                
                # Check if increment value is an attribute
                if isinstance(stmt[2], str) and stmt[2] in STATE_ATTR_MAP:
                    increment_attr = STATE_ATTR_MAP[stmt[2]]
                    increment_value = f"READ_CP_ATTRIB(MY_TRIBE, {increment_attr})"
                else:
                    increment_value = convert_value(stmt[2], variable_map)
                    
                return f"{indent_str}WRITE_CP_ATTRIB(MY_TRIBE, {attr_name}, READ_CP_ATTRIB(MY_TRIBE, {attr_name}) + {increment_value})"
            else:
                # Regular variable increment
                var_name = convert_user_var_name(stmt[1])
                
                # Check if increment value is an attribute
                if isinstance(stmt[2], str) and stmt[2] in STATE_ATTR_MAP:
                    increment_attr = STATE_ATTR_MAP[stmt[2]]
                    increment_value = f"READ_CP_ATTRIB(MY_TRIBE, {increment_attr})"
                else:
                    increment_value = convert_value(stmt[2], variable_map)
                    
                return f"{indent_str}{var_name} = {var_name} + {increment_value}"
        else:
            return f"{indent_str}-- ERROR: Invalid increment statement format: {stmt}"
        
    elif stmt_type == "decrement":
        if len(stmt) >= 3:
            if isinstance(stmt[1], str) and stmt[1] in STATE_ATTR_MAP:
                attr_name = STATE_ATTR_MAP[stmt[1]]
                
                # Check if decrement value is an attribute
                if isinstance(stmt[2], str) and stmt[2] in STATE_ATTR_MAP:
                    decrement_attr = STATE_ATTR_MAP[stmt[2]]
                    decrement_value = f"READ_CP_ATTRIB(MY_TRIBE, {decrement_attr})"
                else:
                    decrement_value = convert_value(stmt[2], variable_map)
                    
                return f"{indent_str}WRITE_CP_ATTRIB(MY_TRIBE, {attr_name}, READ_CP_ATTRIB(MY_TRIBE, {attr_name}) - {decrement_value})"
            else:
                var_name = convert_user_var_name(stmt[1])
                
                # Check if decrement value is an attribute
                if isinstance(stmt[2], str) and stmt[2] in STATE_ATTR_MAP:
                    decrement_attr = STATE_ATTR_MAP[stmt[2]]
                    decrement_value = f"READ_CP_ATTRIB(MY_TRIBE, {decrement_attr})"
                else:
                    decrement_value = convert_value(stmt[2], variable_map)
                    
                return f"{indent_str}{var_name} = {var_name} - {decrement_value}"
        else:
            return f"{indent_str}-- ERROR: Invalid decrement statement format: {stmt}"
        
    # Handle unrecognized statements
    else:
        # Add more detailed debugging info
        return f"{indent_str}-- UNKNOWN STATEMENT TYPE: {stmt_type} - Structure: {str(stmt)[:100]}..."

def convert_every_statement(stmt, tribe, command_map, variable_map, indent_str):
    """
    Convert an EVERY statement to Script4 format
    
    Args:
        stmt: The EVERY statement structure
        tribe: The target tribe for the script
        command_map: Command mapping dictionary
        variable_map: Variable mapping dictionary
        indent_str: Current indentation string
        
    Returns:
        List of converted Script4 statements
    """
    seconds = convert_value(stmt[1], variable_map)
    condition = convert_condition(stmt[2], variable_map)
    inner_statements = convert_statements(stmt[3], tribe, command_map, variable_map)
    
    output = [f"{indent_str}if EverySeconds({seconds}) then"]
    output.append(f"{indent_str}{INDENT_CHAR * INDENT_SIZE}if {condition} then")
    
    for inner in inner_statements:
        output.append(f"{indent_str}{INDENT_CHAR * (2 * INDENT_SIZE)}{inner}")
    
    output.append(f"{indent_str}{INDENT_CHAR * INDENT_SIZE}end")
    output.append(f"{indent_str}end")
    
    return output

def convert_if_statement(stmt, tribe, command_map, variable_map, indent_str):
    """
    Convert an IF statement to Script4 format
    
    Args:
        stmt: The IF statement structure
        tribe: The target tribe for the script
        command_map: Command mapping dictionary
        variable_map: Variable mapping dictionary
        indent_str: Current indentation string
        
    Returns:
        List of converted Script4 statements
    """
    condition = convert_condition(stmt[1], variable_map)
    inner_statements = convert_statements(stmt[2], tribe, command_map, variable_map)
    
    output = [f"{indent_str}if {condition} then"]
    
    for inner in inner_statements:
        output.append(f"{indent_str}{INDENT_CHAR * INDENT_SIZE}{inner}")
    
    output.append(f"{indent_str}end")
    
    return output

def convert_if_else_statement(stmt, tribe, command_map, variable_map, indent_str):
    """
    Convert an IF-ELSE statement to Script4 format
    
    Args:
        stmt: The IF-ELSE statement structure
        tribe: The target tribe for the script
        command_map: Command mapping dictionary
        variable_map: Variable mapping dictionary
        indent_str: Current indentation string
        
    Returns:
        List of converted Script4 statements
    """
    condition = convert_condition(stmt[1], variable_map)
    if_statements = convert_statements(stmt[2], tribe, command_map, variable_map)
    else_statements = convert_statements(stmt[3], tribe, command_map, variable_map)
    
    output = [f"{indent_str}if {condition} then"]
    
    for inner in if_statements:
        output.append(f"{indent_str}{INDENT_CHAR * INDENT_SIZE}{inner}")
    
    output.append(f"{indent_str}else")
    
    for inner in else_statements:
        output.append(f"{indent_str}{INDENT_CHAR * INDENT_SIZE}{inner}")
    
    output.append(f"{indent_str}end")
    
    return output

def convert_comment_block(stmt, indent_str):
    """
    Convert a multi-line comment block to Script4 format
    
    Args:
        stmt: The comment block statement structure
        indent_str: Current indentation string
        
    Returns:
        List of comment lines
    """
    output = [f"{indent_str}{COMMENT_PREFIX} BEGIN COMMENT BLOCK"]
    for line in stmt[1].split('\n'):
        output.append(f"{indent_str}{COMMENT_PREFIX} {line}")
    output.append(f"{indent_str}{COMMENT_PREFIX} END COMMENT BLOCK")
    return output

def convert_statements(statements, tribe, command_map, variable_map):
    """
    Convert a list of Script2 statements to Script4 format
    
    Args:
        statements: The Script2 statement structure
        tribe: The target tribe for the script
        command_map: Command mapping dictionary
        variable_map: Variable mapping dictionary
        
    Returns:
        List of strings containing the converted Script4 statements
    """
    result = []
    
    # If statements is a tuple with 'script' as first element, extract the actual statements
    if isinstance(statements, tuple) and statements[0] == 'script':
        # Structure is ('script', id, statements)
        statements = statements[2]
    
    # Handle the 'statements' wrapper structure
    if isinstance(statements, tuple) and statements[0] == 'statements':
        statements = statements[1]  # Extract the actual list of statements
    
    # Process each statement
    if isinstance(statements, list):
        for stmt in statements:
            converted = convert_statement(stmt, tribe, command_map, variable_map)
            if converted:
                if isinstance(converted, list):
                    result.extend(converted)
                else:
                    result.append(converted)
    else:
        # If it's not a list, try to convert it directly
        converted = convert_statement(statements, tribe, command_map, variable_map)
        if converted:
            if isinstance(converted, list):
                result.extend(converted)
            else:
                result.append(converted)
    
    return result
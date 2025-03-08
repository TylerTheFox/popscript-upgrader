import sys
import logging

"""
Script4_Language/Converters/Expressions.py
Handling of conditions, expressions and value conversions
"""

from Script4_Language.Config import *

def convert_condition(condition, variable_map):
    """
    Convert a Script2 condition structure to a Script4 condition expression
    
    Args:
        condition: The condition structure from the parser
        variable_map: Dictionary of variable mappings
        
    Returns:
        String containing the Script4 equivalent condition
    """
    if not condition:
        return "true"
    
    if isinstance(condition, str):
        # For simple condition statements
        return convert_value(condition, variable_map)
    
    # For complex conditions with operators
    if not isinstance(condition, (list, tuple)) or len(condition) == 0:
        logging.warning(f"Invalid condition format: {condition}")
        return str(condition)
    
    op_type = condition[0]
    
    # Handle logical operators first (AND/OR)
    if op_type in ["AND", "OR", "&&", "||"]:
        # Map operators to Lua syntax
        lua_op = "and" if op_type in ["AND", "&&"] else "or"
        
        # Process all parts of the condition
        parts = []
        for cond in condition[1:]:
            parts.append(f"({convert_condition(cond, variable_map)})")
        
        if not parts:
            return "true"  # Empty condition defaults to true
            
        # Join all parts with the logical operator
        return f" {lua_op} ".join(parts)
    
    # Handle NOT operator
    if op_type == "NOT":
        return f"not ({convert_condition(condition[1], variable_map)})"
    
    # Handle comparison operators like '<', '>', '=='
    if op_type in OPERATOR_MAP:
        if len(condition) >= 3:  # Ensure we have enough elements
            left_expr = convert_value(condition[1], variable_map)
            operator = OPERATOR_MAP.get(op_type, op_type)
            right_expr = convert_value(condition[2], variable_map)
            return f"{left_expr} {operator} {right_expr}"
    
    # Handle tuple format for comparison: ('==', 'USER_TALKSAFE', '0')
    if isinstance(condition, tuple) and len(condition) == 3 and condition[0] in OPERATOR_MAP:
        left_expr = convert_value(condition[1], variable_map)
        operator = OPERATOR_MAP.get(condition[0], condition[0])
        right_expr = convert_value(condition[2], variable_map)
        return f"{left_expr} {operator} {right_expr}"
    
    # Default case - just return as is
    logging.warning(f"Unhandled condition format: {condition}")
    return str(condition)

def convert_variable(var, variable_map, tribe=MY_TRIBE):
    """
    Convert a Script2 variable to its Script4 equivalent
    
    Args:
        var: The variable to convert
        variable_map: Dictionary of variable mappings
        tribe: The target tribe for the script
        
    Returns:
        String containing the Script4 equivalent variable
    """
    if isinstance(var, str):
        # Handle user variables
        if var.startswith(USER_PREFIX):
            return convert_user_var_name(var)
        
        # Handle INT_ constants
        if var.startswith(STR_INT_PREFIX):
            if var in variable_map:
                return variable_map[var]()
            return convert_int_constant(var)
            
    # For non-string values, convert directly
    return convert_value(var, variable_map)

def convert_value(value, variable_map):
    """
    Convert a Script2 value to its Script4 equivalent
    
    Args:
        value: The value to convert
        variable_map: Dictionary of variable mappings
        
    Returns:
        String containing the Script4 equivalent value
    """
    # Handle different types of values
    if value is None:
        return "nil"
    
    if isinstance(value, bool):
        return str(value).lower()  # Convert to lowercase true/false
        
    if isinstance(value, (int, float)):
        return str(value)
    
    if isinstance(value, str):
        # Special case for NO_SPECIFIC_BUILDING
        if value == "INT_NO_SPECIFIC_BUILDING":
            return value
        
        # Special case for CONVERT
        if value == "CONVERT" or value == "INT_CONVERT" or value == "M_SPELL_CONVERT":
            return "M_SPELL_CONVERT_WILD"
        
        # Check if this value has a direct mapping first
        if value in variable_map:
            return variable_map[value]()
        
        # Check if it's a variable or constant
        if value.startswith(USER_PREFIX):
            return convert_user_var_name(value)
            
        if value.startswith(STR_INT_PREFIX):
            # Check if we have a direct mapping
            if value in variable_map:
                return variable_map[value]()
            # Otherwise convert using standard rules
            return convert_int_constant(value)
            
        # Handle operator strings
        if value in OPERATOR_MAP:
            return OPERATOR_MAP[value]
        
        # Add tribe name handling
        if value in (BLUE, RED, GREEN, YELLOW):
            return TRIBE_PREFIX + value
            
        # If it's a regular string literal that's not a keyword or known constant
        if not (value in ["true", "false", "nil"] or 
                value.startswith(SC2_USR_PREFIX) or
                value.isdigit() or
                value in list(variable_map.keys())):
            # Quote the string literal
            return f'{value}'
            
    # Fallback - return as is
    return value

def convert_int_constant(int_value):
    """
    Central function to convert INT_ constants to their Script4 equivalents
    
    Args:
        int_value: The INT_ constant to convert
        
    Returns:
        String containing the Script4 equivalent constant
    """
    # Handle mana variables
    if int_value == "INT_MY_MANA":
        return f"MANA({MY_TRIBE})"
    
    # Handle tribe-specific mana
    mana_map = {
        "INT_BLUE_MANA": f"MANA({TRIBE_BLUE})",
        "INT_RED_MANA": f"MANA({TRIBE_RED})",
        "INT_YELLOW_MANA": f"MANA({TRIBE_YELLOW})",
        "INT_GREEN_MANA": f"MANA({TRIBE_GREEN})"
    }
    
    if int_value in mana_map:
        return mana_map[int_value]

    # Handle INT_ATTR_ variables (add this section)
    if int_value in STATE_ATTR_MAP:
        attr_name = STATE_ATTR_MAP[int_value]
        return f"READ_CP_ATTRIB(MY_TRIBE, {attr_name})"

    # Handle spell cost patterns (INT_X_SPELL_Y_COST)
    if int_value.startswith(STR_INT_PREFIX) and "_SPELL_" in int_value and int_value.endswith("_COST"):
        parts = int_value.split("_")
        if len(parts) >= 5 and parts[1] in TRIBE_MAP:
            tribe = TRIBE_MAP.get(parts[1], MY_TRIBE)
            spell_name = "_".join(parts[2:-1])  # Join everything between tribe code and "_COST"
            return f"PLAYERS_SPELL_COST({tribe}, M_{spell_name})"
    
    # Handle non-string values or empty values
    if not isinstance(int_value, str) or not int_value:
        return int_value
        
    # Prevent USER_ conversion - preserve user variables
    if int_value.startswith(USER_PREFIX):
        return int_value
    
    # Handle special mappings that don't follow standard patterns
    if int_value in SPECIAL_MAPPINGS:
        return SPECIAL_MAPPINGS[int_value]
    
    if int_value in STATE_ATTR_MAP:
        return STATE_ATTR_MAP[int_value]
    
    # Add tribe name handling
    if int_value in (BLUE, RED, GREEN, YELLOW):
        return TRIBE_PREFIX + int_value
    
    # People access - convert to GSI paths when needed
    if int_value in PEOPLE_MAPPINGS:
        return PEOPLE_MAPPINGS[int_value]
    
    # Tribe-specific person counts
    if int_value.startswith(STR_INT_PREFIX) and ("_PERSON_" in int_value):
        # Handle person type constants like INT_B_PERSON_WARRIOR
        parts = int_value.split("_")
        if len(parts) >= 4 and parts[1] in TRIBE_MAP:
            tribe = TRIBE_MAP.get(parts[1], MY_TRIBE)
            person_type = "_".join(parts[2:])  # Get PERSON_X part
            return f"_gsi.Players[{tribe}].NumPeopleOfType[M_{person_type}]"
            
    # Standard spell mappings
    if int_value.startswith(STR_INT_PREFIX) and any(spell in int_value for spell in SPELL_NAMES):
        # Replace INT_ with M_SPELL_ for spell constants
        spell_name = int_value[len(STR_INT_PREFIX):]  # Remove the "INT_" part
        return f"M_SPELL_{spell_name}"
    
    # Building type mappings
    if int_value.startswith(STR_INT_PREFIX) and any(building in int_value for building in BUILDING_TYPES):
        # Transform INT_X_BUILDING_Y to PLAYERS_BUILDING_OF_TYPE(TRIBE_X, M_BUILDING_Y)
        parts = int_value.split("_")
        if len(parts) >= 4 and parts[1] in TRIBE_MAP:  # Tribe prefixed buildings
            tribe = TRIBE_MAP.get(parts[1], MY_TRIBE)
            building_type = "_".join(parts[3:])  # Get the BUILDING_X part
            return f"PLAYERS_BUILDING_OF_TYPE({tribe}, M_BUILDING_{building_type})"
        else:  # Generic building types
            building_type = "_".join(parts[1:])  # Get the part after INT_
            return f"M_BUILDING_{building_type}"
        
    # Person type mappings without tribe prefix (INT_WARRIOR etc.)
    if int_value in [f"{STR_INT_PREFIX}{t}" for t in PERSON_TYPES]:
        person_type = int_value[len(STR_INT_PREFIX):]  # Remove the "INT_" part
        return f"M_PERSON_{person_type}"
    
    # Player-specific prefixes
    prefix_tribe_map = [
        (f"{STR_INT_PREFIX}M_", MY_TRIBE), 
        (f"{STR_INT_PREFIX}B_", TRIBE_BLUE), 
        (f"{STR_INT_PREFIX}R_", TRIBE_RED), 
        (f"{STR_INT_PREFIX}Y_", TRIBE_YELLOW), 
        (f"{STR_INT_PREFIX}G_", TRIBE_GREEN)
    ]
    
    for prefix, tribe in prefix_tribe_map:
        if int_value.startswith(prefix):
            # Transform INT_X_Y to _gsi.Players[TRIBE_X].Y
            remaining = int_value[len(prefix):]
            # Special handling for common patterns
            if remaining.startswith("BUILDING_"):
                building_type = remaining[9:]  # part after BUILDING_
                return f"PLAYERS_BUILDING_OF_TYPE({tribe}, M_BUILDING_{building_type})"
            elif remaining.startswith("PERSON_"):
                person_type = remaining  # Keep PERSON_X part
                return f"_gsi.Players[{tribe}].NumPeopleOfType[M_{person_type}]"
    
    # Default - if it starts with INT_, just remove that prefix
    if int_value.startswith(STR_INT_PREFIX):
        return int_value[len(STR_INT_PREFIX):]  # Remove the "INT_" part
    
    
    return int_value

def convert_user_var_name(var_name):
    """
    Convert USER_ variable names to SC2_USR_ format
    
    Args:
        var_name: The variable name to convert
        
    Returns:
        The converted variable name with SC2_USR_ prefix instead of USER_
    """
    if isinstance(var_name, str) and var_name.startswith(USER_PREFIX):
        return f"{SC2_USR_PREFIX}{var_name[len(USER_PREFIX):]}"  # Replace USER_ with SC2_USR_
    return var_name
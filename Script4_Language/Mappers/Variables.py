from Script4_Language.Config import *

# filepath: c:\Users\Tyler\Documents\Repos\PopTB\CpScript\script-converter\Script4_Language\Mappers\Variables.py

from Script4_Language.Converters.Expressions import (
    convert_value, convert_int_constant, convert_user_var_name
)

"""
Script4_Language/Mappers/Variables.py
Contains mapping functions to convert Script2 variables to Script4 format
"""

def build_variable_map():
    """
    Build a dictionary of variable mapping functions based on the tribe
    
    Args:
        tribe: The target tribe for the script
        
    Returns:
        Dictionary mapping Script2 variables to their Script4 conversion functions
    """
    variable_map = {
        # People count variables
        "INT_MY_NUM_PEOPLE": lambda: f"{PLAYERS_PATH}[{MY_TRIBE}].{NUM_PEOPLE_ATTR}",
        "INT_BLUE_PEOPLE": lambda: f"{PLAYERS_PATH}[{TRIBE_BLUE}].{NUM_PEOPLE_ATTR}",
        "INT_RED_PEOPLE": lambda: f"{PLAYERS_PATH}[{TRIBE_RED}].{NUM_PEOPLE_ATTR}",
        "INT_YELLOW_PEOPLE": lambda: f"{PLAYERS_PATH}[{TRIBE_YELLOW}].{NUM_PEOPLE_ATTR}",
        "INT_GREEN_PEOPLE": lambda: f"{PLAYERS_PATH}[{TRIBE_GREEN}].{NUM_PEOPLE_ATTR}",
        "INT_WILD_PEOPLE": lambda: WILD_PEOPLE_PATH,
        "INT_CP_FREE_ENTRIES": lambda: FREE_ENTRIES_FMT.format(MY_TRIBE),
        "INT_MY_NUM_KILLED_BY_BLUE": lambda: f"{PLAYERS_PATH}[{TRIBE_BLUE}].PeopleKilled[{MY_TRIBE}]",

        # Person type counts for all tribes
        **build_tribe_person_counts(TRIBE_BLUE, "B"),
        **build_tribe_person_counts(TRIBE_RED, "R"),
        **build_tribe_person_counts(TRIBE_YELLOW, "Y"),
        **build_tribe_person_counts(TRIBE_GREEN, "G"),
        **build_tribe_person_counts(MY_TRIBE, "M"),

        # Special constants
        "INT_NO_SPECIFIC_SPELL": lambda: "M_SPELL_NONE",
        "NO_SPECIFIC_BUILDING": lambda: "INT_NO_SPECIFIC_BUILDING",
        "BUILDING": lambda: "ATTACK_BUILDING",
        "MARKER": lambda: "ATTACK_MARKER",
        "INT_WRATH_OF_GOD": lambda: "M_SPELL_ARMAGEDDON",
        "INT_CONVERT": lambda: "M_SPELL_CONVERT_WILD",
        "CONVERT": lambda: "M_SPELL_CONVERT_WILD",
        "INT_TARGET_MEDICINE_MAN": lambda: "ATTACK_TARGET_MEDICINE_MAN",
        "INT_MY_MANA": lambda: f"MANA({MY_TRIBE})",
        "INT_BLUE_MANA": lambda: f"MANA({TRIBE_BLUE})",
        "INT_RED_MANA": lambda: f"MANA({TRIBE_RED})",
        "INT_GREEN_MANA": lambda: f"MANA({TRIBE_GREEN})",
        "INT_YELLOW_MANA": lambda: f"MANA({TRIBE_YELLOW})",
        

        # Tribe constants
        "BLUE": lambda: TRIBE_BLUE,
        "RED": lambda: TRIBE_RED,
        "GREEN": lambda: TRIBE_GREEN,
        "YELLOW": lambda: TRIBE_YELLOW,
        "INT_GAME_TURN": lambda: "getTurn()"
    }

    # Add spell mappings
    for spell in SPELL_NAMES:
        variable_map[f"INT_{spell}"] = lambda spell=spell: f"{SPELL_PREFIX}{spell}"

    # Add building mappings
    for building in BUILDING_TYPES:
        variable_map[f"INT_{building}"] = lambda building=building: f"{BUILDING_PREFIX}{building}"

    # Add person type mappings
    for person in PERSON_TYPES:
        variable_map[f"INT_{person}"] = lambda person=person: f"{PERSON_PREFIX}{person}"

    # Add spell mappings
    for spell in SPELL_NAMES:
        variable_map[f"INT_{spell}"] = lambda spell=spell: f"{SPELL_PREFIX}{spell}"
        # Add spell cost mappings
        for tribe_code, tribe in TRIBE_MAP.items():
            variable_map[f"INT_{tribe_code}_SPELL_{spell}_COST"] = lambda tribe=tribe, spell=spell: f"PLAYERS_SPELL_COST({tribe}, {SPELL_PREFIX}{spell})"
    

    return variable_map

def build_tribe_person_counts(tribe, tribe_short):
    """
    Build variable mappings for person counts by type for a specific tribe
    
    Args:
        tribe: Full tribe name constant
        tribe_short: Single letter abbreviation (B, R, Y, G, M)
        
    Returns:
        Dictionary of variable mappings for this tribe
    """
    person_counts = {}
    
    for person in PERSON_TYPES:
        var_name = f"INT_{tribe_short}_PERSON_{person}"
        person_counts[var_name] = lambda tribe=tribe, person=person: f"{PLAYERS_PATH}[{tribe}].{NUM_PEOPLE_TYPE_PATH}[{PERSON_PREFIX}{person}]"
    
    return person_counts

def tribe_code_to_tribe(tribe_code):
    """
    Convert a single-letter tribe code to full tribe constant
    
    Args:
        tribe_code: Single letter tribe code (B, R, Y, G, M)
        
    Returns:
        Full tribe constant name
    """
    return TRIBE_MAP.get(tribe_code, MY_TRIBE)

def building_to_constant(building_name):
    """
    Convert a building name to its Script4 constant
    
    Args:
        building_name: Name of building
        
    Returns:
        Script4 building constant
    """
    return f"{BUILDING_PREFIX}{building_name}"

def spell_to_constant(spell_name):
    """
    Convert a spell name to its Script4 constant
    
    Args:
        spell_name: Name of spell
        
    Returns:
        Script4 spell constant
    """
    return f"{SPELL_PREFIX}{spell_name}"

def person_to_constant(person_name):
    """
    Convert a person type to its Script4 constant
    
    Args:
        person_name: Name of person type
        
    Returns:
        Script4 person type constant
    """
    return f"{PERSON_PREFIX}{person_name}"
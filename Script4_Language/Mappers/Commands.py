import logging
from Script4_Language.Config import *

"""
Script4_Language/Mappers/Commands.py
Contains mapping functions to convert Script2 commands to Script4 format
"""

from Script4_Language.Converters.Expressions import (
    convert_value, convert_int_constant, convert_user_var_name
)

def build_command_map(variable_map):
    """
    Build a dictionary of command mapping functions based on the tribe
    
    Args:
        tribe: The target tribe for the script
        
    Returns:
        Dictionary mapping Script2 commands to their Script4 conversion functions
    """
    command_map = {
        "GET_SPELLS_CAST": map_get_spells_cast,
        "GET_HEIGHT_AT_POS": map_get_height_at_pos,
        "GET_HEAD_TRIGGER_COUNT": map_get_head_trigger_count,
        "GET_NUM_ONE_OFF_SPELLS": map_get_num_one_off_spells,
        "NAV_CHECK": map_nav_check,
        "COUNT_PEOPLE_IN_MARKER": map_count_people_in_marker,
        
        # Core commands
        "SET_REINCARNATION": map_set_reincarnation,
        "DELAY_MAIN_DRUM_TOWER": map_delay_main_drum_tower,
        "SET_ATTACK_VARIABLE": map_set_attack_variable,
        "DISABLE_USER_INPUTS": map_disable_user_inputs,
        "ENABLE_USER_INPUTS": map_enable_user_inputs,
        
        # State commands - using STATE_SET instead of SET_STATE
        "STATE_BRING_NEW_PEOPLE_BACK": map_state_bring_new_people_back,
        "STATE_TRAIN_PEOPLE": map_state_train_people,
        "STATE_MED_MAN_GET_WILD_PEEPS": map_state_med_man_get_wild_peeps,
        "STATE_CONSTRUCT_BUILDING": map_state_construct_building,
        "STATE_FETCH_WOOD": map_state_fetch_wood,
        "STATE_SEND_GHOSTS": map_state_send_ghosts,
        "STATE_FETCH_LOST_PEOPLE": map_state_fetch_lost_people,
        "STATE_FETCH_FAR_VEHICLE": map_state_fetch_far_vehicle,
        "STATE_FETCH_LOST_VEHICLE": map_state_fetch_lost_vehicle,
        "STATE_DEFEND": map_state_defend,
        "STATE_DEFEND_BASE": map_state_defend_base,
        "STATE_HOUSE_A_PERSON": map_state_house_a_person,
        "STATE_AUTO_ATTACK": map_state_auto_attack,
        "STATE_SPELL_DEFENCE": map_state_spell_defence,
        "STATE_POPULATE_DRUM_TOWER": map_state_populate_drum_tower,
        "STATE_BUILD_VEHICLE": map_state_build_vehicle,
        "STATE_PREACH": map_state_preach,
        "STATE_BUILD_WALLS": map_state_build_walls,
        "STATE_SABOTAGE": map_state_sabotage,
        "STATE_SPELL_OFFENSIVE": map_state_spell_offensive,
        "STATE_SUPER_DEFEND": map_state_super_defend,
        "STATE_MED_MAN_DEFEND": map_state_med_man_defend,
        "STATE_FLATTEN_BASE": map_state_flatten_base,
        "STATE_BUILD_OUTER_DEFENCES": map_state_build_outer_defences,
        "STATE_GUARD_AT_MARKER": map_state_guard_at_marker,
        "STATE_SEND_ALL_TO_MARKER": map_state_send_all_to_marker,
        "STATE_PRAY_AT_HEAD": map_state_pray_at_head,
        "STATE_BOAT_PATROL": map_state_boat_patrol,
        "STATE_DEFEND_SHAMEN": map_state_defend_shamen,

        # Marker and defense commands
        "SET_DEFENCE_RADIUS": map_set_defence_radius,
        "SET_MARKER_ENTRY": map_set_marker_entry,
        "ONLY_STAND_AT_MARKERS": map_only_stand_at_markers,
        "MARKER_ENTRIES": map_marker_entries,
        
        # Spell related commands - removed invalid functions
        
        "SET_SPELL_ENTRY": map_set_spell_entry,        
        "SET_BUCKET_COUNT_FOR_SPELL": map_set_bucket_count_for_spell,
        
        # Flyby commands 
        "FLYBY_CREATE_NEW": map_flyby_create_new,
        "FLYBY_ALLOW_INTERRUPT": map_flyby_allow_interrupt,
        "FLYBY_SET_EVENT_POS": map_flyby_set_event_pos,
        "FLYBY_SET_EVENT_ANGLE": map_flyby_set_event_angle,
        "FLYBY_SET_EVENT_ZOOM": map_flyby_set_event_zoom,
        "FLYBY_SET_EVENT_TOOLTIP": map_flyby_set_event_tooltip,
        "FLYBY_SET_END_TARGET": map_flyby_set_end_target,
        "FLYBY_START": map_flyby_start,

        # Message commands
        "CREATE_MSG_INFORMATION": map_create_msg_information,
        "SET_MSG_AUTO_OPEN_DLG": map_set_msg_auto_open_dlg,
        "SET_MSG_DELETE_ON_OK": map_set_msg_delete_on_ok,

        # Utility commands
        "PARTIAL_BUILDING_COUNT": map_partial_building_count,
        "TRIGGER_THING": map_trigger_thing,
        "REMOVE_HEAD_AT_POS": map_remove_head_at_pos,
        "DEFEND_SHAMEN": map_defend_shamen,
        "TRAIN_PEOPLE_NOW": map_train_people_now,

        # Turn commands
        "TURN_PUSH": map_turn_push,
        "SET_BUCKET_USAGE": map_set_bucket_usage,
        "ATTACK": map_attack_command,
        "GIVE_UP_AND_SULK": map_give_up_and_sulk,

        'BUILD_DRUM_TOWER': map_build_drum_tower,
        'GIVE_ONE_SHOT': map_give_one_shot, 
        'I_HAVE_ONE_SHOT': map_i_have_one_shot,
        'PRAY_AT_HEAD': map_pray_at_head,
        'PUT_PERSON_IN_DT': map_put_person_in_dt,
        'SEND_ALL_PEOPLE_TO_MARKER': map_send_all_people_to_marker,
        'SET_DRUM_TOWER_POS': map_set_drum_tower_pos,
        "SET_NO_BLUE_REINC": map_set_no_blue_reinc,
        'SPELL_AT_MARKER': map_spell_at_marker,
        "CREATE_MSG_NARRATIVE": map_create_msg_narrative,
        "SEND_SHAMEN_DEFENDERS_HOME" : map_send_shaman_denfenders_home,
        "TRIGGER_LEVEL_WON": map_trigger_level_won,
        "SET_MSG_TIMEOUT" : map_set_msg_timeout,
        "CLEAR_ALL_MSG" : map_clear_all_msg,
        "DESELECT_ALL_BLUE_PEOPLE" : map_deselect_all_blue_people,
        "REMOVE_PLAYER_THING" : map_remove_player_thing,
        "ZOOM_TO" : map_zoom_to,
        "KILL_TEAM_IN_AREA" : map_kill_team_in_area,
        "TURN_PANEL_ON" : map_turn_panel_on,
        "GIVE_PLAYER_SPELL" : map_give_player_spell,
        "FLASH_BUTTON" : map_flash_button,
        "COUNT_BLUE_IN_HOUSES" : map_count_blue_in_houses,
        "COUNT_BLUE_WITH_BUILD_COMMAND" : map_count_blue_with_build_command,
        "COUNT_BLUE_SHAPES" : map_count_blue_shapes,
        "MOVE_SHAMAN_TO_MARKER" : map_move_shaman_to_marker,
        "IS_PLAYER_IN_WORLD_VIEW" : map_is_player_in_world_view,
        "SET_AUTO_BUILD" : map_set_auto_build,
        "SET_AUTO_HOUSE" : map_set_auto_house, 
        "GIVE_MANA_TO_PLAYER" : map_give_mana_to_player,
        "CREATE_MSG_INFORMATION_ZOOM" : map_create_msg_information_zoom,
        "TARGET_BLUE_SHAMAN" : map_target_blue_shaman,
        "CLEAR_GUARDING_FROM" : map_clear_guarding_from,
        "CALL_TO_ARMS" : map_call_to_arms,
        "GET_NUM_PEOPLE_BEING_PREACHED": map_get_num_people_being_preached,
        "PREACH_AT_MARKER" : map_preach_at_marker,
        "FIX_WILD_IN_AREA": map_fix_wild_in_area,
        "COUNT_ANGELS": map_count_angels,
        "REMOVE_TIMER": map_remove_timer,
        "HAS_TIMER_REACHED_ZERO": map_has_timer_reached_zero,
        "GUARD_BETWEEN_MARKERS": map_guard_between_markers,
        "IS_SHAMAN_AVAILABLE_FOR_ATTACK": map_is_shaman_available_for_attack,
        "BUILD_MAIN_DRUM_TOWER": map_build_main_drum_tower,
        "BOAT_PATROL": map_boat_patrol,
        "TRIGGER_LEVEL_LOST": map_trigger_level_lost,
        "IS_PRISON_ON_LEVEL": map_is_prison_on_level,
        "IS_BUILDING_NEAR": map_is_building_near,
        "DELETE_SMOKE_STUFF": map_delete_smoke_stuff,
        "AUTO_MESSAGES": map_auto_messages,
        "CONVERT_AT_MARKER": map_convert_at_marker,
        "EXTRA_WOOD_COLLECTION": map_extra_wood_collection,
        "MARVELLOUS_HOUSE_DEATH": map_marvellous_house_death,
        "SET_TIMER_GOING": map_set_timer_going,
        "SET_WOOD_COLLECTION_RADII": map_set_wood_collection_radii,
        "TARGET_BLUE_DRUM_TOWERS": map_target_blue_drum_towers,
        "TARGET_S_WARRIORS": map_target_s_warriors,
        "SET_BASE_MARKER": map_set_base_marker,
        "SET_BASE_RADIUS": map_set_base_radius,
    }
    return command_map

def map_auto_messages(p, variable_map):
    """
    Map AUTO_MESSAGES command to Script4 equivalent
    
    Args:
        p: Command parameters
        variable_map: Dictionary of variable mappings
        
    Returns:
        String containing the Script4 equivalent command
    """
    state = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    return f"AUTO_MESSAGES({state})"

def map_convert_at_marker(p, variable_map):
    """
    Map CONVERT_AT_MARKER command to Script4 equivalent
    
    Args:
        p: Command parameters
        variable_map: Dictionary of variable mappings
        
    Returns:
        String containing the Script4 equivalent command
    """
    marker = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    return f"CONVERT_AT_MARKER({marker})"

def map_extra_wood_collection(p, variable_map):
    """
    Map EXTRA_WOOD_COLLECTION command to Script4 equivalent
    
    Args:
        p: Command parameters
        variable_map: Dictionary of variable mappings
        
    Returns:
        String containing the Script4 equivalent command
    """
    state = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    return f"EXTRA_WOOD_COLLECTION({state})"

def map_marvellous_house_death(p, variable_map):
    """
    Map MARVELLOUS_HOUSE_DEATH command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    return f"MARVELLOUS_HOUSE_DEATH()"

def map_set_timer_going(p, variable_map):
    """
    Map SET_TIMER_GOING command to Script4 equivalent
    
    Args:
        p: Command parameters
        variable_map: Dictionary of variable mappings
        
    Returns:
        String containing the Script4 equivalent command
    """
    time = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    return f"SET_TIMER_GOING({time})"

def map_set_wood_collection_radii(p, variable_map):
    """
    Map SET_WOOD_COLLECTION_RADII command to Script4 equivalent
    
    Args:
        p: Command parameters
        variable_map: Dictionary of variable mappings
        
    Returns:
        String containing the Script4 equivalent command
    """
    min_wood = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    max_wood = convert_value(p[PARAM_INDEX_THIRD_ARG], variable_map)
    min_rf = convert_value(p[PARAM_INDEX_FOURTH_ARG], variable_map)
    max_rf = convert_value(p[PARAM_INDEX_FIFTH_ARG], variable_map)
    return f"SET_WOOD_COLLECTION_RADII({min_wood}, {max_wood}, {min_rf}, {max_rf})"

def map_target_blue_drum_towers(p, variable_map):
    """
    Map TARGET_BLUE_DRUM_TOWERS command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    return f"TARGET_BLUE_DRUM_TOWERS()"

def map_target_s_warriors(p, variable_map):
    """
    Map TARGET_S_WARRIORS command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    return f"TARGET_S_WARRIORS()"

def map_set_base_marker(p, variable_map):
    """
    Map SET_BASE_MARKER command to Script4 equivalent
    
    Args:
        p: Command parameters
        variable_map: Dictionary of variable mappings
        
    Returns:
        String containing the Script4 equivalent command
    """
    marker = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    return f"SET_BASE_MARKER({marker})"

def map_set_base_radius(p, variable_map):
    """
    Map SET_BASE_RADIUS command to Script4 equivalent
    
    Args:
        p: Command parameters
        variable_map: Dictionary of variable mappings
        
    Returns:
        String containing the Script4 equivalent command
    """
    radius = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    return f"SET_BASE_RADIUS({radius})"

def map_delete_smoke_stuff(p, variable_map):
    """
    Map DELETE_SMOKE_STUFF command to Script4 equivalent
    
    Args:
        p: Command parameters
        variable_map: Dictionary of variable mappings
        
    Returns:
        String containing the Script4 equivalent command
    """
    x = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    z = convert_value(p[PARAM_INDEX_THIRD_ARG], variable_map)
    rad = convert_value(p[PARAM_INDEX_FOURTH_ARG], variable_map)
    return f"DELETE_SMOKE_STUFF({x}, {z}, {rad})"

def map_is_building_near(p, variable_map):
    """
    Map IS_BUILDING_NEAR command to Script4 equivalent
    
    Args:
        p: Command parameters
        variable_map: Dictionary of variable mappings
        
    Returns:
        String containing the Script4 equivalent command
    """
    building = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    marker = convert_value(p[PARAM_INDEX_THIRD_ARG], variable_map)
    radius = convert_value(p[PARAM_INDEX_FOURTH_ARG], variable_map)
    var = convert_user_var_name(p[PARAM_INDEX_FIFTH_ARG])
    return f"{var} = IS_BUILDING_NEAR({building}, {marker}, {radius})"

def map_is_prison_on_level(p, variable_map):
    """
    Map IS_PRISON_ON_LEVEL command to Script4 equivalent
    
    Args:
        p: Command parameters
        variable_map: Dictionary of variable mappings
        
    Returns:
        String containing the Script4 equivalent command
    """
    var = convert_user_var_name(p[PARAM_INDEX_SECOND_ARG])
    return f"{var} = IS_PRISON_ON_LEVEL()"

def map_trigger_level_lost(p, variable_map):
    return f"TRIGGER_LEVEL_LOST()"

def map_boat_patrol(p, variable_map):
    """
    Map BOAT_PATROL command to Script4 equivalent
    
    Args:
        p: Command parameters
        variable_map: Dictionary of variable mappings
        
    Returns:
        String containing the Script4 equivalent command
    """
    # Extract parameters for vehicle patrol
    num_people = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    marker1 = convert_value(p[PARAM_INDEX_THIRD_ARG], variable_map)
    marker2 = convert_value(p[PARAM_INDEX_FOURTH_ARG], variable_map)
    marker3 = convert_value(p[PARAM_INDEX_FIFTH_ARG], variable_map)
    marker4 = convert_value(p[6], variable_map)
    
    # Check the vehicle type - code shows it can be BOAT_TYPE or BALLOON_TYPE
    vehicle_type = p[7]
    if vehicle_type == "BOAT_TYPE":
        vehicle_type_value = "M_VEHICLE_BOAT_1"
    elif vehicle_type == "BALLOON_TYPE":
        vehicle_type_value = "M_VEHICLE_AIRSHIP_1"
    else:
        vehicle_type_value = "M_VEHICLE_BOAT_1"  # Default to boat if unspecified
    
    # Map to VEHICLE_PATROL function
    return f"VEHICLE_PATROL({MY_TRIBE}, {num_people}, {marker1}, {marker2}, {marker3}, {marker4}, {vehicle_type_value})"

def map_build_main_drum_tower(p, variable_map):
    return f"_gsi.Players[{MY_TRIBE}].CP.Flags = bit.band(_gsi.Players[{MY_TRIBE}].CP.Flags, bit.bnot(CPF_DONT_BUILD_MAIN_DRUM_TOWER_YET))"

def map_is_shaman_available_for_attack(p, variable_map):
    """
    Map IS_SHAMAN_AVAILABLE_FOR_ATTACK command to Script4 equivalent
    
    Args:
        p: Command parameters
        variable_map: Dictionary of variable mappings
        
    Returns:
        String containing the Script4 equivalent command
    """
    var = convert_user_var_name(p[PARAM_INDEX_SECOND_ARG])
    return f"{var} = IS_SHAMAN_AVAILABLE_FOR_ATTACK({MY_TRIBE})"

def map_guard_between_markers(p, variable_map):
    """
    Map GUARD_BETWEEN_MARKERS command to Script4 equivalent
    
    Args:
        p: Command parameters
        variable_map: Dictionary of variable mappings
        
    Returns:
        String containing the Script4 equivalent command
    """
    marker1 = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    marker2 = convert_value(p[PARAM_INDEX_THIRD_ARG], variable_map)
    num_braves = convert_value(p[PARAM_INDEX_FOURTH_ARG], variable_map)
    num_warriors = convert_value(p[PARAM_INDEX_FIFTH_ARG], variable_map)
    num_s_warriors = convert_value(p[6], variable_map)
    num_preachers = convert_value(p[7], variable_map)
    guard_type = convert_value(p[8], variable_map)
    
    return f"GUARD_BETWEEN_MARKERS({MY_TRIBE}, {marker1}, {marker2}, {num_braves}, {num_warriors}, {num_s_warriors}, {num_preachers}, {guard_type})"

def map_has_timer_reached_zero(p, variable_map):
    """
    Map HAS_TIMER_REACHED_ZERO command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    return "HAS_TIMER_REACHED_ZERO()"

def map_remove_timer(p, variable_map):
    """
    Map REMOVE_TIMER command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    return "REMOVE_TIMER()"

def map_count_angels(p, variable_map):
    """
    Map COUNT_ANGELS command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    tribe = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    var = convert_user_var_name(p[PARAM_INDEX_SECOND_ARG])
    return f"{var} = COUNT_ANGELS({tribe})"

def map_fix_wild_in_area(p, variable_map):
    """
    Map FIX_WILD_IN_AREA command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    x = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    z = convert_value(p[PARAM_INDEX_THIRD_ARG], variable_map)
    Rad = convert_value(p[PARAM_INDEX_FOURTH_ARG], variable_map)
    return f"FIX_WILD_IN_AREA({x}, {z}, {Rad})"

def map_preach_at_marker(p, variable_map):

    """
    Map PREACH_AT_MARKER command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    marker = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    return f"PREACH_AT_MARKER({marker})"

def map_get_num_people_being_preached(p, variable_map):
    """
    Map GET_NUM_PEOPLE_BEING_PREACHED command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    tribe = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    var = convert_user_var_name(p[PARAM_INDEX_THIRD_ARG])
    return f"{var} = GET_NUM_PEOPLE_BEING_PREACHED({tribe})"

def map_call_to_arms(p, variable_map):
    return f"CALL_TO_ARMS({MY_TRIBE})"

def map_clear_guarding_from(p, variable_map):
    """
    Map CLEAR_GUARDING_FROM command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    ent1 = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    ent2 = convert_value(p[PARAM_INDEX_THIRD_ARG], variable_map)
    ent3 = convert_value(p[PARAM_INDEX_FOURTH_ARG], variable_map)
    ent4 = convert_value(p[PARAM_INDEX_FIFTH_ARG], variable_map)
    return f"CLEAR_GUARDING_FROM({ent1}, {ent2}, {ent3}, {ent4})"

def map_target_blue_shaman(p, variable_map):
    return f"TARGET_SHAMAN({TRIBE_BLUE})"

def map_create_msg_information_zoom(p, variable_map):
    """
    Map CREATE_MSG_INFORMATION_ZOOM command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    index = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    x = convert_value(p[PARAM_INDEX_THIRD_ARG], variable_map)
    z = convert_value(p[PARAM_INDEX_FOURTH_ARG], variable_map)
    angle = convert_value(p[PARAM_INDEX_FIFTH_ARG], variable_map)
    return f"CREATE_MSG_INFORMATION_ZOOM({index}, {x}, {z}, {angle})"

def map_give_mana_to_player(p, variable_map):
    """
    Map GIVE_MANA_TO_PLAYER command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    player = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    mana = convert_value(p[PARAM_INDEX_THIRD_ARG], variable_map)
    return f"GIVE_MANA_TO_PLAYER({player}, {mana})"

def map_set_auto_house(p, variable_map):
    """
    Map SET_AUTO_HOUSE command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    state = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    return f"SET_AUTO_HOUSE({state})"

def map_set_auto_build(p, variable_map):
    """
    Map SET_AUTO_BUILD command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    state = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    return f"SET_AUTO_BUILD({state})"

def map_is_player_in_world_view(p, variable_map):
    """
    Map IS_PLAYER_IN_WORLD_VIEW command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    var = convert_user_var_name(p[PARAM_INDEX_SECOND_ARG])
    return f"{var} = IS_PLAYER_IN_WORLD_VIEW({MY_TRIBE})"

def map_move_shaman_to_marker(p, variable_map):
    """
    Map MOVE_SHAMAN_TO_MARKER command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    marker = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    return f"MOVE_SHAMAN_TO_MARKER({marker})"

def map_count_blue_shapes(p, variable_map):
    """
    Map COUNT_BLUE_SHAPES command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    var = convert_user_var_name(p[PARAM_INDEX_SECOND_ARG])
    return f"{var} = COUNT_SHAPES({TRIBE_BLUE})"

def map_count_blue_with_build_command(p, variable_map):
    """
    Map COUNT_BLUE_WITH_BUILD_COMMAND command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    var = convert_user_var_name(p[PARAM_INDEX_SECOND_ARG])
    return f"{var} = COUNT_BLUE_WITH_BUILD_COMMAND({TRIBE_BLUE})"

def map_count_blue_in_houses(p, variable_map):
    """
    Map COUNT_BLUE_IN_HOUSES command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    var = convert_user_var_name(p[PARAM_INDEX_SECOND_ARG])
    return f"{var} = COUNT_PEOPLE_IN_HOUSES({TRIBE_BLUE})"

def map_flash_button(p, variable_map):
    """
    Map FLASH_BUTTON command to Script4 equivalent
    
    Args:
        p: Command parameters
        variable_map: Dictionary of variable mappings
        
    Returns:
        String containing the Script4 equivalent command
    """
    button = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    onoff =  convert_value(p[PARAM_INDEX_THIRD_ARG], variable_map)
    return f"FLASH_BUTTON({button}, {onoff})"

def map_give_player_spell(p, variable_map):
    tribe = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    thing = convert_value(p[PARAM_INDEX_THIRD_ARG], variable_map)

    # Check if thing contains BUILDING or SPELL and set appropriate type
    if "BUILDING" in thing:
        return f"set_player_can_cast({thing}, {tribe})"
    elif "SPELL" in thing:
        return f"set_player_can_build({thing}, {tribe})"
    else:
        raise ValueError(f"Unsupported thing type in REMOVE_PLAYER_THING: {thing}")

def map_turn_panel_on(p, variable_map):
    idx = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    return f"TURN_PANEL_ON({idx})"

def map_kill_team_in_area(p, variable_map):
    """
    Map KILL_TEAM_IN_AREA command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    x = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    z = convert_value(p[PARAM_INDEX_THIRD_ARG], variable_map)
    Rad = convert_value(p[PARAM_INDEX_FOURTH_ARG], variable_map)
    return f"KILL_TEAM_IN_AREA({x}, {z}, {Rad})"

def map_zoom_to(p, variable_map):
    """
    Map ZOOM_TO command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    x = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    z = convert_value(p[PARAM_INDEX_THIRD_ARG], variable_map)
    Angle = convert_value(p[PARAM_INDEX_FOURTH_ARG], variable_map)
    return f"ZOOM_TO({x}, {z}, {Angle})"

def map_remove_player_thing(p, variable_map):
    tribe = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    thing = convert_value(p[PARAM_INDEX_THIRD_ARG], variable_map)

    # Check if thing contains BUILDING or SPELL and set appropriate type
    if "BUILDING" in thing:
        return f"set_player_cannot_cast({thing}, {tribe})"
    elif "SPELL" in thing:
        return f"set_player_cannot_build({thing}, {tribe})"
    else:
        raise ValueError(f"Unsupported thing type in REMOVE_PLAYER_THING: {thing}")
    


def map_deselect_all_blue_people(p, variable_map):
    return f"DESELECT_ALL_BLUE_PEOPLE({TRIBE_BLUE})"

def map_clear_all_msg(p, variable_map):
    return "CLEAR_ALL_MSG()"

def map_set_msg_timeout(p, variable_map):
    """
    Map SET_MSG_TIMEOUT command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    time = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    return f"SET_MSG_TIMEOUT({time})"

def map_trigger_level_won(p, variable_map):
    return f"TRIGGER_LEVEL_WON()"

def map_send_shaman_denfenders_home(p, variable_map):
    return f"SEND_SHAMEN_DEFENDERS_HOME({MY_TRIBE})"

def map_state_bring_new_people_back(p, variable_map):
    return map_state_command(p, "STATE_BRING_NEW_PEOPLE_BACK", variable_map)

def map_state_train_people(p, variable_map):
    return map_state_command(p, "STATE_TRAIN_PEOPLE", variable_map)

def map_state_med_man_get_wild_peeps(p, variable_map):
    return map_state_command(p, "STATE_MED_MAN_GET_WILD_PEEPS", variable_map)

def map_state_construct_building(p, variable_map):
    return map_state_command(p, "STATE_CONSTRUCT_BUILDING", variable_map)

def map_state_fetch_wood(p, variable_map):
    return map_state_command(p, "STATE_FETCH_WOOD", variable_map)

def map_state_send_ghosts(p, variable_map):
    return map_state_command(p, "STATE_SEND_GHOSTS", variable_map)

def map_state_fetch_lost_people(p, variable_map):
    return map_state_command(p, "STATE_FETCH_LOST_PEOPLE", variable_map)

def map_state_fetch_far_vehicle(p, variable_map):
    return map_state_command(p, "STATE_FETCH_FAR_VEHICLE", variable_map)

def map_state_fetch_lost_vehicle(p, variable_map):
    return map_state_command(p, "STATE_FETCH_LOST_VEHICLE", variable_map)

def map_state_defend(p, variable_map):
    return map_state_command(p, "STATE_DEFEND", variable_map)

def map_state_defend_base(p, variable_map):
    return map_state_command(p, "STATE_DEFEND_BASE", variable_map)

def map_state_house_a_person(p, variable_map):
    return map_state_command(p, "STATE_HOUSE_A_PERSON", variable_map)

def map_state_auto_attack(p, variable_map):
    return map_state_command(p, "STATE_AUTO_ATTACK", variable_map)

def map_state_populate_drum_tower(p, variable_map):
    return map_state_command(p, "STATE_POPULATE_DRUM_TOWER", variable_map)

def map_state_build_vehicle(p, variable_map):
    return map_state_command(p, "STATE_BUILD_VEHICLE", variable_map)

def map_state_preach(p, variable_map):
    return map_state_command(p, "STATE_PREACH", variable_map)

def map_state_build_walls(p, variable_map):
    return map_state_command(p, "STATE_BUILD_WALLS", variable_map)

def map_state_sabotage(p, variable_map):
    return map_state_command(p, "STATE_SABOTAGE", variable_map)

def map_state_spell_offensive(p, variable_map):
    return map_state_command(p, "STATE_SPELL_OFFENSIVE", variable_map)

def map_state_super_defend(p, variable_map):
    return map_state_command(p, "STATE_SUPER_DEFEND", variable_map)

def map_state_med_man_defend(p, variable_map):
    return map_state_command(p, "STATE_MED_MAN_DEFEND", variable_map)

def map_state_flatten_base(p, variable_map):
    return map_state_command(p, "STATE_FLATTEN_BASE", variable_map)

def map_state_build_outer_defences(p, variable_map):
    return map_state_command(p, "STATE_BUILD_OUTER_DEFENCES", variable_map)

def map_state_guard_at_marker(p, variable_map):
    return map_state_command(p, "STATE_GUARD_AT_MARKER", variable_map)

def map_state_send_all_to_marker(p, variable_map):
    return map_state_command(p, "STATE_SEND_ALL_TO_MARKER", variable_map)

def map_state_pray_at_head(p, variable_map):
    return map_state_command(p, "STATE_PRAY_AT_HEAD", variable_map)

def map_state_boat_patrol(p, variable_map):
    return map_state_command(p, "STATE_BOAT_PATROL", variable_map)

def map_state_defend_shamen(p, variable_map):
    return map_state_command(p, "STATE_DEFEND_SHAMEN", variable_map)

def map_get_height_at_pos(p, variable_map):
    """
    Map GET_HEIGHT_AT_POS command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    var = convert_user_var_name(p[PARAM_INDEX_THIRD_ARG])
    pos = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    return f"{var} = GET_HEIGHT_AT_POS({pos})"

def map_get_head_trigger_count(p, variable_map):
    """
    Map GET_HEAD_TRIGGER_COUNT command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    var = convert_user_var_name(p[PARAM_INDEX_FOURTH_ARG])
    param1 = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    param2 = convert_value(p[PARAM_INDEX_THIRD_ARG], variable_map)
    return f"{var} = GET_HEAD_TRIGGER_COUNT({param1}, {param2})"

def map_get_num_one_off_spells(p, variable_map):
    """
    Map GET_NUM_ONE_OFF_SPELLS command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    var = convert_user_var_name(p[PARAM_INDEX_FOURTH_ARG])
    spell = convert_value(p[PARAM_INDEX_THIRD_ARG].replace('INT_', 'M_SPELL_'), variable_map)
    return f"{var} = GET_NUM_ONE_OFF_SPELLS({TRIBE_BLUE}, {spell})"

def map_nav_check(p, variable_map):
    """
    Map NAV_CHECK command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    var = convert_user_var_name(p[6])
    param1 = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    param2 = convert_int_constant(p[PARAM_INDEX_THIRD_ARG])
    param3 = convert_value(p[PARAM_INDEX_FOURTH_ARG], variable_map)
    param4 = convert_value(p[PARAM_INDEX_FIFTH_ARG], variable_map)
    return f"{var} = NAV_CHECK({MY_TRIBE}, {param1}, {param2}, {param3}, {param4})"

def map_set_reincarnation(p, variable_map):
    """
    Map SET_REINCARNATION command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    state = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    return f"SET_REINCARNATION({state}, MY_TRIBE)"

def map_delay_main_drum_tower(p, variable_map):
    """
    Map DELAY_MAIN_DRUM_TOWER command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    return f"DELAY_MAIN_DRUM_TOWER(ON, {MY_TRIBE})"

def map_set_attack_variable(p, variable_map):
    """
    Map SET_ATTACK_VARIABLE command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    return f"SET_ATTACK_VARIABLE({MY_TRIBE}, 0) -- TODO! Not supported!"

def map_disable_user_inputs(p, variable_map):
    """
    Map DISABLE_USER_INPUTS command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    return "DISABLE_USER_INPUTS()"

def map_enable_user_inputs(p, variable_map):
    """
    Map ENABLE_USER_INPUTS command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    return "ENABLE_USER_INPUTS()"

def map_state_command(p, state_name, variable_map):
    """
    Map STATE commands to Script4 equivalent
    
    Args:
        p: Command parameters
        state_name: The specific state name from STATE_CP_MAP
        
    Returns:
        String containing the Script4 equivalent command
    """
    state = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    return f"STATE_SET({MY_TRIBE}, {STATE_CP_MAP[state_name]}, {state})"

def map_state_spell_defence(p, variable_map):
    """
    Map STATE_SPELL_DEFENCE command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    param1 = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    param2 = convert_value(p[PARAM_INDEX_THIRD_ARG], variable_map)
    param3 = convert_value(p[PARAM_INDEX_FOURTH_ARG], variable_map)
    return f"SHAMAN_DEFEND({MY_TRIBE}, {param1}, {param2}, {param3})"

def map_set_defence_radius(p, variable_map):
    """
    Map SET_DEFENCE_RADIUS command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    radius = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    return f"SET_DEFENCE_RADIUS({MY_TRIBE}, {radius})"

def map_set_marker_entry(p, variable_map):
    """
    Map SET_MARKER_ENTRY command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    param1 = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    param2 = convert_value(p[PARAM_INDEX_THIRD_ARG], variable_map)
    param3 = convert_value(p[PARAM_INDEX_FOURTH_ARG], variable_map)
    param4 = convert_value(p[PARAM_INDEX_FIFTH_ARG], variable_map)
    param5 = convert_value(p[6], variable_map)
    param6 = convert_value(p[7], variable_map)
    param7 = convert_value(p[8], variable_map)
    return f"SET_MARKER_ENTRY({MY_TRIBE}, {param1}, {param2}, {param3}, {param4}, {param5}, {param6}, {param7})"

def map_only_stand_at_markers(p, variable_map):
    """
    Map ONLY_STAND_AT_MARKERS command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    return f"ONLY_STAND_AT_MARKERS({MY_TRIBE})"

def map_set_bucket_count_for_spell(p, variable_map):
    """
    Map SET_BUCKET_COUNT_FOR_SPELL command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    spell = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    count = convert_value(p[PARAM_INDEX_THIRD_ARG], variable_map)
    return f"SET_BUCKET_COUNT_FOR_SPELL({MY_TRIBE}, {spell}, {count})"

def map_flyby_create_new(p, variable_map):
    """
    Map FLYBY_CREATE_NEW command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    return "FLYBY_CREATE_NEW()"

def map_flyby_allow_interrupt(p, variable_map):
    """
    Map FLYBY_ALLOW_INTERRUPT command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    state = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    return f"FLYBY_ALLOW_INTERRUPT({state})"

def map_flyby_set_event_pos(p, variable_map):
    """
    Map FLYBY_SET_EVENT_POS command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    param1 = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    param2 = convert_value(p[PARAM_INDEX_THIRD_ARG], variable_map)
    param3 = convert_value(p[PARAM_INDEX_FOURTH_ARG], variable_map)
    param4 = convert_value(p[PARAM_INDEX_FIFTH_ARG], variable_map)
    return f"FLYBY_SET_EVENT_POS({param1}, {param2}, {param3}, {param4})"

def map_flyby_set_event_angle(p, variable_map):
    """
    Map FLYBY_SET_EVENT_ANGLE command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    param1 = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    param2 = convert_value(p[PARAM_INDEX_THIRD_ARG], variable_map)
    param3 = convert_value(p[PARAM_INDEX_FOURTH_ARG], variable_map)
    return f"FLYBY_SET_EVENT_ANGLE({param1}, {param2}, {param3})"

def map_flyby_set_event_zoom(p, variable_map):
    """
    Map FLYBY_SET_EVENT_ZOOM command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    param1 = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    param2 = convert_value(p[PARAM_INDEX_THIRD_ARG], variable_map)
    param3 = convert_value(p[PARAM_INDEX_FOURTH_ARG], variable_map)
    return f"FLYBY_SET_EVENT_ZOOM({param1}, {param2}, {param3})"

def map_flyby_set_event_tooltip(p, variable_map):
    """
    Map FLYBY_SET_EVENT_TOOLTIP command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    param1 = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    param2 = convert_value(p[PARAM_INDEX_THIRD_ARG], variable_map)
    param3 = convert_value(p[PARAM_INDEX_FOURTH_ARG], variable_map)
    param4 = convert_value(p[PARAM_INDEX_FIFTH_ARG], variable_map)
    param5 = convert_value(p[6], variable_map)
    return f"FLYBY_SET_EVENT_TOOLTIP({param1}, {param2}, {param3}, {param4}, {param5})"

def map_flyby_set_end_target(p, variable_map):
    """
    Map FLYBY_SET_END_TARGET command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    param1 = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    param2 = convert_value(p[PARAM_INDEX_THIRD_ARG], variable_map)
    param3 = convert_value(p[PARAM_INDEX_FOURTH_ARG], variable_map)
    param4 = convert_value(p[PARAM_INDEX_FIFTH_ARG], variable_map)
    return f"FLYBY_SET_END_TARGET({param1}, {param2}, {param3}, {param4})"

def map_flyby_start(p, variable_map):
    """
    Map FLYBY_START command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    return "FLYBY_START()"

def map_create_msg_information(p, variable_map):
    """
    Map CREATE_MSG_INFORMATION command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    message_id = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    return f"CREATE_MSG_INFORMATION({message_id})"

def map_create_msg_narrative(p, variable_map):
    """
    Map CREATE_MSG_NARRATIVE command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    message_id = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    return f"CREATE_MSG_NARRATIVE({message_id})"

def map_set_msg_auto_open_dlg(p, variable_map):
    """
    Map SET_MSG_AUTO_OPEN_DLG command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    return "SET_MSG_AUTO_OPEN_DLG()"

def map_set_msg_delete_on_ok(p, variable_map):
    """
    Map SET_MSG_DELETE_ON_OK command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    return "SET_MSG_DELETE_ON_OK()"

def map_partial_building_count(p, variable_map):
    """
    Map PARTIAL_BUILDING_COUNT command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    return f"PARTIAL_BUILDING_COUNT({MY_TRIBE})"

def map_trigger_thing(p, variable_map):
    """
    Map TRIGGER_THING command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    thing = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    return f"TRIGGER_THING({thing})"

def map_remove_head_at_pos(p, variable_map):
    """
    Map REMOVE_HEAD_AT_POS command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    param1 = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    param2 = convert_value(p[PARAM_INDEX_THIRD_ARG], variable_map)
    return f"REMOVE_HEAD_AT_POS({param1}, {param2})"

def map_defend_shamen(p, variable_map):
    """
    Map DEFEND_SHAMEN command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    return f"DEFEND_SHAMEN({MY_TRIBE}, _gsi.Players[{MY_TRIBE}].NumPeople)"

def map_train_people_now(p, variable_map):
    """
    Map TRAIN_PEOPLE_NOW command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    param1 = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    param2 = convert_value(p[PARAM_INDEX_THIRD_ARG].replace('INT_', 'M_PERSON_'), variable_map)
    return f"TRAIN_PEOPLE_NOW({MY_TRIBE}, {param1}, {param2})"

def map_turn_push(p, variable_map):
    """
    Map TURN_PUSH command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    turns = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    return f"TURN_PUSH({turns})"

def map_set_bucket_usage(p, variable_map):
    """
    Map SET_BUCKET_USAGE command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    usage = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    return f"SET_BUCKET_USAGE({MY_TRIBE}, {usage})"

def map_give_up_and_sulk(p, variable_map):
    """
    Map GIVE_UP_AND_SULK command to Script4 equivalent
    
    Args:
        p: Command parameters
        
    Returns:
        String containing the Script4 equivalent command
    """
    param = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    return f"GIVE_UP_AND_SULK({MY_TRIBE}, {param})"

def map_set_spell_entry(p, variable_map):
    """Helper function for SET_SPELL_ENTRY command mapping"""
    spell_idx = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)  # The spell slot index
    spell_type = convert_value(p[PARAM_INDEX_THIRD_ARG], variable_map)  # The spell type (INT_BLAST, 0, etc.)
    
    # For the spell parameter in the function
    if spell_type.startswith('INT_'):
        spell_param = spell_type.replace('INT_', SPELL_PREFIX)
    else:
        spell_param = spell_type
    
    # For the spell cost parameter
    if spell_type == '0':
        # Special case: spell type 0 maps to BLAST for cost
        cost_spell = f'{SPELL_PREFIX}BLAST'
    elif spell_type.startswith('INT_'):
        cost_spell = f'{SPELL_PREFIX}{spell_type[4:]}'  # Remove 'INT_' prefix
    elif spell_type.startswith(SPELL_PREFIX):
        cost_spell = spell_type  # Already has the correct prefix
    else:
        cost_spell = f'{SPELL_PREFIX}{spell_type}'
    
    return f"SET_SPELL_ENTRY({MY_TRIBE}, {spell_idx}, {spell_param}, PLAYERS_SPELL_COST({MY_TRIBE}, {cost_spell}), {convert_value(p[5], variable_map)}, {convert_value(p[6], variable_map)}, {convert_value(p[7], variable_map)})"

# Define missing attack command mapper
def map_attack_command(p, variable_map):
    """Helper function for ATTACK command with variable parameters"""
    # Target tribe - always present
    target_tribe = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)

    # Number of attackers
    num_attackers = convert_value(p[PARAM_INDEX_THIRD_ARG], variable_map)

    # Attack type
    attack_type = convert_value(p[PARAM_INDEX_FOURTH_ARG], variable_map)

    # Target building/marker
    target = convert_value(p[PARAM_INDEX_FIFTH_ARG], variable_map)

    # Rest of function remains the same...
    distance = convert_value(p[6], variable_map)
    spell1 = convert_value(p[7] if len(p) > 7 else INT_NO_SPECIFIC_SPELL, variable_map)
    spell2 = convert_value(p[8] if len(p) > 8 else INT_NO_SPECIFIC_SPELL, variable_map)
    spell3 = convert_value(p[9] if len(p) > 9 else INT_NO_SPECIFIC_SPELL, variable_map)
    attack_mode = convert_value(p[10] if len(p) > 10 else ATTACK_NORMAL, variable_map)
    param1 = convert_value(p[11] if len(p) > 11 else "0", variable_map)
    param2 = convert_value(p[12] if len(p) > 12 else "-1", variable_map)
    param3 = convert_value(p[13] if len(p) > 13 else "-1", variable_map)
    param4 = convert_value(p[14] if len(p) > 14 else "-1", variable_map)

    return f"ATTK_RST = ATTACK({MY_TRIBE}, {target_tribe}, {num_attackers}, {attack_type}, {target}, {distance}, {spell1}, {spell2}, {spell3}, {attack_mode}, {param1}, {param2}, {param3}, {param4})"

# Helper function for handling DO_CONVERT_AT_MARKER
def map_convert_at_marker(p, variable_map):
    """Map CONVERT_AT_MARKER command to Script4 equivalent"""
    marker = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    return f"CONVERT_AT_MARKER({MY_TRIBE}, {marker})"

# Helper function for marker handling
def map_marker_entries(p, variable_map):
    """Map MARKER_ENTRIES command to Script4 equivalent"""
    entries = ', '.join([convert_value(p[i], variable_map) if i < len(p) else '-1' for i in range(PARAM_INDEX_SECOND_ARG, PARAM_INDEX_SECOND_ARG + 4)])
    return f"MARKER_ENTRIES({MY_TRIBE}, {entries})"

# Helper function for count people in marker
def map_count_people_in_marker(p, variable_map):
    """Map COUNT_PEOPLE_IN_MARKER command to Script4 equivalent"""
    tribe = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    marker = convert_value(p[PARAM_INDEX_THIRD_ARG], variable_map)
    radius = convert_value(p[PARAM_INDEX_FOURTH_ARG], variable_map)
    result_var = convert_user_var_name(p[PARAM_INDEX_FIFTH_ARG])
    
    return f"{result_var} = COUNT_PEOPLE_IN_MARKER({tribe}, {marker}, {radius})"

# Helper function for spell casting triggers
def map_get_spells_cast(p, variable_map):
    """Map GET_SPELLS_CAST command to Script4 equivalent"""
    tribe = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    spell = convert_value(p[PARAM_INDEX_THIRD_ARG], variable_map)
    result_var = convert_user_var_name(p[PARAM_INDEX_FOURTH_ARG])
    
    return f"{result_var} = GET_SPELLS_CAST({tribe}, {spell})"

def map_build_drum_tower(p, variable_map):
    """Map BUILD_DRUM_TOWER command to Script4 format"""
    x_pos = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    z_pos = convert_value(p[PARAM_INDEX_THIRD_ARG], variable_map)
    return f"BUILD_DRUM_TOWER({MY_TRIBE}, {x_pos}, {z_pos})"

def map_give_one_shot(p, variable_map):
    """Map GIVE_ONE_SHOT command to Script4 format"""
    spell = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    tribe = convert_value(p[PARAM_INDEX_THIRD_ARG], variable_map)
    tribe_converted = convert_int_constant(tribe)
    return f"GIVE_ONE_SHOT({spell}, {tribe_converted})"

def map_i_have_one_shot(p, variable_map):
    """Map I_HAVE_ONE_SHOT command to Script4 format"""
    spell_type = SPELL_TYPE_SPELL if p[PARAM_INDEX_SECOND_ARG] == "SPELL_TYPE" else SPELL_TYPE_BUILDING
    spell = convert_value(p[PARAM_INDEX_THIRD_ARG], variable_map)
    variable = convert_user_var_name(p[PARAM_INDEX_FOURTH_ARG])
    return f"{variable} = I_HAVE_ONE_SHOT({MY_TRIBE}, {spell_type}, {spell})"

def map_pray_at_head(p, variable_map):
    """Map PRAY_AT_HEAD command to Script4 format"""
    num_people = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    marker = convert_value(p[PARAM_INDEX_THIRD_ARG] if len(p) > PARAM_INDEX_THIRD_ARG else "0", variable_map)
    return f"PRAY_AT_HEAD({MY_TRIBE}, {num_people}, {marker})"

def map_put_person_in_dt(p, variable_map):
    """Map PUT_PERSON_IN_DT command to Script4 format"""
    person_type = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    x_pos = convert_value(p[PARAM_INDEX_THIRD_ARG], variable_map)
    z_pos = convert_value(p[PARAM_INDEX_FOURTH_ARG], variable_map)
    return f"PUT_PERSON_IN_DT({MY_TRIBE}, {person_type}, {x_pos}, {z_pos})"

def map_send_all_people_to_marker(p, variable_map):
    """Map SEND_ALL_PEOPLE_TO_MARKER command to Script4 format"""
    marker = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    return f"SEND_ALL_PEOPLE_TO_MARKER({MY_TRIBE}, {marker})"

def map_set_drum_tower_pos(p, variable_map):
    """Map SET_DRUM_TOWER_POS command to Script4 format"""
    x_pos = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    z_pos = convert_value(p[PARAM_INDEX_THIRD_ARG], variable_map)
    return f"SET_DRUM_TOWER_POS({MY_TRIBE}, {x_pos}, {z_pos})"

def map_spell_at_marker(p, variable_map):
    """Map SPELL_AT_MARKER command to Script4 format"""
    spell = convert_value(p[PARAM_INDEX_SECOND_ARG], variable_map)
    marker = convert_value(p[PARAM_INDEX_THIRD_ARG], variable_map)
    direction = convert_value(p[PARAM_INDEX_FOURTH_ARG], variable_map)
    return f"SPELL_ATTACK({MY_TRIBE}, {spell}, {marker}, {direction})"

def map_set_no_blue_reinc(p, variable_map):
    """Map SET_NO_BLUE_REINC command to Script4 format"""
    return f"SET_NO_REINC({TRIBE_BLUE})"

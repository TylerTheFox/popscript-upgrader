"""
Grammar rules for the Script2 language parser
"""
import sys
import os

# Fix import path if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from Utils.Constants_Loader import STATE_TOKENS, DO_COMMANDS, OPERATORS

# Dynamically build the state_token rule based on constants
state_token_rule = '\n        state_token : ' + '\n                   | '.join(STATE_TOKENS)

# Dynamically build a general DO command rule
do_commands_rule = '\n        do_command : ' + '\n                  | '.join(DO_COMMANDS)

# Production rules
grammar_rules = {
    'script': '''
        script : COMPUTER_PLAYER IDENTIFIER statements
              | COMPUTER_PLAYER IDENTIFIER statements SCRIPT_END
    ''',

    'statements': '''
        statements : BEGIN statement_list END
    ''',

    'statement_list': '''
        statement_list : statement statement_list
                     | statement
                     | empty
    ''',

    'statement': '''
        statement : if_statement
                 | do_statement
                 | set_statement
                 | every_statement
                 | multiply_statement
                 | increment_statement
                 | decrement_statement
                 | divide_statement
    ''',

    'if_statement': '''
        if_statement : IF LPAREN expression RPAREN BEGIN statement_list END ENDIF
                    | IF LPAREN expression RPAREN BEGIN statement_list ENDIF
                    | IF LPAREN expression RPAREN BEGIN statement_list END ELSE BEGIN statement_list END ENDIF
                    | IF LPAREN expression RPAREN BEGIN statement_list END ELSE BEGIN statement_list ENDIF
    ''',

    'do_statement': '''
        do_statement : DO DISABLE_USER_INPUTS
                    | DO PARTIAL_BUILDING_COUNT
                    | DO ENABLE_USER_INPUTS
                    | DO ONLY_STAND_AT_MARKERS
                    | DO DELAY_MAIN_DRUM_TOWER
                    | DO FLYBY_CREATE_NEW
                    | DO TRIGGER_LEVEL_WON
                    | DO COUNT_BLUE_IN_HOUSES IDENTIFIER
                    | DO COUNT_BLUE_SHAPES IDENTIFIER
                    | DO COUNT_BLUE_WITH_BUILD_COMMAND IDENTIFIER
                    | DO MOVE_SHAMAN_TO_MARKER IDENTIFIER
                    | DO IS_PLAYER_IN_WORLD_VIEW IDENTIFIER
                    | DO GIVE_MANA_TO_PLAYER IDENTIFIER IDENTIFIER
                    | DO TARGET_BLUE_SHAMAN
                    | DO GET_NUM_PEOPLE_BEING_PREACHED IDENTIFIER IDENTIFIER
                    | DO CLEAR_GUARDING_FROM IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER
                    | DO SET_AUTO_HOUSE ON
                    | DO SET_AUTO_HOUSE OFF
                    | DO SET_AUTO_BUILD ON
                    | DO SET_AUTO_BUILD OFF
                    | DO PREACH_AT_MARKER IDENTIFIER
                    | DO CALL_TO_ARMS
                    | DO FLYBY_ALLOW_INTERRUPT ON
                    | DO FLYBY_ALLOW_INTERRUPT OFF
                    | DO FLYBY_SET_EVENT_POS IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER
                    | DO FLYBY_SET_EVENT_ANGLE IDENTIFIER IDENTIFIER IDENTIFIER
                    | DO FLYBY_SET_EVENT_ZOOM IDENTIFIER IDENTIFIER IDENTIFIER
                    | DO FLYBY_SET_EVENT_TOOLTIP IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER
                    | DO FLYBY_SET_END_TARGET IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER
                    | DO REMOVE_PLAYER_THING IDENTIFIER IDENTIFIER
                    | DO GIVE_PLAYER_SPELL IDENTIFIER IDENTIFIER
                    | DO ZOOM_TO IDENTIFIER IDENTIFIER IDENTIFIER
                    | DO KILL_TEAM_IN_AREA IDENTIFIER IDENTIFIER IDENTIFIER
                    | DO SET_MSG_TIMEOUT IDENTIFIER
                    | DO FLASH_BUTTON IDENTIFIER ON 
                    | DO FLASH_BUTTON IDENTIFIER OFF
                    | DO FLYBY_START
                    | DO CLEAR_ALL_MSG
                    | DO GIVE_UP_AND_SULK ON
                    | DO GIVE_UP_AND_SULK OFF
                    | DO TRAIN_PEOPLE_NOW IDENTIFIER IDENTIFIER
                    | DO DEFEND_SHAMEN IDENTIFIER
                    | DO REMOVE_HEAD_AT_POS IDENTIFIER IDENTIFIER
                    | DO GET_HEIGHT_AT_POS IDENTIFIER IDENTIFIER
                    | DO TRIGGER_THING IDENTIFIER
                    | DO GET_NUM_ONE_OFF_SPELLS IDENTIFIER IDENTIFIER IDENTIFIER
                    | DO GET_HEAD_TRIGGER_COUNT IDENTIFIER IDENTIFIER IDENTIFIER
                    | DO CREATE_MSG_INFORMATION IDENTIFIER
                    | DO SET_REINCARNATION ON
                    | DO SET_REINCARNATION OFF
                    | DO SET_DEFENCE_RADIUS IDENTIFIER
                    | DO TURN_PUSH ON
                    | DO TURN_PUSH OFF
                    | DO SET_MSG_AUTO_OPEN_DLG
                    | DO SET_MSG_DELETE_ON_OK
                    | DO SET_BUCKET_USAGE ON
                    | DO SET_BUCKET_USAGE OFF
                    | DO FIX_WILD_IN_AREA IDENTIFIER IDENTIFIER IDENTIFIER
                    | DO SET_ATTACK_VARIABLE IDENTIFIER
                    | DO SET_BUCKET_COUNT_FOR_SPELL IDENTIFIER IDENTIFIER
                    | DO SET_SPELL_ENTRY IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER
                    | DO STATE_SPELL_DEFENCE IDENTIFIER IDENTIFIER ON
                    | DO STATE_SPELL_DEFENCE IDENTIFIER IDENTIFIER OFF
                    | DO GET_SPELLS_CAST IDENTIFIER IDENTIFIER IDENTIFIER
                    | DO SET_MARKER_ENTRY IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER
                    | DO MARKER_ENTRIES IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER
                    | DO COUNT_PEOPLE_IN_MARKER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER
                    | DO ATTACK IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER
                    | DO ATTACK IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER
                    | DO ATTACK IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER
                    | DO TURN_PANEL_ON IDENTIFIER
                    | DO CREATE_MSG_INFORMATION_ZOOM IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER
                    | DO IDENTIFIER ON
                    | DO IDENTIFIER OFF
                    | DO state_token ON
                    | DO state_token OFF
                    | DO state_token INTEGER INTEGER
                    | DO state_token INTEGER INTEGER INTEGER
                    | DO state_token INTEGER INTEGER ON
                    | DO state_token INTEGER INTEGER OFF
                    | DO CONVERT_AT_MARKER IDENTIFIER 
                    | DO DELETE_SMOKE_STUFF IDENTIFIER IDENTIFIER IDENTIFIER
                    | DO CONVERT_AT_MARKER INTEGER
                    | DO BUILD_MAIN_DRUM_TOWER
                    | DO IS_BUILDING_NEAR IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER 
                    | DO BOAT_PATROL IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER
                    | DO TRIGGER_LEVEL_LOST
                    | DO IS_PRISON_ON_LEVEL IDENTIFIER
                    | DO REMOVE_TIMER
                    | DO GUARD_BETWEEN_MARKERS IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER
                    | DO IS_SHAMAN_AVAILABLE_FOR_ATTACK IDENTIFIER
                    | DO HAS_TIMER_REACHED_ZERO
                    | DO CREATE_MSG_NARRATIVE IDENTIFIER
                    | DO SEND_SHAMEN_DEFENDERS_HOME
                    | DO COUNT_ANGELS IDENTIFIER IDENTIFIER
                    | DO NAV_CHECK IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER
                    | DO SPELL_AT_MARKER IDENTIFIER IDENTIFIER IDENTIFIER
                    | DO SET_DRUM_TOWER_POS IDENTIFIER IDENTIFIER
                    | DO PUT_PERSON_IN_DT IDENTIFIER IDENTIFIER IDENTIFIER 
                    | DO SEND_ALL_PEOPLE_TO_MARKER IDENTIFIER
                    | DO BUILD_DRUM_TOWER IDENTIFIER IDENTIFIER
                    | DO PRAY_AT_HEAD IDENTIFIER IDENTIFIER
                    | DO I_HAVE_ONE_SHOT IDENTIFIER IDENTIFIER IDENTIFIER
                    | DO GIVE_ONE_SHOT IDENTIFIER IDENTIFIER
                    | DO SET_NO_BLUE_REINC IDENTIFIER
                    | DO AUTO_MESSAGES OFF
                    | DO MARVELLOUS_HOUSE_DEATH
                    | DO EXTRA_WOOD_COLLECTION ON
                    | DO EXTRA_WOOD_COLLECTION OFF
                    | DO SET_TIMER_GOING IDENTIFIER
                    | DO SET_WOOD_COLLECTION_RADII IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER
                    | DO TARGET_BLUE_DRUM_TOWERS
                    | DO TARGET_S_WARRIORS
                    | DO SET_BASE_MARKER IDENTIFIER
                    | DO SET_BASE_RADIUS IDENTIFIER
                    | DO do_command arg_list
    ''',
    
    'do_command': do_commands_rule,
    
    'arg_list': '''
        arg_list : arg arg_list
                | arg
                | empty
    ''',
    
    'arg': '''
        arg : IDENTIFIER
            | INTEGER
            | STRING
            | ON
            | OFF
    ''',

    'set_statement': '''
        set_statement : SET IDENTIFIER IDENTIFIER
                     | SET IDENTIFIER expression
                     | SET IDENTIFIER
    ''',

    'every_statement': '''
        every_statement : EVERY IDENTIFIER IDENTIFIER BEGIN statement_list END
                       | EVERY IDENTIFIER BEGIN statement_list END
    ''',

    'multiply_statement': '''
        multiply_statement : MULTIPLY IDENTIFIER IDENTIFIER IDENTIFIER
    ''',

    'increment_statement': '''
        increment_statement : INCREMENT IDENTIFIER IDENTIFIER
    ''',

    'decrement_statement': '''
        decrement_statement : DECREMENT IDENTIFIER IDENTIFIER
    ''',

    'divide_statement': '''
        divide_statement : DIVIDE IDENTIFIER IDENTIFIER IDENTIFIER
    ''',
    
    # Use the dynamically built state token rule
    'state_token': state_token_rule,

    'expression': '''
        expression : IDENTIFIER
                  | INTEGER
                  | STRING
                  | LPAREN expression RPAREN
                  | expression EQ expression
                  | expression NEQ expression
                  | expression LT expression
                  | expression GT expression 
                  | expression LTE expression
                  | expression GTE expression
                  | expression AND expression
                  | expression LOGICAL_AND expression
                  | expression PLUS expression
                  | expression MINUS expression
                  | expression TIMES expression
                  | expression DIVIDE expression
    ''',

    'empty': '''
        empty :
    '''
}

# Define operator precedence
precedence = (
    ('left', 'AND'),  # Lowest precedence
    ('left', 'EQ', 'LT', 'GT', 'LTE', 'GTE', 'NEQ'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE')
)
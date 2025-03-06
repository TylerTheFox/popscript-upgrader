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
                    | DO FLYBY_ALLOW_INTERRUPT ON
                    | DO FLYBY_ALLOW_INTERRUPT OFF
                    | DO FLYBY_SET_EVENT_POS IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER
                    | DO FLYBY_SET_EVENT_ANGLE IDENTIFIER IDENTIFIER IDENTIFIER
                    | DO FLYBY_SET_EVENT_ZOOM IDENTIFIER IDENTIFIER IDENTIFIER
                    | DO FLYBY_SET_EVENT_TOOLTIP IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER
                    | DO FLYBY_SET_END_TARGET IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER
                    | DO FLYBY_START
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
                    | DO SET_ATTACK_VARIABLE IDENTIFIER
                    | DO SET_BUCKET_COUNT_FOR_SPELL IDENTIFIER IDENTIFIER
                    | DO SET_SPELL_ENTRY IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER
                    | DO STATE_SPELL_DEFENCE IDENTIFIER IDENTIFIER ON
                    | DO STATE_SPELL_DEFENCE IDENTIFIER IDENTIFIER OFF
                    | DO GET_SPELLS_CAST IDENTIFIER IDENTIFIER IDENTIFIER
                    | DO SET_MARKER_ENTRY IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER
                    | DO MARKER_ENTRIES IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER
                    | DO COUNT_PEOPLE_IN_MARKER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER
                    | DO ATTACK IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER
                    | DO ATTACK IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER IDENTIFIER
                    | DO IDENTIFIER ON
                    | DO IDENTIFIER OFF
                    | DO state_token ON
                    | DO state_token OFF
                    | DO state_token INTEGER INTEGER
                    | DO state_token INTEGER INTEGER INTEGER
                    | DO state_token INTEGER INTEGER ON
                    | DO state_token INTEGER INTEGER OFF
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
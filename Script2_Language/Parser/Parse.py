"""
Script2_Parser - Library for parsing Populous: The Beginning Script files
"""
import ply.yacc as yacc
import sys
import os

# Fix import path - use relative import
# Import grammar rules and lexer from local Parser directory
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from Parser.Grammar import grammar_rules, precedence as grammar_precedence
from Parser.Lexer import lexer, tokens, test_lexer

# Define precedence - use imported precedence
precedence = grammar_precedence

# Create p_script with the right docstring from grammar_rules
def p_script(p):
    exec(f'p_script.__doc__ = """{grammar_rules["script"]}"""')
    if len(p) <= 4:  # Without SCRIPT_END
        p[0] = ('script', p[2], p[3])
    else:  # With SCRIPT_END
        p[0] = ('script', p[2], p[3])
p_script.__doc__ = grammar_rules['script']

# Create p_statements with the right docstring
def p_statements(p):
    p[0] = ('statements', p[2])
p_statements.__doc__ = grammar_rules['statements']

# Create p_statement_list with the right docstring
def p_statement_list(p):
    if len(p) == 3:
        p[0] = [p[1]] + p[2]
    elif len(p) == 2 and p[1] is not None:  # Only add if not empty
        p[0] = [p[1]]
    else:
        p[0] = []
p_statement_list.__doc__ = grammar_rules['statement_list']

# Create p_statement with the right docstring
def p_statement(p):
    p[0] = p[1]
p_statement.__doc__ = grammar_rules['statement']

# Create p_if_statement with the right docstring
def p_if_statement(p):
    if len(p) <= 9:  # Simple IF statement (with or without END before ENDIF)
        p[0] = ('if', p[3], p[6])
    else:  # IF-ELSE statement
        p[0] = ('if-else', p[3], p[6], p[10])
p_if_statement.__doc__ = grammar_rules['if_statement']

# Create p_do_statement with the right docstring
def p_do_statement(p):
    if len(p) == 3 and p[2] == 'do_command':
        # This handles the general case DO command arg_list
        p[0] = tuple(['do', p[2]] + p[3] if p[3] else [])
    else:
        # Original case for specific DO commands
        args = [p[i] for i in range(2, len(p))]
        p[0] = tuple(['do'] + args)
p_do_statement.__doc__ = grammar_rules['do_statement']

# Create p_set_statement with the right docstring
def p_set_statement(p):
    if len(p) == 4:
        p[0] = ('set', p[2], p[3])
    else:
        p[0] = ('set', p[2], 0)  # Default to 0 for missing values
p_set_statement.__doc__ = grammar_rules['set_statement']

# Create p_every_statement with the right docstring
def p_every_statement(p):
    if len(p) == 7:  # With offset: EVERY IDENTIFIER IDENTIFIER BEGIN statement_list END
        p[0] = ('every', p[2], p[3], p[5])
    else:  # Without offset: EVERY IDENTIFIER BEGIN statement_list END
        p[0] = ('every', p[2], None, p[4])  # Use None as placeholder for missing offset
p_every_statement.__doc__ = grammar_rules['every_statement']

# Create p_multiply_statement with the right docstring
def p_multiply_statement(p):
    p[0] = ('multiply', p[2], p[3], p[4])
p_multiply_statement.__doc__ = grammar_rules['multiply_statement']

# Create p_increment_statement with the right docstring
def p_increment_statement(p):
    p[0] = ('increment', p[2], p[3])
p_increment_statement.__doc__ = grammar_rules['increment_statement']

# Create p_decrement_statement with the right docstring
def p_decrement_statement(p):
    p[0] = ('decrement', p[2], p[3])
p_decrement_statement.__doc__ = grammar_rules['decrement_statement']

# Create p_state_token with the right docstring
def p_state_token(p):
    p[0] = p[1]
p_state_token.__doc__ = grammar_rules['state_token']

# Create p_expression with the right docstring
def p_expression(p):
    if len(p) == 2:
        p[0] = p[1] if p[1] is not None else 0  # Default to 0 for empty values
    elif len(p) > 1 and (p[1] == '(' or p[1] == 'LPAREN'):
        p[0] = p[2] if p[2] is not None else 0  # Make sure nested expressions have a value
    else:
        left = p[1] if p[1] is not None else 0
        # Default right operand to 0 if missing
        right = 0
        if len(p) > 3:
            right = p[3] if p[3] is not None else 0
        p[0] = (p[2], left, right)
p_expression.__doc__ = grammar_rules['expression']

# Create p_empty with the right docstring
def p_empty(p):
    pass
p_empty.__doc__ = grammar_rules['empty']

# Replace the existing p_error function with this improved version

def p_error(p):
    if p:
        print(f"Syntax error at line {p.lineno}, token={p.type}, value={p.value}")
        
        # Store additional error context
        parser.error_token = p
        parser.error_line = p.lineno if hasattr(p, 'lineno') else 'unknown'
        
        # Try to recover by skipping the problematic token
        parser.errok()
        
        # Skip to next statement boundary for better recovery
        while True:
            tok = parser.token()
            if not tok or tok.type in ['BEGIN', 'END', 'IF', 'ELSE', 'DO', 'SET', 'EVERY', 'ENDIF', 'SCRIPT_END']:
                break
        
        return tok
    else:
        print("Syntax error at EOF")

def p_do_command(p):
    p[0] = p[1]
p_do_command.__doc__ = grammar_rules['do_command']

def p_arg_list(p):
    if len(p) == 3:
        p[0] = [p[1]] + p[2]  # Multiple arguments
    elif len(p) == 2:
        p[0] = [p[1]]         # Single argument
    else:
        p[0] = []             # No arguments
p_arg_list.__doc__ = grammar_rules['arg_list']

def p_arg(p):
    p[0] = p[1]
p_arg.__doc__ = grammar_rules['arg']

def p_divide_statement(p):
    p[0] = ('divide', p[2], p[3], p[4])
p_divide_statement.__doc__ = grammar_rules['divide_statement']

# Build the parser
parser = yacc.yacc()
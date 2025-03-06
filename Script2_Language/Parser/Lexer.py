"""
Lexer module for Script2 language parser
"""
import ply.lex as lex
import json
import os
import sys

# Load tokens from JSON file
def load_tokens():
    script_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    config_path = os.path.join(script_dir, 'Config', 'tokens.json')
    
    try:
        with open(config_path, 'r') as f:
            token_data = json.load(f)
            return tuple(token_data['tokens'])
    except Exception as e:
        print(f"Error loading tokens from {config_path}: {str(e)}")
        # Return a minimal set of tokens as fallback
        return ('IDENTIFIER', 'INTEGER', 'STRING')

# Define tokens
tokens = load_tokens()

# Define regular expressions for tokens
t_EQ = r'=='
t_LT = r'<'
t_GT = r'>'
t_LTE = r'<='
t_GTE = r'>='
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_PLUS    = r'\+'
t_MINUS   = r'-'
t_TIMES   = r'\*'
t_DIVIDE  = r'/'
t_LOGICAL_AND = r'&&'
t_NEQ = r'!='

def t_COMMENT(t):
    r'//.*'
    pass  # Ignore comments

def t_IDENTIFIER(t):
    r'-?\d+|"[^"]*"|[a-zA-Z_][a-zA-Z0-9_]*'
    # Check if token is a reserved keyword
    if t.value in tokens:
        t.type = t.value
    else:
        t.type = 'IDENTIFIER'
    return t

def t_INTEGER(t):
    r'-?\d+'  # Added minus sign to support negative integers
    t.value = int(t.value)
    return t

def t_STRING(t):
    r'"[^"]*"'
    t.value = t.value[1:-1]  # Remove quotes
    return t

# Define a function to handle tokens
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)  # Count tokens

t_ignore = ' \t'  # Ignore spaces and tabs

def t_error(t):
    print(f"Illegal character '{t.value[0]}' at token {t.lineno}")
    t.lexer.skip(1)

# Build the lexer
lexer = lex.lex()

# Add this function
def test_lexer(data, debug=False):
    """Test the lexer with the given data"""
    lexer.lineno = 1
    lexer.input(data)
    
    if debug:
        print("TOKEN SEQUENCE:")
    
    # Process all tokens
    tokens_found = []
    while True:
        tok = lexer.token()
        if not tok:
            break
        tokens_found.append(tok)
        if debug:
            print(f"{tok.lineno}: {tok.type} '{tok.value}'")
    
    # Store the last token for error reporting
    lexer.last_token = tokens_found[-1] if tokens_found else None
    
    return tokens_found
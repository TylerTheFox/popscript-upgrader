"""
Script2_Service - Functions for parsing and generating Populous: The Beginning Script files
"""
import sys
import os
import traceback

# Fix import path if needed
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from Parser.Lexer import test_lexer, lexer
from Utils.Gen import Int_Generate_Script
from Parser.Parse import parser
from Utils.Constants_Loader import load_constants

# Load and expose constants for external use
constants = load_constants()

def Generate_Script2(script_code):  
    """Parse a script and return its generated output. Raises exceptions on failure."""
    # Test the lexer separately
    test_lexer(script_code)

    try:
        # Parse the script 
        result = parser.parse(script_code)
        if result is None:
            raise Exception("Parsing failed - no AST generated")
        return Int_Generate_Script(result)
    except Exception as e:
        # Include more details in error message
        error_details = f"{str(e)}\nLast token: {getattr(lexer, 'last_token', 'unknown')}"
        raise Exception(f"Parsing failed: {error_details}")

def Parse_Script2(script_code):
    """Parse a script and return its AST. Raises exceptions on failure."""
    # Test the lexer separately
    test_lexer(script_code)

    try:
        # Parse the script 
        result = parser.parse(script_code, debug=2)  # Enable debug mode
        if result is None:
            # Get last token position if available
            last_pos = getattr(parser, 'symstack', ['unknown'])[-1] if hasattr(parser, 'symstack') else 'unknown'
            raise Exception(f"No AST generated. Last position: {last_pos}")
        return result
        
    except Exception as e:
        # Include stack trace for debugging
        error_msg = f"{str(e)}\n"
        if hasattr(parser, 'symstack'):
            error_msg += f"Parser state: {parser.symstack[-5:] if len(parser.symstack) > 5 else parser.symstack}\n"
        
        raise Exception(f"Parsing failed: {error_msg}")
    
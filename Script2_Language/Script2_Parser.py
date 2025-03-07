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
        result = parser.parse(script_code, debug=True)  # Enable debug mode
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

def Debug_Parse_Script2(script_code):
    """Parse a script with detailed debugging information."""
    try:
        # Show tokenization
        print("--- TOKENIZATION ---")
        test_lexer(script_code, debug=True)
        
        # Parse with verbose output
        print("\n--- PARSING ---")
        result = parser.parse(script_code, debug=True)
        
        if result is None:
            print("\n--- ERROR: No AST generated ---")
            return None
            
        print("\n--- PARSE SUCCESSFUL ---")
        return result
    except Exception as e:
        print(f"\n--- PARSE ERROR ---\n{str(e)}")
        traceback.print_exc()
        return None
    
# Add this function to enable more forgiving parsing

def Safe_Parse_Script2(script_code):
    """Parse a script with fallback mechanisms for better error recovery."""
    try:
        return Parse_Script2(script_code)
    except Exception as e:
        print(f"Standard parsing failed: {str(e)}")
        
        # Try line-by-line parsing to extract as much as possible
        lines = script_code.split("\n")
        valid_statements = []
        
        print("Attempting recovery parsing...")
        in_block = False
        current_block = []
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith("//"):
                continue
                
            if line == "BEGIN":
                in_block = True
                current_block = ["BEGIN"]
            elif line == "END":
                in_block = False
                current_block.append("END")
                valid_statements.append(("\n".join(current_block), i - len(current_block), i))
                current_block = []
            elif in_block:
                current_block.append(line)
            elif line and not in_block and not line.startswith("//"):
                valid_statements.append((line, i, i))
        
        print(f"Recovered {len(valid_statements)} statement blocks")
        
        # Return a simplified AST with the valid parts
        return ('script', 'RECOVERED', ('statements', [s for s, _, _ in valid_statements]))
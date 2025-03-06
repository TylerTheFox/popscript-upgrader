"""
Script2 Generation Utilities - Functions for generating Script2 code from AST
"""
import sys
import os

# Fix import path if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from Utils.Constants_Loader import OPERATORS

def generate_script(ast, indent_level=0):
    """Convert the AST back to script format with proper indentation"""
    if not ast:
        return ""
    
    indent = "    " * indent_level  # 4 spaces per indent level
    
    # Handle integer values properly
    if isinstance(ast, int):
        return str(ast)
    
    # Handle string values
    if isinstance(ast, str):
        return ast
    
    node_type = ast[0] if isinstance(ast, tuple) else None
    
    if node_type == 'script':
        # ('script', player_id, statements)
        player_id = ast[1]
        statements = ast[2]
        # The top-level script doesn't get indented
        return f"COMPUTER_PLAYER {player_id}\n\n{generate_script(statements, indent_level)}"
    
    elif node_type == 'statements':
        # ('statements', statement_list)
        statement_list = ast[1]
        statements = "\n".join([generate_script(stmt, indent_level + 1) for stmt in statement_list])
        return f"{indent}BEGIN\n{statements}\n{indent}END"
    
    elif node_type == 'if':
        # ('if', condition, body)
        condition = generate_script(ast[1], 0)  # Don't indent the condition
        # Indent the body statements
        body = "\n".join([generate_script(stmt, indent_level + 1) for stmt in ast[2]])
        return f"{indent}IF ({condition})\n{indent}BEGIN\n{body}\n{indent}ENDIF"
    
    elif node_type == 'if-else':
        # ('if-else', condition, if_body, else_body)
        condition = generate_script(ast[1], 0)  # Don't indent the condition
        # Indent both if and else body statements
        if_body = "\n".join([generate_script(stmt, indent_level + 1) for stmt in ast[2]])
        else_body = "\n".join([generate_script(stmt, indent_level + 1) for stmt in ast[3]])
        return f"{indent}IF ({condition})\n{indent}BEGIN\n{if_body}\n{indent}END\n{indent}ELSE\n{indent}BEGIN\n{else_body}\n{indent}ENDIF"
    
    elif node_type == 'do':
        # ('do', command, [args...])
        command = ast[1]
        args = ast[2:]
        args_str = " ".join([str(generate_script(arg, 0)) for arg in args])  # Don't indent arguments
        cmd_str = f"DO {command} {args_str}"
        return f"{indent}{cmd_str.strip()}"
    
    elif node_type == 'set':
        # ('set', variable, value)
        variable = ast[1]
        value = generate_script(ast[2], 0)  # Don't indent the value
        return f"{indent}SET {variable} {value}"
    
    elif node_type == 'every':
        # ('every', interval, offset, body)
        interval = ast[1]
        offset = ast[2]
        body_list = ast[3]
        # Indent the body statements
        body = "\n".join([generate_script(stmt, indent_level + 1) for stmt in body_list])
        return f"{indent}EVERY {interval} {offset}\n{indent}BEGIN\n{body}\n{indent}END"
    
    elif node_type == 'multiply':
        # ('multiply', target, source, amount)
        target = ast[1]
        source = ast[2]
        amount = ast[3]
        return f"{indent}MULTIPLY {target} {source} {amount}"
    
    elif node_type == 'increment':
        # ('increment', target, amount)
        target = ast[1]
        amount = ast[2]
        return f"{indent}INCREMENT {target} {amount}"
    
    elif node_type == 'decrement':
        # ('decrement', target, amount)
        target = ast[1]
        amount = ast[2]
        return f"{indent}decrement {target} {amount}"

    elif isinstance(ast, tuple) and len(ast) == 3:
        # This could be an expression like (op, left, right)
        op, left, right = ast
        left_str = generate_script(left, 0)  # Don't indent expressions
        right_str = generate_script(right, 0)
        
        # Convert operator tokens to symbols using OPERATORS dictionary
        op_symbol = OPERATORS.get(op, op)  # Use the original op if not in OPERATORS
            
        return f"{left_str} {op_symbol} {right_str}"
    
    # For literals (strings, integers, identifiers)
    return str(ast)

def Int_Generate_Script(ast):
    """Parse a script and return the generated script text. Raises exceptions on failure."""
    try:
        # Then generate script from AST
        output_script = generate_script(ast)
        if not output_script:
            raise Exception("Script generation failed - no output produced")
        
        return output_script
        
    except Exception as e:
        raise Exception(f"Script generation failed: {str(e)}")
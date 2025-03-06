"""
Utility to load constant definitions from JSON configuration files
"""
import json
import os

def load_constants():
    """Load constants from the constants.json file"""
    script_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    config_path = os.path.join(script_dir, 'Config', 'constants.json')
    
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading constants from {config_path}: {str(e)}")
        # Return empty defaults as fallback
        return {
            "state_tokens": [],
            "do_commands": [],
            "operators": {}
        }

# Make constants available as module-level variables
constants = load_constants()
STATE_TOKENS = constants.get('state_tokens', [])
DO_COMMANDS = constants.get('do_commands', [])
OPERATORS = constants.get('operators', {})
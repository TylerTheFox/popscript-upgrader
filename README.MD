# Populous: The Beginning - Script Converter

This tool converts Populous: The Beginning Script2 (.SCR) files to Script4 (Lua) format for use in the remastered version of the game.

## Overview

The script converter takes original Populous: The Beginning AI scripts written in the Script2 format and translates them to the new Script4 Lua-based format. This allows legacy scripts to work with the remastered game engine.

## Features

- Parses original Script2 syntax (.SCR files)
- Translates game state commands to their Script4 equivalents
- Maps legacy variables to new naming conventions
- Generates clean, readable Lua code
- Preserves script functionality and logic flow
- Batch processing support for converting multiple scripts

## Dependencies

The following Python packages are required:

- Python 3.8 or higher
- ply (Python Lex-Yacc)
- argparse (included in Python standard library)

### Installing Dependencies

```bash
# Install required packages
pip install ply
```

## Usage

### Basic Usage

```bash
# Single file conversion
python script2_to_script4.py -f <input_file> <output_file> <system_spec_file> [--tribe TRIBE]

# Batch conversion of all SCR files in a directory
python script2_to_script4.py -b <input_directory> <output_directory> <system_spec_file> [--tribe TRIBE]
```

### Parameters

- `-f, --file`: Single file conversion mode
- `-b, --batch`: Batch conversion mode for all SCR files in a directory
- `input`: Path to the input Script2 file or directory (for batch mode)
- `output`: Path for the output Lua script or directory (for batch mode)
- `system_spec`: Path to the system specification JSON file (defines available modules and functions)
- `--tribe`: Default tribe for commands (default: `TRIBE_BLUE`)
    - Options: `TRIBE_BLUE`, `TRIBE_RED`, `TRIBE_YELLOW`, `TRIBE_GREEN`

### Examples

```bash
# Convert single Blue tribe script
python script2_to_script4.py -f cpscr10.scr Level1_Blue.lua Script4_Language/System/script4_system_spec.json --tribe TRIBE_BLUE

# Convert Red tribe script
python script2_to_script4.py -f cpscr21.scr Level2_Red.lua Script4_Language/System/script4_system_spec.json --tribe TRIBE_RED

# Batch convert all scripts in a directory
python script2_to_script4.py -b original_scripts/ converted_scripts/ Script4_Language/System/script4_system_spec.json --tribe TRIBE_BLUE
```

## Project Structure

- `Script2_Language/`: Contains the parser and utilities for Script2
    - `Parser/`: Contains lexer and parser components
    - `Utils/`: Helper functions for code generation
    - `Config/`: JSON configuration files
- `Script4_Language/`: Contains target language specifications
    - `System/`: System specifications for the Script4 language
    - `Converters/`: Modules for different conversion tasks
      - `Core.py`: Main conversion logic
      - `Expressions.py`: Handles conditions and expressions
      - `Statements.py`: Converts Script2 statements to Script4
      - `Structure.py`: Manages script structure generation

## Configuration Files

- `tokens.json`: Defines tokens used by the Script2 language
- `commands.json`: Maps Script2 commands to their syntax and descriptions
- `constants.json`: Defines constants and operators for Script2
- `script4_system_spec.json`: Defines available modules and functions in Script4

## Conversion Process

1. The input Script2 file is lexed and parsed into an Abstract Syntax Tree (AST)
2. The AST is traversed and converted to equivalent Script4 Lua code
3. Variables and commands are mapped to their Script4 equivalents
4. User-defined variables are identified and properly declared
5. The resulting Lua code is saved to the output file
6. In batch mode, a summary report is generated showing conversion success rates

## Extending the Converter

To add support for new commands or mappings:
1. Update the `constants.json` file with any new tokens or operators
2. Update the command mapping functions in the appropriate modules
3. Add test cases to verify the conversion accuracy

## Troubleshooting

- If you encounter parsing errors, check the syntax of your input file
- For command mapping errors, ensure the command is properly defined in the configuration files
- For module availability errors, check the system specification file contains all required modules
- Check the summary report in batch mode for details on any failed conversions

## License

This project is licensed under the MIT License - see the LICENSE file for details.
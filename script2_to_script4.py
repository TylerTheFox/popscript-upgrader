import argparse
import json
import sys
import os
import logging
from pathlib import Path

from Script4_Language.Mappers.Commands import build_command_map
from Script4_Language.Mappers.Variables import build_variable_map
from Script4_Language.Converters.Core import convert_script_file, load_system_spec, validate_command_map, extract_user_variables
from Script4_Language.Config import *

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def parse_arguments():
    """Parse command line arguments"""
    par = argparse.ArgumentParser(description='Convert Script2 to Script4 (Lua)')
    
    # Add batch processing mode option
    group = par.add_mutually_exclusive_group(required=True)
    group.add_argument('-f', '--file', action='store_true', help='Single file conversion mode')
    group.add_argument('-b', '--batch', action='store_true', help='Batch conversion mode for all SCR files in a directory')
    
    # Common arguments
    par.add_argument('input', help='Input script file or directory (for batch mode)')
    par.add_argument('output', help='Output Lua file or directory (for batch mode)')
    par.add_argument('system_spec', help='System specification JSON file')
    par.add_argument('--tribe', default='TRIBE_BLUE', 
                     choices=['TRIBE_BLUE', 'TRIBE_RED', 'TRIBE_YELLOW', 'TRIBE_GREEN'],
                     help='Default tribe for commands (default: TRIBE_BLUE)')
    return par.parse_args()

def process_directory(input_dir, output_dir, tribe, command_map, variable_map):
    """
    Process all SCR files in a directory
    
    Args:
        input_dir: Path to the input directory containing SCR files
        output_dir: Path to save the output Lua files

        tribe: The target tribe for the script
        command_map: Command mapping dictionary
        variable_map: Variable mapping dictionary
        
    Returns:
        Tuple containing (success_count, failure_count, failed_files)
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    logging.info(f"Output directory: {output_dir}")
    
    # Find all .SCR files (case insensitive)
    scr_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.scr')]
    
    total_files = len(scr_files)
    logging.info(f"Found {total_files} SCR files to process")
    
    # Process each file
    success_count = 0
    failure_count = 0
    failed_files = []
    
    for i, scr_file in enumerate(sorted(scr_files), 1):
        input_path = os.path.join(input_dir, scr_file)
        
        # Generate output filename - replace .SCR with .lua
        output_file = os.path.splitext(scr_file)[0] + '.lua'
        output_path = os.path.join(output_dir, output_file)
        
        # Show progress
        progress = (i / total_files) * 100
        print(f"[{i}/{total_files} - {progress:.1f}%] Processing {scr_file}...", end="", flush=True)
        
        #try:
        result = convert_script_file(input_path, output_path, tribe, command_map, variable_map)
        if result == SUCCESS:
            success_count += 1
            print(" ✓")
        else:
            failure_count += 1
            error_msg = f"Conversion failed with status {result}"
            failed_files.append((scr_file, error_msg))
            print(f" ✗ - Error: {error_msg}")
        #except Exception as e:
        #    failure_count += 1
        #    error_msg = str(e)
        #    failed_files.append((scr_file, error_msg))
        #    print(f" ✗ - Error: {error_msg[:50]}...")
    
    # Print summary report
    _write_summary_report(total_files, success_count, failure_count, failed_files, output_dir)
    
    return success_count, failure_count, failed_files

def _write_summary_report(total_files, success_count, failure_count, failed_files, output_dir):
    """Write a summary report of the conversion process"""
    # Calculate completion percentage
    completion_percentage = (success_count / total_files) * 100 if total_files > 0 else 0
    
    # Display summary report
    print("\n" + "="*50)
    print("CONVERSION SUMMARY:")
    print(f"  Total files: {total_files}")
    print(f"  Successfully converted: {success_count}")
    print(f"  Failed conversions: {failure_count}")
    print(f"  Completion percentage: {completion_percentage:.2f}%")
    
    # Display failed files if any
    if failed_files:
        print("\nFailed files:")
        for file, error in failed_files:
            print(f"  • {file}: {error[:100]}{'...' if len(error) > 100 else ''}")
        
        # Generate a detailed report file
        report_path = os.path.join(output_dir, "conversion_report.txt")
        with open(report_path, 'w') as report_file:
            report_file.write(f"SCRIPT CONVERSION REPORT\n")
            report_file.write(f"=====================\n\n")
            report_file.write(f"Total files: {total_files}\n")
            report_file.write(f"Successfully converted: {success_count}\n")
            report_file.write(f"Failed conversions: {failure_count}\n")
            report_file.write(f"Completion percentage: {completion_percentage:.2f}%\n\n")
            report_file.write("FAILED FILES DETAILS\n")
            report_file.write("===================\n\n")
            
            for file, error in failed_files:
                report_file.write(f"File: {file}\n")
                report_file.write(f"Error: {error}\n")
                report_file.write("-"*50 + "\n")
        
        print(f"\nDetailed conversion report written to: {report_path}")
    else:
        print("\nAll files were successfully converted!")

def print_command_map_info(command_map, variable_map):
    """Print information about available commands in the command map"""
    print("\nCommand Map Function Parameters:")
    print("-" * 50)
    
    # Test each command with dummy parameters to see output format
    test_params = ['DO', 'CMD', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0']

    for cmd_name, cmd_func in sorted(command_map.items()):
        try:
            result = cmd_func(test_params, variable_map)
            if '(' in result:
                func_name = result.split('(')[0]
                params = result.split('(')[1].rstrip(')')
                print(f"{cmd_name}:")
                print(f"  {func_name}({params})")
                print()
            else:
                print(f"{cmd_name}: {result}\n")
        except Exception as e:
            print(f"{cmd_name}: Error analyzing parameters - {str(e)}\n")

def main():
    """Main function with command line argument support"""
    args = parse_arguments()

    # Load system specification
    system_spec = load_system_spec(args.system_spec)
    if not system_spec:
        logging.error("Failed to load system specification")
        return 1

    # Build variable and command maps
    variable_map = build_variable_map()
    command_map = build_command_map(variable_map)
    
    # Print debug information about commands
    print_command_map_info(command_map, variable_map)
    
    # Validate command mappings
    valid_commands, invalid_commands = validate_command_map(command_map, system_spec, variable_map)

    # Report any invalid commands
    if invalid_commands:
        print("WARNING: Some commands are not valid in the system specification:")
        for cmd, reason in invalid_commands.items():
            print(f"  {cmd}: {reason}")

    # Perform conversion based on mode
    if args.file:
        # Single file conversion
        result = convert_script_file(args.input, args.output, args.tribe, valid_commands, variable_map)
        return 0 if result == SUCCESS else 1
    elif args.batch:
        # Batch conversion - process all SCR files in a directory
        success, failures, _ = process_directory(
            args.input, args.output, args.tribe, command_map, variable_map
        )
        return 0 if failures == 0 else 1
    
    return 0

if __name__ == "__main__":
    main()

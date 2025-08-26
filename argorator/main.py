#!/usr/bin/env python3
"""
Argorator main module - A shell script argument parser and modifier

Takes a shell script as input, parses variable usage, creates an argparse parser,
and modifies the script before execution.
"""

import os
import sys
import re
import argparse
import subprocess
import shlex
from typing import Dict, List, Set, Tuple, Any


# Regex patterns for different variable usage types
VAR_PATTERNS = {
    'simple_var': re.compile(r'\$([A-Za-z_][A-Za-z0-9_]*)'),
    'braced_var': re.compile(r'\$\{([A-Za-z_][A-Za-z0-9_]*)\}'),
    'positional': re.compile(r'\$(\d+)'),
    'special_params': re.compile(r'\$[@*#?$!0-]'),
    'assignment': re.compile(r'^([A-Za-z_][A-Za-z0-9_]*)='),
}


def parse_script(script_content: str) -> Dict[str, Any]:
    """Parse script content and extract variable information."""
    lines = script_content.split('\n')
    
    # Track different types of variables
    used_vars = set()
    defined_vars = set()
    positional_args = set()
    has_varargs = False
    
    for line in lines:
        # Skip comments and empty lines
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        # Find variable assignments (definitions)
        assignment_match = VAR_PATTERNS['assignment'].search(line)
        if assignment_match:
            defined_vars.add(assignment_match.group(1))
        
        # Find variable usages
        for match in VAR_PATTERNS['simple_var'].finditer(line):
            used_vars.add(match.group(1))
        
        for match in VAR_PATTERNS['braced_var'].finditer(line):
            used_vars.add(match.group(1))
        
        # Find positional parameters
        for match in VAR_PATTERNS['positional'].finditer(line):
            pos_num = int(match.group(1))
            if pos_num > 0:  # $0 is script name
                positional_args.add(pos_num)
        
        # Check for special parameters
        if '$@' in line or '$*' in line:
            has_varargs = True
    
    return {
        'used_vars': used_vars,
        'defined_vars': defined_vars,
        'positional_args': positional_args,
        'has_varargs': has_varargs,
        'undefined_vars': used_vars - defined_vars
    }


def create_argument_parser(script_analysis: Dict[str, Any], script_name: str) -> argparse.ArgumentParser:
    """Create an argparse parser based on the script analysis."""
    parser = argparse.ArgumentParser(
        description=f"Arguments for shell script: {script_name}",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Add positional arguments first
    max_pos = max(script_analysis['positional_args']) if script_analysis['positional_args'] else 0
    for i in range(1, max_pos + 1):
        if i in script_analysis['positional_args']:
            parser.add_argument(f'arg{i}', help=f'Positional argument ${i}')
        else:
            # Add optional positional for gaps
            parser.add_argument(f'arg{i}', nargs='?', default='', help=f'Positional argument ${i}')
    
    # Add varargs if needed
    if script_analysis['has_varargs']:
        parser.add_argument('remaining_args', nargs='*', help='Additional arguments ($@)')
    
    # Add undefined variables as required options
    for var in sorted(script_analysis['undefined_vars']):
        # Skip if it's a known environment variable
        if var in os.environ:
            continue
        parser.add_argument(f'--{var}', required=True, help=f'Value for undefined variable ${var}')
    
    # Add environment variables as optional arguments with defaults
    for var in sorted(script_analysis['undefined_vars']):
        if var in os.environ:
            parser.add_argument(
                f'--{var}', 
                default=os.environ[var],
                help=f'Value for environment variable ${var} (default: {os.environ[var]})'
            )
    
    return parser


def modify_script(script_content: str, variables: Dict[str, str], positional_args: List[str]) -> str:
    """Modify script by adding variable definitions at the top."""
    lines = script_content.split('\n')
    
    # Find the insertion point (after shebang and initial comments)
    insert_idx = 0
    for i, line in enumerate(lines):
        if line.startswith('#!'):
            insert_idx = i + 1
            continue
        if line.strip().startswith('#') or not line.strip():
            insert_idx = i + 1
            continue
        break
    
    # Prepare variable definitions
    var_definitions = []
    
    # Reset positional parameters and set new ones
    if positional_args:
        var_definitions.append('# Set positional arguments from argorator')
        quoted_args = [shlex.quote(arg) for arg in positional_args]
        var_definitions.append(f'set -- {" ".join(quoted_args)}')
        var_definitions.append('')
    
    # Add variable assignments
    if variables:
        var_definitions.append('# Variable definitions from argorator')
    
    for var_name, var_value in sorted(variables.items()):
        if var_value is None:
            var_definitions.append(f'{var_name}=""')
        else:
            var_definitions.append(f'{var_name}={shlex.quote(str(var_value))}')
    
    if var_definitions:
        var_definitions.append('')  # Add blank line after definitions
    
    # Insert the definitions
    modified_lines = lines[:insert_idx] + var_definitions + lines[insert_idx:]
    
    return '\n'.join(modified_lines)


def extract_args_from_parsed(args, script_analysis: Dict[str, Any]) -> Tuple[Dict[str, str], List[str]]:
    """Extract variables and positional arguments from parsed args."""
    variables = {}
    positional_args = []
    
    # Get positional arguments
    max_pos = max(script_analysis['positional_args']) if script_analysis['positional_args'] else 0
    for i in range(1, max_pos + 1):
        arg_name = f'arg{i}'
        if hasattr(args, arg_name):
            value = getattr(args, arg_name)
            if value:  # Only add non-empty positional args
                positional_args.append(value)
    
    # Add remaining args if present
    if hasattr(args, 'remaining_args'):
        positional_args.extend(args.remaining_args)
    
    # Get variable values
    for var in script_analysis['undefined_vars']:
        if hasattr(args, var):
            variables[var] = getattr(args, var)
        elif var not in os.environ:
            variables[var] = None
    
    return variables, positional_args


def execute_script(modified_script: str) -> int:
    """Execute the modified script and return exit code."""
    try:
        result = subprocess.run(['bash'], input=modified_script, text=True, capture_output=False)
        return result.returncode
    except Exception as e:
        print(f"Error executing script: {e}", file=sys.stderr)
        return 1


def handle_compile_command(script_content: str, variables: Dict[str, str], positional_args: List[str]) -> None:
    """Handle the compile command - print modified script."""
    modified_script = modify_script(script_content, variables, positional_args)
    print(modified_script)


def handle_export_command(variables: Dict[str, str]) -> None:
    """Handle the export command - print export statements."""
    for var_name, var_value in sorted(variables.items()):
        if var_value is not None:
            print(f'export {var_name}={shlex.quote(str(var_value))}')


def handle_execute_command(script_content: str, variables: Dict[str, str], positional_args: List[str]) -> int:
    """Handle the execute command - run the modified script."""
    modified_script = modify_script(script_content, variables, positional_args)
    return execute_script(modified_script)


def parse_command_line() -> Tuple[str, str, List[str]]:
    """Parse command line arguments and return command, script_file, and script_args."""
    # Check if we're being used as a shebang
    if len(sys.argv) >= 2 and not sys.argv[1].startswith('-'):
        # Could be direct script execution or subcommand
        first_arg = sys.argv[1]
        
        if first_arg in ['compile', 'export']:
            # Subcommand mode
            command = first_arg
            if len(sys.argv) < 3:
                print(f"Error: {command} command requires a script file", file=sys.stderr)
                sys.exit(1)
            script_file = sys.argv[2]
            script_args = sys.argv[3:]
        else:
            # Direct execution mode
            command = 'execute'
            script_file = first_arg
            script_args = sys.argv[2:]
    else:
        print("Usage: argorator <script> [args...] | argorator compile <script> [args...] | argorator export <script> [args...]")
        sys.exit(1)
    
    return command, script_file, script_args


def read_script_file(script_file: str) -> str:
    """Read and return script file content."""
    try:
        with open(script_file, 'r') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: Script file '{script_file}' not found", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading script file: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point for argorator."""
    # Parse command line
    command, script_file, script_args = parse_command_line()
    
    # Read the script file
    script_content = read_script_file(script_file)
    
    # Parse the script
    analysis = parse_script(script_content)
    
    # Create argument parser
    arg_parser = create_argument_parser(analysis, script_file)
    
    # Parse the provided arguments
    try:
        args = arg_parser.parse_args(script_args)
    except SystemExit:
        # argparse calls sys.exit on error, we catch it to handle gracefully
        sys.exit(1)
    
    # Extract variables and positional arguments from parsed args
    variables, positional_args = extract_args_from_parsed(args, analysis)
    
    # Execute the appropriate command
    if command == 'compile':
        handle_compile_command(script_content, variables, positional_args)
        return 0
    elif command == 'export':
        handle_export_command(variables)
        return 0
    elif command == 'execute':
        return handle_execute_command(script_content, variables, positional_args)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
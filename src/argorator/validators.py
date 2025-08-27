"""Argument validation and transformation steps.

This module contains validator functions that validate and transform parsed
arguments after argparse processing but before compilation. This allows for:
- Additional validation beyond what argparse provides
- Type transformations (e.g., string paths to pathlib.Path objects)
- Cross-argument validation
- Value normalization
"""
import os
from pathlib import Path
from typing import Any

from .contexts import ValidateContext
from .registry import validator


@validator(order=10)
def validate_file_paths(context: ValidateContext) -> None:
    """Validate and transform file path arguments to pathlib.Path objects."""
    if not context.parsed_args:
        return
    
    # Find arguments that look like file paths based on annotations
    path_vars = []
    for var_name, annotation in context.annotations.items():
        if annotation.help and any(keyword in annotation.help.lower() 
                                 for keyword in ['path', 'file', 'directory', 'dir']):
            path_vars.append(var_name)
    
    # Transform string paths to Path objects and validate existence for files
    for var_name in path_vars:
        if hasattr(context.parsed_args, var_name):
            value = getattr(context.parsed_args, var_name)
            if value and isinstance(value, str):
                path_obj = Path(value).expanduser().resolve()
                
                # Store original string for shell script compatibility
                context.temp_data[f'{var_name}_original'] = value
                
                # For files, validate existence if it's not an output path
                annotation = context.annotations.get(var_name)
                if annotation and annotation.help:
                    help_text = annotation.help.lower()
                    if 'file' in help_text and 'output' not in help_text and 'create' not in help_text:
                        if not path_obj.exists():
                            raise ValueError(f"File not found: {value}")
                        if not path_obj.is_file():
                            raise ValueError(f"Path is not a file: {value}")
                
                print(f"🔍 Validated path: {var_name} = {path_obj}")


@validator(order=20)
def validate_numeric_ranges(context: ValidateContext) -> None:
    """Validate numeric arguments are within reasonable ranges."""
    if not context.parsed_args:
        return
    
    # Check for common numeric arguments that should have sensible ranges
    for var_name, annotation in context.annotations.items():
        if annotation.type in ['int', 'float'] and hasattr(context.parsed_args, var_name):
            value = getattr(context.parsed_args, var_name)
            if value is not None:
                # Apply common sense validations
                if 'port' in var_name.lower():
                    if not (1 <= value <= 65535):
                        raise ValueError(f"Port {var_name} must be between 1-65535, got {value}")
                elif 'timeout' in var_name.lower() or 'delay' in var_name.lower():
                    if value < 0:
                        raise ValueError(f"Timeout/delay {var_name} cannot be negative, got {value}")
                elif 'retry' in var_name.lower() or 'attempt' in var_name.lower():
                    if value < 0:
                        raise ValueError(f"Retry count {var_name} cannot be negative, got {value}")
                    if value > 100:
                        print(f"⚠️  Warning: {var_name}={value} seems unusually high")


@validator(order=30)
def normalize_boolean_strings(context: ValidateContext) -> None:
    """Normalize boolean values to consistent string representation."""
    if not context.parsed_args:
        return
    
    # Find boolean arguments and ensure consistent string representation
    for var_name, annotation in context.annotations.items():
        if annotation.type == 'bool' and hasattr(context.parsed_args, var_name):
            value = getattr(context.parsed_args, var_name)
            if isinstance(value, bool):
                # Store normalized boolean for later use
                context.temp_data[f'{var_name}_normalized'] = "true" if value else "false"


@validator(order=40)
def validate_environment_dependencies(context: ValidateContext) -> None:
    """Validate that required environment variables are available."""
    if not context.parsed_args:
        return
    
    # Check for variables that might depend on environment setup
    env_dependent_vars = []
    for var_name, annotation in context.annotations.items():
        if annotation.help and any(keyword in annotation.help.lower() 
                                 for keyword in ['token', 'key', 'auth', 'credential']):
            env_dependent_vars.append(var_name)
    
    # Warn about potentially sensitive variables
    for var_name in env_dependent_vars:
        if hasattr(context.parsed_args, var_name):
            value = getattr(context.parsed_args, var_name)
            if value:
                print(f"🔐 Security notice: Using credential variable {var_name}")


@validator(order=50)
def cross_argument_validation(context: ValidateContext) -> None:
    """Perform validation that requires multiple arguments."""
    if not context.parsed_args:
        return
    
    # Example: Validate that output path is different from input path
    input_vars = []
    output_vars = []
    
    for var_name, annotation in context.annotations.items():
        if annotation.help:
            help_lower = annotation.help.lower()
            if 'input' in help_lower or ('file' in help_lower and 'output' not in help_lower):
                input_vars.append(var_name)
            elif 'output' in help_lower:
                output_vars.append(var_name)
    
    # Check for input/output conflicts
    for input_var in input_vars:
        for output_var in output_vars:
            if (hasattr(context.parsed_args, input_var) and 
                hasattr(context.parsed_args, output_var)):
                input_val = getattr(context.parsed_args, input_var)
                output_val = getattr(context.parsed_args, output_var)
                if input_val and output_val and input_val == output_val:
                    raise ValueError(f"Input and output paths cannot be the same: {input_val}")


@validator(order=60)
def prepare_shell_compatibility(context: ValidateContext) -> None:
    """Prepare argument values for shell script compatibility."""
    if not context.parsed_args:
        return
    
    # Store shell-compatible representations of complex types
    for var_name in context.undefined_vars.keys():
        if hasattr(context.parsed_args, var_name):
            value = getattr(context.parsed_args, var_name)
            
            # Convert Path objects back to strings for shell compatibility
            if isinstance(value, Path):
                shell_value = str(value)
                setattr(context.parsed_args, var_name, shell_value)
                print(f"🔄 Converted {var_name} to shell-compatible string: {shell_value}")
    
    print("✅ Arguments validated and prepared for compilation")
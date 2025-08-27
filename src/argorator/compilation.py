"""Script compilation steps that transform shell scripts.

This module contains compiler functions that modify shell scripts by injecting
variable assignments, transforming to echo mode, or generating export lines.
All compilers use the decorator pattern and operate on the PipelineContext.
"""
import re
import shlex
from typing import Dict, List

from .contexts import CompileContext
from .registry import compiler
from .macros.processor import macro_processor


@compiler(order=5)
def process_iteration_macros(context: CompileContext) -> None:
    """Process iteration macros and transform them into bash loops."""
    try:
        # Extract variable types from annotations and pass to macro processor
        variable_types = {}
        
        # Get types from argument annotations (if available)
        if context.annotations:
            for var_name, annotation in context.annotations.items():
                variable_types[var_name] = annotation.type
        
        # Set variable types in macro processor
        macro_processor.set_variable_types(variable_types)
        
        # Validate macros first
        errors = macro_processor.validate_macros(context.script_text)
        if errors:
            error_msg = "\n".join(errors)
            raise ValueError(f"Macro validation failed:\n{error_msg}")
        
        # Process macros
        context.script_text = macro_processor.process_macros(context.script_text)
        
    except Exception as e:
        raise ValueError(f"Macro processing failed: {e}")


@compiler(order=10)
def collect_variable_assignments(context: CompileContext) -> None:
    """Collect resolved variable assignments from parsed arguments."""
    if not context.parsed_args:
        return
    
    assignments: Dict[str, str] = {}
    undefined_vars = sorted(context.undefined_vars.keys())
    
    # Process undefined variables (required args)
    for name in undefined_vars:
        value = getattr(context.parsed_args, name, None)
        if value is None:
            raise ValueError(f"Missing required --{name}")
        # Convert boolean values to lowercase string for shell compatibility
        if isinstance(value, bool):
            assignments[name] = "true" if value else "false"
        else:
            assignments[name] = str(value)
    
    # Process environment variables (optional args with defaults)
    for name, env_value in context.env_vars.items():
        value = getattr(context.parsed_args, name, env_value)
        # Convert boolean values to lowercase string for shell compatibility
        if isinstance(value, bool):
            assignments[name] = "true" if value else "false"
        else:
            assignments[name] = str(value)
    
    context.variable_assignments = assignments


@compiler(order=20)
def collect_positional_values(context: CompileContext) -> None:
    """Collect positional argument values from parsed arguments."""
    if not context.parsed_args:
        return
    
    positional_values: List[str] = []
    
    for index in sorted(context.positional_indices):
        attr = f"ARG{index}"
        value = getattr(context.parsed_args, attr, None)
        if value is None:
            raise ValueError(f"Missing positional argument ${index}")
        positional_values.append(str(value))
    
    if context.varargs:
        positional_values.extend([str(v) for v in getattr(context.parsed_args, "ARGS", [])])
    
    context.positional_values = positional_values


@compiler(order=30)
def inject_variable_assignments(context: CompileContext) -> None:
    """Insert shell assignments for provided variables at the top of the script."""
    script_text = context.script_text
    assignments = context.variable_assignments
    
    lines = script_text.splitlines()
    injection_lines = ["# argorator: injected variable definitions"]
    for name in sorted(assignments.keys()):
        value = assignments[name]
        injection_lines.append(f"{name}={shlex.quote(value)}")
    injection_block = "\n".join(injection_lines) + "\n"
    
    if lines and lines[0].startswith("#!"):
        modified_text = (lines[0] + "\n" + injection_block + "\n".join(lines[1:]) + 
               ("\n" if script_text.endswith("\n") else ""))
    else:
        modified_text = injection_block + script_text
    
    context.compiled_script = modified_text


@compiler(order=40)
def transform_script_to_echo_mode(context: CompileContext) -> None:
    """Transform the script for echo mode if requested."""
    if not context.echo_mode:
        return
    
    script_text = context.compiled_script
    lines = script_text.splitlines()
    result_lines: List[str] = []

    idx = 0
    # Preserve shebang line
    if lines and lines[0].startswith("#!"):
        result_lines.append(lines[0])
        idx = 1

    # Preserve argorator injection block if present
    # Look for the marker comment and include following assignment lines (until a blank line break or non-assignment)
    if idx < len(lines) and lines[idx].startswith("# argorator: injected variable definitions"):
        result_lines.append(lines[idx])
        idx += 1
        while idx < len(lines):
            line = lines[idx]
            # Keep variable assignment lines (NAME=...)
            if re.match(r"^\s*[A-Za-z_][A-Za-z0-9_]*=", line):
                result_lines.append(line)
                idx += 1
                continue
            break

    # Process the rest: echo each non-empty, non-comment line
    while idx < len(lines):
        line = lines[idx]
        # Preserve exact blank lines
        if line.strip() == "":
            result_lines.append(line)
            idx += 1
            continue
        # Keep pure comment lines as-is (not echoed)
        if line.lstrip().startswith("#"):
            result_lines.append(line)
            idx += 1
            continue
        # Escape backslashes and double quotes so we can wrap with double quotes.
        escaped = line.replace("\\", "\\\\").replace('"', '\\"')
        result_lines.append(f'echo "{escaped}"')
        idx += 1

    # Ensure trailing newline behavior matches input
    context.compiled_script = "\n".join(result_lines) + ("\n" if script_text.endswith("\n") else "")


def generate_export_lines(assignments: Dict[str, str]) -> str:
    """Return shell lines exporting the provided assignments.

    Format: export VAR='value'
    """
    lines = []
    for name in sorted(assignments.keys()):
        value = assignments[name]
        lines.append(f"export {name}={shlex.quote(value)}")
    return "\n".join(lines)
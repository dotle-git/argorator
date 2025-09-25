"""Transformers for updating argparse parsers based on script analysis.

This module contains transformer functions that take the pipeline context and
build appropriate argparse parsers using the decorator pattern. Each transformer
handles a specific aspect of parser construction.
"""
import argparse
from typing import Dict, List, Optional

from .contexts import TransformContext
from .models import ArgumentAnnotation
from .registry import transformer


@transformer(order=10)
def create_base_parser(context: TransformContext) -> None:
    """Create the base ArgumentParser with conflict detection."""
    # Detect conflicts between environment defaults and annotation defaults
    conflicts = []
    for name in context.env_vars.keys():
        annotation = context.annotations.get(name)
        if annotation and annotation.default is not None:
            env_value = context.env_vars[name]
            annotation_default = annotation.default
            if str(env_value) != str(annotation_default):
                conflicts.append((name, env_value, annotation_default))
    
    # Create custom ArgumentParser to add conflict warnings to help
    class ConflictAwareArgumentParser(argparse.ArgumentParser):
        def format_help(self):
            help_text = super().format_help()
            if conflicts:
                warning_lines = ["\nWARNING: Default value conflicts detected:"]
                for var_name, env_val, ann_val in conflicts:
                    warning_lines.append(f"  {var_name}: environment='{env_val}' vs annotation='{ann_val}' (using environment)")
                warning_lines.append("")
                help_text = help_text + "\n".join(warning_lines)
            return help_text
    
    # Determine description from script metadata
    description = None
    if context.script_metadata and context.script_metadata.description:
        description = context.script_metadata.description
    
    parser = ConflictAwareArgumentParser(
        add_help=True, 
        prog=context.get_script_name(),
        description=description
    )
    context.argument_parser = parser
    
    # Store conflicts for use by other transformers
    context.temp_data['conflicts'] = conflicts


@transformer(order=20)
def add_undefined_variable_arguments(context: TransformContext) -> None:
    """Add required arguments for undefined variables."""
    if not context.argument_parser:
        raise ValueError("Base parser must be created first")
    
    undefined_vars = sorted(context.undefined_vars.keys())
    conflicts = context.temp_data.get('conflicts', [])
    
    for name in undefined_vars:
        add_variable_argument(
            context.argument_parser,
            name,
            context.annotations.get(name, ArgumentAnnotation()),
            required=True,
            env_value=None,
            conflicts=conflicts
        )


@transformer(order=30)
def add_environment_variable_arguments(context: TransformContext) -> None:
    """Add optional arguments for environment variables."""
    if not context.argument_parser:
        raise ValueError("Base parser must be created first")
    
    conflicts = context.temp_data.get('conflicts', [])
    
    for name, value in context.env_vars.items():
        add_variable_argument(
            context.argument_parser,
            name,
            context.annotations.get(name, ArgumentAnnotation()),
            required=False,
            env_value=value,
            conflicts=conflicts
        )


@transformer(order=40)
def add_positional_arguments(context: TransformContext) -> None:
    """Add positional arguments for script parameters."""
    if not context.argument_parser:
        raise ValueError("Base parser must be created first")
    
    # Get function parameter variables that are used with iterator macros
    macro_function_param_vars = context.temp_data.get('macro_function_param_vars', set())
    
    # Add numbered positional arguments, excluding those used with iterator macros
    for index in sorted(context.positional_indices):
        if str(index) not in macro_function_param_vars:
            context.argument_parser.add_argument(f"ARG{index}")
    
    # Add varargs if needed
    if context.varargs:
        context.argument_parser.add_argument("ARGS", nargs="*")


def get_type_converter(type_str: str):
    """Get appropriate type converter function for argument type."""
    if type_str == 'int':
        return int
    elif type_str == 'float':
        return float
    else:  # str, string or choice
        return str


def add_variable_argument(
    parser: argparse.ArgumentParser,
    name: str,
    annotation: ArgumentAnnotation,
    required: bool,
    env_value: str,
    conflicts: List
):
    """Add a variable argument to the parser."""
    # Build argument names
    arg_names = [f"--{name.lower()}"]
    if annotation.alias:
        arg_names.insert(0, annotation.alias)  # Put alias first
    
    kwargs = {
        'dest': name,
    }
    
    # Handle boolean type specially
    if annotation.type == 'bool':
        add_boolean_argument(
            parser, arg_names, kwargs, annotation, required, env_value, name, conflicts
        )
    else:
        add_typed_argument(
            parser, arg_names, kwargs, annotation, required, env_value, name, conflicts
        )


def add_boolean_argument(
    parser: argparse.ArgumentParser,
    arg_names: List[str],
    kwargs: Dict,
    annotation: ArgumentAnnotation,
    required: bool,
    env_value: str,
    name: str,
    conflicts: List
):
    """Add a boolean argument to the parser."""
    if env_value is not None:
        # Environment-backed boolean
        default_bool = env_value.lower() in ('true', '1', 'yes', 'y')
    elif annotation.default is not None:
        # Annotation-backed boolean
        default_bool = annotation.default.lower() in ('true', '1', 'yes', 'y')
    else:
        # Required boolean defaults to False
        default_bool = False
    
    if default_bool:
        # Default is True, so flag should store_false
        kwargs['action'] = 'store_false'
        kwargs['default'] = True
        help_parts = []
        if annotation.help:
            help_parts.append(annotation.help)
        if env_value is not None:
            if name in [c[0] for c in conflicts]:
                help_parts.append("(default from env: true, overriding annotation)")
            else:
                help_parts.append(f"(default from env: {env_value})")
        else:
            help_parts.append("(default: true)")
        kwargs['help'] = ' '.join(help_parts)
    else:
        # Default is False, so flag should store_true
        kwargs['action'] = 'store_true'
        kwargs['default'] = False
        help_parts = []
        if annotation.help:
            help_parts.append(annotation.help)
        if env_value is not None:
            if name in [c[0] for c in conflicts]:
                help_parts.append("(default from env: false, overriding annotation)")
            else:
                help_parts.append(f"(default from env: {env_value})")
        else:
            help_parts.append("(default: false)")
        kwargs['help'] = ' '.join(help_parts)
    
    # Boolean flags are never required (they have implicit defaults)
    kwargs['required'] = False
    parser.add_argument(*arg_names, **kwargs)


def add_typed_argument(
    parser: argparse.ArgumentParser,
    arg_names: List[str],
    kwargs: Dict,
    annotation: ArgumentAnnotation,
    required: bool,
    env_value: str,
    name: str,
    conflicts: List
):
    """Add a typed (non-boolean) argument to the parser."""
    kwargs['type'] = get_type_converter(annotation.type)
    
    if env_value is not None:
        # Environment-backed variable
        kwargs['default'] = get_type_converter(annotation.type)(env_value)
        kwargs['required'] = False
        
        # Build help text with default value info
        help_parts = []
        if annotation.help:
            help_parts.append(annotation.help)
        if name in [c[0] for c in conflicts]:
            help_parts.append(f"(default from env: {env_value}, overriding annotation)")
        else:
            help_parts.append(f"(default from env: {env_value})")
        kwargs['help'] = ' '.join(help_parts)
    elif annotation.default is not None:
        # Annotation provides default
        kwargs['default'] = get_type_converter(annotation.type)(annotation.default)
        kwargs['required'] = False
        if annotation.help:
            kwargs['help'] = f"{annotation.help} (default: {annotation.default})"
        else:
            kwargs['help'] = f"(default: {annotation.default})"
    else:
        # Required variable
        kwargs['required'] = required
        if annotation.help:
            kwargs['help'] = annotation.help
    
    if annotation.choices:
        kwargs['choices'] = annotation.choices
    
    parser.add_argument(*arg_names, **kwargs)


def build_top_level_parser(script_name: str = "argorator", script_description: Optional[str] = None) -> argparse.ArgumentParser:
    """Build the top-level argparse parser with run/compile/export subcommands.
    
    Args:
        script_name: The script name to use for the program name (defaults to "argorator")
        script_description: Optional script description to use instead of default
    """
    description = script_description or "Execute or compile shell scripts with CLI-exposed variables"
    
    parser = argparse.ArgumentParser(
        prog=script_name, 
        description=description
    )
    subparsers = parser.add_subparsers(dest="subcmd")
    
    # run
    run_parser = subparsers.add_parser("run", help="Run script (default)", description=script_description)
    run_parser.add_argument("script", help="Path to the shell script")
    run_parser.add_argument("--echo", action="store_true", help="Print commands that would run (no execution)")
    
    # compile
    compile_parser = subparsers.add_parser("compile", help="Print modified script", description=script_description)
    compile_parser.add_argument("script", help="Path to the shell script")
    compile_parser.add_argument("--echo", action="store_true", help="Print echo-transformed script (dry run view)")
    
    # export
    export_parser = subparsers.add_parser("export", help="Print export lines", description=script_description)
    export_parser.add_argument("script", help="Path to the shell script")
    
    # explain
    explain_parser = subparsers.add_parser("explain", help="Print script interface as JSON", description=script_description)
    explain_parser.add_argument("script", help="Path to the shell script")
    
    return parser
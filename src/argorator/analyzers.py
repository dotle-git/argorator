"""Script analyzers for extracting information from bash scripts.

This module contains analyzer functions that parse shell scripts to extract:
- Variable definitions and usages
- Positional parameter usages
- Shell interpreter requirements
- Annotation metadata

All analyzers are registered using the decorator pattern and operate on the
PipelineContext object.
"""
import os
from typing import Dict, Optional, Set, Tuple

from .annotations import parse_arg_annotations, parse_script_description
from .contexts import AnalysisContext
from .models import ScriptMetadata
from .parsers import script_parser
from .registry import analyzer


SPECIAL_VARS: Set[str] = {"@", "*", "#", "?", "$", "!", "0"}


@analyzer(order=10)
def detect_shell_interpreter(context: AnalysisContext) -> None:
    """Detect the shell interpreter command for the script.

    Honors a shebang if present, normalizing to a common shell path. Defaults to
    bash when a shebang is not detected.
    """
    first_line = context.script_text.splitlines()[0] if context.script_text else ""
    if first_line.startswith("#!"):
        shebang = first_line[2:].strip()
        # Normalize common shells
        if "bash" in shebang:
            context.shell_cmd = ["/bin/bash"]
        elif any(shell in shebang for shell in ["sh", "dash"]):
            context.shell_cmd = ["/bin/sh"]
        elif "zsh" in shebang:
            context.shell_cmd = ["/bin/zsh"]
        elif "ksh" in shebang:
            context.shell_cmd = ["/bin/ksh"]
        else:
            context.shell_cmd = ["/bin/bash"]  # Default for unknown shebangs
    else:
        # Default
        context.shell_cmd = ["/bin/bash"]


def parse_defined_variables(script_text: str) -> Set[str]:
    """Extract variable names that are assigned within the script.

    Matches plain assignments and common declaration forms like export/local/
    declare/readonly at the start of a line.
    """
    return script_parser.parse_defined_variables(script_text)


def parse_variable_usages(script_text: str) -> Set[str]:
    """Find variable names referenced by $VAR or ${VAR...} syntax.

    Special shell parameters (e.g., $@, $1) are excluded; see SPECIAL_VARS.
    """
    return script_parser.parse_variable_usages(script_text)


def parse_positional_usages(script_text: str) -> Tuple[Set[int], bool]:
    """Extract positional parameter indices and varargs usage from script.
    
    Returns:
        Tuple of (positional_indices, varargs_present)
    """
    return script_parser.parse_positional_usages(script_text)


@analyzer(order=20)
def analyze_variable_usages(context: AnalysisContext) -> None:
    """Find all variables referenced in the script."""
    context.all_used_vars = parse_variable_usages(context.script_text)


@analyzer(order=21)
def analyze_defined_variables(context: AnalysisContext) -> None:
    """Extract variables that are defined within the script."""
    context.defined_vars = parse_defined_variables(context.script_text)


@analyzer(order=21.5)
def identify_macro_iterator_variables(context: AnalysisContext) -> None:
    """Identify iterator variables from iteration macros to exclude from undefined variables."""
    try:
        from .macros.parser import macro_parser
        
        # Find all iteration macro comments
        macro_comments = macro_parser.find_macro_comments(context.script_text)
        iterator_vars = set()
        
        for comment in macro_comments:
            if comment.macro_type == 'iteration':
                try:
                    # Parse the iteration macro to extract iterator variable
                    # We need a dummy target to parse the macro
                    target = macro_parser.find_target_for_macro(context.script_text, comment.line_number)
                    if target:
                        iteration_macro = macro_parser.parse_iteration_macro(comment, target)
                        iterator_vars.add(iteration_macro.iterator_var)
                except Exception:
                    # If parsing fails, continue with other macros
                    pass
        
        # Store iterator variables in temp_data for use in next analyzer
        context.temp_data['macro_iterator_vars'] = iterator_vars
        
    except ImportError:
        # If macro modules aren't available, skip this step
        context.temp_data['macro_iterator_vars'] = set()


@analyzer(order=22)
def analyze_undefined_variables(context: AnalysisContext) -> None:
    """Identify variables that are used but not defined in the script."""
    # Get iterator variables identified by macro analysis
    macro_iterator_vars = context.temp_data.get('macro_iterator_vars', set())
    
    # Exclude iterator variables from undefined variables
    undefined_vars = context.all_used_vars - context.defined_vars - macro_iterator_vars
    context.undefined_vars = {name: None for name in sorted(undefined_vars)}


@analyzer(order=23)
def analyze_environment_variables(context: AnalysisContext) -> None:
    """Separate undefined variables into those with environment defaults and truly undefined."""
    env_vars: Dict[str, str] = {}
    remaining_undefined: Dict[str, Optional[str]] = {}
    
    for name in context.undefined_vars.keys():
        if name in os.environ:
            env_vars[name] = os.environ[name]
        else:
            remaining_undefined[name] = None
    
    context.env_vars = env_vars
    context.undefined_vars = remaining_undefined


@analyzer(order=30)
def analyze_positional_parameters(context: AnalysisContext) -> None:
    """Detect positional parameter usage and varargs references in the script."""
    indices, varargs = parse_positional_usages(context.script_text)
    context.positional_indices = indices
    context.varargs = varargs


@analyzer(order=40)
def analyze_annotations(context: AnalysisContext) -> None:
    """Parse comment-based annotations for argument metadata."""
    context.annotations = parse_arg_annotations(context.script_text)


@analyzer(order=50)
def analyze_script_metadata(context: AnalysisContext) -> None:
    """Parse script-level metadata from comments."""
    description = parse_script_description(context.script_text)
    if description:
        context.script_metadata = ScriptMetadata(description=description)
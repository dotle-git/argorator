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
import re
from typing import Dict, Optional, Set

from .annotations import parse_arg_annotations
from .context import PipelineContext
from .registry import analyzer


SPECIAL_VARS: Set[str] = {"@", "*", "#", "?", "$", "!", "0"}


@analyzer(order=10)
def detect_shell_interpreter(context: PipelineContext) -> PipelineContext:
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
        elif re.search(r"\b(sh|dash)\b", shebang):
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
    
    return context


def parse_defined_variables(script_text: str) -> Set[str]:
    """Extract variable names that are assigned within the script.

    Matches plain assignments and common declaration forms like export/local/
    declare/readonly at the start of a line.
    """
    assignment_pattern = re.compile(
        r"^\s*(?:export\s+|local\s+|declare(?:\s+-[a-zA-Z]+)?\s+|readonly\s+)?"
        r"([A-Za-z_][A-Za-z0-9_]*)\s*=", 
        re.MULTILINE
    )
    return set(assignment_pattern.findall(script_text))


def parse_variable_usages(script_text: str) -> Set[str]:
    """Find variable names referenced by $VAR or ${VAR...} syntax.

    Special shell parameters (e.g., $@, $1) are excluded; see SPECIAL_VARS.
    """
    brace_pattern = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)[^}]*\}")
    simple_pattern = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*)")
    candidates: Set[str] = set()
    candidates.update(brace_pattern.findall(script_text))
    candidates.update(simple_pattern.findall(script_text))
    return {name for name in candidates if name and name not in SPECIAL_VARS}


@analyzer(order=20)
def analyze_variables(context: PipelineContext) -> PipelineContext:
    """Classify used variables into defined, undefined, and environment-backed."""
    defined_vars = parse_defined_variables(context.script_text)
    used_vars = parse_variable_usages(context.script_text)
    undefined_or_env = used_vars - defined_vars
    
    context.defined_vars = defined_vars
    env_vars: Dict[str, str] = {}
    undefined_vars: Dict[str, Optional[str]] = {}
    
    for name in sorted(undefined_or_env):
        if name in os.environ:
            env_vars[name] = os.environ[name]
        else:
            undefined_vars[name] = None
    
    context.env_vars = env_vars
    context.undefined_vars = undefined_vars
    
    return context


@analyzer(order=30)
def analyze_positional_parameters(context: PipelineContext) -> PipelineContext:
    """Detect positional parameter usage and varargs references in the script."""
    digit_pattern = re.compile(r"\$([1-9][0-9]*)")
    varargs_pattern = re.compile(r"\$(?:@|\*)")
    
    indices = {int(m) for m in digit_pattern.findall(context.script_text)}
    varargs = bool(varargs_pattern.search(context.script_text))
    
    context.positional_indices = indices
    context.varargs = varargs
    
    return context


@analyzer(order=40)
def analyze_annotations(context: PipelineContext) -> PipelineContext:
    """Parse comment-based annotations for argument metadata."""
    context.annotations = parse_arg_annotations(context.script_text)
    return context
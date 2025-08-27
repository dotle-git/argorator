"""Script analyzers for extracting information from bash scripts.

This module contains analyzers that parse shell scripts to extract:
- Variable definitions and usages
- Positional parameter usages
- Shell interpreter requirements
- Annotation metadata
"""
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from .annotations import parse_arg_annotations
from .models import ArgumentAnnotation


SPECIAL_VARS: Set[str] = {"@", "*", "#", "?", "$", "!", "0"}


class ScriptAnalysisResult:
    """Container for all script analysis results."""
    
    def __init__(self):
        self.defined_vars: Set[str] = set()
        self.undefined_vars: Dict[str, Optional[str]] = {}
        self.env_vars: Dict[str, str] = {}
        self.positional_indices: Set[int] = set()
        self.varargs: bool = False
        self.annotations: Dict[str, ArgumentAnnotation] = {}
        self.shell_cmd: List[str] = []
        self.script_text: str = ""
        self.script_path: Optional[Path] = None


class ShellInterpreterAnalyzer:
    """Analyzes shell interpreter requirements from script content."""
    
    @staticmethod
    def detect_shell_interpreter(script_text: str) -> List[str]:
        """Detect the shell interpreter command for the script.

        Honors a shebang if present, normalizing to a common shell path. Defaults to
        bash when a shebang is not detected.

        Args:
            script_text: The full script content

        Returns:
            A list suitable for subprocess (e.g. ["/bin/bash"])
        """
        first_line = script_text.splitlines()[0] if script_text else ""
        if first_line.startswith("#!"):
            shebang = first_line[2:].strip()
            # Normalize common shells
            if "bash" in shebang:
                return ["/bin/bash"]
            if re.search(r"\b(sh|dash)\b", shebang):
                return ["/bin/sh"]
            if "zsh" in shebang:
                return ["/bin/zsh"]
            if "ksh" in shebang:
                return ["/bin/ksh"]
        # Default
        return ["/bin/bash"]


class VariableAnalyzer:
    """Analyzes variable definitions and usages in shell scripts."""
    
    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def determine_variables(script_text: str) -> Tuple[Set[str], Dict[str, Optional[str]], Dict[str, str]]:
        """Classify used variables into defined, undefined, and environment-backed.

        Args:
            script_text: The script content to analyze

        Returns:
            (defined_vars, undefined_vars, env_vars)
            - defined_vars: variables assigned within the script
            - undefined_vars: mapping of missing variable names -> None
            - env_vars: mapping of variable names -> current environment default
        """
        defined_vars = VariableAnalyzer.parse_defined_variables(script_text)
        used_vars = VariableAnalyzer.parse_variable_usages(script_text)
        undefined_or_env = used_vars - defined_vars
        env_vars: Dict[str, str] = {}
        undefined_vars: Dict[str, Optional[str]] = {}
        for name in sorted(undefined_or_env):
            if name in os.environ:
                env_vars[name] = os.environ[name]
            else:
                undefined_vars[name] = None
        return defined_vars, undefined_vars, env_vars


class PositionalAnalyzer:
    """Analyzes positional parameter usage in shell scripts."""
    
    @staticmethod
    def parse_positional_usages(script_text: str) -> Tuple[Set[int], bool]:
        """Detect positional parameter usage and varargs references in the script.

        Returns a tuple of (set of numeric positions used, varargs_flag) where
        varargs_flag is True if $@ or $* appears in the script.
        """
        digit_pattern = re.compile(r"\$([1-9][0-9]*)")
        varargs_pattern = re.compile(r"\$(?:@|\*)")
        indices = {int(m) for m in digit_pattern.findall(script_text)}
        varargs = bool(varargs_pattern.search(script_text))
        return indices, varargs


class AnnotationAnalyzer:
    """Analyzes comment-based annotations in shell scripts."""
    
    @staticmethod
    def parse_annotations(script_text: str) -> Dict[str, ArgumentAnnotation]:
        """Parse comment-based annotations for argument metadata.
        
        Delegates to the existing parse_arg_annotations function.
        """
        return parse_arg_annotations(script_text)


class ScriptAnalyzer:
    """Main script analyzer that coordinates all analysis stages."""
    
    def __init__(self):
        self.shell_analyzer = ShellInterpreterAnalyzer()
        self.variable_analyzer = VariableAnalyzer()
        self.positional_analyzer = PositionalAnalyzer()
        self.annotation_analyzer = AnnotationAnalyzer()
    
    def analyze_script(self, script_path: Path, script_text: str) -> ScriptAnalysisResult:
        """Perform complete analysis of a shell script.
        
        Args:
            script_path: Path to the script file
            script_text: Content of the script
            
        Returns:
            ScriptAnalysisResult containing all analysis data
        """
        result = ScriptAnalysisResult()
        result.script_path = script_path
        result.script_text = script_text
        
        # Analyze shell interpreter
        result.shell_cmd = self.shell_analyzer.detect_shell_interpreter(script_text)
        
        # Analyze variables
        result.defined_vars, result.undefined_vars, result.env_vars = (
            self.variable_analyzer.determine_variables(script_text)
        )
        
        # Analyze positional parameters
        result.positional_indices, result.varargs = (
            self.positional_analyzer.parse_positional_usages(script_text)
        )
        
        # Analyze annotations
        result.annotations = self.annotation_analyzer.parse_annotations(script_text)
        
        return result
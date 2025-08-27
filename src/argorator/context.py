"""Pipeline context object for passing data through the pipeline stages."""
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Set

from .models import ArgumentAnnotation


class PipelineContext:
    """Context object that flows through all pipeline stages, accumulating data."""
    
    def __init__(self):
        # Command line parsing
        self.command: str = ""
        self.script_path: Optional[Path] = None
        self.echo_mode: bool = False
        self.rest_args: List[str] = []
        
        # Script content
        self.script_text: str = ""
        
        # Analysis results
        self.shell_cmd: List[str] = []
        
        # Variable analysis intermediate results
        self.all_used_vars: Set[str] = set()  # All variables referenced in script
        self.defined_vars: Set[str] = set()   # Variables defined within script
        self.undefined_vars: Dict[str, Optional[str]] = {}  # Variables not defined in script
        self.env_vars: Dict[str, str] = {}    # Variables with environment defaults
        
        # Positional parameter analysis
        self.positional_indices: Set[int] = set()
        self.varargs: bool = False
        
        # Annotation analysis
        self.annotations: Dict[str, ArgumentAnnotation] = {}
        
        # Parser and parsed arguments
        self.argument_parser: Optional[argparse.ArgumentParser] = None
        self.parsed_args: Optional[argparse.Namespace] = None
        
        # Compilation results
        self.variable_assignments: Dict[str, str] = {}
        self.positional_values: List[str] = []
        self.compiled_script: str = ""
        
        # Output
        self.output: str = ""
        self.exit_code: int = 0
    
    def get_script_name(self) -> Optional[str]:
        """Get the script name for display purposes."""
        return self.script_path.name if self.script_path else None
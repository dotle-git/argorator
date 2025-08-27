"""Pipeline context object for passing data through the pipeline stages."""
import argparse
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field, ConfigDict, field_validator

from .models import ArgumentAnnotation


class PipelineContext(BaseModel):
    """Context object that flows through all pipeline stages, accumulating data.
    
    Uses Pydantic for data validation and serialization.
    """
    
    model_config = ConfigDict(
        # Allow arbitrary types like argparse objects
        arbitrary_types_allowed=True,
        # Validate assignment to catch errors early
        validate_assignment=True,
        # Extra fields are forbidden to catch typos
        extra='forbid'
    )
    
    # Command line parsing
    command: str = Field(default="", description="The command to execute (run/compile/export)")
    script_path: Optional[Path] = Field(default=None, description="Path to the script file")
    echo_mode: bool = Field(default=False, description="Whether to run in echo mode")
    rest_args: List[str] = Field(default_factory=list, description="Remaining command line arguments")
    
    # Script content
    script_text: str = Field(default="", description="Content of the script file")
    
    # Analysis results
    shell_cmd: List[str] = Field(default_factory=list, description="Shell command for execution")
    
    # Variable analysis intermediate results
    all_used_vars: Set[str] = Field(default_factory=set, description="All variables referenced in script")
    defined_vars: Set[str] = Field(default_factory=set, description="Variables defined within script")
    undefined_vars: Dict[str, Optional[str]] = Field(default_factory=dict, description="Variables not defined in script")
    env_vars: Dict[str, str] = Field(default_factory=dict, description="Variables with environment defaults")
    
    # Positional parameter analysis
    positional_indices: Set[int] = Field(default_factory=set, description="Positional parameter indices used")
    varargs: bool = Field(default=False, description="Whether script uses varargs ($@ or $*)")
    
    # Annotation analysis
    annotations: Dict[str, ArgumentAnnotation] = Field(default_factory=dict, description="Parsed annotations")
    
    # Parser and parsed arguments
    argument_parser: Optional[argparse.ArgumentParser] = Field(default=None, description="Built argument parser")
    parsed_args: Optional[argparse.Namespace] = Field(default=None, description="Parsed command line arguments")
    
    # Compilation results
    variable_assignments: Dict[str, str] = Field(default_factory=dict, description="Resolved variable assignments")
    positional_values: List[str] = Field(default_factory=list, description="Positional argument values")
    compiled_script: str = Field(default="", description="Compiled script with injected variables")
    
    # Output
    output: str = Field(default="", description="Generated output")
    exit_code: int = Field(default=0, description="Exit code from execution")
    
    # Temporary data for pipeline steps
    temp_data: Dict[str, Any] = Field(default_factory=dict, description="Temporary data for pipeline steps")
    
    @field_validator('positional_indices')
    @classmethod
    def validate_positional_indices(cls, v: Set[int]) -> Set[int]:
        """Validate that positional indices are positive."""
        if any(idx <= 0 for idx in v):
            raise ValueError("Positional indices must be positive")
        return v
    
    @field_validator('exit_code')
    @classmethod
    def validate_exit_code(cls, v: int) -> int:
        """Validate that exit code is within reasonable range."""
        if not (0 <= v <= 255):
            raise ValueError("Exit code must be between 0 and 255")
        return v
    
    def get_script_name(self) -> Optional[str]:
        """Get the script name for display purposes (without extension)."""
        return self.script_path.stem if self.script_path else None
"""Stage-specific context models for the pipeline architecture.

Each context contains only the fields needed for its specific stage,
enforcing separation of concerns and type safety.
"""
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Set, Any

from pydantic import BaseModel, Field, ConfigDict, field_validator

from .models import ArgumentAnnotation, ScriptMetadata


class BaseContext(BaseModel):
    """Base class for all pipeline contexts."""
    pass


class AnalysisContext(BaseContext):
    """Context for the analysis stage - script analysis only."""
    model_config = ConfigDict(arbitrary_types_allowed=True, validate_assignment=True, extra='forbid')

    # INPUTS: What analysis needs
    script_text: str = Field(description="Content of the script file")
    script_path: Optional[Path] = Field(default=None, description="Path to the script file")
    command: str = Field(default="", description="The command to execute (run/compile/export)")

    # OUTPUTS: What analysis produces
    shell_cmd: List[str] = Field(default_factory=list, description="Shell command for execution")
    all_used_vars: Set[str] = Field(default_factory=set, description="All variables referenced in script")
    defined_vars: Set[str] = Field(default_factory=set, description="Variables defined within script")
    loop_vars: Set[str] = Field(default_factory=set, description="Variables defined in loop constructs")
    undefined_vars: Dict[str, Optional[str]] = Field(default_factory=dict, description="Variables not defined in script")
    env_vars: Dict[str, str] = Field(default_factory=dict, description="Variables with environment defaults")
    positional_indices: Set[int] = Field(default_factory=set, description="Positional parameter indices used")
    varargs: bool = Field(default=False, description="Whether script uses varargs ($@ or $*)")
    annotations: Dict[str, ArgumentAnnotation] = Field(default_factory=dict, description="Parsed annotations")
    script_metadata: Optional[ScriptMetadata] = Field(default=None, description="Script-level metadata from comments")

    # Temporary data for pipeline steps
    temp_data: Dict[str, Any] = Field(default_factory=dict, description="Temporary data for pipeline steps")

    def get_script_name(self) -> Optional[str]:
        """Get the script name for display purposes (without extension)."""
        return self.script_path.stem if self.script_path else None

    @field_validator('positional_indices')
    @classmethod
    def validate_positional_indices(cls, v: Set[int]) -> Set[int]:
        """Validate that positional indices are positive."""
        if any(idx <= 0 for idx in v):
            raise ValueError("Positional indices must be positive")
        return v


class TransformContext(BaseContext):
    """Context for the transform stage - parser building only."""
    model_config = ConfigDict(arbitrary_types_allowed=True, validate_assignment=True, extra='forbid')

    # INPUTS: Analysis results needed for parser building
    undefined_vars: Dict[str, Optional[str]] = Field(default_factory=dict, description="Variables not defined in script")
    env_vars: Dict[str, str] = Field(default_factory=dict, description="Variables with environment defaults")
    positional_indices: Set[int] = Field(default_factory=set, description="Positional parameter indices used")
    varargs: bool = Field(default=False, description="Whether script uses varargs ($@ or $*)")
    annotations: Dict[str, ArgumentAnnotation] = Field(default_factory=dict, description="Parsed annotations")
    script_metadata: Optional[ScriptMetadata] = Field(default=None, description="Script-level metadata from comments")
    script_path: Optional[Path] = Field(default=None, description="Path to the script file")  # For parser name

    # OUTPUTS: What transform produces
    argument_parser: Optional[argparse.ArgumentParser] = Field(default=None, description="Built argument parser")

    # Temporary data for pipeline steps
    temp_data: Dict[str, Any] = Field(default_factory=dict, description="Temporary data for pipeline steps")

    def get_script_name(self) -> Optional[str]:
        """Get the script name for display purposes (without extension)."""
        return self.script_path.stem if self.script_path else None


class ValidateContext(BaseContext):
    """Context for the validate stage - argument validation and transformation only."""
    model_config = ConfigDict(arbitrary_types_allowed=True, validate_assignment=True, extra='forbid')

    # INPUTS: Parser and parsed args for validation
    argument_parser: Optional[argparse.ArgumentParser] = Field(default=None, description="Built argument parser")
    parsed_args: Optional[argparse.Namespace] = Field(default=None, description="Parsed command line arguments")

    # OUTPUTS: None (validation modifies parsed_args in place)
    # Temporary data for pipeline steps
    temp_data: Dict[str, Any] = Field(default_factory=dict, description="Temporary data for pipeline steps")


class CompileContext(BaseContext):
    """Context for the compile stage - script compilation only."""
    model_config = ConfigDict(arbitrary_types_allowed=True, validate_assignment=True, extra='forbid')

    # INPUTS: Script and arguments needed for compilation
    script_text: str = Field(description="Content of the script file")
    parsed_args: Optional[argparse.Namespace] = Field(default=None, description="Parsed command line arguments")
    echo_mode: bool = Field(default=False, description="Whether to run in echo mode")
    positional_indices: Set[int] = Field(default_factory=set, description="Positional parameter indices used")
    varargs: bool = Field(default=False, description="Whether script uses varargs ($@ or $*)")
    
    # Variable information needed for compilation
    undefined_vars: Dict[str, Optional[str]] = Field(default_factory=dict, description="Variables not defined in script")
    env_vars: Dict[str, str] = Field(default_factory=dict, description="Variables with environment defaults")
    annotations: Dict[str, ArgumentAnnotation] = Field(default_factory=dict, description="Parsed argument annotations")

    # OUTPUTS: What compile produces
    compiled_script: str = Field(default="", description="Compiled script with injected variables")
    variable_assignments: Dict[str, str] = Field(default_factory=dict, description="Resolved variable assignments")
    positional_values: List[str] = Field(default_factory=list, description="Positional argument values")

    # Temporary data for pipeline steps
    temp_data: Dict[str, Any] = Field(default_factory=dict, description="Temporary data for pipeline steps")


class ExecuteContext(BaseContext):
    """Context for the execute stage - script execution only."""
    model_config = ConfigDict(arbitrary_types_allowed=True, validate_assignment=True, extra='forbid')

    # INPUTS: Everything needed for execution
    compiled_script: str = Field(description="Compiled script with injected variables")
    shell_cmd: List[str] = Field(default_factory=list, description="Shell command for execution")
    positional_values: List[str] = Field(default_factory=list, description="Positional argument values")

    # OUTPUTS: What execute produces
    exit_code: int = Field(default=0, description="Exit code from execution")

    # Temporary data for pipeline steps
    temp_data: Dict[str, Any] = Field(default_factory=dict, description="Temporary data for pipeline steps")

    @field_validator('exit_code')
    @classmethod
    def validate_exit_code(cls, v: int) -> int:
        """Validate that exit code is within reasonable range."""
        if not (0 <= v <= 255):
            raise ValueError("Exit code must be between 0 and 255")
        return v


# Context transition functions
def create_transform_context(analysis: AnalysisContext) -> TransformContext:
    """Create a TransformContext from AnalysisContext results."""
    return TransformContext(
        undefined_vars=analysis.undefined_vars,
        env_vars=analysis.env_vars,
        positional_indices=analysis.positional_indices,
        varargs=analysis.varargs,
        annotations=analysis.annotations,
        script_metadata=analysis.script_metadata,
        script_path=analysis.script_path,
        temp_data=analysis.temp_data.copy()
    )


def create_validate_context(transform: TransformContext, parsed_args: argparse.Namespace) -> ValidateContext:
    """Create a ValidateContext from TransformContext and parsed args."""
    return ValidateContext(
        argument_parser=transform.argument_parser,
        parsed_args=parsed_args
    )


def create_compile_context(
    analysis: AnalysisContext, 
    validate: ValidateContext, 
    echo_mode: bool
) -> CompileContext:
    """Create a CompileContext from analysis and validation results."""
    return CompileContext(
        script_text=analysis.script_text,
        parsed_args=validate.parsed_args,
        echo_mode=echo_mode,
        positional_indices=analysis.positional_indices,
        varargs=analysis.varargs,
        undefined_vars=analysis.undefined_vars,
        env_vars=analysis.env_vars,
        annotations=analysis.annotations
    )


def create_execute_context(analysis: AnalysisContext, compile_ctx: CompileContext) -> ExecuteContext:
    """Create an ExecuteContext from analysis and compilation results."""
    return ExecuteContext(
        compiled_script=compile_ctx.compiled_script,
        shell_cmd=analysis.shell_cmd,
        positional_values=compile_ctx.positional_values
    )
"""Stage-specific context models for the pipeline.

Each stage has its own context model that exposes only the data and operations
appropriate for that stage, ensuring proper encapsulation and preventing
unauthorized access to pipeline data.
"""
import argparse
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field, ConfigDict, field_validator

from .models import ArgumentAnnotation


class BaseContext(BaseModel):
    """Base context with common fields available to all stages."""
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    # Command line parsing (read-only for most stages)
    command: str = Field(default="", description="The command to execute (run/compile/export)")
    script_path: Optional[Path] = Field(default=None, description="Path to the script file")
    echo_mode: bool = Field(default=False, description="Whether to run in echo mode")
    rest_args: List[str] = Field(default_factory=list, description="Remaining command line arguments")
    
    # Script content (read-only after initialization)
    script_text: str = Field(default="", description="Content of the script file")
    
    # Temporary data for pipeline steps
    temp_data: Dict[str, Any] = Field(default_factory=dict, description="Temporary data for pipeline steps")
    
    def get_script_name(self) -> Optional[str]:
        """Get the script name for display purposes."""
        return self.script_path.name if self.script_path else None


class AnalysisContext(BaseContext):
    """Context for the analysis stage - can read script and write analysis results."""
    
    # Analysis results - writable during analysis stage
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
    
    @field_validator('positional_indices')
    @classmethod
    def validate_positional_indices(cls, v: Set[int]) -> Set[int]:
        """Validate that positional indices are positive."""
        if any(idx <= 0 for idx in v):
            raise ValueError("Positional indices must be positive")
        return v


class TransformContext(BaseContext):
    """Context for the transform stage - can read analysis results and create/modify parser."""
    
    # Analysis results - read-only during transform stage
    shell_cmd: List[str] = Field(default_factory=list, description="Shell command for execution")
    all_used_vars: Set[str] = Field(default_factory=set, description="All variables referenced in script")
    defined_vars: Set[str] = Field(default_factory=set, description="Variables defined within script")
    undefined_vars: Dict[str, Optional[str]] = Field(default_factory=dict, description="Variables not defined in script")
    env_vars: Dict[str, str] = Field(default_factory=dict, description="Variables with environment defaults")
    positional_indices: Set[int] = Field(default_factory=set, description="Positional parameter indices used")
    varargs: bool = Field(default=False, description="Whether script uses varargs ($@ or $*)")
    annotations: Dict[str, ArgumentAnnotation] = Field(default_factory=dict, description="Parsed annotations")
    
    # Parser - writable during transform stage
    argument_parser: Optional[argparse.ArgumentParser] = Field(default=None, description="Built argument parser")


class ValidateContext(BaseContext):
    """Context for the validate stage - can read parser/args and write validated/transformed args."""
    
    # Analysis results - read-only during validate stage
    undefined_vars: Dict[str, Optional[str]] = Field(default_factory=dict, description="Variables not defined in script")
    env_vars: Dict[str, str] = Field(default_factory=dict, description="Variables with environment defaults")
    positional_indices: Set[int] = Field(default_factory=set, description="Positional parameter indices used")
    varargs: bool = Field(default=False, description="Whether script uses varargs ($@ or $*)")
    annotations: Dict[str, ArgumentAnnotation] = Field(default_factory=dict, description="Parsed annotations")
    
    # Parser and parsed arguments - readable and writable during validate stage
    argument_parser: Optional[argparse.ArgumentParser] = Field(default=None, description="Built argument parser")
    parsed_args: Optional[argparse.Namespace] = Field(default=None, description="Parsed command line arguments (can be modified)")


class CompileContext(BaseContext):
    """Context for the compile stage - can read validated args and write compilation results."""
    
    # Analysis results - read-only during compile stage
    shell_cmd: List[str] = Field(default_factory=list, description="Shell command for execution")
    undefined_vars: Dict[str, Optional[str]] = Field(default_factory=dict, description="Variables not defined in script")
    env_vars: Dict[str, str] = Field(default_factory=dict, description="Variables with environment defaults")
    positional_indices: Set[int] = Field(default_factory=set, description="Positional parameter indices used")
    varargs: bool = Field(default=False, description="Whether script uses varargs ($@ or $*)")
    
    # Parser and validated arguments - read-only during compile stage
    argument_parser: Optional[argparse.ArgumentParser] = Field(default=None, description="Built argument parser")
    parsed_args: Optional[argparse.Namespace] = Field(default=None, description="Validated and transformed arguments")
    
    # Compilation results - writable during compile stage
    variable_assignments: Dict[str, str] = Field(default_factory=dict, description="Resolved variable assignments")
    positional_values: List[str] = Field(default_factory=list, description="Positional argument values")
    compiled_script: str = Field(default="", description="Compiled script with injected variables")


class ExecuteContext(BaseContext):
    """Context for the execute stage - can read compilation results and write execution results."""
    
    # Shell command - read-only during execute stage
    shell_cmd: List[str] = Field(default_factory=list, description="Shell command for execution")
    
    # Compilation results - read-only during execute stage
    compiled_script: str = Field(default="", description="Compiled script with injected variables")
    positional_values: List[str] = Field(default_factory=list, description="Positional argument values")
    
    # Execution results - writable during execute stage
    output: str = Field(default="", description="Generated output")
    exit_code: int = Field(default=0, description="Exit code from execution")
    
    @field_validator('exit_code')
    @classmethod
    def validate_exit_code(cls, v: int) -> int:
        """Validate that exit code is within reasonable range."""
        if not (0 <= v <= 255):
            raise ValueError("Exit code must be between 0 and 255")
        return v


class FullPipelineContext(BaseContext):
    """Full context for pipeline orchestration - has access to all fields."""
    
    # Analysis results
    shell_cmd: List[str] = Field(default_factory=list, description="Shell command for execution")
    all_used_vars: Set[str] = Field(default_factory=set, description="All variables referenced in script")
    defined_vars: Set[str] = Field(default_factory=set, description="Variables defined within script")
    undefined_vars: Dict[str, Optional[str]] = Field(default_factory=dict, description="Variables not defined in script")
    env_vars: Dict[str, str] = Field(default_factory=dict, description="Variables with environment defaults")
    positional_indices: Set[int] = Field(default_factory=set, description="Positional parameter indices used")
    varargs: bool = Field(default=False, description="Whether script uses varargs ($@ or $*)")
    annotations: Dict[str, ArgumentAnnotation] = Field(default_factory=dict, description="Parsed annotations")
    
    # Parser and parsed arguments
    argument_parser: Optional[argparse.ArgumentParser] = Field(default=None, description="Built argument parser")
    parsed_args: Optional[argparse.Namespace] = Field(default=None, description="Parsed command line arguments")
    
    # Compilation results
    variable_assignments: Dict[str, str] = Field(default_factory=dict, description="Resolved variable assignments")
    positional_values: List[str] = Field(default_factory=list, description="Positional argument values")
    compiled_script: str = Field(default="", description="Compiled script with injected variables")
    
    # Execution results
    output: str = Field(default="", description="Generated output")
    exit_code: int = Field(default=0, description="Exit code from execution")
    
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


def create_stage_context(full_context: FullPipelineContext, stage: str) -> BaseContext:
    """Create a stage-specific context from the full pipeline context."""
    full_data = full_context.model_dump()
    
    if stage == 'analyze':
        # Only pass fields that AnalysisContext expects
        stage_fields = AnalysisContext.model_fields.keys()
        filtered_data = {k: v for k, v in full_data.items() if k in stage_fields}
        return AnalysisContext(**filtered_data)
    elif stage == 'transform':
        # Only pass fields that TransformContext expects
        stage_fields = TransformContext.model_fields.keys()
        filtered_data = {k: v for k, v in full_data.items() if k in stage_fields}
        return TransformContext(**filtered_data)
    elif stage == 'validate':
        # Only pass fields that ValidateContext expects
        stage_fields = ValidateContext.model_fields.keys()
        filtered_data = {k: v for k, v in full_data.items() if k in stage_fields}
        return ValidateContext(**filtered_data)
    elif stage == 'compile':
        # Only pass fields that CompileContext expects
        stage_fields = CompileContext.model_fields.keys()
        filtered_data = {k: v for k, v in full_data.items() if k in stage_fields}
        return CompileContext(**filtered_data)
    elif stage == 'execute':
        # Only pass fields that ExecuteContext expects
        stage_fields = ExecuteContext.model_fields.keys()
        filtered_data = {k: v for k, v in full_data.items() if k in stage_fields}
        return ExecuteContext(**filtered_data)
    else:
        raise ValueError(f"Unknown stage: {stage}")


def update_full_context(full_context: FullPipelineContext, stage_context: BaseContext) -> None:
    """Update the full context with changes from a stage-specific context."""
    # Get the updated data from the stage context
    stage_data = stage_context.model_dump()
    
    # Update only the fields that exist in both contexts
    for field_name, field_value in stage_data.items():
        if hasattr(full_context, field_name):
            setattr(full_context, field_name, field_value)
"""Main pipeline orchestrator for Argorator using decorator pattern.

This module provides the main Pipeline class that coordinates all stages using
the decorator registration system:
1. Command line parsing
2. Script analysis to extract information
3. Parser transformation to build argparse interfaces  
4. Argument parsing to get actual values
5. Script compilation to transform the script
6. Script execution or output generation
"""
import argparse
import sys
from pathlib import Path
from typing import List, Optional, Sequence, Dict, Any

from .compilation import generate_export_lines
from .contexts import (
    AnalysisContext, TransformContext, ValidateContext, 
    CompileContext, ExecuteContext
)
from .execution import validate_script_path
from .registry import pipeline_registry
from .transformers import build_top_level_parser

# Import all modules to register their decorated functions
from . import analyzers, transformers, validators, compilation, execution


class PipelineData:
    """Simple data holder for pipeline state."""
    
    def __init__(self):
        self.data: Dict[str, Any] = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        self.data[key] = value
    
    def update(self, **kwargs) -> None:
        self.data.update(kwargs)


class PipelineCommand:
    """Represents a command to be executed by the pipeline."""
    
    def __init__(self, command: str, script_path: Path, echo_mode: bool = False, rest_args: Optional[List[str]] = None):
        self.command = command
        self.script_path = script_path
        self.echo_mode = echo_mode
        self.rest_args = rest_args or []


class Pipeline:
    """Main pipeline class that orchestrates all processing stages using decorator pattern."""
    
    def __init__(self):
        self.registry = pipeline_registry
    
    def parse_command_line(self, argv: Optional[Sequence[str]] = None) -> PipelineCommand:
        """Parse command line arguments to determine pipeline execution mode.
        
        Args:
            argv: Command line arguments (defaults to sys.argv[1:])
            
        Returns:
            PipelineCommand containing execution parameters
        """
        argv = list(argv) if argv is not None else sys.argv[1:]
        
        # If first token is a known subcommand, parse with subparsers; otherwise treat as implicit run
        subcommands = {"run", "compile", "export"}
        if argv and argv[0] in subcommands:
            return self._parse_explicit_subcommand(argv)
        else:
            return self._parse_implicit_run(argv)
    
    def _parse_explicit_subcommand(self, argv: List[str]) -> PipelineCommand:
        """Parse explicit subcommand invocation."""
        parser = build_top_level_parser()
        ns, unknown = parser.parse_known_args(argv)
        command = ns.subcmd or "run"
        script_arg: Optional[str] = getattr(ns, "script", None)
        rest_args: List[str] = unknown
        echo_mode: bool = bool(getattr(ns, "echo", False))
        
        if script_arg is None:
            print("error: script path is required", file=sys.stderr)
            sys.exit(2)
        
        script_path = validate_script_path(script_arg)
        return PipelineCommand(command, script_path, echo_mode, rest_args)
    
    def _parse_implicit_run(self, argv: List[str]) -> PipelineCommand:
        """Parse implicit run invocation."""
        # Implicit run path: use a minimal parser that captures the remainder so --help
        # is handled by the dynamic parser, not this minimal one. Detect --echo in remainder.
        implicit = argparse.ArgumentParser(
            prog="argorator", 
            add_help=True, 
            description="Execute or compile shell scripts with CLI-exposed variables"
        )
        implicit.add_argument("script", help="Path to the shell script")
        implicit.add_argument("rest", nargs=argparse.REMAINDER, help=argparse.SUPPRESS)
        
        try:
            in_ns = implicit.parse_args(argv)
        except SystemExit as exc:
            sys.exit(int(exc.code))
        
        command = "run"
        script_arg = in_ns.script
        
        # Determine echo mode and strip flag from remainder
        incoming_rest: List[str] = list(in_ns.rest or [])
        echo_mode = False
        filtered_rest: List[str] = []
        for token in incoming_rest:
            if token == "--":
                # Preserve separator; after this, do not interpret flags
                filtered_rest.append(token)
                filtered_rest.extend(incoming_rest[incoming_rest.index(token) + 1:])
                break
            if token == "--echo":
                echo_mode = True
                continue
            filtered_rest.append(token)
        
        script_path = validate_script_path(script_arg)
        return PipelineCommand(command, script_path, echo_mode, filtered_rest)
    
    def initialize_data(self, command: PipelineCommand) -> PipelineData:
        """Initialize the pipeline data from command parameters."""
        data = PipelineData()
        data.update(
            command=command.command,
            script_path=command.script_path,
            echo_mode=command.echo_mode,
            rest_args=command.rest_args,
            script_text=command.script_path.read_text(encoding="utf-8")
        )
        return data
    
    def create_stage_context(self, data: PipelineData, stage: str) -> Any:
        """Create a stage-specific context from pipeline data."""
        pipeline_dict = data.data
        
        if stage == 'analyze':
            # Only pass fields that AnalysisContext expects
            stage_fields = AnalysisContext.model_fields.keys()
            filtered_data = {k: v for k, v in pipeline_dict.items() if k in stage_fields}
            return AnalysisContext(**filtered_data)
        elif stage == 'transform':
            # Only pass fields that TransformContext expects
            stage_fields = TransformContext.model_fields.keys()
            filtered_data = {k: v for k, v in pipeline_dict.items() if k in stage_fields}
            return TransformContext(**filtered_data)
        elif stage == 'validate':
            # Only pass fields that ValidateContext expects
            stage_fields = ValidateContext.model_fields.keys()
            filtered_data = {k: v for k, v in pipeline_dict.items() if k in stage_fields}
            return ValidateContext(**filtered_data)
        elif stage == 'compile':
            # Only pass fields that CompileContext expects
            stage_fields = CompileContext.model_fields.keys()
            filtered_data = {k: v for k, v in pipeline_dict.items() if k in stage_fields}
            return CompileContext(**filtered_data)
        elif stage == 'execute':
            # Only pass fields that ExecuteContext expects
            stage_fields = ExecuteContext.model_fields.keys()
            filtered_data = {k: v for k, v in pipeline_dict.items() if k in stage_fields}
            return ExecuteContext(**filtered_data)
        else:
            raise ValueError(f"Unknown stage: {stage}")
    
    def update_pipeline_data(self, data: PipelineData, stage_context: Any) -> None:
        """Update pipeline data with changes from a stage-specific context."""
        # Get the updated data from the stage context
        stage_data = stage_context.model_dump()
        
        # Update the pipeline data
        data.data.update(stage_data)
    
    def run_analysis_stage(self, data: PipelineData) -> None:
        """Stage 1: Run script analyzers to extract information from the bash script."""
        stage_context = self.create_stage_context(data, 'analyze')
        self.registry.execute_stage('analyze', stage_context)
        self.update_pipeline_data(data, stage_context)
    
    def run_transform_stage(self, data: PipelineData) -> None:
        """Stage 2: Transform analysis results into an argparse parser."""
        stage_context = self.create_stage_context(data, 'transform')
        self.registry.execute_stage('transform', stage_context)
        self.update_pipeline_data(data, stage_context)
    
    def parse_arguments(self, data: PipelineData) -> None:
        """Stage 3: Parse arguments to get actual values."""
        argument_parser = data.get('argument_parser')
        if not argument_parser:
            raise ValueError("No argument parser available")
        
        try:
            parsed_args = argument_parser.parse_args(data.get('rest_args', []))
            data.set('parsed_args', parsed_args)
        except SystemExit as exc:
            sys.exit(int(exc.code))
    
    def run_validation_stage(self, data: PipelineData) -> None:
        """Stage 4: Validate and transform parsed arguments."""
        stage_context = self.create_stage_context(data, 'validate')
        self.registry.execute_stage('validate', stage_context)
        self.update_pipeline_data(data, stage_context)
    
    def run_compilation_stage(self, data: PipelineData) -> None:
        """Stage 5: Compile the script with variable assignments and transformations."""
        stage_context = self.create_stage_context(data, 'compile')
        self.registry.execute_stage('compile', stage_context)
        self.update_pipeline_data(data, stage_context)
    
    def run_execution_stage(self, data: PipelineData) -> None:
        """Stage 6: Execute the compiled script."""
        stage_context = self.create_stage_context(data, 'execute')
        self.registry.execute_stage('execute', stage_context)
        self.update_pipeline_data(data, stage_context)
    
    def generate_output(self, data: PipelineData) -> str:
        """Generate output based on the command type."""
        command = data.get('command')
        if command == "export":
            return generate_export_lines(data.get('variable_assignments', {}))
        elif command == "compile":
            return data.get('compiled_script', '')
        else:
            # For run command, output is handled by execution stage
            return ""
    
    def run(self, command: PipelineCommand) -> int:
        """Run the complete pipeline with the given command.
        
        Args:
            command: PipelineCommand specifying what to execute
            
        Returns:
            Exit code (0 for success)
        """
        try:
            # Initialize pipeline data
            data = self.initialize_data(command)
            
            # Stage 1: Analyze script
            self.run_analysis_stage(data)
            
            # Stage 2: Build argument parser
            self.run_transform_stage(data)
            
            # Stage 3: Parse arguments
            self.parse_arguments(data)
            
            # Stage 4: Validate and transform arguments
            self.run_validation_stage(data)
            
            # Stage 5: Compile script
            self.run_compilation_stage(data)
            
            # Generate output for export/compile commands
            command_type = data.get('command')
            if command_type in ["export", "compile"]:
                output = self.generate_output(data)
                if output:
                    # Handle line ending consistency
                    if command_type == "compile":
                        print(output, end="" if output.endswith("\n") else "\n")
                    else:
                        print(output)
                return 0
            
            # Stage 6: Execute script (run command)
            self.run_execution_stage(data)
            return data.get('exit_code', 0)
            
        except FileNotFoundError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"error: unexpected error: {e}", file=sys.stderr)
            return 1
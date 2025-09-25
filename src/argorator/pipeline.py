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
    CompileContext, ExecuteContext,
    create_transform_context, create_validate_context,
    create_compile_context, create_execute_context
)
from .models import ScriptInterface, ArgumentInfo, PositionalInfo
from .execution import validate_script_path
from .registry import pipeline_registry
from .transformers import build_top_level_parser

# Import all modules to register their decorated functions
from . import analyzers, transformers, validators, compilation, execution





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
        subcommands = {"run", "compile", "export", "explain"}
        if argv and argv[0] in subcommands:
            return self._parse_explicit_subcommand(argv)
        else:
            return self._parse_implicit_run(argv)
    
    def _extract_script_name_from_args(self, argv: List[str]) -> str:
        """Extract script name from command line arguments for program name display.
        
        Args:
            argv: Command line arguments
            
        Returns:
            Script name without extension, or "argorator" if not found
        """
        # Look for script argument after subcommand
        # Expected format: ['compile', 'script.sh', ...]
        if len(argv) >= 2:
            script_arg = argv[1]
            # Skip if this is a flag (starts with -)
            if script_arg.startswith('-'):
                return "argorator"
            
            # Remove extension and get just the basename
            try:
                script_path = Path(script_arg)
                return script_path.stem
            except Exception:
                # If path parsing fails, fall back to default
                pass
        
        return "argorator"
    
    def _extract_script_description_from_args(self, argv: List[str]) -> Optional[str]:
        """Extract script description from the script file for help display.
        
        Args:
            argv: Command line arguments
            
        Returns:
            Script description if found, None otherwise
        """
        # Look for script argument after subcommand
        # Expected format: ['compile', 'script.sh', ...]
        if len(argv) >= 2:
            script_arg = argv[1]
            # Skip if this is a flag (starts with -)
            if script_arg.startswith('-'):
                return None
            
            try:
                script_path = Path(script_arg)
                if script_path.exists() and script_path.is_file():
                    # Read the script and parse description
                    script_text = script_path.read_text(encoding="utf-8")
                    # Import here to avoid circular import
                    from .annotations import parse_script_description
                    return parse_script_description(script_text)
            except Exception:
                # If file reading/parsing fails, return None
                pass
        
        return None
    
    def _parse_explicit_subcommand(self, argv: List[str]) -> PipelineCommand:
        """Parse explicit subcommand invocation."""
        # Extract script name early for proper program name in help
        script_name = self._extract_script_name_from_args(argv)
        
        # Extract script description early for proper help display
        script_description = self._extract_script_description_from_args(argv)
        
        parser = build_top_level_parser(script_name, script_description)
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
    
    def create_analysis_context(self, command: PipelineCommand) -> AnalysisContext:
        """Create initial AnalysisContext from command parameters."""
        return AnalysisContext(
            script_text=command.script_path.read_text(encoding="utf-8"),
            script_path=command.script_path,
            command=command.command
        )
    
    def run_analysis_stage(self, analysis: AnalysisContext) -> AnalysisContext:
        """Stage 1: Run script analyzers to extract information from the bash script."""
        self.registry.execute_stage('analyze', analysis)
        return analysis
    
    def run_transform_stage(self, analysis: AnalysisContext) -> TransformContext:
        """Stage 2: Transform analysis results into an argparse parser."""
        transform = create_transform_context(analysis)
        self.registry.execute_stage('transform', transform)
        return transform
    
    def parse_arguments(self, transform: TransformContext, rest_args: List[str]) -> argparse.Namespace:
        """Stage 3: Parse arguments to get actual values."""
        if not transform.argument_parser:
            raise ValueError("No argument parser available")
        
        return transform.argument_parser.parse_args(rest_args)
    
    def run_validation_stage(self, transform: TransformContext, parsed_args: argparse.Namespace) -> ValidateContext:
        """Stage 4: Validate and transform parsed arguments."""
        validate = create_validate_context(transform, parsed_args)
        self.registry.execute_stage('validate', validate)
        return validate
    
    def run_compilation_stage(self, analysis: AnalysisContext, validate: ValidateContext, echo_mode: bool) -> CompileContext:
        """Stage 5: Compile the script with variable assignments and transformations."""
        compile_ctx = create_compile_context(analysis, validate, echo_mode)
        self.registry.execute_stage('compile', compile_ctx)
        return compile_ctx
    
    def run_execution_stage(self, analysis: AnalysisContext, compile_ctx: CompileContext) -> ExecuteContext:
        """Stage 6: Execute the compiled script."""
        execute = create_execute_context(analysis, compile_ctx)
        self.registry.execute_stage('execute', execute)
        return execute
    
    def generate_output(self, command: str, compile_ctx: CompileContext) -> str:
        """Generate output based on the command type."""
        if command == "export":
            return generate_export_lines(compile_ctx.variable_assignments)
        elif command == "compile":
            return compile_ctx.compiled_script
        else:
            # For run command, output is handled by execution stage
            return ""
    
    def _generate_explain_output(self, context: AnalysisContext) -> str:
        """Generate JSON output for the explain command from analysis context."""
        # Build arguments list
        arguments = []
        
        # Add undefined variables (required arguments)
        for name in sorted(context.undefined_vars.keys()):
            annotation = context.annotations.get(name)
            if annotation:
                arg_info = ArgumentInfo(
                    name=name,
                    type=annotation.type,
                    help=annotation.help,
                    default=annotation.default,
                    required=True,
                    alias=annotation.alias,
                    choices=annotation.choices
                )
            else:
                arg_info = ArgumentInfo(
                    name=name,
                    type='str',
                    help='',
                    default=None,
                    required=True,
                    alias=None,
                    choices=None
                )
            arguments.append(arg_info)
        
        # Add environment variables (optional arguments)
        for name, env_value in context.env_vars.items():
            annotation = context.annotations.get(name)
            if annotation:
                arg_info = ArgumentInfo(
                    name=name,
                    type=annotation.type,
                    help=annotation.help,
                    default=env_value,  # Environment value takes precedence
                    required=False,
                    alias=annotation.alias,
                    choices=annotation.choices
                )
            else:
                arg_info = ArgumentInfo(
                    name=name,
                    type='str',
                    help='',
                    default=env_value,
                    required=False,
                    alias=None,
                    choices=None
                )
            arguments.append(arg_info)
        
        # Build positionals list
        positionals = []
        for index in sorted(context.positional_indices):
            positional_info = PositionalInfo(
                name=f"ARG{index}",
                index=index
            )
            positionals.append(positional_info)
        
        # Create the script interface
        script_interface = ScriptInterface(
            description=context.script_metadata.description if context.script_metadata else None,
            arguments=arguments,
            positionals=positionals,
            varargs=context.varargs
        )
        
        # Return formatted JSON
        return script_interface.model_dump_json(indent=2)
    
    def run(self, command: PipelineCommand) -> int:
        """Run the complete pipeline with the given command.
        
        Args:
            command: PipelineCommand specifying what to execute
            
        Returns:
            Exit code (0 for success)
        """
        try:
            # Stage 1: Analyze script
            analysis = self.create_analysis_context(command)
            analysis = self.run_analysis_stage(analysis)
            
            # Handle explain command - generate JSON output from analysis
            if command.command == "explain":
                output = self._generate_explain_output(analysis)
                print(output)
                return 0
            
            # Stage 2: Build argument parser
            transform = self.run_transform_stage(analysis)
            
            # Stage 3: Parse arguments
            parsed_args = self.parse_arguments(transform, command.rest_args)
            
            # Stage 4: Validate and transform arguments
            validate = self.run_validation_stage(transform, parsed_args)
            
            # Stage 5: Compile script
            compile_ctx = self.run_compilation_stage(analysis, validate, command.echo_mode)
            
            # Generate output for export/compile commands
            if command.command in ["export", "compile"]:
                output = self.generate_output(command.command, compile_ctx)
                if output:
                    # Handle line ending consistency
                    if command.command == "compile":
                        print(output, end="" if output.endswith("\n") else "\n")
                    else:
                        print(output)
                return 0
            
            # Stage 6: Execute script (run command)
            execute = self.run_execution_stage(analysis, compile_ctx)
            return execute.exit_code
            
        except SystemExit as e:
            # Handle argparse help/error exits
            return int(e.code) if e.code is not None else 0
        except FileNotFoundError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"error: unexpected error: {e}", file=sys.stderr)
            return 1
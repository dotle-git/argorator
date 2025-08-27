"""Main pipeline orchestrator for Argorator.

This module provides the main Pipeline class that coordinates all stages:
1. Script analysis to extract information
2. Parser transformation to build argparse interfaces  
3. Argument parsing to get actual values
4. Script compilation to transform the script
5. Script execution or output generation
"""
import argparse
import sys
from pathlib import Path
from typing import List, Optional, Sequence

from .analyzers import ScriptAnalyzer, ScriptAnalysisResult
from .compilation import ArgumentProcessor, ScriptCompiler
from .execution import FileHandler, ScriptExecutor
from .transformers import ArgumentParserTransformer, TopLevelParserTransformer


class PipelineCommand:
    """Represents a command to be executed by the pipeline."""
    
    def __init__(self, command: str, script_path: Path, echo_mode: bool = False, rest_args: Optional[List[str]] = None):
        self.command = command
        self.script_path = script_path
        self.echo_mode = echo_mode
        self.rest_args = rest_args or []


class Pipeline:
    """Main pipeline class that orchestrates all processing stages."""
    
    def __init__(self):
        self.analyzer = ScriptAnalyzer()
        self.parser_transformer = ArgumentParserTransformer()
        self.compiler = ScriptCompiler()
        self.executor = ScriptExecutor()
        self.file_handler = FileHandler()
        self.arg_processor = ArgumentProcessor()
    
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
        parser = TopLevelParserTransformer.build_top_level_parser()
        ns, unknown = parser.parse_known_args(argv)
        command = ns.subcmd or "run"
        script_arg: Optional[str] = getattr(ns, "script", None)
        rest_args: List[str] = unknown
        echo_mode: bool = bool(getattr(ns, "echo", False))
        
        if script_arg is None:
            print("error: script path is required", file=sys.stderr)
            sys.exit(2)
        
        script_path = self.file_handler.validate_script_path(script_arg)
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
        
        script_path = self.file_handler.validate_script_path(script_arg)
        return PipelineCommand(command, script_path, echo_mode, filtered_rest)
    
    def analyze_script(self, script_path: Path) -> ScriptAnalysisResult:
        """Stage 1: Run script analyzers to extract information from the bash script.
        
        Args:
            script_path: Path to the script to analyze
            
        Returns:
            ScriptAnalysisResult containing all extracted information
        """
        script_text = self.file_handler.read_text_file(script_path)
        return self.analyzer.analyze_script(script_path, script_text)
    
    def build_argument_parser(self, analysis_result: ScriptAnalysisResult) -> argparse.ArgumentParser:
        """Stage 2: Transform analysis results into an argparse parser.
        
        Args:
            analysis_result: Results from script analysis
            
        Returns:
            Configured ArgumentParser for the script
        """
        script_name = analysis_result.script_path.name if analysis_result.script_path else None
        return self.parser_transformer.build_dynamic_arg_parser(analysis_result, script_name)
    
    def parse_arguments(self, parser: argparse.ArgumentParser, args: List[str]) -> argparse.Namespace:
        """Stage 3: Parse arguments to get actual values.
        
        Args:
            parser: ArgumentParser configured for the script
            args: Command line arguments to parse
            
        Returns:
            Namespace containing parsed argument values
        """
        try:
            return parser.parse_args(args)
        except SystemExit as exc:
            sys.exit(int(exc.code))
    
    def compile_script(
        self, 
        analysis_result: ScriptAnalysisResult, 
        parsed_args: argparse.Namespace,
        echo_mode: bool = False
    ) -> str:
        """Stage 4: Compile the script with variable assignments and transformations.
        
        Args:
            analysis_result: Results from script analysis
            parsed_args: Parsed command line arguments
            echo_mode: Whether to transform script to echo mode
            
        Returns:
            Compiled script text ready for execution
        """
        # Collect variable assignments
        undefined_vars = sorted(analysis_result.undefined_vars.keys())
        assignments = self.arg_processor.collect_variable_assignments(
            parsed_args, undefined_vars, analysis_result.env_vars
        )
        
        # Inject variable assignments
        modified_text = self.compiler.inject_variable_assignments(
            analysis_result.script_text, assignments
        )
        
        # Apply echo transformation if requested
        if echo_mode:
            modified_text = self.compiler.transform_script_to_echo_mode(modified_text)
        
        return modified_text
    
    def execute_script(
        self, 
        analysis_result: ScriptAnalysisResult,
        parsed_args: argparse.Namespace,
        compiled_script: str
    ) -> int:
        """Stage 5: Execute the compiled script.
        
        Args:
            analysis_result: Results from script analysis
            parsed_args: Parsed command line arguments
            compiled_script: Compiled script text
            
        Returns:
            Exit code from script execution
        """
        # Collect positional arguments
        positional_values = self.arg_processor.collect_positional_values(
            parsed_args, analysis_result.positional_indices, analysis_result.varargs
        )
        
        # Execute the script
        return self.executor.run_script_with_args(
            analysis_result.shell_cmd, compiled_script, positional_values
        )
    
    def generate_export_lines(
        self, 
        analysis_result: ScriptAnalysisResult, 
        parsed_args: argparse.Namespace
    ) -> str:
        """Generate export lines for variable assignments.
        
        Args:
            analysis_result: Results from script analysis
            parsed_args: Parsed command line arguments
            
        Returns:
            Export lines as a string
        """
        undefined_vars = sorted(analysis_result.undefined_vars.keys())
        assignments = self.arg_processor.collect_variable_assignments(
            parsed_args, undefined_vars, analysis_result.env_vars
        )
        return self.compiler.generate_export_lines(assignments)
    
    def run(self, command: PipelineCommand) -> int:
        """Run the complete pipeline with the given command.
        
        Args:
            command: PipelineCommand specifying what to execute
            
        Returns:
            Exit code (0 for success)
        """
        try:
            # Stage 1: Analyze script
            analysis_result = self.analyze_script(command.script_path)
            
            # Stage 2: Build argument parser
            parser = self.build_argument_parser(analysis_result)
            
            # Stage 3: Parse arguments
            parsed_args = self.parse_arguments(parser, command.rest_args)
            
            # Execute based on command type
            if command.command == "export":
                export_lines = self.generate_export_lines(analysis_result, parsed_args)
                print(export_lines)
                return 0
            
            # Stage 4: Compile script
            compiled_script = self.compile_script(analysis_result, parsed_args, command.echo_mode)
            
            if command.command == "compile":
                print(compiled_script, end="" if compiled_script.endswith("\n") else "\n")
                return 0
            
            # Stage 5: Execute script (run command)
            return self.execute_script(analysis_result, parsed_args, compiled_script)
            
        except FileNotFoundError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"error: unexpected error: {e}", file=sys.stderr)
            return 1
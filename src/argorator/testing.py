"""Testing utilities for running pipeline subsets and creating test parsers.

This module provides helper functions for testing individual pipeline stages
and creating argument parsers for testing purposes.
"""
import argparse
from pathlib import Path
from typing import Dict, Set, List, Optional

from .contexts import (
    AnalysisContext, TransformContext, 
    create_transform_context
)
from .models import ArgumentAnnotation
from .registry import pipeline_registry

# Import all modules to register their decorated functions
from . import analyzers, transformers, validators, compilation, execution


def create_test_analysis_context(
    script_text: str = "",
    script_path: Optional[Path] = None,
    command: str = "run"
) -> AnalysisContext:
    """Create AnalysisContext for testing purposes.
    
    Args:
        script_text: The script content
        script_path: Path to the script file
        command: The command to execute
        
    Returns:
        AnalysisContext configured for testing
    """
    return AnalysisContext(
        script_text=script_text,
        script_path=script_path or Path("test.sh"),
        command=command
    )


def run_analysis_stage(script_text: str) -> AnalysisContext:
    """Run only the analysis stage for testing.
    
    Args:
        script_text: Script content to analyze
        
    Returns:
        AnalysisContext with analysis results
    """
    analysis = create_test_analysis_context(script_text)
    
    # Run analysis stage
    pipeline_registry.execute_stage('analyze', analysis)
    
    return analysis


def run_transform_stage(analysis: AnalysisContext) -> TransformContext:
    """Run only the transform stage for testing.
    
    Args:
        analysis: AnalysisContext with analysis results
        
    Returns:
        TransformContext with built ArgumentParser
    """
    # Create transform context and run transformers
    transform = create_transform_context(analysis)
    
    # Run transform stage
    pipeline_registry.execute_stage('transform', transform)
    
    return transform


def build_test_parser(
    undefined_vars: List[str],
    env_vars: Dict[str, str],
    positional_indices: Set[int],
    varargs: bool,
    annotations: Dict[str, ArgumentAnnotation]
) -> argparse.ArgumentParser:
    """Build an argument parser for testing (compatibility function).
    
    This function provides compatibility with the old build_dynamic_arg_parser
    interface for testing purposes.
    
    Args:
        undefined_vars: List of undefined variables
        env_vars: Environment variables with defaults  
        positional_indices: Set of positional parameter indices
        varargs: Whether script uses varargs
        annotations: Variable annotations
        
    Returns:
        Built ArgumentParser
    """
    # Create test analysis context with the required data
    analysis = AnalysisContext(
        script_text="",  # Not needed for parser building
        script_path=Path("test.sh"),
        command="run",
        undefined_vars={var: None for var in undefined_vars},
        env_vars=env_vars,
        positional_indices=positional_indices,
        varargs=varargs,
        annotations=annotations
    )
    
    # Run transform stage to build parser
    transform = run_transform_stage(analysis)
    
    return transform.argument_parser


def run_pipeline_stages(script_text: str, rest_args: List[str]) -> tuple[AnalysisContext, TransformContext]:
    """Run analysis and transform stages for testing.
    
    Args:
        script_text: Script content to analyze
        rest_args: Command line arguments to parse (not used in this function)
        
    Returns:
        Tuple of (AnalysisContext, TransformContext) with results
    """
    # Run analysis
    analysis = run_analysis_stage(script_text)
    
    # Run transform
    transform = run_transform_stage(analysis)
    
    return analysis, transform
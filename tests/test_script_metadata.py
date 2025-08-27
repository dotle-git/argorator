import pytest
from pathlib import Path
from argorator.annotations import parse_script_description
from argorator.models import ScriptMetadata
from argorator.analyzers import analyze_script_metadata
from argorator.contexts import AnalysisContext
from argorator.transformers import create_base_parser
from argorator.pipeline import Pipeline


def test_parse_script_description_basic():
    """Test parsing basic script description."""
    script = """#!/bin/bash
# Description: This script does something useful
echo "Hello World"
"""
    description = parse_script_description(script)
    assert description == "This script does something useful"


def test_parse_script_description_case_insensitive():
    """Test that description parsing is case insensitive."""
    script = """#!/bin/bash
# description: This script does something useful
echo "Hello World"
"""
    description = parse_script_description(script)
    assert description == "This script does something useful"


def test_parse_script_description_no_space_after_hash():
    """Test parsing when there's no space after the hash."""
    script = """#!/bin/bash
#Description: This script does something useful
echo "Hello World"
"""
    description = parse_script_description(script)
    assert description == "This script does something useful"


def test_parse_script_description_extra_spaces():
    """Test parsing with extra spaces around colon."""
    script = """#!/bin/bash
# Description   :   This script does something useful
echo "Hello World"
"""
    description = parse_script_description(script)
    assert description == "This script does something useful"


def test_parse_script_description_not_found():
    """Test when no description is found."""
    script = """#!/bin/bash
# Some other comment
echo "Hello World"
"""
    description = parse_script_description(script)
    assert description is None


def test_parse_script_description_multiple_lines():
    """Test that only the first description is returned."""
    script = """#!/bin/bash
# Description: First description
# Description: Second description
echo "Hello World"
"""
    description = parse_script_description(script)
    assert description == "First description"


def test_script_metadata_model():
    """Test ScriptMetadata model creation and validation."""
    metadata = ScriptMetadata(description="Test description")
    assert metadata.description == "Test description"
    
    # Test with None description
    metadata_none = ScriptMetadata()
    assert metadata_none.description is None


def test_analyze_script_metadata_with_description():
    """Test the analyze_script_metadata function with a description."""
    script_text = """#!/bin/bash
# Description: My awesome script
echo "Hello World"
"""
    context = AnalysisContext(script_text=script_text)
    
    analyze_script_metadata(context)
    
    assert context.script_metadata is not None
    assert context.script_metadata.description == "My awesome script"


def test_analyze_script_metadata_no_description():
    """Test the analyze_script_metadata function without a description."""
    script_text = """#!/bin/bash
# Some comment
echo "Hello World"
"""
    context = AnalysisContext(script_text=script_text)
    
    analyze_script_metadata(context)
    
    assert context.script_metadata is None


def test_get_script_name_strips_extension():
    """Test that get_script_name strips file extensions."""
    script_path = Path("/path/to/my_script.sh")
    context = AnalysisContext(script_text="", script_path=script_path)
    
    assert context.get_script_name() == "my_script"


def test_get_script_name_no_extension():
    """Test get_script_name with files that have no extension."""
    script_path = Path("/path/to/my_script")
    context = AnalysisContext(script_text="", script_path=script_path)
    
    assert context.get_script_name() == "my_script"


def test_get_script_name_multiple_extensions():
    """Test get_script_name with multiple extensions."""
    script_path = Path("/path/to/my_script.test.sh")
    context = AnalysisContext(script_text="", script_path=script_path)
    
    # .stem removes only the last extension
    assert context.get_script_name() == "my_script.test"


def test_get_script_name_none_path():
    """Test get_script_name when script_path is None."""
    context = AnalysisContext(script_text="")
    
    assert context.get_script_name() is None


def test_parser_creation_with_description(tmp_path):
    """Test that ArgumentParser is created with script description."""
    script_content = """#!/bin/bash
# Description: This is my test script for validation
# NAME: User name
echo "Hello $NAME"
"""
    
    script_path = tmp_path / "test_script.sh"
    script_path.write_text(script_content)
    
    # Create a pipeline and run the analysis and transform stages
    pipeline = Pipeline()
    command = pipeline.parse_command_line(["run", str(script_path)])
    
    # Run analysis stage
    analysis = pipeline.create_analysis_context(command)
    analysis = pipeline.run_analysis_stage(analysis)
    
    # Run transform stage  
    transform = pipeline.run_transform_stage(analysis)
    
    # Check that the parser has the correct program name and description
    assert transform.argument_parser is not None
    assert transform.argument_parser.prog == "test_script"
    assert transform.argument_parser.description == "This is my test script for validation"


def test_parser_creation_without_description(tmp_path):
    """Test that ArgumentParser is created without description when none provided."""
    script_content = """#!/bin/bash
# NAME: User name
echo "Hello $NAME"
"""
    
    script_path = tmp_path / "test_script.sh"
    script_path.write_text(script_content)
    
    # Create a pipeline and run the analysis and transform stages
    pipeline = Pipeline()
    command = pipeline.parse_command_line(["run", str(script_path)])
    
    # Run analysis stage
    analysis = pipeline.create_analysis_context(command)
    analysis = pipeline.run_analysis_stage(analysis)
    
    # Run transform stage  
    transform = pipeline.run_transform_stage(analysis)
    
    # Check that the parser has the correct program name but no description
    assert transform.argument_parser is not None
    assert transform.argument_parser.prog == "test_script"
    assert transform.argument_parser.description is None


def test_help_output_includes_description(tmp_path):
    """Test that --help output includes the script description."""
    script_content = """#!/bin/bash
# Description: A helpful script that greets users
# NAME: The user's name
echo "Hello $NAME"
"""
    
    script_path = tmp_path / "greet.sh"
    script_path.write_text(script_content)
    
    # Create a pipeline and try to parse --help
    pipeline = Pipeline()
    command = pipeline.parse_command_line(["run", str(script_path)])
    
    # Run analysis and transform stages
    analysis = pipeline.create_analysis_context(command)
    analysis = pipeline.run_analysis_stage(analysis)
    transform = pipeline.run_transform_stage(analysis)
    
    # Get help text
    help_text = transform.argument_parser.format_help()
    
    # Check that description and program name are in help text
    assert "greet" in help_text  # program name without extension
    assert "A helpful script that greets users" in help_text  # description


def test_help_output_without_description(tmp_path):
    """Test that --help output works correctly without a description."""
    script_content = """#!/bin/bash
# NAME: The user's name
echo "Hello $NAME"
"""
    
    script_path = tmp_path / "greet.sh"
    script_path.write_text(script_content)
    
    # Create a pipeline and try to parse --help
    pipeline = Pipeline()
    command = pipeline.parse_command_line(["run", str(script_path)])
    
    # Run analysis and transform stages
    analysis = pipeline.create_analysis_context(command)
    analysis = pipeline.run_analysis_stage(analysis)
    transform = pipeline.run_transform_stage(analysis)
    
    # Get help text
    help_text = transform.argument_parser.format_help()
    
    # Check that program name is in help text but no description
    assert "greet" in help_text  # program name without extension
    # Should not contain any mention of description
    assert "description" not in help_text.lower()
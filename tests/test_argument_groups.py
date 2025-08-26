"""Tests for argument groups and mutually exclusive groups functionality."""

import pytest
from pathlib import Path
from argorator import cli
from argorator.annotations import parse_arg_annotations
from argorator.models import ArgumentAnnotation


def test_parse_group_annotations():
    """Test parsing group annotations from comments."""
    script = """
    # SERVER_HOST (str) [group: Server Configuration]: Host for the server
    # SERVER_PORT (int) [group: Server Configuration]: Port for the server
    # LOG_LEVEL (choice[debug, info, warn, error]) [group: Logging]: Log level
    # LOG_FORMAT (str) [group: Logging]: Log format string
    """
    annotations = parse_arg_annotations(script)
    
    assert "SERVER_HOST" in annotations
    assert annotations["SERVER_HOST"].group == "Server Configuration"
    assert annotations["SERVER_HOST"].exclusive_group is None
    
    assert "SERVER_PORT" in annotations
    assert annotations["SERVER_PORT"].group == "Server Configuration"
    assert annotations["SERVER_PORT"].type == "int"
    
    assert "LOG_LEVEL" in annotations
    assert annotations["LOG_LEVEL"].group == "Logging"
    assert annotations["LOG_LEVEL"].type == "choice"
    
    assert "LOG_FORMAT" in annotations
    assert annotations["LOG_FORMAT"].group == "Logging"


def test_parse_exclusive_group_annotations():
    """Test parsing mutually exclusive group annotations."""
    script = """
    # VERBOSE (bool) [exclusive_group: Output Mode]: Enable verbose output
    # QUIET (bool) [exclusive_group: Output Mode]: Enable quiet mode
    # JSON_OUTPUT (bool) [exclusive_group: Output Format]: Output in JSON format
    # XML_OUTPUT (bool) [exclusive_group: Output Format]: Output in XML format
    """
    annotations = parse_arg_annotations(script)
    
    assert "VERBOSE" in annotations
    assert annotations["VERBOSE"].exclusive_group == "Output Mode"
    assert annotations["VERBOSE"].group is None
    assert annotations["VERBOSE"].type == "bool"
    
    assert "QUIET" in annotations
    assert annotations["QUIET"].exclusive_group == "Output Mode"
    assert annotations["QUIET"].type == "bool"
    
    assert "JSON_OUTPUT" in annotations
    assert annotations["JSON_OUTPUT"].exclusive_group == "Output Format"
    
    assert "XML_OUTPUT" in annotations
    assert annotations["XML_OUTPUT"].exclusive_group == "Output Format"


def test_parse_exclusive_group_shorthand():
    """Test parsing xgroup shorthand for exclusive groups."""
    script = """
    # VERBOSE (bool) [xgroup: Output Mode]: Enable verbose output
    # QUIET (bool) [xgroup: Output Mode]: Enable quiet mode  
    # DEBUG (bool) [exclusive_group: Debug Mode]: Enable debug mode
    # TRACE (bool) [xgroup: Debug Mode]: Enable trace mode
    """
    annotations = parse_arg_annotations(script)
    
    # Test xgroup shorthand
    assert "VERBOSE" in annotations
    assert annotations["VERBOSE"].exclusive_group == "Output Mode"
    assert annotations["VERBOSE"].group is None
    assert annotations["VERBOSE"].type == "bool"
    
    assert "QUIET" in annotations
    assert annotations["QUIET"].exclusive_group == "Output Mode"
    
    # Test mixing full name and shorthand in same group
    assert "DEBUG" in annotations
    assert annotations["DEBUG"].exclusive_group == "Debug Mode"
    
    assert "TRACE" in annotations
    assert annotations["TRACE"].exclusive_group == "Debug Mode"


def test_parse_mixed_group_annotations():
    """Test parsing mixed annotations with groups, exclusive groups, and ungrouped."""
    script = """
    # CONFIG_FILE (str): Configuration file path
    # LOG_LEVEL (choice[debug, info, warn]) [group: Logging]: Log level
    # LOG_FILE (str) [group: Logging]: Log file path
    # VERBOSE (bool) [exclusive_group: Verbosity]: Enable verbose output
    # QUIET (bool) [exclusive_group: Verbosity]: Enable quiet mode
    # OUTPUT_DIR (str): Output directory
    """
    annotations = parse_arg_annotations(script)
    
    # Ungrouped
    assert annotations["CONFIG_FILE"].group is None
    assert annotations["CONFIG_FILE"].exclusive_group is None
    assert annotations["OUTPUT_DIR"].group is None
    assert annotations["OUTPUT_DIR"].exclusive_group is None
    
    # Regular group
    assert annotations["LOG_LEVEL"].group == "Logging"
    assert annotations["LOG_FILE"].group == "Logging"
    
    # Exclusive group
    assert annotations["VERBOSE"].exclusive_group == "Verbosity"
    assert annotations["QUIET"].exclusive_group == "Verbosity"


def test_argument_annotation_model_validation():
    """Test that ArgumentAnnotation model validates group constraints."""
    # Valid: group only
    annotation = ArgumentAnnotation(group="Test Group", type="str")
    assert annotation.group == "Test Group"
    assert annotation.exclusive_group is None
    
    # Valid: exclusive_group only
    annotation = ArgumentAnnotation(exclusive_group="Test Exclusive", type="bool")
    assert annotation.exclusive_group == "Test Exclusive"
    assert annotation.group is None
    
    # Invalid: both group and exclusive_group
    with pytest.raises(ValueError, match="argument cannot be in both a regular group and an exclusive group"):
        ArgumentAnnotation(group="Regular", exclusive_group="Exclusive", type="str")


def test_build_parser_with_argument_groups():
    """Test that argument groups are created correctly in the parser."""
    # Mock annotations with groups
    annotations = {
        "SERVER_HOST": ArgumentAnnotation(type="str", group="Server Configuration", help="Server host"),
        "SERVER_PORT": ArgumentAnnotation(type="int", group="Server Configuration", help="Server port"),
        "LOG_LEVEL": ArgumentAnnotation(type="str", group="Logging", help="Log level"),
        "CONFIG_FILE": ArgumentAnnotation(type="str", help="Config file path"),  # No group
    }
    
    undefined_vars = ["SERVER_HOST", "SERVER_PORT", "LOG_LEVEL", "CONFIG_FILE"]
    env_vars = {}
    positional_indices = set()
    varargs = False
    
    parser = cli.build_dynamic_arg_parser(
        undefined_vars, env_vars, positional_indices, varargs, annotations
    )
    
    # Check that the parser was created successfully
    assert parser is not None
    
    # Parse help to see if groups are present (this is a basic integration test)
    help_text = parser.format_help()
    assert "Server Configuration" in help_text
    assert "Logging" in help_text
    assert "--server_host" in help_text
    assert "--server_port" in help_text
    assert "--log_level" in help_text
    assert "--config_file" in help_text


def test_build_parser_with_exclusive_groups():
    """Test that mutually exclusive groups are created correctly."""
    annotations = {
        "VERBOSE": ArgumentAnnotation(type="bool", exclusive_group="Verbosity", help="Verbose mode"),
        "QUIET": ArgumentAnnotation(type="bool", exclusive_group="Verbosity", help="Quiet mode"),
        "JSON_OUTPUT": ArgumentAnnotation(type="bool", exclusive_group="Output Format", help="JSON output"),
        "XML_OUTPUT": ArgumentAnnotation(type="bool", exclusive_group="Output Format", help="XML output"),
        "CONFIG": ArgumentAnnotation(type="str", help="Config file"),  # No group
    }
    
    undefined_vars = ["VERBOSE", "QUIET", "JSON_OUTPUT", "XML_OUTPUT", "CONFIG"]
    env_vars = {}
    positional_indices = set()
    varargs = False
    
    parser = cli.build_dynamic_arg_parser(
        undefined_vars, env_vars, positional_indices, varargs, annotations
    )
    
    # Test that mutually exclusive arguments cannot be used together
    with pytest.raises(SystemExit):
        parser.parse_args(["--verbose", "--quiet", "--config", "test.conf"])
    
    with pytest.raises(SystemExit):
        parser.parse_args(["--json_output", "--xml_output", "--config", "test.conf"])
    
    # Test that single arguments from exclusive groups work
    args = parser.parse_args(["--verbose", "--json_output", "--config", "test.conf"])
    assert args.VERBOSE is True
    assert args.QUIET is False
    assert args.JSON_OUTPUT is True
    assert args.XML_OUTPUT is False
    assert args.CONFIG == "test.conf"


def test_build_parser_with_mixed_groups():
    """Test parser with both regular groups and exclusive groups."""
    annotations = {
        # Regular group
        "DB_HOST": ArgumentAnnotation(type="str", group="Database", help="Database host"),
        "DB_PORT": ArgumentAnnotation(type="int", group="Database", help="Database port", default="5432"),
        
        # Exclusive group
        "VERBOSE": ArgumentAnnotation(type="bool", exclusive_group="Verbosity", help="Verbose mode"),
        "QUIET": ArgumentAnnotation(type="bool", exclusive_group="Verbosity", help="Quiet mode"),
        
        # No group
        "OUTPUT_FILE": ArgumentAnnotation(type="str", help="Output file path"),
    }
    
    undefined_vars = ["DB_HOST", "OUTPUT_FILE", "VERBOSE", "QUIET"]  # Added missing boolean vars
    env_vars = {"DB_PORT": "3306"}  # Environment variable with default
    positional_indices = set()
    varargs = False
    
    parser = cli.build_dynamic_arg_parser(
        undefined_vars, env_vars, positional_indices, varargs, annotations
    )
    
    # Test successful parsing
    args = parser.parse_args([
        "--db_host", "localhost",
        "--output_file", "output.txt",
        "--verbose"
    ])
    
    assert args.DB_HOST == "localhost"
    assert args.DB_PORT == 5432  # From annotation default, not environment
    assert args.OUTPUT_FILE == "output.txt"
    assert args.VERBOSE is True
    assert args.QUIET is False


def test_env_vars_in_groups():
    """Test that environment variables work correctly with groups."""
    annotations = {
        "API_KEY": ArgumentAnnotation(type="str", group="API Configuration", help="API key"),
        "API_URL": ArgumentAnnotation(type="str", group="API Configuration", help="API URL"),
        "TIMEOUT": ArgumentAnnotation(type="int", group="API Configuration", help="Request timeout"),
    }
    
    undefined_vars = []
    env_vars = {
        "API_KEY": "secret123",
        "API_URL": "https://api.example.com",
        "TIMEOUT": "30"
    }
    positional_indices = set()
    varargs = False
    
    parser = cli.build_dynamic_arg_parser(
        undefined_vars, env_vars, positional_indices, varargs, annotations
    )
    
    # Test with default values from environment
    args = parser.parse_args([])
    assert args.API_KEY == "secret123"
    assert args.API_URL == "https://api.example.com"
    assert args.TIMEOUT == 30
    
    # Test overriding environment values
    args = parser.parse_args(["--api_key", "newsecret", "--timeout", "60"])
    assert args.API_KEY == "newsecret"
    assert args.API_URL == "https://api.example.com"  # Still from env
    assert args.TIMEOUT == 60


def write_temp_script(tmp_path: Path, content: str) -> Path:
    """Helper function to write a temporary script file."""
    path = tmp_path / "script.sh"
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)
    return path


def test_integration_script_with_groups(tmp_path: Path):
    """Integration test with a complete script using groups."""
    script_content = """#!/bin/bash
# SERVER_HOST (str) [group: Server]: Server hostname
# SERVER_PORT (int) [group: Server]: Server port. Default: 8080
# LOG_LEVEL (choice[debug, info, warn, error]) [group: Logging]: Log level. Default: info
# LOG_FILE (str) [group: Logging]: Log file path
# VERBOSE (bool) [exclusive_group: Output]: Verbose output
# QUIET (bool) [exclusive_group: Output]: Quiet output

echo "Starting server on $SERVER_HOST:$SERVER_PORT"
echo "Log level: $LOG_LEVEL"
echo "Log file: $LOG_FILE"
echo "Verbose: $VERBOSE"
echo "Quiet: $QUIET"
"""
    
    script_path = write_temp_script(tmp_path, script_content)
    
    # Test the argument parsing
    from argorator.cli import main
    
    # Test help output includes groups
    try:
        main(["compile", str(script_path), "--help"])
    except SystemExit:
        pass  # Expected for --help
    
    # Test successful execution
    result = main([
        "compile", str(script_path),
        "--server_host", "localhost",
        "--log_file", "/var/log/app.log",
        "--verbose"
    ])
    
    assert result == 0


def test_groups_with_aliases():
    """Test that groups work correctly with argument aliases."""
    annotations = {
        "VERBOSE": ArgumentAnnotation(
            type="bool", 
            exclusive_group="Verbosity", 
            alias="-v",
            help="Verbose mode"
        ),
        "QUIET": ArgumentAnnotation(
            type="bool", 
            exclusive_group="Verbosity", 
            alias="-q",
            help="Quiet mode"
        ),
        "CONFIG_FILE": ArgumentAnnotation(
            type="str",
            group="Configuration",
            alias="-c",
            help="Configuration file"
        ),
    }
    
    undefined_vars = ["CONFIG_FILE", "VERBOSE", "QUIET"]  # Added missing boolean vars
    env_vars = {}
    positional_indices = set()
    varargs = False
    
    parser = cli.build_dynamic_arg_parser(
        undefined_vars, env_vars, positional_indices, varargs, annotations
    )
    
    # Test using aliases
    args = parser.parse_args(["-c", "config.json", "-v"])
    assert args.CONFIG_FILE == "config.json"
    assert args.VERBOSE is True
    assert args.QUIET is False
    
    # Test that mutually exclusive aliases work
    with pytest.raises(SystemExit):
        parser.parse_args(["-c", "config.json", "-v", "-q"])
"""Tests for natural language group syntax."""

import pytest
from pathlib import Path
from argorator import cli
from argorator.annotations import parse_arg_annotations, parse_group_declarations
from argorator.models import ArgumentAnnotation


def test_parse_group_declarations_basic():
    """Test parsing basic group declarations."""
    script = """
    # group SERVER_HOST, SERVER_PORT as Server Configuration
    # one of VERBOSE, QUIET as Output Mode
    """
    group_annotations = parse_group_declarations(script)
    
    # Regular group
    assert "SERVER_HOST" in group_annotations
    assert group_annotations["SERVER_HOST"].group == "Server Configuration"
    assert group_annotations["SERVER_HOST"].exclusive_group is None
    
    assert "SERVER_PORT" in group_annotations
    assert group_annotations["SERVER_PORT"].group == "Server Configuration"
    
    # Exclusive group
    assert "VERBOSE" in group_annotations
    assert group_annotations["VERBOSE"].exclusive_group == "Output Mode"
    assert group_annotations["VERBOSE"].group is None
    
    assert "QUIET" in group_annotations
    assert group_annotations["QUIET"].exclusive_group == "Output Mode"


def test_parse_group_declarations_auto_naming():
    """Test automatic group naming when 'as Name' is omitted."""
    script = """
    # group DB_HOST, DB_PORT, DB_NAME
    # group LOG_LEVEL, LOG_FILE
    # one of DEBUG, TRACE
    # one of JSON_OUTPUT, XML_OUTPUT
    """
    group_annotations = parse_group_declarations(script)
    
    # Auto-named regular groups
    assert group_annotations["DB_HOST"].group == "Group1"
    assert group_annotations["DB_PORT"].group == "Group1"
    assert group_annotations["DB_NAME"].group == "Group1"
    
    assert group_annotations["LOG_LEVEL"].group == "Group2"
    assert group_annotations["LOG_FILE"].group == "Group2"
    
    # Auto-named exclusive groups
    assert group_annotations["DEBUG"].exclusive_group == "ExclusiveGroup1"
    assert group_annotations["TRACE"].exclusive_group == "ExclusiveGroup1"
    
    assert group_annotations["JSON_OUTPUT"].exclusive_group == "ExclusiveGroup2"
    assert group_annotations["XML_OUTPUT"].exclusive_group == "ExclusiveGroup2"


def test_parse_group_declarations_mixed_spacing():
    """Test parsing with various spacing and formatting."""
    script = """
    #group SERVER_HOST,SERVER_PORT,SERVER_TIMEOUT as Server
    # one of VERBOSE, QUIET, DEBUG as   Output Level  
    #   group   API_KEY  ,   API_SECRET   
    """
    group_annotations = parse_group_declarations(script)
    
    # Test tight spacing
    assert group_annotations["SERVER_HOST"].group == "Server"
    assert group_annotations["SERVER_PORT"].group == "Server"
    assert group_annotations["SERVER_TIMEOUT"].group == "Server"
    
    # Test extra spaces in group name
    assert group_annotations["VERBOSE"].exclusive_group == "Output Level"
    assert group_annotations["QUIET"].exclusive_group == "Output Level"
    assert group_annotations["DEBUG"].exclusive_group == "Output Level"
    
    # Test variable name spacing
    assert group_annotations["API_KEY"].group == "Group1"
    assert group_annotations["API_SECRET"].group == "Group1"


def test_parse_combined_natural_and_individual():
    """Test combining natural language groups with individual annotations."""
    script = """
    # group SERVER_HOST, SERVER_PORT as Server
    # one of VERBOSE, QUIET as Output
    
    # SERVER_HOST (str): Server hostname
    # SERVER_PORT (int): Server port. Default: 8080
    # VERBOSE (bool) [alias: -v]: Enable verbose output
    # QUIET (bool) [alias: -q]: Enable quiet mode
    # CONFIG_FILE (str): Configuration file path
    """
    annotations = parse_arg_annotations(script)
    
    # Variables with both group and individual annotations
    assert annotations["SERVER_HOST"].group == "Server"
    assert annotations["SERVER_HOST"].type == "str"
    assert annotations["SERVER_HOST"].help == "Server hostname"
    
    assert annotations["SERVER_PORT"].group == "Server"
    assert annotations["SERVER_PORT"].type == "int"
    assert annotations["SERVER_PORT"].default == "8080"
    
    assert annotations["VERBOSE"].exclusive_group == "Output"
    assert annotations["VERBOSE"].alias == "-v"
    assert annotations["VERBOSE"].help == "Enable verbose output"
    
    assert annotations["QUIET"].exclusive_group == "Output"
    assert annotations["QUIET"].alias == "-q"
    
    # Variable with only individual annotation
    assert annotations["CONFIG_FILE"].group is None
    assert annotations["CONFIG_FILE"].exclusive_group is None
    assert annotations["CONFIG_FILE"].help == "Configuration file path"





def test_variables_only_in_groups():
    """Test variables that are only mentioned in group declarations."""
    script = """
    # group API_KEY, API_SECRET as Authentication
    # one of JSON_OUTPUT, XML_OUTPUT as Format
    
    # CONFIG_FILE (str): Configuration file
    """
    annotations = parse_arg_annotations(script)
    
    # Variables only in group declarations should have basic annotations
    assert annotations["API_KEY"].group == "Authentication"
    assert annotations["API_KEY"].type == "str"  # Default type
    assert annotations["API_KEY"].help == ""  # No help text
    
    assert annotations["API_SECRET"].group == "Authentication"
    assert annotations["API_SECRET"].type == "str"
    
    assert annotations["JSON_OUTPUT"].exclusive_group == "Format"
    assert annotations["JSON_OUTPUT"].type == "str"
    
    assert annotations["XML_OUTPUT"].exclusive_group == "Format"
    
    # Variable with individual annotation
    assert annotations["CONFIG_FILE"].help == "Configuration file"


def test_build_parser_with_natural_syntax():
    """Test that the parser builder works with natural language groups."""
    script = """
    # group DB_HOST, DB_PORT as Database
    # one of VERBOSE, QUIET as Output
    
    # DB_HOST (str): Database hostname
    # DB_PORT (int): Database port. Default: 5432
    # VERBOSE (bool): Verbose mode
    # QUIET (bool): Quiet mode
    # CONFIG_FILE (str): Config file
    
    echo "Connecting to $DB_HOST:$DB_PORT"
    echo "Config: $CONFIG_FILE"
    echo "Verbose: $VERBOSE, Quiet: $QUIET"
    """
    
    # Parse the script
    from argorator.cli import determine_variables
    defined_vars, undefined_vars, env_vars = determine_variables(script)
    annotations = parse_arg_annotations(script)
    
    # Build parser
    undefined_names = sorted(undefined_vars.keys())
    parser = cli.build_dynamic_arg_parser(
        undefined_names, env_vars, set(), False, annotations
    )
    
    # Test successful parsing
    args = parser.parse_args([
        "--db_host", "localhost",
        "--config_file", "config.json",
        "--verbose"
    ])
    
    assert args.DB_HOST == "localhost"
    assert args.DB_PORT == 5432  # Default value
    assert args.CONFIG_FILE == "config.json"
    assert args.VERBOSE is True
    assert args.QUIET is False
    
    # Test mutual exclusivity
    with pytest.raises(SystemExit):
        parser.parse_args([
            "--db_host", "localhost",
            "--config_file", "config.json", 
            "--verbose", "--quiet"
        ])


def test_integration_natural_syntax_script(tmp_path: Path):
    """Integration test with a complete script using natural syntax."""
    script_content = """#!/bin/bash
# group SERVER_HOST, SERVER_PORT, SERVER_TIMEOUT as Server Configuration
# one of VERBOSE, QUIET as Output Mode
# group LOG_LEVEL, LOG_FILE as Logging

# SERVER_HOST (str): Server hostname to connect to
# SERVER_PORT (int): Server port. Default: 8080
# SERVER_TIMEOUT (int): Connection timeout. Default: 30
# VERBOSE (bool) [alias: -v]: Enable verbose output
# QUIET (bool) [alias: -q]: Enable quiet mode
# LOG_LEVEL (choice[debug, info, warn, error]): Logging level. Default: info
# LOG_FILE (str): Path to log file
# CONFIG_FILE (str): Configuration file path

echo "Server: $SERVER_HOST:$SERVER_PORT (timeout: $SERVER_TIMEOUT)"
echo "Logging: $LOG_LEVEL to $LOG_FILE"
echo "Config: $CONFIG_FILE"
echo "Verbose: $VERBOSE, Quiet: $QUIET"
"""
    
    # Write script to file
    script_path = tmp_path / "natural_test.sh"
    script_path.write_text(script_content)
    script_path.chmod(0o755)
    
    # Test compilation
    from argorator.cli import main
    result = main([
        "compile", str(script_path),
        "--server_host", "api.example.com",
        "--log_file", "/var/log/app.log",
        "--config_file", "config.json",
        "-v"
    ])
    
    assert result == 0


def test_case_insensitive_keywords():
    """Test that group keywords are case insensitive."""
    script = """
    # GROUP SERVER_HOST, SERVER_PORT as Server
    # One Of VERBOSE, QUIET as Output
    # group DB_HOST, DB_PORT
    # ONE OF DEBUG, TRACE
    """
    group_annotations = parse_group_declarations(script)
    
    assert group_annotations["SERVER_HOST"].group == "Server"
    assert group_annotations["SERVER_PORT"].group == "Server"
    
    assert group_annotations["VERBOSE"].exclusive_group == "Output"
    assert group_annotations["QUIET"].exclusive_group == "Output"
    
    assert group_annotations["DB_HOST"].group == "Group1"
    assert group_annotations["DB_PORT"].group == "Group1"
    
    assert group_annotations["DEBUG"].exclusive_group == "ExclusiveGroup1"
    assert group_annotations["TRACE"].exclusive_group == "ExclusiveGroup1"


def test_complex_group_names():
    """Test group names with spaces and special characters."""
    script = """
    # group API_KEY, API_SECRET as API Configuration & Authentication
    # one of VERBOSE, QUIET as Output Mode (Level 1)
    """
    group_annotations = parse_group_declarations(script)
    
    assert group_annotations["API_KEY"].group == "API Configuration & Authentication"
    assert group_annotations["API_SECRET"].group == "API Configuration & Authentication"
    
    assert group_annotations["VERBOSE"].exclusive_group == "Output Mode (Level 1)"
    assert group_annotations["QUIET"].exclusive_group == "Output Mode (Level 1)"


def write_temp_script(tmp_path: Path, content: str) -> Path:
    """Helper function to write a temporary script file."""
    path = tmp_path / "script.sh"
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)
    return path
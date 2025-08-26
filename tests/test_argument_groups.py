"""Tests for argument groups and mutually exclusive groups functionality."""

import pytest
from pathlib import Path
from argorator import cli
from argorator.annotations import parse_arg_annotations
from argorator.models import ArgumentAnnotation





def test_build_parser_with_argument_groups():
    """Test that argument groups are created correctly with natural syntax."""
    script = """
    # group SERVER_HOST, SERVER_PORT as Server Configuration
    # group LOG_LEVEL as Logging
    
    # SERVER_HOST (str): Server host
    # SERVER_PORT (int): Server port
    # LOG_LEVEL (str): Log level
    # CONFIG_FILE (str): Config file path
    
    echo "Connecting to $SERVER_HOST:$SERVER_PORT"
    echo "Log level: $LOG_LEVEL"
    echo "Config: $CONFIG_FILE"
    """
    
    from argorator.cli import determine_variables
    defined_vars, undefined_vars, env_vars = determine_variables(script)
    annotations = parse_arg_annotations(script)
    
    undefined_names = sorted(undefined_vars.keys())
    parser = cli.build_dynamic_arg_parser(
        undefined_names, env_vars, set(), False, annotations
    )
    
    # Check that the parser was created successfully
    assert parser is not None
    
    # Parse help to see if groups are present
    help_text = parser.format_help()
    assert "Server Configuration" in help_text
    assert "Logging" in help_text
    assert "--server_host" in help_text
    assert "--server_port" in help_text
    assert "--log_level" in help_text
    assert "--config_file" in help_text


def test_build_parser_with_exclusive_groups():
    """Test that mutually exclusive groups are created correctly with natural syntax."""
    script = """
    # one of VERBOSE, QUIET as Verbosity
    # one of JSON_OUTPUT, XML_OUTPUT as Output Format
    
    # VERBOSE (bool): Verbose mode
    # QUIET (bool): Quiet mode
    # JSON_OUTPUT (bool): JSON output
    # XML_OUTPUT (bool): XML output
    # CONFIG (str): Config file
    
    echo "Verbose: $VERBOSE, Quiet: $QUIET"
    echo "JSON: $JSON_OUTPUT, XML: $XML_OUTPUT"
    echo "Config: $CONFIG"
    """
    
    from argorator.cli import determine_variables
    defined_vars, undefined_vars, env_vars = determine_variables(script)
    annotations = parse_arg_annotations(script)
    
    undefined_names = sorted(undefined_vars.keys())
    parser = cli.build_dynamic_arg_parser(
        undefined_names, env_vars, set(), False, annotations
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
    """Test parser with both regular groups and exclusive groups using natural syntax."""
    script = """
    # group DB_HOST as Database
    # one of VERBOSE, QUIET as Verbosity
    
    # DB_HOST (str): Database host
    # DB_PORT (int): Database port. Default: 5432
    # VERBOSE (bool): Verbose mode
    # QUIET (bool): Quiet mode
    # OUTPUT_FILE (str): Output file path
    
    echo "Database: $DB_HOST:$DB_PORT"
    echo "Output: $OUTPUT_FILE"
    echo "Verbose: $VERBOSE, Quiet: $QUIET"
    """
    
    from argorator.cli import determine_variables
    defined_vars, undefined_vars, env_vars = determine_variables(script)
    annotations = parse_arg_annotations(script)
    
    # Set up environment variable
    import os
    os.environ["DB_PORT"] = "3306"
    defined_vars, undefined_vars, env_vars = determine_variables(script)
    
    undefined_names = sorted(undefined_vars.keys())
    parser = cli.build_dynamic_arg_parser(
        undefined_names, env_vars, set(), False, annotations
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
    
    # Clean up
    del os.environ["DB_PORT"]


def test_env_vars_in_groups():
    """Test that environment variables work correctly with natural language groups."""
    script = """
    # group API_KEY, API_URL, TIMEOUT as API Configuration
    
    # API_KEY (str): API key
    # API_URL (str): API URL  
    # TIMEOUT (int): Request timeout
    
    echo "API: $API_KEY @ $API_URL (timeout: $TIMEOUT)"
    """
    
    import os
    # Set up environment variables
    os.environ["API_KEY"] = "secret123"
    os.environ["API_URL"] = "https://api.example.com"
    os.environ["TIMEOUT"] = "30"
    
    from argorator.cli import determine_variables
    defined_vars, undefined_vars, env_vars = determine_variables(script)
    annotations = parse_arg_annotations(script)
    
    undefined_names = sorted(undefined_vars.keys())
    parser = cli.build_dynamic_arg_parser(
        undefined_names, env_vars, set(), False, annotations
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
    
    # Clean up
    del os.environ["API_KEY"]
    del os.environ["API_URL"] 
    del os.environ["TIMEOUT"]


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
    """Test that natural language groups work correctly with argument aliases."""
    script = """
    # one of VERBOSE, QUIET as Verbosity
    # group CONFIG_FILE as Configuration
    
    # VERBOSE (bool) [alias: -v]: Verbose mode
    # QUIET (bool) [alias: -q]: Quiet mode
    # CONFIG_FILE (str) [alias: -c]: Configuration file
    
    echo "Config: $CONFIG_FILE"
    echo "Verbose: $VERBOSE, Quiet: $QUIET"
    """
    
    from argorator.cli import determine_variables
    defined_vars, undefined_vars, env_vars = determine_variables(script)
    annotations = parse_arg_annotations(script)
    
    undefined_names = sorted(undefined_vars.keys())
    parser = cli.build_dynamic_arg_parser(
        undefined_names, env_vars, set(), False, annotations
    )
    
    # Test using aliases
    args = parser.parse_args(["-c", "config.json", "-v"])
    assert args.CONFIG_FILE == "config.json"
    assert args.VERBOSE is True
    assert args.QUIET is False
    
    # Test that mutually exclusive aliases work
    with pytest.raises(SystemExit):
        parser.parse_args(["-c", "config.json", "-v", "-q"])
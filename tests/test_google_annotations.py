import pytest
from pathlib import Path
from argorator import cli
from argorator.annotations import parse_arg_annotations
from argorator.models import ArgumentAnnotation
from argorator.testing import build_test_parser


def test_parse_basic_google_annotation():
    """Test parsing basic Google-style annotations."""
    script = """
    # NAME: The user's name
    # AGE (int): The user's age
    echo "Hello $NAME, you are $AGE"
    """
    annotations = parse_arg_annotations(script)
    
    assert "NAME" in annotations
    assert annotations["NAME"].help == "The user's name"
    assert annotations["NAME"].type == "str"
    
    assert "AGE" in annotations
    assert annotations["AGE"].help == "The user's age"
    assert annotations["AGE"].type == "int"


def test_parse_google_with_defaults():
    """Test parsing Google-style annotations with default values."""
    script = """
    # PORT (int): Server port. Default: 8080
    # HOST (str): Server host. Default: localhost
    # DEBUG (bool): Enable debug mode. Default: false
    """
    annotations = parse_arg_annotations(script)
    
    assert annotations["PORT"].type == "int"
    assert annotations["PORT"].default == "8080"
    assert annotations["PORT"].help == "Server port"
    
    assert annotations["HOST"].type == "str"
    assert annotations["HOST"].default == "localhost"
    
    assert annotations["DEBUG"].type == "bool"
    assert annotations["DEBUG"].default == "false"


def test_parse_google_choice_annotations():
    """Test parsing Google-style choice annotations."""
    script = """
    # ENV (choice[dev, staging, prod]): Deployment environment
    # COLOR (choice[red, green, blue]): Favorite color. Default: blue
    """
    annotations = parse_arg_annotations(script)
    
    assert annotations["ENV"].type == "choice"
    assert annotations["ENV"].choices == ["dev", "staging", "prod"]
    assert annotations["ENV"].help == "Deployment environment"
    
    assert annotations["COLOR"].type == "choice"
    assert annotations["COLOR"].choices == ["red", "green", "blue"]
    assert annotations["COLOR"].default == "blue"


def test_parse_lowercase_parameter_names():
    """Test that lowercase parameter names in annotations are normalized to uppercase."""
    script = """
    # name (str): The user's name. Default: John
    # age (int): The user's age  
    # debug_mode (bool): Enable debug mode. Default: false
    # env_type (choice[dev, prod]): Environment type
    echo "Hello $NAME, you are $AGE, debug=$DEBUG_MODE, env=$ENV_TYPE"
    """
    annotations = parse_arg_annotations(script)
    
    # All parameter names should be normalized to uppercase
    assert "NAME" in annotations
    assert "AGE" in annotations  
    assert "DEBUG_MODE" in annotations
    assert "ENV_TYPE" in annotations
    
    # Verify the annotation data is preserved correctly
    assert annotations["NAME"].type == "str"
    assert annotations["NAME"].default == "John"
    assert annotations["NAME"].help == "The user's name"
    
    assert annotations["AGE"].type == "int"
    assert annotations["AGE"].help == "The user's age"
    
    assert annotations["DEBUG_MODE"].type == "bool"
    assert annotations["DEBUG_MODE"].default == "false"
    
    assert annotations["ENV_TYPE"].type == "choice"
    assert annotations["ENV_TYPE"].choices == ["dev", "prod"]


def test_parse_mixed_case_parameter_names():
    """Test that mixed case parameter names work correctly."""
    script = """
    # User_Name (str): Mixed case name
    # PORT_number (int): Port number
    # enableDebug (bool): Debug flag
    """
    annotations = parse_arg_annotations(script)
    
    # All should be normalized to uppercase
    assert "USER_NAME" in annotations
    assert "PORT_NUMBER" in annotations
    assert "ENABLEDEBUG" in annotations
    
    assert annotations["USER_NAME"].help == "Mixed case name"
    assert annotations["PORT_NUMBER"].type == "int"
    assert annotations["ENABLEDEBUG"].type == "bool"


def test_parse_google_all_types():
    """Test parsing all supported types."""
    script = """
    # NAME (str): String parameter
    # COUNT (int): Integer parameter
    # PRICE (float): Float parameter
    # ENABLED (bool): Boolean parameter
    # MODE (choice[fast, slow]): Choice parameter
    """
    annotations = parse_arg_annotations(script)
    
    assert annotations["NAME"].type == "str"
    assert annotations["COUNT"].type == "int"
    assert annotations["PRICE"].type == "float"
    assert annotations["ENABLED"].type == "bool"
    assert annotations["MODE"].type == "choice"
    assert annotations["MODE"].choices == ["fast", "slow"]


def test_google_annotations_with_argparse():
    """Test that Google annotations work with argparse."""
    annotations = {
        "PORT": ArgumentAnnotation(type="int", help="Port", default="8080"),
        "HOST": ArgumentAnnotation(type="str", help="Host", default="localhost"),
        "DEBUG": ArgumentAnnotation(type="bool", help="Debug mode", default="false"),
    }
    
    # All should be optional due to defaults
    parser = build_test_parser(
        ["PORT", "HOST", "DEBUG"],
        {},
        set(),
        False,
        annotations
    )
    
    # Test with no arguments (should use defaults)
    args = parser.parse_args([])
    assert args.PORT == 8080
    assert args.HOST == "localhost"
    assert args.DEBUG is False
    
    # Test with overrides
    args = parser.parse_args(["--port", "9000", "--debug"])
    assert args.PORT == 9000
    assert args.DEBUG is True


def test_mixed_required_optional():
    """Test mix of required and optional parameters."""
    annotations = {
        "SERVICE": ArgumentAnnotation(type="str", help="Service name"),  # No default = required
        "PORT": ArgumentAnnotation(type="int", help="Port", default="8080"),  # Has default = optional
    }
    
    parser = build_test_parser(
        ["SERVICE", "PORT"],
        {},
        set(),
        False,
        annotations
    )
    
    # Should fail without required SERVICE
    with pytest.raises(SystemExit):
        parser.parse_args([])
    
    # Should work with just SERVICE
    args = parser.parse_args(["--service", "api"])
    assert args.SERVICE == "api"
    assert args.PORT == 8080


def test_case_insensitive_variable_names():
    """Test that variable names work case-insensitively."""
    script = """
    # service_name (str): Service to deploy
    # SERVICE_PORT (int): Port number
    # Service_Type (choice[web, api]): Type of service
    """
    annotations = parse_arg_annotations(script)
    
    # Parser should find them with uppercase names
    assert "SERVICE_NAME" in annotations or "service_name" in annotations
    assert "SERVICE_PORT" in annotations
    assert "SERVICE_TYPE" in annotations or "Service_Type" in annotations


def test_integration_google_style(tmp_path: Path):
    """Test full integration with Google-style annotated script."""
    script_content = """#!/bin/bash
# SERVICE (str): Service name to deploy
# ENVIRONMENT (choice[dev, prod]): Target environment
# REPLICAS (int): Number of replicas. Default: 2
# DRY_RUN (bool): Dry run mode. Default: false

echo "Deploying $SERVICE to $ENVIRONMENT with $REPLICAS replicas"
if [ "$DRY_RUN" = "true" ]; then
    echo "(dry run)"
fi
"""
    
    script_path = tmp_path / "deploy.sh"
    script_path.write_text(script_content)
    script_path.chmod(0o755)
    
    # Test with minimal arguments (using defaults)
    result = cli.main(["compile", str(script_path), 
                      "--service", "api", 
                      "--environment", "dev"])
    
    assert result == 0  # Should succeed with defaults
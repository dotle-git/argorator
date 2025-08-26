import pytest
from pathlib import Path
from argorator import cli


def test_parse_basic_param_annotation():
    """Test parsing basic :param annotations."""
    script = """
    # :param NAME: The user's name
    # :param AGE: The user's age
    echo "Hello $NAME, you are $AGE"
    """
    annotations = cli.parse_arg_annotations(script)
    
    assert "NAME" in annotations
    assert annotations["NAME"]["help"] == "The user's name"
    assert annotations["NAME"]["type"] == "str"
    
    assert "AGE" in annotations
    assert annotations["AGE"]["help"] == "The user's age"
    assert annotations["AGE"]["type"] == "str"


def test_parse_type_annotations():
    """Test parsing separate :type annotations."""
    script = """
    # :param COUNT: Number of items
    # :type COUNT: int
    # :param PRICE: Price per item
    # :type PRICE: float
    # :param ENABLED: Enable feature
    # :type ENABLED: bool
    """
    annotations = cli.parse_arg_annotations(script)
    
    assert annotations["COUNT"]["type"] == "int"
    assert annotations["PRICE"]["type"] == "float"
    assert annotations["ENABLED"]["type"] == "bool"


def test_parse_inline_type_annotations():
    """Test parsing inline type in :param annotations."""
    script = """
    # :param int COUNT: Number of items
    # :param float PRICE: Price per item
    # :param bool ENABLED: Enable feature
    # :param str NAME: User name
    """
    annotations = cli.parse_arg_annotations(script)
    
    assert annotations["COUNT"]["type"] == "int"
    assert annotations["COUNT"]["help"] == "Number of items"
    
    assert annotations["PRICE"]["type"] == "float"
    assert annotations["PRICE"]["help"] == "Price per item"
    
    assert annotations["ENABLED"]["type"] == "bool"
    assert annotations["ENABLED"]["help"] == "Enable feature"
    
    assert annotations["NAME"]["type"] == "str"
    assert annotations["NAME"]["help"] == "User name"


def test_parse_choice_annotations():
    """Test parsing choice type with :choices annotation."""
    script = """
    # :param ENV: Deployment environment
    # :type ENV: choice
    # :choices ENV: dev, staging, prod
    
    # :param COLOR: Favorite color
    # :choices COLOR: red, green, blue
    """
    annotations = cli.parse_arg_annotations(script)
    
    assert annotations["ENV"]["type"] == "choice"
    assert annotations["ENV"]["choices"] == ["dev", "staging", "prod"]
    
    assert annotations["COLOR"]["type"] == "choice"  # Auto-set when choices present
    assert annotations["COLOR"]["choices"] == ["red", "green", "blue"]


def test_type_converter_functions():
    """Test that type converters work correctly."""
    # Test through build_dynamic_arg_parser
    annotations = {
        "COUNT": {"type": "int", "help": "Count"},
        "PRICE": {"type": "float", "help": "Price"},
        "ENABLED": {"type": "bool", "help": "Enabled"},
        "NAME": {"type": "str", "help": "Name"},
    }
    
    parser = cli.build_dynamic_arg_parser(
        ["COUNT", "PRICE", "ENABLED", "NAME"],
        {},
        set(),
        False,
        annotations
    )
    
    # Test integer conversion
    args = parser.parse_args(["--count", "42", "--price", "19.99", "--enabled", "true", "--name", "test"])
    assert args.COUNT == 42
    assert isinstance(args.COUNT, int)
    
    # Test float conversion
    assert args.PRICE == 19.99
    assert isinstance(args.PRICE, float)
    
    # Test boolean conversion
    assert args.ENABLED is True
    assert isinstance(args.ENABLED, bool)
    
    # Test string (no conversion)
    assert args.NAME == "test"
    assert isinstance(args.NAME, str)


def test_bool_converter_values():
    """Test various boolean string values."""
    annotations = {"FLAG": {"type": "bool", "help": "Flag"}}
    
    parser = cli.build_dynamic_arg_parser(["FLAG"], {}, set(), False, annotations)
    
    # Test truthy values
    for val in ["true", "True", "TRUE", "1", "yes", "Yes", "y", "Y"]:
        args = parser.parse_args(["--flag", val])
        assert args.FLAG is True, f"Failed for value: {val}"
    
    # Test falsy values
    for val in ["false", "False", "0", "no", "n", ""]:
        args = parser.parse_args(["--flag", val])
        assert args.FLAG is False, f"Failed for value: {val}"


def test_choice_validation():
    """Test that choices are validated by argparse."""
    annotations = {
        "ENV": {
            "type": "choice",
            "help": "Environment",
            "choices": ["dev", "staging", "prod"]
        }
    }
    
    parser = cli.build_dynamic_arg_parser(["ENV"], {}, set(), False, annotations)
    
    # Valid choice
    args = parser.parse_args(["--env", "dev"])
    assert args.ENV == "dev"
    
    # Invalid choice should raise SystemExit
    with pytest.raises(SystemExit):
        parser.parse_args(["--env", "invalid"])


def test_integration_with_script(tmp_path: Path):
    """Test full integration with annotated script."""
    script_content = """#!/bin/bash
# :param str SERVICE: Service name to deploy
# :param ENVIRONMENT: Target environment
# :type ENVIRONMENT: choice
# :choices ENVIRONMENT: dev, prod
# :param int REPLICAS: Number of replicas

echo "Deploying $SERVICE to $ENVIRONMENT with $REPLICAS replicas"
"""
    
    script_path = tmp_path / "deploy.sh"
    script_path.write_text(script_content)
    script_path.chmod(0o755)
    
    # Test compile mode to see injected variables
    result = cli.main(["compile", str(script_path), 
                      "--service", "api", 
                      "--environment", "dev", 
                      "--replicas", "3"])
    
    assert result == 0  # Should succeed
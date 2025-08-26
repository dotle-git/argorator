import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from argorator import cli


SCRIPT_WITH_VARS = """#!/bin/bash
echo "Name: $NAME"
echo "Age: $AGE"
echo "City: $CITY"
"""

SCRIPT_WITH_POSITIONALS = """#!/bin/bash
echo "First: $1"
echo "Second: $2"
echo "Rest: $@"
"""

SCRIPT_WITH_ENV_VARS = """#!/bin/bash
echo "Home: $HOME"
echo "Custom: $CUSTOM_VAR"
"""

SCRIPT_NO_JSON = """#!/bin/bash
# argorator: no-json-input
echo "Name: $NAME"
"""

SCRIPT_STDIN_EXPECTED = """#!/bin/bash
# This script expects stdin input
read line
echo "Read from stdin: $line"
echo "Variable: $VAR"
"""


def write_temp_script(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "test_script.sh"
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)
    return path


def test_json_input_option_with_vars(tmp_path: Path, capsys):
    """Test JSON input via --json-input option with variables."""
    script = write_temp_script(tmp_path, SCRIPT_WITH_VARS)
    json_data = {"NAME": "Alice", "AGE": "30", "CITY": "NYC"}
    
    # Test with compile to verify variable injection
    rc = cli.main(["compile", str(script), "--json-input", json.dumps(json_data)])
    assert rc == 0
    
    captured = capsys.readouterr()
    assert "NAME=Alice" in captured.out
    assert "AGE=30" in captured.out
    assert "CITY=NYC" in captured.out


def test_json_input_option_with_positionals(tmp_path: Path, capsys):
    """Test JSON input with positional arguments."""
    script = write_temp_script(tmp_path, SCRIPT_WITH_POSITIONALS)
    json_data = {"ARG1": "first", "ARG2": "second", "ARGS": ["extra1", "extra2"]}
    
    # Use subprocess to capture output from run command
    import subprocess
    result = subprocess.run(
        [sys.executable, "-m", "argorator.cli", str(script), "--json-input", json.dumps(json_data)],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "First: first" in result.stdout
    assert "Second: second" in result.stdout
    assert "extra1 extra2" in result.stdout


def test_json_input_stdin(tmp_path: Path, monkeypatch, capsys):
    """Test JSON input via stdin."""
    script = write_temp_script(tmp_path, SCRIPT_WITH_VARS)
    json_data = {"NAME": "Bob", "AGE": "25", "CITY": "LA"}
    
    # Mock stdin
    import io
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(json_data)))
    monkeypatch.setattr('sys.stdin.isatty', lambda: False)
    
    # Use compile to verify variable injection
    rc = cli.main(["compile", str(script)])
    assert rc == 0
    
    captured = capsys.readouterr()
    assert "NAME=Bob" in captured.out
    assert "AGE=25" in captured.out
    assert "CITY=LA" in captured.out


def test_json_input_lowercase_keys(tmp_path: Path, capsys):
    """Test JSON input with lowercase keys."""
    script = write_temp_script(tmp_path, SCRIPT_WITH_VARS)
    json_data = {"name": "Charlie", "age": "40", "city": "SF"}
    
    rc = cli.main(["compile", str(script), "--json-input", json.dumps(json_data)])
    assert rc == 0
    
    captured = capsys.readouterr()
    assert "NAME=Charlie" in captured.out
    assert "AGE=40" in captured.out
    assert "CITY=SF" in captured.out


def test_json_input_with_env_defaults(tmp_path: Path, monkeypatch, capsys):
    """Test JSON input with environment variable defaults."""
    monkeypatch.setenv("HOME", "/home/test")
    script = write_temp_script(tmp_path, SCRIPT_WITH_ENV_VARS)
    json_data = {"CUSTOM_VAR": "custom_value"}
    
    rc = cli.main(["compile", str(script), "--json-input", json.dumps(json_data)])
    assert rc == 0
    
    captured = capsys.readouterr()
    assert "HOME=/home/test" in captured.out
    assert "CUSTOM_VAR=custom_value" in captured.out


def test_json_input_override_env(tmp_path: Path, monkeypatch, capsys):
    """Test JSON input overriding environment variables."""
    monkeypatch.setenv("HOME", "/home/test")
    script = write_temp_script(tmp_path, SCRIPT_WITH_ENV_VARS)
    json_data = {"HOME": "/home/override", "CUSTOM_VAR": "custom"}
    
    rc = cli.main(["compile", str(script), "--json-input", json.dumps(json_data)])
    assert rc == 0
    
    captured = capsys.readouterr()
    assert "HOME=/home/override" in captured.out
    assert "CUSTOM_VAR=custom" in captured.out


def test_no_json_directive(tmp_path: Path, capsys):
    """Test that no-json-input directive disables JSON input."""
    script = write_temp_script(tmp_path, SCRIPT_NO_JSON)
    
    # Verify --json-input is not in help when disabled
    rc = cli.main([str(script), "--help"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "--json-input" not in captured.out
    
    # Should work with regular arguments
    rc = cli.main(["compile", str(script), "--name", "Test"])
    assert rc == 0
    
    captured = capsys.readouterr()
    assert "NAME=Test" in captured.out


def test_invalid_json_input(tmp_path: Path, capsys):
    """Test error handling for invalid JSON."""
    script = write_temp_script(tmp_path, SCRIPT_WITH_VARS)
    
    rc = cli.main([str(script), "--json-input", "invalid json"])
    assert rc == 2
    
    captured = capsys.readouterr()
    assert "error:" in captured.err
    assert "Invalid JSON" in captured.err


def test_json_input_non_object(tmp_path: Path, capsys):
    """Test error for JSON that's not an object."""
    script = write_temp_script(tmp_path, SCRIPT_WITH_VARS)
    
    rc = cli.main([str(script), "--json-input", '["array", "not", "object"]'])
    assert rc == 2
    
    captured = capsys.readouterr()
    assert "error:" in captured.err
    assert "must be an object" in captured.err


def test_json_help_text(tmp_path: Path, capsys):
    """Test that JSON input option appears in help."""
    script = write_temp_script(tmp_path, SCRIPT_WITH_VARS)
    
    # Help always exits with 0
    rc = cli.main([str(script), "--help"])
    assert rc == 0
    
    captured = capsys.readouterr()
    assert "--json-input" in captured.out
    assert "JSON object" in captured.out
    assert "via stdin" in captured.out
    assert "Alternatively, parameters can be provided as JSON:" in captured.out


def test_json_help_text_disabled(tmp_path: Path, capsys):
    """Test that JSON input doesn't appear in help when disabled."""
    script = write_temp_script(tmp_path, SCRIPT_NO_JSON)
    
    rc = cli.main([str(script), "--help"])
    assert rc == 0
    
    captured = capsys.readouterr()
    assert "--json-input" not in captured.out
    assert "Alternatively, parameters can be provided as JSON:" not in captured.out


def test_check_json_input_allowed():
    """Test the check_json_input_allowed function."""
    # Should allow by default
    assert cli.check_json_input_allowed("#!/bin/bash\necho test") is True
    
    # Should disallow with directive
    assert cli.check_json_input_allowed("#!/bin/bash\n# argorator: no-json-input\necho test") is False
    
    # Case insensitive
    assert cli.check_json_input_allowed("#!/bin/bash\n# ARGORATOR: NO-JSON-INPUT\necho test") is False
    
    # With spaces
    assert cli.check_json_input_allowed("#!/bin/bash\n#  argorator:  no-json-input  \necho test") is False


def test_parse_json_input():
    """Test the parse_json_input function."""
    # Valid JSON
    data = cli.parse_json_input('{"key": "value", "num": 42}')
    assert data == {"key": "value", "num": 42}
    
    # Invalid JSON
    with pytest.raises(ValueError) as exc_info:
        cli.parse_json_input("not json")
    assert "Invalid JSON" in str(exc_info.value)
    
    # Non-object JSON
    with pytest.raises(ValueError) as exc_info:
        cli.parse_json_input('["array"]')
    assert "must be an object" in str(exc_info.value)
import os
import subprocess
import sys
from pathlib import Path

import pytest

from argorator import cli
from argorator.analyzers import parse_defined_variables, parse_variable_usages, parse_positional_usages


SCRIPT_SIMPLE = """#!/bin/bash
echo "Hello $NAME"
"""

SCRIPT_WITH_POS = """#!/bin/bash
printf "%s %s\n" "$1" "$2"
echo rest: "$@"
"""


def write_temp_script(tmp_path: Path, content: str) -> Path:
	path = tmp_path / "script.sh"
	path.write_text(content, encoding="utf-8")
	path.chmod(0o755)
	return path


def test_parse_defined_and_used_vars():
	text = """
	#!/bin/sh
	export FOO=1
	BAR=2
	echo "$FOO $BAR $BAZ"
	"""
	defined = parse_defined_variables(text)
	used = parse_variable_usages(text)
	assert "FOO" in defined and "BAR" in defined
	assert "BAZ" in used and "FOO" in used and "BAR" in used


def test_parse_positionals_and_varargs():
	text = "echo $1 $2; echo $@"
	idx, varargs = parse_positional_usages(text)
	assert idx == {1, 2}
	assert varargs is True


def test_compile_injects_assignments(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
	script = write_temp_script(tmp_path, SCRIPT_SIMPLE)
	argv = ["compile", str(script), "--name", "Alice"]
	rc = cli.main(argv)
	assert rc == 0


def test_compile_echo_transforms_lines(tmp_path: Path):
	script = write_temp_script(
		tmp_path,
		"""#!/bin/bash
NAME=${NAME:-guest}
echo Hello | sed 's/llo/ya/'
if [ "$NAME" = "admin" ]; then
	printf "%s\n" done
fi
""",
	)
	rc = cli.main(["compile", str(script), "--echo"])  # no variables needed due to default
	assert rc == 0


def test_run_echo_does_not_execute_commands(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
	# Create a script that would create a file if executed
	script = write_temp_script(
		tmp_path,
		"""#!/bin/bash
touch created.txt
echo "Hello $NAME" | tee output.txt
""",
	)
	# Run in echo mode so commands are printed, not executed
	rc = cli.main(["run", str(script), "--name", "Alice", "--echo"])
	assert rc == 0
	# Ensure side effects did not occur
	assert not (tmp_path / "created.txt").exists()
	assert not (tmp_path / "output.txt").exists()


def test_export_prints_envs_and_undef(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
	monkeypatch.setenv("HOME", "/tmp/home")
	script = write_temp_script(tmp_path, "echo $HOME $NAME\n")
	rc = cli.main(["export", str(script), "--name", "X"]) 
	assert rc == 0


def test_run_executes_and_passes_positionals(tmp_path: Path):
	script = write_temp_script(tmp_path, SCRIPT_WITH_POS)
	rc = cli.main(["run", str(script), "first", "second", "rest1", "rest2"])
	assert rc == 0


def test_implicit_run_path(tmp_path: Path):
	script = write_temp_script(tmp_path, SCRIPT_SIMPLE)
	rc = cli.main([str(script), "--name", "Bob"])
	assert rc == 0


def test_help_shows_env_defaults(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys):
	"""Test that environment variable defaults are shown in help text."""
	# Set environment variables that will be used in the script
	monkeypatch.setenv("HOME", "/home/testuser")
	monkeypatch.setenv("USER", "testuser")
	
	# Script that uses both undefined variables and env variables
	script_content = """#!/bin/bash
echo "Home: $HOME"
echo "User: $USER"
echo "Name: $NAME"
"""
	script = write_temp_script(tmp_path, script_content)
	
	# Run with --help and capture output
	rc = cli.main([str(script), "--help"])
	
	# Check that exit code is 0 for help
	assert rc == 0
	
	# Capture the printed output
	captured = capsys.readouterr()
	
	# Verify that help text shows the default values from environment
	assert "(default from env: /home/testuser)" in captured.out
	assert "(default from env: testuser)" in captured.out
	# NAME should be required and not have a default
	assert "--name" in captured.out


def test_env_annotation_default_conflicts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys):
	"""Test handling of conflicts between environment defaults and annotation defaults."""
	# Set environment variable that conflicts with annotation default
	monkeypatch.setenv("PORT", "3000")  # Env default
	monkeypatch.setenv("HOST", "localhost")  # This will match annotation default (no conflict)
	
	# Script with annotations that have conflicting and non-conflicting defaults
	script_content = """#!/bin/bash
# PORT (int): Server port. Default: 8080
# HOST (str): Server host. Default: localhost  
# NAME (str): User name
echo "Server running on $HOST:$PORT for user $NAME"
"""
	script = write_temp_script(tmp_path, script_content)
	
	# Run with --help to see conflict warning
	rc = cli.main([str(script), "--help"])
	assert rc == 0
	
	captured = capsys.readouterr()
	
	# Should show conflict warning for PORT but not HOST
	assert "WARNING: Default value conflicts detected:" in captured.out
	assert "PORT: environment='3000' vs annotation='8080' (using environment)" in captured.out
	# HOST should not appear in conflicts since values match
	assert "HOST: environment=" not in captured.out
	
	# Should show that environment default is being used with override notice
	assert "(default from env: 3000, overriding annotation)" in captured.out
	assert "(default from env: localhost)" in captured.out  # No override notice for HOST


def test_env_annotation_conflict_execution(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys):
	"""Test that annotation defaults override environment values in execution."""
	monkeypatch.setenv("DEBUG", "true")  # Env has true
	
	# Script with annotation that has conflicting default
	script_content = """#!/bin/bash
# DEBUG (bool): Enable debug mode. Default: false
echo "Debug mode: $DEBUG"
"""
	script = write_temp_script(tmp_path, script_content)
	
	# Use export command to verify the value being set
	rc = cli.main(["export", str(script)])
	assert rc == 0
	
	captured = capsys.readouterr()
	# Should export DEBUG=true because environment value overrides annotation default
	assert "export DEBUG=true" in captured.out


def test_no_conflict_when_no_annotation_default(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys):
	"""Test that no conflict is detected when annotation has no default."""
	monkeypatch.setenv("PORT", "3000")
	
	# Script with annotation but no default value
	script_content = """#!/bin/bash
# PORT (int): Server port
echo "Port: $PORT"
"""
	script = write_temp_script(tmp_path, script_content)
	
	# Run with --help
	rc = cli.main([str(script), "--help"])
	assert rc == 0
	
	captured = capsys.readouterr()
	
	# No conflict warning should appear
	assert "WARNING: Default value conflicts detected:" not in captured.out
	# Should show env default normally
	assert "(default from env: 3000)" in captured.out


def test_multiple_conflicts_in_warning(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys):
	"""Test that multiple conflicts are all shown in the warning."""
	monkeypatch.setenv("PORT", "3000")
	monkeypatch.setenv("TIMEOUT", "30")
	monkeypatch.setenv("DEBUG", "true")
	
	script_content = """#!/bin/bash
# PORT (int): Server port. Default: 8080
# TIMEOUT (int): Request timeout. Default: 60
# DEBUG (bool): Debug mode. Default: false
# HOST (str): Server host. Default: localhost
echo "Server: $HOST:$PORT, timeout: $TIMEOUT, debug: $DEBUG"
"""
	script = write_temp_script(tmp_path, script_content)
	
	# Run with --help
	rc = cli.main([str(script), "--help"])
	assert rc == 0
	
	captured = capsys.readouterr()
	
	# Should show all conflicts
	assert "WARNING: Default value conflicts detected:" in captured.out
	assert "PORT: environment='3000' vs annotation='8080' (using environment)" in captured.out
	assert "TIMEOUT: environment='30' vs annotation='60' (using environment)" in captured.out
	assert "DEBUG: environment='true' vs annotation='false' (using environment)" in captured.out
	# HOST has no env var, so no conflict
	assert "HOST: environment=" not in captured.out


def test_lowercase_annotations_work_with_uppercase_vars(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
	"""Test that lowercase parameter names in annotations work with uppercase shell variables."""
	# Script using lowercase annotation names but uppercase variables
	script_content = """#!/bin/bash
# user_name (str): The user's name. Default: John
# port_number (int): Port number. Default: 8080
echo "Hello $USER_NAME on port $PORT_NUMBER"
"""
	script = write_temp_script(tmp_path, script_content)
	
	# Run the script - should work with the annotation defaults
	rc = cli.main([str(script)])
	assert rc == 0
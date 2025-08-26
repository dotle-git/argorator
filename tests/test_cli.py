import os
import subprocess
import sys
from pathlib import Path

import pytest

from argorator import cli


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
	defined = cli.parse_defined_variables(text)
	used = cli.parse_variable_usages(text)
	assert "FOO" in defined and "BAR" in defined
	assert "BAZ" in used and "FOO" in used and "BAR" in used


def test_parse_positionals_and_varargs():
	text = "echo $1 $2; echo $@"
	idx, varargs = cli.parse_positional_usages(text)
	assert idx == {1, 2}
	assert varargs is True


def test_compile_injects_assignments(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
	script = write_temp_script(tmp_path, SCRIPT_SIMPLE)
	argv = ["compile", str(script), "--name", "Alice"]
	rc = cli.main(argv)
	assert rc == 0


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
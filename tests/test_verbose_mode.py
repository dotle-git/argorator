import subprocess
import sys
from pathlib import Path

import pytest

from argorator import cli


def write_script(tmp_path: Path, name: str, content: str) -> Path:
	path = tmp_path / name
	path.write_text(content, encoding="utf-8")
	path.chmod(0o755)
	return path


def test_verbose_flag_parsing():
	"""Test that verbose flag is properly parsed."""
	# Test with run subcommand
	rc = cli.main(["run", "-v", "--help"])
	assert rc == 0
	
	# Test with compile subcommand
	rc = cli.main(["compile", "--verbose", "--help"])
	assert rc == 0
	
	# Test with export subcommand  
	rc = cli.main(["export", "-v", "--help"])
	assert rc == 0


def test_verbose_output_shows_debug_info(tmp_path: Path):
	"""Test that verbose mode produces debug output."""
	script = write_script(tmp_path, "verbose_test.sh", """#!/bin/bash
# @type COUNT: int
echo "Hello $NAME"
echo "Count: $COUNT"
""")
	
	# Run with verbose flag and capture stderr
	result = subprocess.run(
		[sys.executable, "-m", "argorator.cli", "-v", str(script), 
		 "--name", "Test", "--count", "42"],
		capture_output=True,
		text=True
	)
	
	assert result.returncode == 0
	stderr = result.stderr
	
	# Check for expected debug messages
	assert "[DEBUG] Reading script:" in stderr
	assert "[DEBUG] Script size:" in stderr
	assert "[DEBUG] Undefined variables (required): ['COUNT', 'NAME']" in stderr
	assert "[DEBUG] Type hints found: {'COUNT': 'int'}" in stderr
	assert "[DEBUG] Variable COUNT = 42" in stderr
	assert "[DEBUG] Variable NAME = Test" in stderr
	assert "[DEBUG] Executing command: run" in stderr


def test_verbose_with_implicit_run(tmp_path: Path):
	"""Test verbose mode works with implicit run (no subcommand)."""
	script = write_script(tmp_path, "implicit_test.sh", """#!/bin/bash
echo "Value: $VALUE"
""")
	
	# Run without explicit 'run' subcommand
	result = subprocess.run(
		[sys.executable, "-m", "argorator.cli", str(script), "-v", "--value", "123"],
		capture_output=True,
		text=True
	)
	
	assert result.returncode == 0
	assert "[DEBUG]" in result.stderr
	assert "Value: 123" in result.stdout


def test_verbose_with_env_vars(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
	"""Test verbose mode shows environment variable info."""
	monkeypatch.setenv("DEFAULT_USER", "admin")
	
	script = write_script(tmp_path, "env_test.sh", """#!/bin/bash
echo "User: $DEFAULT_USER"
""")
	
	# Run with verbose to see env var detection
	result = subprocess.run(
		[sys.executable, "-m", "argorator.cli", "-v", str(script)],
		capture_output=True,
		text=True
	)
	
	assert result.returncode == 0
	assert "[DEBUG] Environment variables (optional): ['DEFAULT_USER']" in result.stderr
	assert "[DEBUG] Variable DEFAULT_USER = admin (from environment)" in result.stderr


def test_verbose_with_positionals(tmp_path: Path):
	"""Test verbose mode with positional arguments."""
	script = write_script(tmp_path, "pos_test.sh", """#!/bin/bash
echo "Args: $1 $2"
echo "All: $@"
""")
	
	result = subprocess.run(
		[sys.executable, "-m", "argorator.cli", "-v", str(script), "first", "second", "third"],
		capture_output=True,
		text=True
	)
	
	assert result.returncode == 0
	stderr = result.stderr
	
	assert "[DEBUG] Positional arguments used: $1, $2" in stderr
	assert "[DEBUG] Varargs detected: $@ or $*" in stderr
	assert "[DEBUG] Positional $1 = first" in stderr
	assert "[DEBUG] Positional $2 = second" in stderr
	assert "[DEBUG] Varargs = ['third']" in stderr


def test_no_verbose_no_debug_output(tmp_path: Path):
	"""Test that without verbose flag, no debug output is shown."""
	script = write_script(tmp_path, "quiet_test.sh", """#!/bin/bash
echo "Hello $NAME"
""")
	
	result = subprocess.run(
		[sys.executable, "-m", "argorator.cli", str(script), "--name", "Test"],
		capture_output=True,
		text=True
	)
	
	assert result.returncode == 0
	assert "[DEBUG]" not in result.stderr
	assert result.stderr == ""  # Should be empty
	assert "Hello Test" in result.stdout
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


def test_parse_type_hints():
	"""Test that type hints are correctly parsed from comments."""
	script = """#!/bin/bash
# @type COUNT: int
# @type PRICE: float
# @type ENABLED: bool
# @type NAME: str

echo "Count: $COUNT"
echo "Price: $PRICE"
echo "Enabled: $ENABLED"
echo "Name: $NAME"
"""
	hints = cli.parse_type_hints(script)
	assert hints == {
		"COUNT": "int",
		"PRICE": "float", 
		"ENABLED": "bool",
		"NAME": "str"
	}


def test_type_conversion_int(tmp_path: Path):
	"""Test integer type conversion."""
	script = write_script(tmp_path, "int_test.sh", """#!/bin/bash
# @type AGE: int
echo "Age: $AGE"
""")
	
	# Valid int
	rc = cli.main(["run", str(script), "--age", "25"])
	assert rc == 0
	
	# Invalid int should fail
	rc = cli.main(["run", str(script), "--age", "not_a_number"])
	assert rc == 2


def test_type_conversion_float(tmp_path: Path):
	"""Test float type conversion."""
	script = write_script(tmp_path, "float_test.sh", """#!/bin/bash
# @type PRICE: float
echo "Price: $PRICE"
""")
	
	# Valid float
	rc = cli.main(["run", str(script), "--price", "19.99"])
	assert rc == 0
	
	# Integer should also work for float
	rc = cli.main(["run", str(script), "--price", "20"])
	assert rc == 0
	
	# Invalid float should fail
	rc = cli.main(["run", str(script), "--price", "abc"])
	assert rc == 2


def test_type_conversion_bool(tmp_path: Path):
	"""Test boolean type conversion."""
	script = write_script(tmp_path, "bool_test.sh", """#!/bin/bash
# @type DEBUG: bool
if [ "$DEBUG" = "true" ]; then
  echo "Debug is ON"
else
  echo "Debug is OFF"
fi
""")
	
	# Test various true values
	for value in ["true", "True", "TRUE", "1", "yes", "Yes", "y", "on"]:
		output = subprocess.check_output(
			[sys.executable, "-m", "argorator.cli", str(script), "--debug", value],
			text=True
		)
		assert "Debug is ON" in output
	
	# Test various false values
	for value in ["false", "False", "0", "no", "n", "off"]:
		output = subprocess.check_output(
			[sys.executable, "-m", "argorator.cli", str(script), "--debug", value],
			text=True
		)
		assert "Debug is OFF" in output


def test_mixed_types(tmp_path: Path):
	"""Test script with multiple typed variables."""
	script = write_script(tmp_path, "mixed_test.sh", """#!/bin/bash
# @type ITERATIONS: int
# @type THRESHOLD: float
# @type VERBOSE: bool

echo "Running $ITERATIONS iterations"
echo "Threshold: $THRESHOLD"
if [ "$VERBOSE" = "true" ]; then
  echo "Verbose mode enabled"
fi
""")
	
	output = subprocess.check_output(
		[sys.executable, "-m", "argorator.cli", str(script), 
		 "--iterations", "10", "--threshold", "0.95", "--verbose", "yes"],
		text=True
	)
	
	assert "Running 10 iterations" in output
	assert "Threshold: 0.95" in output
	assert "Verbose mode enabled" in output


def test_type_hints_with_env_vars(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
	"""Test that type hints work with environment variable defaults."""
	monkeypatch.setenv("MAX_RETRIES", "3")
	
	script = write_script(tmp_path, "env_test.sh", """#!/bin/bash
# @type MAX_RETRIES: int
echo "Max retries: $MAX_RETRIES"
""")
	
	# Should use env var default
	output = subprocess.check_output(
		[sys.executable, "-m", "argorator.cli", str(script)],
		text=True
	)
	assert "Max retries: 3" in output
	
	# Should override with typed value
	output = subprocess.check_output(
		[sys.executable, "-m", "argorator.cli", str(script), "--max_retries", "5"],
		text=True
	)
	assert "Max retries: 5" in output
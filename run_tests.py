#!/usr/bin/env python3
"""Run tests without pytest to check for failures."""

import sys
import os
import tempfile
import subprocess
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from argorator import cli


def write_temp_script(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "script.sh"
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)
    return path


def test_compile_injects_assignments():
    """Test that compile correctly injects variable assignments."""
    print("Running test_compile_injects_assignments...", end=" ")
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        script_content = """#!/bin/bash
echo "Hello $NAME"
"""
        script = write_temp_script(tmp_path, script_content)
        
        # Capture output by redirecting stdout
        from io import StringIO
        import contextlib
        
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        try:
            rc = cli.main(["compile", str(script), "--name", "Alice"])
            output = captured_output.getvalue()
            
            # Restore stdout
            sys.stdout = old_stdout
            
            assert rc == 0
            assert "NAME=Alice" in output
            assert "# argorator: injected variable definitions" in output
            
            print("PASSED")
        except Exception as e:
            sys.stdout = old_stdout
            print(f"FAILED: {e}")
            return False
    
    return True


def test_help_shows_env_defaults():
    """Test that environment variable defaults are shown in help text."""
    print("Running test_help_shows_env_defaults...", end=" ")
    
    # Set environment variables
    os.environ["TEST_HOME"] = "/home/testuser"
    os.environ["TEST_USER"] = "testuser"
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        script_content = """#!/bin/bash
echo "Home: $TEST_HOME"
echo "User: $TEST_USER"
echo "Name: $NAME"
"""
        script = write_temp_script(tmp_path, script_content)
        
        # Capture output
        from io import StringIO
        import contextlib
        
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = captured_output = StringIO()
        sys.stderr = captured_error = StringIO()
        
        exit_code = None  # Initialize exit_code
        
        try:
            # This should exit with SystemExit
            try:
                cli.main([str(script), "--help"])
            except SystemExit as e:
                exit_code = e.code
            
            output = captured_output.getvalue()
            error = captured_error.getvalue()
            
            # Restore stdout/stderr
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            
            # Check results
            assert exit_code == 0, f"Expected exit code 0, got {exit_code}"
            assert "(default from env: /home/testuser)" in output, f"Expected default value for TEST_HOME in output:\n{output}"
            assert "(default from env: testuser)" in output, f"Expected default value for TEST_USER in output:\n{output}"
            assert "--name" in output, f"Expected --name in output:\n{output}"
            
            print("PASSED")
        except Exception as e:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            print(f"FAILED: {e}")
            return False
        finally:
            # Clean up env vars
            del os.environ["TEST_HOME"]
            del os.environ["TEST_USER"]
    
    return True


def test_implicit_run():
    """Test implicit run without 'run' subcommand."""
    print("Running test_implicit_run...", end=" ")
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        script_content = """#!/bin/bash
echo "Hello $NAME"
"""
        script = write_temp_script(tmp_path, script_content)
        
        # Use subprocess to avoid stdout capture issues
        result = subprocess.run(
            [sys.executable, "-m", "argorator.cli", str(script), "--name", "Bob"],
            cwd=os.path.join(os.path.dirname(__file__), "src"),
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0 and "Hello Bob" in result.stdout:
            print("PASSED")
            return True
        else:
            print(f"FAILED: rc={result.returncode}, stdout={result.stdout}, stderr={result.stderr}")
            return False


def main():
    """Run all tests."""
    print("Running tests without pytest...\n")
    
    tests = [
        test_compile_injects_assignments,
        test_help_shows_env_defaults,
        test_implicit_run,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1
    
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
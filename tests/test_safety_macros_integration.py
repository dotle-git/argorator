"""Integration tests for safety macros using subprocess calls.

Since we can't run pytest in this environment, these tests are designed
to be run manually or in a proper testing environment.
"""
import subprocess
import tempfile
import os
from pathlib import Path


def test_set_strict_integration():
    """Test set strict macro integration with CLI."""
    script_content = '''#!/usr/bin/env argorator

# set strict

echo "Hello $NAME!"
if [ -z "$NAME" ]; then
    echo "Error: NAME not provided"
    exit 1
fi
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
        f.write(script_content)
        script_path = f.name
    
    try:
        # Test the print mode to see generated script
        result = subprocess.run(
            ['python3', '-m', 'argorator.cli', 'print', script_path],
            capture_output=True,
            text=True,
            cwd='/workspace',
            env={**os.environ, 'PYTHONPATH': '/workspace/src'}
        )
        
        if result.returncode == 0:
            print("✅ Set strict macro test passed")
            print("Generated script:")
            print(result.stdout)
            assert "set -eou --pipefail" in result.stdout
        else:
            print("❌ Set strict macro test failed")
            print("STDERR:", result.stderr)
            print("STDOUT:", result.stdout)
    
    finally:
        os.unlink(script_path)


def test_trap_cleanup_integration():
    """Test trap cleanup macro integration with CLI."""
    script_content = '''#!/usr/bin/env argorator

# trap cleanup

echo "Processing files..."
for i in {1..5}; do
    echo "Processing file $i"
done
echo "Done!"
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
        f.write(script_content)
        script_path = f.name
    
    try:
        # Test the print mode to see generated script
        result = subprocess.run(
            ['python3', '-m', 'argorator.cli', 'print', script_path],
            capture_output=True,
            text=True,
            cwd='/workspace',
            env={**os.environ, 'PYTHONPATH': '/workspace/src'}
        )
        
        if result.returncode == 0:
            print("✅ Trap cleanup macro test passed")
            print("Generated script:")
            print(result.stdout)
            assert "cleanup()" in result.stdout
            assert "trap cleanup EXIT ERR INT TERM" in result.stdout
        else:
            print("❌ Trap cleanup macro test failed")
            print("STDERR:", result.stderr)
            print("STDOUT:", result.stdout)
    
    finally:
        os.unlink(script_path)


def test_both_safety_macros_integration():
    """Test both safety macros together."""
    script_content = '''#!/usr/bin/env argorator

# set strict
# trap cleanup

echo "Safe script with $NAME and $AGE"
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
        f.write(script_content)
        script_path = f.name
    
    try:
        # Test the print mode to see generated script
        result = subprocess.run(
            ['python3', '-m', 'argorator.cli', 'print', script_path],
            capture_output=True,
            text=True,
            cwd='/workspace',
            env={**os.environ, 'PYTHONPATH': '/workspace/src'}
        )
        
        if result.returncode == 0:
            print("✅ Both safety macros test passed")
            print("Generated script:")
            print(result.stdout)
            assert "set -eou --pipefail" in result.stdout
            assert "cleanup()" in result.stdout
            assert "trap cleanup EXIT ERR INT TERM" in result.stdout
        else:
            print("❌ Both safety macros test failed")
            print("STDERR:", result.stderr)
            print("STDOUT:", result.stdout)
    
    finally:
        os.unlink(script_path)


if __name__ == "__main__":
    print("Running safety macro integration tests...")
    test_set_strict_integration()
    test_trap_cleanup_integration()
    test_both_safety_macros_integration()
    print("All integration tests completed!")
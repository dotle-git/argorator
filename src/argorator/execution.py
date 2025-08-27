"""Script execution module for running transformed shell scripts.

This module handles the execution of compiled shell scripts with proper
argument passing and shell detection using the decorator pattern.
"""
import subprocess
from pathlib import Path

from .contexts import ExecuteContext
from .registry import executor


@executor(order=10)
def execute_script(context: ExecuteContext) -> None:
    """Execute the compiled script with shell and positional arguments."""
    cmd = list(context.shell_cmd) + ["-s", "--"] + context.positional_values
    process = subprocess.Popen(cmd, stdin=subprocess.PIPE, text=True)
    assert process.stdin is not None
    process.stdin.write(context.compiled_script)
    process.stdin.close()
    context.exit_code = process.wait()


def validate_script_path(script_arg: str) -> Path:
    """Validate and normalize a script path.
    
    Args:
        script_arg: Script path argument from command line
        
    Returns:
        Validated and resolved Path object
        
    Raises:
        FileNotFoundError: If script doesn't exist or isn't a file
    """
    script_path = Path(script_arg).expanduser()
    try:
        script_path = script_path.resolve(strict=False)
    except Exception:
        # Fallback to the provided path if resolution fails (e.g., permissions)
        pass
    
    if not script_path.exists() or not script_path.is_file():
        raise FileNotFoundError(f"Script not found: {script_path}")
    
    return script_path
"""Script execution module for running transformed shell scripts.

This module handles the execution of compiled shell scripts with proper
argument passing and shell detection.
"""
import subprocess
from pathlib import Path
from typing import List


class ScriptExecutor:
    """Executes shell scripts with proper shell detection and argument handling."""
    
    @staticmethod
    def run_script_with_args(shell_cmd: List[str], script_text: str, positional_args: List[str]) -> int:
        """Execute the provided script text with a shell, passing positional args.

        Runs the shell with -s -- to read the script from stdin. Returns the exit code.
        """
        cmd = list(shell_cmd) + ["-s", "--"] + positional_args
        process = subprocess.Popen(cmd, stdin=subprocess.PIPE, text=True)
        assert process.stdin is not None
        process.stdin.write(script_text)
        process.stdin.close()
        return process.wait()


class FileHandler:
    """Handles file operations for script processing."""
    
    @staticmethod
    def read_text_file(file_path: Path) -> str:
        """Read and return the file's content as UTF-8 text.

        Args:
            file_path: Path to the file

        Returns:
            Entire file content as a string
        """
        with file_path.open("r", encoding="utf-8") as f:
            return f.read()
    
    @staticmethod
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
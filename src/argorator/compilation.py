"""Script compilation steps that transform shell scripts.

This module contains compilers that modify shell scripts by injecting
variable assignments, transforming to echo mode, or generating export lines.
"""
import re
import shlex
from typing import Dict, List


class ScriptCompiler:
    """Compiles shell scripts by injecting variable assignments and transformations."""
    
    @staticmethod
    def inject_variable_assignments(script_text: str, assignments: Dict[str, str]) -> str:
        """Insert shell assignments for provided variables at the top of the script.

        Assignments are added after the shebang if present; values are shell-quoted.
        """
        lines = script_text.splitlines()
        injection_lines = ["# argorator: injected variable definitions"]
        for name in sorted(assignments.keys()):
            value = assignments[name]
            injection_lines.append(f"{name}={shlex.quote(value)}")
        injection_block = "\n".join(injection_lines) + "\n"
        
        if lines and lines[0].startswith("#!"):
            return (lines[0] + "\n" + injection_block + "\n".join(lines[1:]) + 
                   ("\n" if script_text.endswith("\n") else ""))
        return injection_block + script_text

    @staticmethod
    def transform_script_to_echo_mode(script_text: str) -> str:
        """Transform the provided script so each executable line is echoed instead of run.

        Rules:
        - Preserve shebang if present
        - Preserve the argorator injection block and assignments so variables expand in echoes
        - For other non-empty, non-comment lines, output: echo "<line>" with quotes-escaped
        - Wrap the entire original line in double quotes to neutralize pipes and operators
        """
        lines = script_text.splitlines()
        result_lines: List[str] = []

        idx = 0
        # Preserve shebang line
        if lines and lines[0].startswith("#!"):
            result_lines.append(lines[0])
            idx = 1

        # Preserve argorator injection block if present
        # Look for the marker comment and include following assignment lines (until a blank line break or non-assignment)
        if idx < len(lines) and lines[idx].startswith("# argorator: injected variable definitions"):
            result_lines.append(lines[idx])
            idx += 1
            while idx < len(lines):
                line = lines[idx]
                # Keep variable assignment lines (NAME=...)
                if re.match(r"^\s*[A-Za-z_][A-Za-z0-9_]*=", line):
                    result_lines.append(line)
                    idx += 1
                    continue
                break

        # Process the rest: echo each non-empty, non-comment line
        while idx < len(lines):
            line = lines[idx]
            # Preserve exact blank lines
            if line.strip() == "":
                result_lines.append(line)
                idx += 1
                continue
            # Keep pure comment lines as-is (not echoed)
            if line.lstrip().startswith("#"):
                result_lines.append(line)
                idx += 1
                continue
            # Escape backslashes and double quotes so we can wrap with double quotes.
            escaped = line.replace("\\", "\\\\").replace('"', '\\"')
            result_lines.append(f'echo "{escaped}"')
            idx += 1

        # Ensure trailing newline behavior matches input
        return "\n".join(result_lines) + ("\n" if script_text.endswith("\n") else "")

    @staticmethod
    def generate_export_lines(assignments: Dict[str, str]) -> str:
        """Return shell lines exporting the provided assignments.

        Format: export VAR='value'
        """
        lines = []
        for name in sorted(assignments.keys()):
            value = assignments[name]
            lines.append(f"export {name}={shlex.quote(value)}")
        return "\n".join(lines)


class ArgumentProcessor:
    """Processes parsed arguments to prepare variable assignments."""
    
    @staticmethod
    def collect_variable_assignments(
        dyn_ns, 
        undefined_vars: List[str], 
        env_vars: Dict[str, str]
    ) -> Dict[str, str]:
        """Collect resolved variable assignments from parsed arguments.
        
        Args:
            dyn_ns: Namespace from argparse containing parsed arguments
            undefined_vars: List of undefined variable names
            env_vars: Dict of environment variable names to values
            
        Returns:
            Dict mapping variable names to their resolved string values
        """
        assignments: Dict[str, str] = {}
        
        # Process undefined variables (required args)
        for name in undefined_vars:
            value = getattr(dyn_ns, name, None)
            if value is None:
                raise ValueError(f"Missing required --{name}")
            # Convert boolean values to lowercase string for shell compatibility
            if isinstance(value, bool):
                assignments[name] = "true" if value else "false"
            else:
                assignments[name] = str(value)
        
        # Process environment variables (optional args with defaults)
        for name, env_value in env_vars.items():
            value = getattr(dyn_ns, name, env_value)
            # Convert boolean values to lowercase string for shell compatibility
            if isinstance(value, bool):
                assignments[name] = "true" if value else "false"
            else:
                assignments[name] = str(value)
        
        return assignments
    
    @staticmethod
    def collect_positional_values(dyn_ns, positional_indices, varargs) -> List[str]:
        """Collect positional argument values from parsed arguments.
        
        Args:
            dyn_ns: Namespace from argparse containing parsed arguments
            positional_indices: Set of positional indices used in script
            varargs: Whether script uses varargs ($@ or $*)
            
        Returns:
            List of positional argument values as strings
        """
        positional_values: List[str] = []
        
        for index in sorted(positional_indices):
            attr = f"ARG{index}"
            value = getattr(dyn_ns, attr, None)
            if value is None:
                raise ValueError(f"Missing positional argument ${index}")
            positional_values.append(str(value))
        
        if varargs:
            positional_values.extend([str(v) for v in getattr(dyn_ns, "ARGS", [])])
        
        return positional_values
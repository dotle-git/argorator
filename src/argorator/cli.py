"""Argorator CLI: expose shell script variables and positionals as CLI arguments.

This tool parses a shell script to discover variable/positional usage, builds a
matching argparse interface for undefined/environment-backed variables, and then
either injects definitions and executes, prints the modified script, or prints
export lines.
"""
import argparse
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple

from .annotations import parse_arg_annotations
from .models import ArgumentAnnotation


SPECIAL_VARS: Set[str] = {"@", "*", "#", "?", "$", "!", "0"}


def read_text_file(file_path: Path) -> str:
	"""Read and return the file's content as UTF-8 text.

	Args:
		file_path: Path to the file

	Returns:
		Entire file content as a string
	"""
	with file_path.open("r", encoding="utf-8") as f:
		return f.read()


def detect_shell_interpreter(script_text: str) -> List[str]:
	"""Detect the shell interpreter command for the script.

	Honors a shebang if present, normalizing to a common shell path. Defaults to
	bash when a shebang is not detected.

	Args:
		script_text: The full script content

	Returns:
		A list suitable for subprocess (e.g. ["/bin/bash"])
	"""
	first_line = script_text.splitlines()[0] if script_text else ""
	if first_line.startswith("#!"):
		shebang = first_line[2:].strip()
		# Normalize common shells
		if "bash" in shebang:
			return ["/bin/bash"]
		if re.search(r"\b(sh|dash)\b", shebang):
			return ["/bin/sh"]
		if "zsh" in shebang:
			return ["/bin/zsh"]
		if "ksh" in shebang:
			return ["/bin/ksh"]
	# Default
	return ["/bin/bash"]


def parse_defined_variables(script_text: str) -> Set[str]:
	"""Extract variable names that are assigned within the script.

	Matches plain assignments and common declaration forms like export/local/
	declare/readonly at the start of a line.
	"""
	assignment_pattern = re.compile(r"^\s*(?:export\s+|local\s+|declare(?:\s+-[a-zA-Z]+)?\s+|readonly\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=", re.MULTILINE)
	return set(assignment_pattern.findall(script_text))


def parse_variable_usages(script_text: str) -> Set[str]:
	"""Find variable names referenced by $VAR or ${VAR...} syntax.

	Special shell parameters (e.g., $@, $1) are excluded; see SPECIAL_VARS.
	"""
	brace_pattern = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)[^}]*\}")
	simple_pattern = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*)")
	candidates: Set[str] = set()
	candidates.update(brace_pattern.findall(script_text))
	candidates.update(simple_pattern.findall(script_text))
	return {name for name in candidates if name and name not in SPECIAL_VARS}


def parse_positional_usages(script_text: str) -> Tuple[Set[int], bool]:
	"""Detect positional parameter usage and varargs references in the script.

	Returns a tuple of (set of numeric positions used, varargs_flag) where
	varargs_flag is True if $@ or $* appears in the script.
	"""
	digit_pattern = re.compile(r"\$([1-9][0-9]*)")
	varargs_pattern = re.compile(r"\$(?:@|\*)")
	indices = {int(m) for m in digit_pattern.findall(script_text)}
	varargs = bool(varargs_pattern.search(script_text))
	return indices, varargs


def determine_variables(script_text: str) -> Tuple[Set[str], Dict[str, Optional[str]], Dict[str, str]]:
	"""Classify used variables into defined, undefined, and environment-backed.

	Args:
		script_text: The script content to analyze

	Returns:
		(defined_vars, undefined_vars, env_vars)
		- defined_vars: variables assigned within the script
		- undefined_vars: mapping of missing variable names -> None
		- env_vars: mapping of variable names -> current environment default
	"""
	defined_vars = parse_defined_variables(script_text)
	used_vars = parse_variable_usages(script_text)
	undefined_or_env = used_vars - defined_vars
	env_vars: Dict[str, str] = {}
	undefined_vars: Dict[str, Optional[str]] = {}
	for name in sorted(undefined_or_env):
		if name in os.environ:
			env_vars[name] = os.environ[name]
		else:
			undefined_vars[name] = None
	return defined_vars, undefined_vars, env_vars


def build_dynamic_arg_parser(
	undefined_vars: Sequence[str], 
	env_vars: Dict[str, str], 
	positional_indices: Set[int], 
	varargs: bool,
	annotations: Optional[Dict[str, ArgumentAnnotation]] = None
) -> argparse.ArgumentParser:
	"""Construct an argparse parser for script-specific variables and positionals.

	- Undefined variables become required options: --var (lowercase)
	- Env-backed variables become optional with defaults from the environment
	- Numeric positional references ($1, $2, ...) become positionals ARG1, ARG2, ...
	- Varargs ($@ or $*) collects remaining args via an ARGS positional with nargs='*'
	- Annotations from comments provide type information and help text
	"""
	if annotations is None:
		annotations = {}
	
	parser = argparse.ArgumentParser(add_help=True)
	
	# Helper function to get type converter
	def get_type_converter(type_str: str):
		if type_str == 'int':
			return int
		elif type_str == 'float':
			return float
		else:  # str, string or choice
			return str
	
	# Options for variables
	for name in undefined_vars:
		annotation = annotations.get(name, ArgumentAnnotation())
		
		# Build argument names
		arg_names = [f"--{name.lower()}"]
		if annotation.alias:
			arg_names.insert(0, annotation.alias)  # Put alias first
		
		kwargs = {
			'dest': name,
		}
		
		# Handle boolean type specially
		if annotation.type == 'bool':
			# Determine default boolean value
			if annotation.default is not None:
				default_bool = annotation.default.lower() in ('true', '1', 'yes', 'y')
			else:
				default_bool = False  # Default to False for required booleans
			
			if default_bool:
				# Default is True, so flag should store_false
				kwargs['action'] = 'store_false'
				kwargs['default'] = True
				if annotation.help:
					kwargs['help'] = f"{annotation.help} (default: true)"
				else:
					kwargs['help'] = "(default: true)"
			else:
				# Default is False, so flag should store_true
				kwargs['action'] = 'store_true'
				kwargs['default'] = False
				if annotation.help:
					kwargs['help'] = f"{annotation.help} (default: false)"
				else:
					kwargs['help'] = "(default: false)"
			
			# Boolean flags are never required (they have implicit defaults)
			kwargs['required'] = False
		else:
			# Non-boolean types
			kwargs['type'] = get_type_converter(annotation.type)
			
			# If annotation provides a default, make it optional
			if annotation.default is not None:
				kwargs['default'] = get_type_converter(annotation.type)(annotation.default)
				kwargs['required'] = False
				if annotation.help:
					kwargs['help'] = f"{annotation.help} (default: {annotation.default})"
				else:
					kwargs['help'] = f"(default: {annotation.default})"
			else:
				kwargs['required'] = True
				if annotation.help:
					kwargs['help'] = annotation.help
			
			if annotation.choices:
				kwargs['choices'] = annotation.choices
		
		parser.add_argument(*arg_names, **kwargs)
		
	for name, value in env_vars.items():
		annotation = annotations.get(name, ArgumentAnnotation())
		
		# Build argument names
		arg_names = [f"--{name.lower()}"]
		if annotation.alias:
			arg_names.insert(0, annotation.alias)  # Put alias first
		
		# Use annotation default if provided, otherwise use env value
		default_value = annotation.default if annotation.default is not None else value
		
		kwargs = {
			'dest': name,
			'required': False,
		}
		
		# Handle boolean type specially
		if annotation.type == 'bool':
			# Determine default boolean value
			if annotation.default is not None:
				default_bool = annotation.default.lower() in ('true', '1', 'yes', 'y')
			else:
				default_bool = value.lower() in ('true', '1', 'yes', 'y')
			
			if default_bool:
				# Default is True, so flag should store_false
				kwargs['action'] = 'store_false'
				kwargs['default'] = True
				help_parts = []
				if annotation.help:
					help_parts.append(annotation.help)
				if annotation.default is not None:
					help_parts.append("(default: true)")
				else:
					help_parts.append(f"(default from env: {value})")
				kwargs['help'] = ' '.join(help_parts)
			else:
				# Default is False, so flag should store_true
				kwargs['action'] = 'store_true'
				kwargs['default'] = False
				help_parts = []
				if annotation.help:
					help_parts.append(annotation.help)
				if annotation.default is not None:
					help_parts.append("(default: false)")
				else:
					help_parts.append(f"(default from env: {value})")
				kwargs['help'] = ' '.join(help_parts)
		else:
			# Non-boolean types
			kwargs['type'] = get_type_converter(annotation.type)
			kwargs['default'] = get_type_converter(annotation.type)(default_value)
			
			# Build help text with default value info
			help_parts = []
			if annotation.help:
				help_parts.append(annotation.help)
			if annotation.default is not None:
				help_parts.append(f"(default: {annotation.default})")
			else:
				help_parts.append(f"(default from env: {value})")
			kwargs['help'] = ' '.join(help_parts)
			
			if annotation.choices:
				kwargs['choices'] = annotation.choices
		
		parser.add_argument(*arg_names, **kwargs)
		
	# Positional arguments
	for index in sorted(positional_indices):
		parser.add_argument(f"ARG{index}")
	if varargs:
		parser.add_argument("ARGS", nargs="*")
	return parser


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
		return lines[0] + "\n" + injection_block + "\n".join(lines[1:]) + ("\n" if script_text.endswith("\n") else "")
	return injection_block + script_text


def generate_export_lines(assignments: Dict[str, str]) -> str:
	"""Return shell lines exporting the provided assignments.

	Format: export VAR='value'
	"""
	lines = []
	for name in sorted(assignments.keys()):
		value = assignments[name]
		lines.append(f"export {name}={shlex.quote(value)}")
	return "\n".join(lines)


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


def build_top_level_parser() -> argparse.ArgumentParser:
	"""Build the top-level argparse parser with run/compile/export subcommands."""
	parser = argparse.ArgumentParser(prog="argorator", description="Execute or compile shell scripts with CLI-exposed variables")
	subparsers = parser.add_subparsers(dest="subcmd")
	# run
	run_parser = subparsers.add_parser("run", help="Run script (default)")
	run_parser.add_argument("script", help="Path to the shell script")
	# compile
	compile_parser = subparsers.add_parser("compile", help="Print modified script")
	compile_parser.add_argument("script", help="Path to the shell script")
	# export
	export_parser = subparsers.add_parser("export", help="Print export lines")
	export_parser.add_argument("script", help="Path to the shell script")
	return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
	"""Program entry point.

	Top-level flow:
	1) Decide whether a subcommand (run/compile/export) is given
	2) Otherwise, treat invocation as implicit `run <script> ...`
	3) Parse script to discover variables/positionals and build a dynamic parser
	4) Execute command: run/compile/export
	"""
	argv = list(argv) if argv is not None else sys.argv[1:]
	# If first token is a known subcommand, parse with subparsers; otherwise treat as implicit run
	subcommands = {"run", "compile", "export"}
	if argv and argv[0] in subcommands:
		parser = build_top_level_parser()
		ns, unknown = parser.parse_known_args(argv)
		command = ns.subcmd or "run"
		script_arg: Optional[str] = getattr(ns, "script", None)
		rest_args: List[str] = unknown
		if script_arg is None:
			print("error: script path is required", file=sys.stderr)
			return 2
	else:
		# Implicit run path: use a minimal parser to capture script and remainder
		implicit = argparse.ArgumentParser(prog="argorator", add_help=True, description="Execute or compile shell scripts with CLI-exposed variables")
		implicit.add_argument("script", help="Path to the shell script")
		implicit.add_argument("rest", nargs=argparse.REMAINDER, help=argparse.SUPPRESS)
		try:
			in_ns = implicit.parse_args(argv)
		except SystemExit as exc:
			return int(exc.code)
		command = "run"
		script_arg = in_ns.script
		rest_args = list(in_ns.rest or [])
	# Validate and normalize script path
	script_path = Path(script_arg).expanduser()
	try:
		script_path = script_path.resolve(strict=False)
	except Exception:
		# Fallback to the provided path if resolution fails (e.g., permissions)
		pass
	if not script_path.exists() or not script_path.is_file():
		print(f"error: script not found: {script_path}", file=sys.stderr)
		return 2
	script_text = read_text_file(script_path)
	# Parse script
	defined_vars, undefined_vars_map, env_vars = determine_variables(script_text)
	positional_indices, varargs = parse_positional_usages(script_text)
	annotations = parse_arg_annotations(script_text)
	# Build dynamic parser
	undefined_names = sorted(undefined_vars_map.keys())
	dyn_parser = build_dynamic_arg_parser(undefined_names, env_vars, positional_indices, varargs, annotations)
	try:
		dyn_ns = dyn_parser.parse_args(rest_args)
	except SystemExit as exc:
		return int(exc.code)
	# Collect resolved variable assignments
	assignments: Dict[str, str] = {}
	for name in undefined_names:
		value = getattr(dyn_ns, name, None)
		if value is None:
			print(f"error: missing required --{name}", file=sys.stderr)
			return 1
		# Convert boolean values to lowercase string for shell compatibility
		if isinstance(value, bool):
			assignments[name] = "true" if value else "false"
		else:
			assignments[name] = str(value)
	for name, env_value in env_vars.items():
		value = getattr(dyn_ns, name, env_value)
		# Convert boolean values to lowercase string for shell compatibility
		if isinstance(value, bool):
			assignments[name] = "true" if value else "false"
		else:
			assignments[name] = str(value)
	# Collect positional args for shell invocation
	positional_values: List[str] = []
	for index in sorted(positional_indices):
		attr = f"ARG{index}"
		value = getattr(dyn_ns, attr, None)
		if value is None:
			print(f"error: missing positional argument ${index}", file=sys.stderr)
			return 2
		positional_values.append(str(value))
	if varargs:
		positional_values.extend([str(v) for v in getattr(dyn_ns, "ARGS", [])])
	# Prepare outputs per command
	if command == "export":
		print(generate_export_lines(assignments))
		return 0
	modified_text = inject_variable_assignments(script_text, assignments)
	if command == "compile":
		print(modified_text, end="" if modified_text.endswith("\n") else "\n")
		return 0
	# run
	shell_cmd = detect_shell_interpreter(script_text)
	return run_script_with_args(shell_cmd, modified_text, positional_values)


if __name__ == "__main__":
	sys.exit(main())
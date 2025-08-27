"""Argorator CLI: expose shell script variables and positionals as CLI arguments.

This tool parses a shell script to discover variable/positional usage, builds a
matching argparse interface for undefined/environment-backed variables, and then
either injects definitions and executes, prints the modified script, or prints
export lines.

This module provides the main entry point and maintains backward compatibility
while delegating the actual work to the new pipeline architecture.
"""
import sys
from typing import Optional, Sequence

from .pipeline import Pipeline


def main(argv: Optional[Sequence[str]] = None) -> int:
	"""Program entry point.

	Pipeline flow:
	1) Parse command line to determine execution mode
	2) Run script analyzers to extract information from the bash script
	3) Run transformers to build argparse parser according to the collected information
	4) Parse arguments to get actual values
	5) Run compilation steps to transform the script
	6) Run the transformed script or output results
	"""
	pipeline = Pipeline()
	command = pipeline.parse_command_line(argv)
	return pipeline.run(command)


if __name__ == "__main__":
	sys.exit(main())
from pathlib import Path

from argorator import cli
from argorator.analyzers import parse_variable_usages


def write_script(tmp_path: Path, name: str, content: str) -> Path:
	path = tmp_path / name
	path.write_text(content, encoding="utf-8")
	path.chmod(0o755)
	return path


def test_parameter_expansion_detects_variable_usage():
	text = "echo ${NAME:-guest}\n"
	used = parse_variable_usages(text)
	assert "NAME" in used


def test_array_assignment_is_treated_as_defined_and_runs(tmp_path: Path):
	script = write_script(
		tmp_path,
		"array.sh",
		"""#!/bin/bash
	arr=(one two three)

echo "first=${arr[0]}"

echo "all=${arr[@]}"
	""",
	)
	# Should not require any options; runs as-is
	rc = cli.main(["run", str(script)])
	assert rc == 0


def test_here_doc_unquoted_expands_and_runs(tmp_path: Path):
	script = write_script(
		tmp_path,
		"heredoc.sh",
		"""#!/bin/bash
cat <<EOF
Hello $NAME
EOF
	""",
	)
	rc = cli.main(["run", str(script), "--name", "World"])  # required by dynamic parser
	assert rc == 0


def test_here_doc_quoted_present_but_we_still_accept_option(tmp_path: Path):
	script = write_script(
		tmp_path,
		"heredoc_quoted.sh",
		"""#!/bin/bash
cat <<'EOF'
Hello $NAME
EOF
	""",
	)
	# Our parser will detect NAME and require it; passing makes it run successfully
	rc = cli.main(["run", str(script), "--name", "Ignored"])  # expansion won't occur because it's quoted
	assert rc == 0
## Argorator

Execute or compile shell scripts with CLI-exposed variables.

[![PyPI](https://img.shields.io/pypi/v/argorator.svg)](https://pypi.org/project/argorator/)
[![Python Versions](https://img.shields.io/pypi/pyversions/argorator.svg)](https://pypi.org/project/argorator/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

### Why Argorator?

- **Turn shell variables into CLI flags**: `$VAR` becomes `--var`. Undefined variables are required, env-backed variables are optional with defaults.
- **Respect positionals**: `$1`, `$2`, … become `ARG1`, `ARG2`, …; `$@`/`$*` collects the rest.
- **Three modes**: run the script, print a compiled script with injected definitions, or print `export VAR=...` lines.
- **Shebang-friendly**: `#!/usr/bin/env argorator` lets scripts self-document required inputs.
- **Shell-aware**: honors shebangs for `bash`, `sh/dash`, `zsh`, `ksh` (defaults to `bash`).

### Installation

```bash
pip install argorator
```

### Requirements

- **Python**: 3.9+
- **OS**: Unix-like (Linux, macOS, WSL)

## Quick start

```bash
# script.sh
#!/bin/bash
echo "Hello, $NAME!"
```

```bash
# Provide required variable via flag (lowercased)
argorator script.sh --name Alice
# Hello, Alice!
```

## CLI overview

You can run directly or use explicit subcommands:

```bash
argorator <script> [--var value ...] [ARG1 ARG2 ...]
argorator run <script> [--var value ...] [ARG1 ARG2 ...]
argorator compile <script> [--var value ...]
argorator export <script> [--var value ...]
```

- **Undefined variables** in the script become **required** flags: `--var` (lowercased; maps to original `$VAR`).
- **Environment-backed variables** become **optional** flags with defaults from your environment.
- **Positionals** `$1`, `$2`, … map to `ARG1`, `ARG2`, … and are required when referenced.
- **Varargs** `$@`/`$*` collects remaining arguments as additional positionals after the numbered ones.

### Shebang usage

```bash
# deploy.sh
#!/usr/bin/env argorator

echo "Deploying $APP_NAME to $ENVIRONMENT"
echo "Version: ${VERSION:-latest}"
```

```bash
chmod +x deploy.sh
./deploy.sh --app_name myapp --environment staging
```

## Examples

### Required variables become flags

```bash
# script.sh
#!/bin/bash
echo "Hello, $NAME!"
echo "You are $AGE years old."
```

```bash
argorator script.sh --name Alice --age 25
# Hello, Alice!
# You are 25 years old.
```

### Env-backed variables are optional

```bash
# script.sh
#!/bin/bash
echo "Home: $HOME"
echo "User: $USER"
echo "Custom: $CUSTOM_VAR"
```

```bash
# Override env values if desired
argorator script.sh --home /custom/home --custom_var test
# Home: /custom/home
# User: [your current user]
# Custom: test

# Or use existing environment
argorator script.sh --custom_var test
# Home: /home/youruser
# User: youruser
# Custom: test
```

### Positionals and varargs

```bash
# greet.sh
#!/bin/bash
echo "Hello $1!"
echo "Your message: $2"
```

```bash
argorator greet.sh World "Have a nice day"
# Hello World!
# Your message: Have a nice day
```

```bash
# process.sh
#!/bin/bash
echo "Command: $1"
echo "Options: $2"
shift 2
echo "Files to process: $@"
```

```bash
argorator process.sh build --verbose file1.txt file2.txt file3.txt
# Command: build
# Options: --verbose
# Files to process: file1.txt file2.txt file3.txt
```

### Compile mode (print modified script)

```bash
# template.sh
#!/bin/bash
SERVICE_NAME=$SERVICE_NAME
PORT=${PORT:-8080}
echo "Starting $SERVICE_NAME on port $PORT"
```

```bash
argorator compile template.sh --service_name api-server --port 3000
# Prints a script with injected assignments at the top
# ... which you can redirect to a new file if desired
argorator compile template.sh --service_name api-server > start-api.sh
```

### Export mode (print exports)

```bash
argorator export config.sh --db_host localhost --db_port 5432 --api_key secret123
# export DB_HOST='localhost'
# export DB_PORT='5432'
# export API_KEY='secret123'

# Convenient for shell sessions
eval "$(argorator export config.sh --db_host localhost --db_port 5432 --api_key secret123)"
```

## How it works

- Parses your script to find:
  - **Defined variables**: assignments in the script (e.g., `FOO=bar`, `export FOO=bar`)
  - **Referenced variables**: `$VAR` or `${VAR}` usages
  - **Positionals**: `$1`, `$2`, … and varargs `$@`/`$*`
- Builds a dynamic `argparse` interface:
  - Missing variables → required `--var` options
  - Env variables present → optional `--var` with defaults
  - `$1`, `$2`, … → positional arguments `ARG1`, `ARG2`, …
- Injects resolved assignments at the top of the script (after the shebang if present), using safe shell quoting.
- Executes using the detected shell, or prints the compiled script/exports.

## Limitations and notes

- Parsing is regex-based and targets common patterns. Extremely dynamic shell constructs may not be detected.
- Option names are lowercased (e.g., `$API_KEY` → `--api_key`) but values are assigned back to the original variable names.
- Scripts can still reassign variables after injection, which may affect behavior.
- Shebang detection normalizes common shells; default is `/bin/bash`.
- Windows is not supported natively; use WSL.

## Troubleshooting

- **Missing required variable**: Provide it as a flag, e.g., `--var value`.
- **Missing positional `$N`**: Supply the corresponding positional (e.g., `ARG1` for `$1`).
- **Script not found**: Ensure the path exists; relative and absolute paths are supported.

## Development

```bash
# Clone and install in editable mode
python -m pip install --upgrade pip
pip install -e .

# Run tests
pytest -q
```

## Contributing

Issues and pull requests are welcome. Please include reproduction steps and tests when possible.

## License

MIT — see [LICENSE](./LICENSE).

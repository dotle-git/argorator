# Argorator

Execute or compile shell scripts with CLI-exposed variables.

Usage:

```bash
argorator <script> [--var value ...] [ARG1 ARG2 ...]
argorator compile <script> [--var value ...] [ARG1 ARG2 ...]
argorator export <script> [--var value ...] [ARG1 ARG2 ...]
```

- Undefined variables in the script become required `--var` options (lowercase).
- Variables found only in the environment become optional `--var` options with defaults.
- `$1`, `$2`, ... become positional arguments; `$@` or `$*` collect remaining args.
- `compile` prints the modified script; `export` prints `export VAR=...` lines; default runs the script.

Shebang:

```sh
#!/usr/bin/env argorator
# your script follows
```

## Examples

### Basic Usage: Undefined Variables

When your script uses undefined variables, they become required CLI options:

```bash
# script.sh
#!/bin/bash
echo "Hello, $NAME!"
echo "You are $AGE years old."
```

```bash
# Running the script
$ argorator script.sh --name Alice --age 25
Hello, Alice!
You are 25 years old.

# Missing required variable shows error
$ argorator script.sh --name Alice
error: the following arguments are required: --age
```

### Environment Variables with Defaults

Variables that exist in your environment become optional CLI options:

```bash
# script.sh
#!/bin/bash
echo "Home: $HOME"
echo "User: $USER"
echo "Custom: $CUSTOM_VAR"
```

```bash
# Environment variables can be overridden
$ argorator script.sh --home /custom/home --custom_var test
Home: /custom/home
User: [your current user]
Custom: test

# Or use existing environment values
$ argorator script.sh --custom_var test
Home: /home/youruser
User: youruser
Custom: test
```

### Positional Arguments

Scripts using `$1`, `$2`, etc. accept positional arguments:

```bash
# greet.sh
#!/bin/bash
echo "Hello $1!"
echo "Your message: $2"
```

```bash
$ argorator greet.sh World "Have a nice day"
Hello World!
Your message: Have a nice day
```

### Variable Arguments with $@ or $*

Use `$@` or `$*` to collect remaining arguments:

```bash
# process.sh
#!/bin/bash
echo "Command: $1"
echo "Options: $2"
shift 2
echo "Files to process: $@"
```

```bash
$ argorator process.sh build --verbose file1.txt file2.txt file3.txt
Command: build
Options: --verbose
Files to process: file1.txt file2.txt file3.txt
```

### Compile Mode

Generate the modified script without executing it:

```bash
# template.sh
#!/bin/bash
SERVICE_NAME=$SERVICE_NAME
PORT=${PORT:-8080}
echo "Starting $SERVICE_NAME on port $PORT"
```

```bash
# Compile with injected variables
$ argorator compile template.sh --service_name api-server --port 3000
#!/bin/bash
SERVICE_NAME="api-server"
PORT="3000"
SERVICE_NAME=$SERVICE_NAME
PORT=${PORT:-8080}
echo "Starting $SERVICE_NAME on port $PORT"

# Redirect to create a new script
$ argorator compile template.sh --service_name api-server > start-api.sh
```

### Export Mode

Generate export statements for use in shell environments:

```bash
# config.sh
#!/bin/bash
echo "Database: $DB_HOST:$DB_PORT"
echo "API Key: $API_KEY"
```

```bash
# Generate exports
$ argorator export config.sh --db_host localhost --db_port 5432 --api_key secret123
export DB_HOST="localhost"
export DB_PORT="5432"
export API_KEY="secret123"

# Use in shell session
$ eval "$(argorator export config.sh --db_host localhost --db_port 5432 --api_key secret123)"
$ echo $DB_HOST
localhost
```

### Using Argorator as Shebang

Make scripts directly executable with argument handling:

```bash
# deploy.sh
#!/usr/bin/env argorator
# Script to deploy an application

echo "Deploying $APP_NAME to $ENVIRONMENT"
echo "Version: ${VERSION:-latest}"

if [ "$ENVIRONMENT" = "production" ]; then
    echo "🚨 Production deployment - be careful!"
fi

echo "Deploying to server: $1"
shift
echo "Additional options: $@"
```

```bash
# Make executable and run directly
$ chmod +x deploy.sh
$ ./deploy.sh --app_name myapp --environment staging server1.example.com --dry-run --verbose
Deploying myapp to staging
Version: latest
Deploying to server: server1.example.com
Additional options: --dry-run --verbose
```

### Complex Example: Build Script

```bash
# build.sh
#!/usr/bin/env argorator
# Build script with multiple options

set -e  # Exit on error

echo "Building $PROJECT_NAME"
echo "Build type: ${BUILD_TYPE:-release}"
echo "Output directory: ${OUTPUT_DIR:-./build}"

# Use positional arguments for build targets
if [ $# -eq 0 ]; then
    TARGETS="all"
else
    TARGETS="$@"
fi

echo "Building targets: $TARGETS"

# Conditional logic based on variables
if [ "$CLEAN" = "true" ]; then
    echo "Cleaning build directory..."
    rm -rf "${OUTPUT_DIR:-./build}"
fi

if [ "$VERBOSE" = "true" ]; then
    echo "Verbose mode enabled"
    set -x
fi

echo "Build complete!"
```

```bash
# Various ways to use the build script
$ ./build.sh --project_name myproject
$ ./build.sh --project_name myproject --build_type debug --clean true
$ ./build.sh --project_name myproject --verbose true lib tests docs
$ ./build.sh --project_name myproject --output_dir /tmp/build all
```

## Installation

```bash
pip install argorator
```

## Requirements

- Python 3.8+
- Unix-like operating system (Linux, macOS, WSL)

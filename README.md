# Argorator

Execute or compile shell scripts with CLI-exposed variables and arguments.

Argorator automatically analyzes your shell scripts and converts undefined variables into CLI options, making your scripts more user-friendly and self-documenting.

## Installation

```bash
pip install argorator
```

## Quick Start

Given a simple shell script:

```bash
#!/bin/bash
# greet.sh
echo "Hello $NAME, welcome to $PROJECT!"
echo "You provided: $@"
```

Argorator automatically creates CLI options for undefined variables:

```bash
argorator greet.sh --NAME "Alice" --PROJECT "MyApp" arg1 arg2
# Output:
# Hello Alice, welcome to MyApp!
# You provided: arg1 arg2
```

## Usage

```bash
argorator <script> [--VAR value ...] [ARG1 ARG2 ...]
argorator compile <script> [--VAR value ...] [ARG1 ARG2 ...]
argorator export <script> [--VAR value ...] [ARG1 ARG2 ...]
```

### How It Works

- **Undefined variables** in the script become **required** `--VAR` options
- **Environment variables** become **optional** `--VAR` options with current values as defaults
- **Positional parameters** (`$1`, `$2`, etc.) become positional CLI arguments
- **Variable arguments** (`$@` or `$*`) collect remaining arguments

## Examples

### Basic Variable Substitution

**Script:** `hello.sh`
```bash
#!/bin/bash
echo "Hello $NAME from $LOCATION!"
```

**Usage:**
```bash
argorator hello.sh --NAME "Bob" --LOCATION "Tokyo"
# Output: Hello Bob from Tokyo!
```

### Environment Variables with Defaults

**Script:** `deploy.sh`
```bash
#!/bin/bash
echo "Deploying to $ENVIRONMENT"
echo "Using config: $CONFIG_FILE"
echo "Debug mode: $DEBUG"
```

**Setup:**
```bash
export ENVIRONMENT="staging"
export CONFIG_FILE="config.yml"
```

**Usage:**
```bash
# Uses environment defaults
argorator deploy.sh --DEBUG "false"

# Override environment variables
argorator deploy.sh --ENVIRONMENT "production" --CONFIG_FILE "prod.yml" --DEBUG "true"
```

### Positional Arguments

**Script:** `backup.sh`
```bash
#!/bin/bash
SOURCE_DIR="$1"
DEST_DIR="$2"
echo "Backing up $SOURCE_DIR to $DEST_DIR"
echo "Additional options: $@"
```

**Usage:**
```bash
argorator backup.sh /home/user /backup/location --exclude "*.tmp" --verbose
# $1 = /home/user
# $2 = /backup/location  
# $@ = /home/user /backup/location --exclude *.tmp --verbose
```

### Mixed Variables and Arguments

**Script:** `process.sh`
```bash
#!/bin/bash
echo "Processing $1 with $MODE mode"
echo "Output directory: $OUTPUT_DIR"
echo "Remaining files: ${@:2}"
```

**Usage:**
```bash
argorator process.sh --MODE "fast" --OUTPUT_DIR "/tmp/output" input.txt file1.txt file2.txt
# $1 = input.txt
# $MODE = fast
# $OUTPUT_DIR = /tmp/output
# ${@:2} = file1.txt file2.txt
```

### Advanced Parameter Expansion

**Script:** `configure.sh`
```bash
#!/bin/bash
echo "Database: ${DB_HOST:-localhost}"
echo "Port: ${DB_PORT:-5432}"
echo "User: ${DB_USER:?Database user required}"
```

**Usage:**
```bash
# DB_USER is required due to :? expansion
argorator configure.sh --DB_USER "admin" --DB_HOST "db.example.com"
```

## Commands

### `run` (default)

Executes the script with variable substitution:

```bash
argorator run script.sh --VAR value
# or simply:
argorator script.sh --VAR value
```

### `compile`

Prints the modified script with variables injected:

```bash
argorator compile script.sh --NAME "Alice" --COUNT "5"
```

**Output:**
```bash
#!/bin/bash
NAME='Alice'
COUNT='5'
echo "Hello $NAME, count is $COUNT"
```

### `export`

Prints export statements for use in other contexts:

```bash
argorator export script.sh --API_KEY "secret123" --TIMEOUT "30"
```

**Output:**
```bash
export API_KEY='secret123'
export TIMEOUT='30'
```

Use with eval:
```bash
eval "$(argorator export config.sh --ENV prod --DEBUG false)"
```

## Shebang Support

Make your scripts directly executable with argorator:

```bash
#!/usr/bin/env argorator
echo "Hello $NAME!"
echo "Processing: $@"
```

```bash
chmod +x script.sh
./script.sh --NAME "World" file1 file2
```

## Complex Examples

### Build Script

**Script:** `build.sh`
```bash
#!/usr/bin/env argorator
TARGET="${1:-all}"
BUILD_TYPE="${BUILD_TYPE:-release}"
PARALLEL_JOBS="${PARALLEL_JOBS:-$(nproc)}"

echo "Building target: $TARGET"
echo "Build type: $BUILD_TYPE"
echo "Parallel jobs: $PARALLEL_JOBS"

make -j$PARALLEL_JOBS $BUILD_TYPE $TARGET
```

**Usage:**
```bash
./build.sh                                    # Uses defaults
./build.sh server                             # TARGET=server
./build.sh --BUILD_TYPE debug                 # Debug build
./build.sh --PARALLEL_JOBS 4 client          # 4 jobs, build client
```

### Docker Deployment

**Script:** `docker-deploy.sh`
```bash
#!/usr/bin/env argorator
IMAGE_TAG="${1:?Image tag required}"
REGISTRY="${REGISTRY:-docker.io}"
NAMESPACE="${NAMESPACE:-default}"
REPLICAS="${REPLICAS:-3}"

echo "Deploying $REGISTRY/$IMAGE_TAG to $NAMESPACE"
echo "Replica count: $REPLICAS"
echo "Extra args: ${@:2}"

kubectl create deployment app \
  --image="$REGISTRY/$IMAGE_TAG" \
  --replicas="$REPLICAS" \
  --namespace="$NAMESPACE" \
  "${@:2}"
```

**Usage:**
```bash
./docker-deploy.sh myapp:v1.0                           # Basic deployment
./docker-deploy.sh --REGISTRY gcr.io myapp:v2.0         # Custom registry  
./docker-deploy.sh --NAMESPACE prod --REPLICAS 5 myapp:v1.0 --port 8080
```

### Data Processing Pipeline

**Script:** `process-data.sh`
```bash
#!/usr/bin/env argorator
INPUT_FORMAT="${INPUT_FORMAT:-csv}"
OUTPUT_FORMAT="${OUTPUT_FORMAT:-json}"
BATCH_SIZE="${BATCH_SIZE:-1000}"
PARALLEL="${PARALLEL:-true}"

for file in "$@"; do
    echo "Processing $file: $INPUT_FORMAT -> $OUTPUT_FORMAT (batch: $BATCH_SIZE)"
    if [ "$PARALLEL" = "true" ]; then
        process_file_parallel "$file" &
    else
        process_file_sequential "$file"
    fi
done

if [ "$PARALLEL" = "true" ]; then
    wait
fi
```

**Usage:**
```bash
./process-data.sh data1.csv data2.csv data3.csv
./process-data.sh --INPUT_FORMAT xml --OUTPUT_FORMAT csv --PARALLEL false *.xml
./process-data.sh --BATCH_SIZE 500 large_dataset.csv
```

## Tips

1. **Help Generation**: Argorator automatically generates help text:
   ```bash
   argorator script.sh --help
   ```

2. **Variable Discovery**: Use `compile` to see what variables argorator detected:
   ```bash
   argorator compile script.sh --help
   ```

3. **Environment Integration**: Set common variables in your environment:
   ```bash
   export PROJECT_ROOT="/opt/myproject"
   export LOG_LEVEL="info"
   ```

4. **Error Handling**: Scripts exit with proper codes when required variables are missing.

## License

MIT License

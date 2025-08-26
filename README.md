# Argorator 🎯

[![PyPI version](https://badge.fury.io/py/argorator.svg)](https://badge.fury.io/py/argorator)
[![Python](https://img.shields.io/pypi/pyversions/argorator.svg)](https://pypi.org/project/argorator/)
[![Tests](https://github.com/dotle/argorator/actions/workflows/tests.yml/badge.svg)](https://github.com/dotle/argorator/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Transform any shell script into a fully-featured command-line tool with zero effort.**

Argorator automatically converts your shell scripts' variables and positional arguments into a proper CLI interface with `--help`, argument validation, and type conversion - all without modifying your original script.

## 🚀 Why Argorator?

Have you ever wanted to:
- Share a shell script with your team but worried about hardcoded values?
- Convert environment variables into command-line options automatically?
- Add proper CLI argument parsing to a script without rewriting it in Python?
- Make your deployment scripts more user-friendly with `--help` documentation?

Argorator does all of this automatically by analyzing your script and creating a proper CLI interface on the fly.

## 📦 Installation

```bash
pip install argorator
```

Or with [pipx](https://pypa.github.com/pipx/) (recommended for global installation):

```bash
pipx install argorator
```

## 🎯 Quick Start

Take any shell script with variables:

```bash
# deploy.sh
#!/bin/bash
echo "Deploying $SERVICE to $ENVIRONMENT"
echo "Version: $VERSION"
```

Run it with Argorator:

```bash
$ argorator deploy.sh --help
usage: argorator deploy.sh [-h] --service SERVICE --environment ENVIRONMENT --version VERSION

optional arguments:
  -h, --help            show this help message and exit
  --service SERVICE
  --environment ENVIRONMENT
  --version VERSION

$ argorator deploy.sh --service api --environment prod --version v1.2.3
Deploying api to prod
Version: v1.2.3
```

That's it! No modifications needed to your script.

## 📚 Core Features

### 1. Automatic Variable Detection

Undefined variables in your script become **required** CLI arguments:

```bash
# greet.sh
echo "Hello, $NAME!"
echo "You are $AGE years old"
```

```bash
$ argorator greet.sh --name Alice --age 30
Hello, Alice!
You are 30 years old
```

### 2. Environment Variable Defaults

Variables that exist in your environment become **optional** arguments with defaults:

```bash
# show-env.sh
echo "Home: $HOME"
echo "User: $USER"
echo "Custom: $CUSTOM_VAR"
```

```bash
$ argorator show-env.sh --custom-var "test"
Home: /home/yourusername
User: yourusername
Custom: test

# Override environment variables
$ argorator show-env.sh --home /tmp --user root --custom-var "test"
Home: /tmp
User: root
Custom: test
```

### 3. Positional Arguments

Scripts using `$1`, `$2`, etc. automatically accept positional arguments:

```bash
# backup.sh
#!/bin/bash
echo "Backing up $1 to $2"
echo "Compression: ${COMPRESSION:-gzip}"
```

```bash
$ argorator backup.sh /data /backups --compression bzip2
Backing up /data to /backups
Compression: bzip2
```

### 4. Variable Arguments with `$@`

Collect multiple arguments using `$@` or `$*`:

```bash
# process-files.sh
#!/bin/bash
COMMAND=$1
shift
echo "Running $COMMAND on files:"
for file in "$@"; do
    echo "  - $file"
done
```

```bash
$ argorator process-files.sh compress doc1.txt doc2.txt doc3.txt
Running compress on files:
  - doc1.txt
  - doc2.txt
  - doc3.txt
```

## 🛠️ Advanced Usage

### Compile Mode

Generate a standalone script with variables pre-filled:

```bash
# template.sh
#!/bin/bash
SERVICE=${SERVICE}
PORT=${PORT:-8080}
echo "Starting $SERVICE on port $PORT"
```

```bash
# Generate a script with hardcoded values
$ argorator compile template.sh --service nginx --port 80 > start-nginx.sh
$ cat start-nginx.sh
#!/bin/bash
SERVICE="nginx"
PORT="80"
SERVICE=${SERVICE}
PORT=${PORT:-8080}
echo "Starting $SERVICE on port $PORT"

$ bash start-nginx.sh
Starting nginx on port 80
```

### Export Mode

Generate shell export statements for sourcing:

```bash
# config.sh
DB_HOST=${DB_HOST}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME}
```

```bash
# Generate exports
$ argorator export config.sh --db-host localhost --db-name myapp
export DB_HOST="localhost"
export DB_PORT="5432"
export DB_NAME="myapp"

# Use in your shell
$ eval "$(argorator export config.sh --db-host localhost --db-name myapp)"
$ echo $DB_HOST
localhost
```

### Direct Execution with Shebang

Make your scripts directly executable:

```bash
#!/usr/bin/env argorator
# deploy-service.sh

set -e

echo "🚀 Deploying $SERVICE_NAME to $ENVIRONMENT"
echo "📦 Version: ${VERSION:-latest}"
echo "🔄 Replicas: ${REPLICAS:-3}"

if [ "$DRY_RUN" = "true" ]; then
    echo "🔍 DRY RUN - No changes will be made"
fi

# Your deployment logic here
echo "✅ Deployment complete!"
```

```bash
$ chmod +x deploy-service.sh
$ ./deploy-service.sh --help
$ ./deploy-service.sh --service-name api --environment staging --dry-run true
```

## 🎨 Real-World Examples

### Configuration Management

```bash
#!/usr/bin/env argorator
# configure-app.sh

cat > config.json <<EOF
{
  "database": {
    "host": "$DB_HOST",
    "port": ${DB_PORT:-5432},
    "name": "$DB_NAME",
    "user": "$DB_USER"
  },
  "redis": {
    "host": "${REDIS_HOST:-localhost}",
    "port": ${REDIS_PORT:-6379}
  },
  "debug": ${DEBUG:-false}
}
EOF

echo "✅ Configuration written to config.json"
```

### Docker Compose Wrapper

```bash
#!/usr/bin/env argorator
# docker-deploy.sh

# Set defaults
COMPOSE_FILE=${COMPOSE_FILE:-docker-compose.yml}
PROJECT_NAME=${PROJECT_NAME:-myproject}

# Handle commands
case "$1" in
    up)
        docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME up -d $2
        ;;
    down)
        docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME down
        ;;
    logs)
        shift
        docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME logs -f "$@"
        ;;
    *)
        echo "Usage: $0 {up|down|logs} [services...]"
        exit 1
        ;;
esac
```

### Build Script with Multiple Targets

```bash
#!/usr/bin/env argorator
# build.sh

set -e

echo "🔨 Building $PROJECT"
echo "📁 Output: ${OUTPUT_DIR:-./dist}"
echo "🎯 Type: ${BUILD_TYPE:-release}"

# Clean if requested
if [ "$CLEAN" = "true" ]; then
    echo "🧹 Cleaning previous build..."
    rm -rf "${OUTPUT_DIR:-./dist}"
fi

# Build targets
if [ $# -eq 0 ]; then
    TARGETS="all"
else
    TARGETS="$@"
fi

for target in $TARGETS; do
    echo "📦 Building target: $target"
    # Your build logic here
done

echo "✅ Build complete!"
```

## 🔧 How It Works

1. **Script Analysis**: Argorator parses your shell script using pattern matching to identify:
   - Undefined variables (`$VAR` or `${VAR}`)
   - Environment variables with defaults (`${VAR:-default}`)
   - Positional parameters (`$1`, `$2`, `$@`, etc.)

2. **CLI Generation**: Creates an argparse interface with:
   - Required arguments for undefined variables
   - Optional arguments for environment variables
   - Positional arguments for `$1`, `$2`, etc.
   - Variadic arguments for `$@` or `$*`

3. **Script Execution**: Injects variable definitions at the top of your script and executes it with the proper shell interpreter.

## 📋 Requirements

- Python 3.9+
- Unix-like operating system (Linux, macOS, WSL)
- Bash or compatible shell

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Clone the repository
git clone https://github.com/dotle/argorator.git
cd argorator

# Install in development mode
pip install -e .

# Run tests
pytest
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

Argorator was inspired by the need to make shell scripts more shareable and user-friendly without requiring rewrites in other languages.

---

**Made with ❤️ by the Argorator team**

*Transform your scripts, empower your workflows.*

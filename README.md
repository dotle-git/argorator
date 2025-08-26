<div align="center">

# 🚀 Argorator

**Transform shell scripts into CLI applications with automatic argument parsing**

[![PyPI version](https://badge.fury.io/py/argorator.svg)](https://badge.fury.io/py/argorator)
[![Python Support](https://img.shields.io/pypi/pyversions/argorator.svg)](https://pypi.org/project/argorator/)
[![Tests](https://github.com/dotle/argorator/workflows/tests/badge.svg)](https://github.com/dotle/argorator/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

*Automatically expose shell script variables and positional arguments as CLI options*

[Installation](#installation) •
[Quick Start](#quick-start) •
[Examples](#examples) •
[Documentation](#documentation) •
[Contributing](#contributing)

</div>

---

## 🎯 What is Argorator?

Argorator bridges the gap between shell scripts and modern CLI applications. It automatically analyzes your bash scripts to discover variables and positional arguments, then generates a beautiful command-line interface with proper help text, validation, and argument parsing.

**Transform this:**
```bash
#!/bin/bash
echo "Deploying $APP_NAME to $ENVIRONMENT"
echo "Version: ${VERSION:-latest}"
echo "Server: $1"
```

**Into this:**
```bash
$ ./deploy.sh --help
usage: deploy.sh [-h] [--app_name APP_NAME] [--environment ENVIRONMENT] [--version VERSION] server

positional arguments:
  server                    Server argument

optional arguments:
  -h, --help               show this help message and exit
  --app_name APP_NAME      APP_NAME variable (required)
  --environment ENVIRONMENT ENVIRONMENT variable (required)
  --version VERSION        VERSION variable (default: latest)
```

## ✨ Key Features

- 🔍 **Automatic Discovery**: Scans scripts for undefined variables and positional arguments
- 🛠️ **Smart Defaults**: Uses environment variables as defaults when available
- 📋 **Multiple Modes**: Execute, compile, or export variable definitions
- 🎨 **Clean Interface**: Generates professional CLI help and error messages
- 🔗 **Shebang Support**: Use as interpreter for direct script execution
- ⚡ **Zero Dependencies**: Pure Python implementation with no external requirements
- 🐍 **Python 3.9+**: Modern Python support across all major versions

## 🚀 Installation

### From PyPI (Recommended)

```bash
pip install argorator
```

### From Source

```bash
git clone https://github.com/dotle/argorator.git
cd argorator
pip install -e .
```

### Verify Installation

```bash
argorator --help
```

## ⚡ Quick Start

### 1. Basic Script with Variables

Create a script with undefined variables:

```bash
# greet.sh
#!/bin/bash
echo "Hello, $NAME!"
echo "You are $AGE years old."
```

Run with Argorator:

```bash
$ argorator greet.sh --name Alice --age 25
Hello, Alice!
You are 25 years old.
```

### 2. Use as Shebang Interpreter

Make your scripts directly executable:

```bash
#!/usr/bin/env argorator
echo "Deploying $APP_NAME to $ENVIRONMENT"
echo "Server: $1"
```

```bash
$ chmod +x deploy.sh
$ ./deploy.sh --app_name myapp --environment prod server1.example.com
Deploying myapp to prod
Server: server1.example.com
```

### 3. Generate Reusable Scripts

Compile scripts with injected variables:

```bash
$ argorator compile template.sh --service_name api > start-api.sh
$ chmod +x start-api.sh
$ ./start-api.sh  # Ready to run!
```

## 📖 Examples

### Environment Variables with Defaults

Variables that exist in your environment become optional with defaults:

```bash
# config.sh
#!/bin/bash
echo "Home: $HOME"
echo "User: $USER"  
echo "Database: $DB_HOST"
```

```bash
$ argorator config.sh --db_host localhost
Home: /home/alice
User: alice
Database: localhost
```

### Positional Arguments

Scripts using `$1`, `$2`, etc. accept positional arguments:

```bash
# process.sh
#!/bin/bash
echo "Command: $1"
echo "Target: $2"
echo "Files: $@"
```

```bash
$ argorator process.sh build production file1.txt file2.txt
Command: build
Target: production
Files: build production file1.txt file2.txt
```

### Complex Build Script

```bash
#!/usr/bin/env argorator
# build.sh - Production build script

set -euo pipefail

echo "🏗️  Building $PROJECT_NAME"
echo "📝 Build type: ${BUILD_TYPE:-release}"
echo "📁 Output: ${OUTPUT_DIR:-./dist}"

# Clean if requested
if [ "${CLEAN:-false}" = "true" ]; then
    echo "🧹 Cleaning previous builds..."
    rm -rf "${OUTPUT_DIR:-./dist}"
fi

# Build targets (use remaining args or default to 'all')
TARGETS="${*:-all}"
echo "🎯 Targets: $TARGETS"

if [ "${VERBOSE:-false}" = "true" ]; then
    set -x
fi

echo "✅ Build complete!"
```

```bash
$ ./build.sh --project_name myapp --build_type debug --clean true --verbose true frontend backend
🏗️  Building myapp  
📝 Build type: debug
📁 Output: ./dist
🧹 Cleaning previous builds...
🎯 Targets: frontend backend
+ echo '✅ Build complete!'
✅ Build complete!
```

### Export Mode for Environment Setup

Generate export statements for shell environments:

```bash
$ argorator export config.sh --api_key secret --db_port 5432
export API_KEY="secret"
export DB_PORT="5432"

# Use in your shell
$ eval "$(argorator export config.sh --api_key secret --db_port 5432)"
```

### CI/CD Pipeline Integration

```bash
#!/usr/bin/env argorator
# deploy.sh - Deployment script

echo "🚀 Deploying $SERVICE_NAME"
echo "🌍 Environment: $ENVIRONMENT" 
echo "🏷️  Version: ${VERSION:-latest}"

if [ "$ENVIRONMENT" = "production" ]; then
    echo "⚠️  Production deployment detected!"
    echo "🔍 Running pre-deployment checks..."
fi

echo "📡 Deploying to: $@"
```

```bash
# In your CI/CD pipeline
$ ./deploy.sh \
    --service_name api-gateway \
    --environment production \
    --version v2.1.0 \
    server1.prod.com server2.prod.com
```

## 📚 Documentation

### CLI Usage

```bash
argorator <script> [--var value ...] [ARG1 ARG2 ...]     # Execute script
argorator compile <script> [--var value ...] [ARG1 ...]  # Print modified script
argorator export <script> [--var value ...]              # Print export statements
```

### Variable Resolution

| Variable Type | Behavior | CLI Option | Required |
|---------------|----------|------------|----------|
| Undefined in script | Becomes required option | `--variable_name` | ✅ Yes |
| Set in environment | Becomes optional with default | `--variable_name` | ❌ No |
| Positional (`$1`, `$2`) | Positional argument | - | ✅ Yes |
| Variable args (`$@`, `$*`) | Remaining arguments | - | ❌ No |

### Advanced Features

- **Shell Detection**: Automatically detects interpreter from shebang
- **Error Handling**: Proper exit codes and error messages
- **Variable Injection**: Clean variable assignment at script start
- **Argument Validation**: Built-in validation for required parameters

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### Development Setup

```bash
# Clone the repository
git clone https://github.com/dotle/argorator.git
cd argorator

# Install in development mode
pip install -e .

# Install development dependencies
pip install pytest black flake8

# Run tests
pytest

# Format code
black src/ tests/
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=argorator

# Run specific test file
pytest tests/test_cli.py
```

### Project Structure

```
argorator/
├── src/argorator/          # Main package
│   ├── __init__.py        # Version info
│   └── cli.py             # CLI implementation
├── tests/                 # Test suite
├── .github/workflows/     # CI/CD configuration
└── pyproject.toml         # Project configuration
```

### Contribution Guidelines

1. 🍴 Fork the repository
2. 🌿 Create a feature branch (`git checkout -b feature/amazing-feature`)
3. ✅ Add tests for new functionality
4. 🧹 Ensure code passes linting (`black src/ tests/`)
5. ✅ Run the test suite (`pytest`)
6. 📝 Commit changes (`git commit -m 'Add amazing feature'`)
7. 📤 Push to branch (`git push origin feature/amazing-feature`)
8. 🔄 Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋‍♀️ Support

- 📖 **Documentation**: Check our [examples](#examples) and [documentation](#documentation)
- 🐛 **Bug Reports**: [Open an issue](https://github.com/dotle/argorator/issues)
- 💡 **Feature Requests**: [Start a discussion](https://github.com/dotle/argorator/discussions)
- 💬 **Questions**: Use [GitHub Discussions](https://github.com/dotle/argorator/discussions)

## 🎯 Roadmap

- [ ] 🔧 Configuration file support (`.argorator.yml`)
- [ ] 📝 Custom help text and descriptions
- [ ] 🎨 Theme support for CLI output
- [ ] 🔍 Advanced variable validation (types, ranges)
- [ ] 📦 Integration with package managers
- [ ] 🌐 Multi-shell support (zsh, fish)

---

<div align="center">

**Made with ❤️ for the shell scripting community**

[⭐ Star us on GitHub](https://github.com/dotle/argorator) • [🐛 Report Bug](https://github.com/dotle/argorator/issues) • [💡 Request Feature](https://github.com/dotle/argorator/issues)

</div>

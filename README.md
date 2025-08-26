# Argorator 🎯

[![PyPI version](https://badge.fury.io/py/argorator.svg)](https://badge.fury.io/py/argorator)
[![Python](https://img.shields.io/pypi/pyversions/argorator.svg)](https://pypi.org/project/argorator/)
[![Tests](https://github.com/dotle/argorator/actions/workflows/tests.yml/badge.svg)](https://github.com/dotle/argorator/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Transform any shell script into a fully-featured command-line tool with zero effort.**

Argorator automatically converts your shell scripts' variables and positional arguments into a proper CLI interface with `--help`, argument validation, and type conversion - all without modifying your original script.

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

## 🚀 Direct Execution with Shebang

Make your scripts directly executable:

```bash
#!/usr/bin/env argorator
# deploy-service.sh

echo "🚀 Deploying $SERVICE_NAME to $ENVIRONMENT"
echo "📦 Version: ${VERSION:-latest}"

if [ "$DRY_RUN" = "true" ]; then
    echo "🔍 DRY RUN - No changes will be made"
fi

echo "✅ Deployment complete!"
```

```bash
$ chmod +x deploy-service.sh
$ ./deploy-service.sh --help
usage: deploy-service.sh [-h] --service_name SERVICE_NAME --environment ENVIRONMENT [--version VERSION] [--dry_run DRY_RUN]

options:
  -h, --help            show this help message and exit
  --service_name SERVICE_NAME
  --environment ENVIRONMENT
  --version VERSION     (default from env: latest)
  --dry_run DRY_RUN

$ ./deploy-service.sh --service-name api --environment staging --dry-run true
🚀 Deploying api to staging
📦 Version: latest
🔍 DRY RUN - No changes will be made
✅ Deployment complete!
```

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
$ argorator show-env.sh --help
usage: argorator show-env.sh [-h] --custom_var CUSTOM_VAR [--home HOME] [--user USER]

options:
  -h, --help            show this help message and exit
  --custom_var CUSTOM_VAR
  --home HOME           (default from env: /home/yourusername)
  --user USER           (default from env: yourusername)

$ argorator show-env.sh --custom-var "test"
Home: /home/yourusername
User: yourusername
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
$ argorator backup.sh --help
usage: argorator backup.sh [-h] [--compression COMPRESSION] ARG1 ARG2

positional arguments:
  ARG1
  ARG2

options:
  -h, --help            show this help message and exit
  --compression COMPRESSION
                        (default from env: gzip)

$ argorator backup.sh /data /backups --compression bzip2
Backing up /data to /backups
Compression: bzip2
```

### 4. Variable Arguments with `$@`

Collect multiple arguments using `$@` or `$*`:

```bash
# process-files.sh
#!/bin/bash
echo "Processing files:"
for file in "$@"; do
    echo "  - $file"
done
```

```bash
$ argorator process-files.sh doc1.txt doc2.txt doc3.txt
Processing files:
  - doc1.txt
  - doc2.txt
  - doc3.txt
```

## 🛠️ Advanced Usage

### Compile Mode

Generate a standalone script with variables pre-filled:

```bash
$ argorator compile script.sh --var value > compiled.sh
```

### Export Mode

Generate shell export statements:

```bash
$ eval "$(argorator export script.sh --var value)"
```

## 🔧 How It Works

1. **Script Analysis**: Argorator parses your shell script to identify variables and positional arguments
2. **CLI Generation**: Creates an argparse interface with appropriate options
3. **Script Execution**: Injects variable definitions and runs your script

## 📋 Requirements

- Python 3.9+
- Unix-like operating system (Linux, macOS, WSL)
- Bash or compatible shell

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

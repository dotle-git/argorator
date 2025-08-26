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
$ ./deploy-service.sh --service-name api --environment staging --dry-run true
🚀 Deploying api to staging
📦 Version: latest
🔍 DRY RUN - No changes will be made
✅ Deployment complete!
```

## 📚 Core Features

### Automatic Variable Detection

Undefined variables become **required** CLI arguments, while environment variables become **optional** with defaults:

```bash
# backup.sh
#!/bin/bash
echo "Backing up $SOURCE to $DESTINATION"
echo "User: $USER"
echo "Compression: ${COMPRESSION:-gzip}"
```

```bash
$ argorator backup.sh --help
usage: argorator backup.sh [-h] --source SOURCE --destination DESTINATION [--user USER] [--compression COMPRESSION]

options:
  -h, --help            show this help message and exit
  --source SOURCE
  --destination DESTINATION
  --user USER           (default from env: yourusername)
  --compression COMPRESSION
                        (default from env: gzip)

$ argorator backup.sh --source /data --destination /backups --compression bzip2
Backing up /data to /backups
User: yourusername
Compression: bzip2
```

### Positional Arguments

Scripts using `$1`, `$2`, etc. automatically accept positional arguments:

```bash
# copy-files.sh
#!/bin/bash
echo "Copying $1 to $2"
echo "Options: ${OPTIONS:-none}"
```

```bash
$ argorator copy-files.sh source.txt dest.txt --options "-v -r"
Copying source.txt to dest.txt
Options: -v -r
```

### Variable Arguments

Collect multiple arguments using `$@`:

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

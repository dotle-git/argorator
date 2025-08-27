# Argorator 🎯

[![PyPI version](https://img.shields.io/pypi/v/argorator.svg)](https://pypi.org/project/argorator/)
[![Python](https://img.shields.io/pypi/pyversions/argorator.svg)](https://pypi.org/project/argorator/)
[![Tests](https://github.com/dotle-git/argorator/actions/workflows/tests.yml/badge.svg)](https://github.com/dotle-git/argorator/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Stop writing argument parsing in bash.**

Ever written a script that needs input? Argorator automatically creates command-line options for your script's variables. No need to change your script at all!

## Install

```bash
pip install argorator
```

## How to Use

### Step 1: Write a normal script

```bash
echo "Hello $NAME!"
echo "You are $AGE years old"
```

### Step 2: Run it with Argorator

```bash
argorator hello.sh --name John --age 25
```

Output:
```
Hello John!
You are 25 years old
```

### Get automatic help

```bash
argorator hello.sh --help
```

Output:
```
usage: hello.sh [-h] --name NAME --age AGE

options:
  -h, --help   show this help message and exit
  --name NAME
  --age AGE
```

That's it! Your script now has professional command-line options.

## Make Scripts Executable

Add this line to the top of your script:

```bash
#!/usr/bin/env argorator

echo "Hi $NAME!"
if [ "$LOUD" = "true" ]; then
    echo "NICE TO MEET YOU!"
fi
```

Make it executable and run it:

```bash
chmod +x greet.sh
./greet.sh --name Alice --loud true
```

Output:
```
Hi Alice!
NICE TO MEET YOU!
```

## What Argorator Does

### Variables become options

Any `$VARIABLE` in your script becomes a `--variable` option:

```bash
echo "Copying $SOURCE to $DEST"
```

Run it:
```bash
argorator backup.sh --source file.txt --dest backup.txt
```

### Environment variables are optional

If a variable exists in your environment, it becomes optional with a default:

```bash
echo "Current user: $USER"
echo "Home folder: $HOME"
```

Run it:
```bash
argorator show-user.sh --help
```

Shows:
```
--user USER     (default: your-username)
--home HOME     (default: /home/your-username)
```

### Use $1, $2 for ordered inputs

```bash
cp $1 $2
echo "Copied $1 to $2"
```

Run it:
```bash
argorator copy.sh file1.txt file2.txt
```

### Use $@ for multiple files

```bash
echo "Files:"
for file in "$@"; do
    echo "- $file"
done
```

Run it:
```bash
argorator list.sh doc1.txt doc2.txt doc3.txt
```

## 🔄 Iteration Macros: Python-Style Loops in Bash

**NEW!** Use simple comments to create powerful loops automatically.

### File Processing

Process every line in a file:

```bash
#!/usr/bin/env argorator

# LOGFILE (file): Input log file to analyze

# for line in $LOGFILE
echo "Processing: $line" | grep "ERROR"
```

Run it:
```bash
argorator analyze.sh --logfile /var/log/app.log
```

### Pattern Iteration

Process matching files:

```bash
#!/usr/bin/env argorator

# for image in *.jpg
    echo "Converting: $image"
    convert "$image" "thumbnails/${image%.jpg}_thumb.jpg"
```

### Delimited Data Processing

Handle CSV, paths, and custom separators:

```bash
#!/usr/bin/env argorator

# CSV_DATA (str): Comma-separated values  
# PATHS (str): Colon-separated paths

# for item in $CSV_DATA sep ,
    echo "Item: $item"

# for path in $PATHS separated by :
    echo "Path: $path"  

# for field in $DATA separated by "::"
    echo "Field: $field"
```

### Function-Based Processing

Use functions for complex processing:

```bash
#!/usr/bin/env argorator

# for file in *.log
analyze_log() {
    echo "=== Analyzing $1 ==="
    grep -c "ERROR" "$1"
    grep -c "WARN" "$1"  
}
```

Generated bash handles everything automatically:
- File line iteration (`while read`)
- Array splitting for delimited data  
- Proper quoting and error handling
- Function parameter passing

## Before and After

### Before: Manual argument parsing (painful!)

```bash
#!/bin/bash

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --name)
      NAME="$2"
      shift 2
      ;;
    --age)
      AGE="$2"
      shift 2
      ;;
    --help)
      echo "Usage: $0 --name NAME --age AGE"
      echo "  --name NAME    Your name"
      echo "  --age AGE      Your age"
      exit 0
      ;;
    *)
      echo "Unknown option $1"
      exit 1
      ;;
  esac
done

# Check required arguments
if [[ -z "$NAME" ]]; then
  echo "Error: --name is required"
  exit 1
fi

if [[ -z "$AGE" ]]; then
  echo "Error: --age is required"
  exit 1
fi

# Finally, your actual script
echo "Hello $NAME!"
echo "You are $AGE years old"
```

### After: With Argorator (simple!)

```bash
echo "Hello $NAME!"
echo "You are $AGE years old"
```

Run it:
```bash
argorator script.sh --name John --age 25
```

## Requirements

- Python 3.9 or newer
- Linux, macOS, or Windows with WSL
- Bash shell

## Contributing

Want to help improve Argorator?

1. Fork this repository
2. Make your changes
3. Submit a pull request

We welcome all contributions!

## License

MIT License - use it however you want!

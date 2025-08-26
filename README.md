# Argorator

A Python-based CLI program that takes shell scripts as input, parses their variable usage, and creates dynamic argument parsers before execution.

## Features

- **Variable Analysis**: Parses shell scripts to identify:
  - Undefined variables (become required arguments)
  - Environment variables (become optional arguments with defaults)
  - Positional parameters ($1, $2, etc.)
  - Variable arguments ($@, $*)

- **Dynamic Argument Parsing**: Creates `argparse` parsers based on script analysis

- **Multiple Execution Modes**:
  - `argorator <script> [args...]` - Execute the script with modifications
  - `argorator compile <script> [args...]` - Print the modified script content
  - `argorator export <script> [args...]` - Print variable exports for sourcing

- **Shebang Support**: Can be used as a shebang line for direct script execution

## Installation

### From Source (Recommended for Development)

1. Clone or download the repository
2. Install using pip:
```bash
pip install -e .
```

3. Or install from PyPI (when published):
```bash
pip install argorator
```

### Manual Installation

If you prefer not to install via pip, you can use the entry point script directly:
```bash
chmod +x argorator_entry_point.py
# Use ./argorator_entry_point.py instead of argorator command
```

## Usage Examples

### Basic Usage

Given a script `example.sh`:
```bash
#!/bin/bash
echo "Hello $NAME"
echo "Your age is $AGE"
echo "First argument: $1"
```

Run with argorator:
```bash
argorator example.sh --NAME "John" --AGE "25" "first_arg"
```

### View Help
```bash
argorator example.sh --help
```

### Compile Mode
View the modified script without execution:
```bash
argorator compile example.sh --NAME "John" --AGE "25" "first_arg"
```

### Export Mode
Generate export statements for use with original script:
```bash
argorator export example.sh --NAME "John" --AGE "25" "first_arg"
```

### Shebang Usage
Create a script with argorator as shebang:
```bash
#!/usr/local/bin/argorator
# or if using the entry point script directly:
#!/path/to/argorator_entry_point.py
echo "Processing: $FILENAME"
echo "Mode: $MODE"
```

Make it executable and run:
```bash
chmod +x script.sh
./script.sh --FILENAME "data.txt" --MODE "process"
```

## How It Works

1. **Parse Script**: Analyzes shell script to find variable usage patterns
2. **Classify Variables**: 
   - Variables not defined in script but exist in environment → optional with defaults
   - Variables not defined anywhere → required arguments
   - Positional parameters ($1, $2) → positional arguments
3. **Generate Parser**: Creates dynamic `argparse` parser based on analysis
4. **Modify Script**: Injects variable definitions at the top of the script
5. **Execute**: Runs the modified script through bash

## Variable Types Supported

- **Simple variables**: `$VAR`
- **Braced variables**: `${VAR}`
- **Positional parameters**: `$1`, `$2`, etc.
- **Variable arguments**: `$@`, `$*`
- **Environment variables**: Variables that exist in the current environment
- **Local definitions**: Variables defined within the script are detected and not made into arguments

## Package Structure

The project is organized as a proper Python package:

```
argorator/
├── argorator/
│   ├── __init__.py      # Package initialization
│   └── main.py          # Main functionality (refactored to use functions)
├── pyproject.toml       # Modern Python packaging configuration
├── setup.py             # Backward compatibility setup
├── MANIFEST.in          # Additional files to include in package
├── README.md            # This file
└── LICENSE              # MIT License
```

## Examples

See the included test scripts:
- `test_script1.sh` - Complex example with various variable types
- `test_script2.sh` - Simple example  
- `test_script3.sh` - Shebang usage example (legacy)
- `test_script_package.sh` - Package-based shebang example
- `argorator_entry_point.py` - Standalone entry point for manual installation

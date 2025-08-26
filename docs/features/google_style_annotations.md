---
layout: page
title: Google-Style Annotations
permalink: /docs/features/google_style_annotations/
---

# Argorator Google-Style Annotations

*Added in version 0.3.0*

Argorator supports Google docstring-style annotations in shell script comments to provide type information, help text, and default values for your script arguments.

## Basic Format

```bash
# VARIABLE_NAME (type): Description. Default: default_value
# VARIABLE_NAME (type) [alias: -x]: Description with short alias
```

## Examples

### Basic Annotations

```bash
#!/bin/bash
# NAME: Your name (no type = defaults to string)
# AGE (int): Your age in years
# EMAIL (str): Your email address

echo "Hello $NAME, age $AGE!"
echo "Email: $EMAIL"
```

### With Default Values

```bash
#!/bin/bash
# SERVICE (str): Service to deploy
# PORT (int): Port number. Default: 8080
# DEBUG (bool): Enable debug mode. Default: false

echo "Starting $SERVICE on port $PORT"
if [ "$DEBUG" = "true" ]; then
    echo "Debug mode enabled"
fi
```

### Boolean Flags

Boolean parameters are handled specially as flags (no value required):

```bash
#!/bin/bash
# VERBOSE (bool) [alias: -v]: Enable verbose output. Default: false
# QUIET (bool) [alias: -q]: Suppress output. Default: true

# Usage:
# script.sh -v          # Sets VERBOSE=true
# script.sh --verbose   # Sets VERBOSE=true
# script.sh -q          # Toggles QUIET to false (from default true)
```

**Boolean behavior:**
- Default `false`: Flag presence sets to `true` (uses `store_true`)
- Default `true`: Flag presence sets to `false` (uses `store_false`)
- No value needed after the flag

### Parameter Aliases

Add short aliases for convenience:

```bash
#!/bin/bash
# SERVICE (str) [alias: -s]: Service name
# PORT (int) [alias: -p]: Port number. Default: 8080
# VERBOSE (bool) [alias: -v]: Enable verbose mode. Default: false

# Usage:
# script.sh -s api -p 9000 -v
# script.sh --service api --port 9000 --verbose
```

### Choice Parameters

```bash
#!/bin/bash
# ENVIRONMENT (choice[dev, staging, prod]): Deployment environment
# LOG_LEVEL (choice[debug, info, warn, error]): Log level. Default: info

echo "Deploying to $ENVIRONMENT with log level $LOG_LEVEL"
```

## Supported Types

- `str` (or `string`) - String values (default if no type specified)
- `int` - Integer values
- `float` - Floating-point numbers  
- `bool` - Boolean flags (no value required)
- `choice[opt1, opt2, ...]` - String with restricted set of values

## Complete Example

```bash
#!/usr/bin/env argorator
#!/bin/bash
# Deploy script with comprehensive annotations

# SERVICE_NAME (str) [alias: -s]: Name of the service to deploy
# ENVIRONMENT (choice[dev, staging, prod]) [alias: -e]: Target deployment environment
# VERSION (str): Version tag to deploy. Default: latest
# REPLICAS (int) [alias: -r]: Number of replicas. Default: 3
# CPU_LIMIT (float): CPU limit per replica. Default: 0.5
# MEMORY_LIMIT (str): Memory limit per replica. Default: 512Mi
# DRY_RUN (bool) [alias: -n]: Perform a dry run. Default: false
# VERBOSE (bool) [alias: -v]: Enable verbose output. Default: false

echo "🚀 Deployment Configuration:"
echo "  Service: $SERVICE_NAME"
echo "  Environment: $ENVIRONMENT"
echo "  Version: $VERSION"
echo "  Replicas: $REPLICAS"
echo "  Resources: CPU=$CPU_LIMIT, Memory=$MEMORY_LIMIT"

if [ "$DRY_RUN" = "true" ]; then
    echo ""
    echo "🔍 DRY RUN MODE - No changes will be made"
fi

if [ "$VERBOSE" = "true" ]; then
    echo ""
    echo "Verbose: All parameters expanded..."
    set -x
fi

# Deployment logic here...
echo "✅ Deployment complete!"
```

## Running Annotated Scripts

```bash
# View generated help
$ argorator deploy.sh --help
usage: argorator deploy.sh [-h] -s SERVICE_NAME -e {dev,staging,prod}
                          [--version VERSION] [-r REPLICAS]
                          [--cpu_limit CPU_LIMIT] [--memory_limit MEMORY_LIMIT]
                          [-n] [-v]

options:
  -h, --help            show this help message and exit
  -s, --service_name SERVICE_NAME
                        Name of the service to deploy
  -e, --environment {dev,staging,prod}
                        Target deployment environment
  --version VERSION     Version tag to deploy (default: latest)
  -r, --replicas REPLICAS
                        Number of replicas (default: 3)
  --cpu_limit CPU_LIMIT
                        CPU limit per replica (default: 0.5)
  --memory_limit MEMORY_LIMIT
                        Memory limit per replica (default: 512Mi)
  -n, --dry_run         Perform a dry run (default: false)
  -v, --verbose         Enable verbose output (default: false)

# Run with minimal arguments (using defaults)
$ argorator deploy.sh -s api -e prod

# Run with all options using short aliases
$ argorator deploy.sh -s api -e prod -r 5 -n -v

# Mix short and long options
$ argorator deploy.sh --service-name api -e prod --version v2.0.1 -v
```

## Benefits

1. **Clean Syntax**: Google-style format is concise and readable
2. **Default Values**: Optional parameters with defaults reduce boilerplate
3. **Type Safety**: Automatic type conversion and validation
4. **Better Help**: Generated help includes descriptions and defaults
5. **Short Aliases**: Support for convenient short option names
6. **Boolean Flags**: Proper flag behavior without requiring values
7. **IDE Friendly**: Familiar format for developers
8. **Flexible**: Works with or without type annotations

## Tips

- Variable names should be in UPPERCASE (following shell conventions)
- Omit the type to default to string: `# VAR: Description`
- Default values make parameters optional
- Use `choice[...]` for parameters with fixed options
- Boolean flags don't need values: `-v` instead of `--verbose true`
- Aliases should start with a single dash: `[alias: -x]`
- The format is case-insensitive for types but uppercase is preferred for variable names
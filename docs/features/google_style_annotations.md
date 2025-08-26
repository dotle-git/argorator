# Argorator Google-Style Annotations

Argorator supports Google docstring-style annotations in shell script comments to provide type information, help text, and default values for your script arguments.

## Basic Format

```bash
# VARIABLE_NAME (type): Description. Default: default_value
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
- `bool` - Boolean values (accepts: true/false, 1/0, yes/no, y/n)
- `choice[opt1, opt2, ...]` - String with restricted set of values

## Complete Example

```bash
#!/usr/bin/env argorator
#!/bin/bash
# Deploy script with comprehensive annotations

# SERVICE_NAME (str): Name of the service to deploy
# ENVIRONMENT (choice[dev, staging, prod]): Target deployment environment
# VERSION (str): Version tag to deploy. Default: latest
# REPLICAS (int): Number of replicas. Default: 3
# CPU_LIMIT (float): CPU limit per replica. Default: 0.5
# MEMORY_LIMIT (str): Memory limit per replica. Default: 512Mi
# DRY_RUN (bool): Perform a dry run. Default: false
# VERBOSE (bool): Enable verbose output. Default: false

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
usage: argorator deploy.sh [-h] --service_name SERVICE_NAME 
                          --environment {dev,staging,prod}
                          [--version VERSION] [--replicas REPLICAS]
                          [--cpu_limit CPU_LIMIT] [--memory_limit MEMORY_LIMIT]
                          [--dry_run DRY_RUN] [--verbose VERBOSE]

options:
  -h, --help            show this help message and exit
  --service_name SERVICE_NAME
                        Name of the service to deploy
  --environment {dev,staging,prod}
                        Target deployment environment
  --version VERSION     Version tag to deploy (default: latest)
  --replicas REPLICAS   Number of replicas (default: 3)
  --cpu_limit CPU_LIMIT
                        CPU limit per replica (default: 0.5)
  --memory_limit MEMORY_LIMIT
                        Memory limit per replica (default: 512Mi)
  --dry_run DRY_RUN     Perform a dry run (default: false)
  --verbose VERBOSE     Enable verbose output (default: false)

# Run with minimal arguments (using defaults)
$ argorator deploy.sh --service-name api --environment prod

# Run with all options
$ argorator deploy.sh --service-name api --environment prod \
    --version v2.0.1 --replicas 5 --cpu-limit 1.0 \
    --memory-limit 1Gi --dry-run true --verbose true
```

## Benefits

1. **Clean Syntax**: Google-style format is concise and readable
2. **Default Values**: Optional parameters with defaults reduce boilerplate
3. **Type Safety**: Automatic type conversion and validation
4. **Better Help**: Generated help includes descriptions and defaults
5. **IDE Friendly**: Familiar format for developers
6. **Flexible**: Works with or without type annotations

## Tips

- Variable names should be in UPPERCASE (following shell conventions)
- Omit the type to default to string: `# VAR: Description`
- Default values make parameters optional
- Use `choice[...]` for parameters with fixed options
- Boolean parameters accept various formats (true/false, yes/no, 1/0)
- The format is case-insensitive for types but uppercase is preferred for variable names
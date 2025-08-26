# Argorator Features

This directory contains detailed documentation for Argorator's features.

## Available Features

### [Google-Style Annotations](google_style_annotations.md)

Add type information, help text, and default values to your shell script arguments using Google docstring-style comments.

```bash
# SERVICE_NAME (str): Name of the service to deploy
# PORT (int): Port number. Default: 8080
# DEBUG (bool): Enable debug mode. Default: false
```

- Type safety with automatic conversion
- Input validation for choices
- Default values for optional parameters
- Rich help text generation

### Core Features

Additional documentation for core features:

- **Variable Detection**: Automatically detects undefined variables in your scripts
- **Environment Defaults**: Uses environment variables as default values
- **Positional Arguments**: Supports `$1`, `$2`, etc. and `$@`
- **Multiple Execution Modes**: Run, compile, or export modes
- **Shebang Support**: Use `#!/usr/bin/env argorator` for direct execution

## Contributing

To add documentation for a new feature:

1. Create a new markdown file in this directory
2. Follow the existing documentation style
3. Include practical examples
4. Update this README with a link to your documentation

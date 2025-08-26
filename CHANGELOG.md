# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2024-01-XX

### Added
- **Type Hints Support**: Add type annotations to variables using special comments (`# @type VAR: type`)
  - Supported types: `int`, `float`, `bool`, `str`
  - Automatic validation and conversion of command-line arguments
  - Boolean values accept multiple formats: true/1/yes/y/on for true, false/0/no/n/off for false
- **Verbose/Debug Mode**: Add `-v` or `--verbose` flag to see detailed parsing information
  - Shows detected variables (defined, undefined, environment-backed)
  - Displays type hints found in the script
  - Logs argument parsing and variable assignments
  - Helps troubleshoot script parsing issues

### Changed
- Updated documentation with examples of new features

## [0.2.0] - Previous Release

### Added
- Initial release with core functionality
- Automatic variable detection from shell scripts
- Environment variable defaults
- Positional argument support
- Variable arguments with `$@` support
- Compile and export modes
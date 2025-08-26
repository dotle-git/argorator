---
layout: page
title: Changelog
permalink: /changelog/
---

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Argument groups and mutually exclusive groups support**
  - Group related arguments together for better help organization
  - Mutually exclusive groups ensure only one option from a set can be specified
  - **Natural language syntax**: `# group VAR1, VAR2 as GroupName` and `# one of VAR1, VAR2 as GroupName`
  - Auto-naming: Groups without explicit names get auto-generated names (Group1, Group2, etc.)
  - Validates that variables cannot be in multiple groups

### Changed
- Simplified group syntax - removed old bracket-based group annotations for cleaner, more intuitive natural language approach
- GitHub Pages documentation site with Jekyll
  - Main landing page with full project overview
  - Organized documentation structure in docs/ folder
  - Google-style annotations feature documentation

### Fixed
- Tests badge in README now points to correct repository (dotle-git/argorator)
- PyPI version badge switched to shields.io for better reliability and update frequency
  - Automated deployment via GitHub Actions
  - Local development setup with Gemfile
  - Modern Minima theme with syntax highlighting

## [0.3.0] - 2024-12-19

### Added
- Google-style docstring annotations for shell script arguments
  - Support for type annotations: `# VAR (type): Description`
  - Default values: `# VAR (type): Description. Default: value`
  - Parameter aliases: `# VAR (type) [alias: -x]: Description`
  - Choice parameters: `# VAR (choice[opt1, opt2]): Description`
- Proper boolean flag handling using store_true/store_false actions
  - Boolean arguments no longer require values (`-v` instead of `--verbose true`)
  - Flags with default true use store_false action
- Short aliases for all parameter types
- New `annotations.py` module for better code organization
- Pydantic models for argument annotations providing better type safety and validation
- `pydantic>=2.0` as a dependency

### Changed
- Boolean arguments now use flag syntax without values
- Refactored annotation parsing into separate module
- Updated documentation with comprehensive examples
- Argument annotations now use Pydantic `ArgumentAnnotation` model instead of plain dictionaries
- Removed separate CONTRIBUTING.md file - contributing guidelines are now in the main README

### Fixed
- Boolean values are properly converted to lowercase "true"/"false" for shell compatibility
- Alias validation now automatically prepends '-' if not present

### Removed
- Example scripts directory - examples are now in documentation
- Old :param style annotation tests (only Google-style is supported)

## [0.2.0] - Previous release

### Added
- Initial implementation of shell script variable detection
- Environment variable defaults
- Positional argument support
- Run, compile, and export modes
- Shebang support
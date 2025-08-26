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

### Changed
- Updated tagline to "stop writing argument parsing in bash"
- Added before/after example showing bash argument parsing complexity vs Argorator
- Moved before/after section lower in README for better flow
- Simplified README.md language and examples for new developers
- Removed file name comments from examples for cleaner code blocks
- Removed advanced usage and "how it works" sections
- Streamlined examples for better clarity and focus

### Added
- GitHub Pages documentation site with Jekyll
  - Main landing page with full project overview
  - Organized documentation structure in docs/ folder
  - Google-style annotations feature documentation
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
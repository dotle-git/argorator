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
- **NEW FEATURE**: Iteration macros for simplified bash loops using Python-style syntax
  - `# for iterator in source` comments transform lines or functions into bash loops
  - Supports file line iteration: `# for line in $FILE`
  - Supports pattern iteration: `# for file in *.txt`
  - Supports range iteration: `# for i in {1..10}`
  - Supports array iteration: `# for item in $ARRAY`
  - Function annotation: macros before function definitions generate loops that call the function
  - Parameter passing: `# for file in *.txt | with $OUTPUT_DIR` passes additional parameters
  - Uses parsy-based parser for accurate bash function detection and transformation
  - Integrates seamlessly with existing variable system and CLI argument parsing

### Changed
- **INTERNAL**: Refactored codebase to use decorator registration pattern with stage-specific Pydantic context models
  - Replaced static methods with module-level functions using decorator registration
  - **Created stage-specific context models with strict access controls**:
    - `AnalysisContext`: Can read script and write analysis results (no parser access)
    - `TransformContext`: Can read analysis results and create/modify parser (no compilation access)
    - `CompileContext`: Can read parser/args and write compilation results (no analysis modification)
    - `ExecuteContext`: Can read compilation results and write execution results (limited scope)
    - `FullPipelineContext`: Used only by pipeline orchestrator with full access
  - **Pipeline steps now mutate context in-place (no return values required)**
  - Created `registry.py` with decorator-based registration system for pipeline steps
  - Refactored `analyzers.py` to use `@analyzer` decorators with ordered execution
  - Split variable analysis into granular steps: variable usages, defined variables, undefined variables, environment variables
  - **Split `transformers.py` into 4 independent steps**: base parser creation, undefined variables, environment variables, positional arguments
  - Refactored `compilation.py` to use `@compiler` decorators
  - Refactored `execution.py` to use `@executor` decorators
  - Updated `pipeline.py` to orchestrate stages using the registry system with proper context isolation
  - Added data validation for exit codes (0-255) and positional indices (positive integers)
  - **Added new VALIDATE stage infrastructure for future argument validation and transformation**:
    - `ValidateContext`: Can read parser/args and write validated/transformed arguments
    - Empty stage ready for future validation step implementations
    - Extensible via `@validator` decorators for custom validation logic
  - **Enforced proper separation of concerns through Pydantic model validation**
  - Maintained full backward compatibility while improving extensibility and testability
  - Pipeline stages: 1) Script analysis (7 steps), 2) Parser transformation (4 steps), 3) Argument parsing, 4) **Argument validation (0 steps - infrastructure ready)**, 5) Script compilation (4 steps), 6) Script execution (1 step)

### Fixed
 - Remove accidentally committed pip installation log file `=2.0` from repo root
## [0.4.0] - 2025-08-27

### Added
- New `--echo` option to preview what the script would execute without running it
  - Works with `run` (prints commands while doing no work) and `compile` (prints echo-transformed script)
  - Special handling for pipes and operators by quoting entire original lines

### Fixed
- Set parser program name to the script name instead of "cli.py" in help output

## [0.3.1] - 2025-08-26

### Fixed
- Handle environment variable default and annotation default conflicts
  - Environment variable defaults now properly take precedence over annotation defaults
  - Warning message displayed in --help when conflicts are detected
  - Help text indicates when environment value overrides annotation default
- Allow lowercase parameter names in annotation comments
  - Parameter names in Google-style comments are now normalized to uppercase
  - Enables more natural annotation syntax (e.g., `# user_name` for `$USER_NAME`)

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
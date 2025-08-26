# Contributing to Argorator

Thank you for your interest in contributing to Argorator! This guide will help you get started.

## Development Setup

1. Fork and clone the repository
2. Create a virtual environment: `python3 -m venv venv`
3. Activate it: `source venv/bin/activate`
4. Install in development mode: `pip install -e .`
5. Install test dependencies: `pip install pytest`

## Making Changes

### 1. Create a Feature Branch
```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes
- Follow PEP 8 for Python code
- Add tests for new functionality
- Update documentation as needed

### 3. Update the Changelog
**IMPORTANT**: Always update `CHANGELOG.md` when making changes!

Add your changes under the `[Unreleased]` section:

```markdown
## [Unreleased]

### Added
- Your new feature here

### Changed
- Your changes here

### Fixed
- Your bug fixes here
```

Use these categories:
- **Added**: New features
- **Changed**: Changes to existing functionality
- **Deprecated**: Features that will be removed
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security fixes

### 4. Run Tests
```bash
python -m pytest tests/
```

### 5. Commit Your Changes
Write clear commit messages:
```bash
git commit -m "Add support for feature X

- Detail 1
- Detail 2"
```

## Version Management

We follow [Semantic Versioning](https://semver.org/):
- **MAJOR** (x.0.0): Breaking changes
- **MINOR** (0.x.0): New features, backwards compatible
- **PATCH** (0.0.x): Bug fixes only

### When to Update Version

Version updates are typically done by maintainers when preparing a release:

1. Update version in `pyproject.toml`
2. Move `[Unreleased]` changelog entries to a new version section with date
3. Update version references in documentation
4. Commit with message: `Release v0.x.x`

## Pull Request Process

1. Ensure all tests pass
2. Update documentation
3. Update CHANGELOG.md
4. Submit PR with clear description
5. Link any related issues

## Code Style Guidelines

### Python
- Follow PEP 8
- Use type hints where appropriate
- Write descriptive docstrings
- Keep functions focused and small

### Shell Scripts
- Use UPPERCASE for variable names
- Add descriptive comments
- Test scripts with bash, sh, and zsh if possible

### Documentation
- Use clear, simple language
- Include practical examples
- Keep examples up-to-date
- Add version info for new features

## Testing Guidelines

- Write tests for all new functionality
- Use pytest for Python tests
- Test edge cases
- Use temporary files for integration tests
- Ensure tests are independent

## Questions?

Feel free to open an issue for discussion or clarification!
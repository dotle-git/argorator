# Release Process Documentation

This document describes the automated version bump and release process for the argorator package.

## Overview

The release process is fully automated and supports:
- Semantic versioning (major, minor, patch)
- Custom version numbers
- Automatic PyPI publishing
- GitHub releases with artifacts
- Git tagging

## Release Methods

### 1. GitHub Actions (Recommended for Production Releases)

Use the GitHub Actions workflow for official releases:

1. Go to the [Actions tab](../../actions) in your repository
2. Click on "Release" workflow
3. Click "Run workflow"
4. Select version bump type:
   - `patch`: 0.1.0 → 0.1.1
   - `minor`: 0.1.0 → 0.2.0
   - `major`: 0.1.0 → 1.0.0
   - `custom`: Enter specific version in the next field

The workflow will automatically:
- Bump version in `pyproject.toml` and `__init__.py`
- Commit the changes
- Create and push a git tag
- Build the package
- Publish to PyPI
- Create a GitHub release

### 2. Local Release with Make (For Development)

Use the Makefile for local development and testing:

```bash
# Check current version
make check-version

# Bump version
make bump-patch    # 0.1.0 → 0.1.1
make bump-minor    # 0.1.0 → 0.2.0
make bump-major    # 0.1.0 → 1.0.0
make bump v=1.2.3  # Custom version

# Full release process (bump patch + tag)
make release

# Quick releases (bump + tag)
make quick-patch
make quick-minor
make quick-major

# Manual steps after local bump
git push && git push --tags
```

### 3. Direct Script Usage

For more control, use the version bump script directly:

```bash
# Bump versions
python scripts/bump_version.py patch
python scripts/bump_version.py minor
python scripts/bump_version.py major
python scripts/bump_version.py 1.2.3  # Custom version

# Dry run (preview changes)
python scripts/bump_version.py patch --dry-run
```

## Version Management

Versions are synchronized in two locations:
- `pyproject.toml`: The source of truth for package metadata
- `src/argorator/__init__.py`: For runtime version access

The version bump script ensures both locations are always in sync.

## Workflow Details

### Automatic PyPI Publishing

The `pypi-publish.yml` workflow triggers automatically when a tag starting with 'v' is pushed:

```bash
git tag v1.0.0
git push origin v1.0.0
```

This uses PyPI's Trusted Publisher feature for secure, token-free publishing.

### Manual Release Workflow

The `release.yml` workflow provides a complete release pipeline:

1. **Version Bump**: Updates version files
2. **Git Operations**: Commits changes and creates tag
3. **Build**: Creates wheel and source distributions
4. **Publish**: Uploads to PyPI
5. **GitHub Release**: Creates release with artifacts

## Best Practices

1. **Always test locally first**:
   ```bash
   make build
   make publish-test  # Publishes to TestPyPI
   ```

2. **Use semantic versioning**:
   - PATCH: Bug fixes (0.1.0 → 0.1.1)
   - MINOR: New features (0.1.0 → 0.2.0)
   - MAJOR: Breaking changes (0.1.0 → 1.0.0)

3. **Document changes**: Update CHANGELOG.md before releasing

4. **Verify before pushing**:
   ```bash
   make check-version
   git show  # Review commit
   ```

## Troubleshooting

### Version Mismatch

If versions are out of sync:
```bash
make check-version  # See current versions
python scripts/bump_version.py 0.1.0  # Force specific version
```

### Failed PyPI Upload

1. Check PyPI credentials/trusted publisher settings
2. Ensure version doesn't already exist on PyPI
3. Verify package builds correctly: `make build`

### Git Tag Issues

```bash
# Delete local tag
git tag -d v1.0.0

# Delete remote tag
git push origin :refs/tags/v1.0.0

# Recreate tag
git tag v1.0.0
git push origin v1.0.0
```

## Configuration

### PyPI Trusted Publisher

To enable GitHub Actions to publish to PyPI:

1. Go to PyPI project settings
2. Add trusted publisher:
   - Owner: your-github-username
   - Repository: your-repo-name
   - Workflow: `pypi-publish.yml`
   - Environment: (leave blank)

### Required Secrets

No secrets needed! The workflows use:
- `GITHUB_TOKEN`: Automatically provided
- PyPI: Trusted Publisher (OIDC)

## Quick Reference

```bash
# Most common commands
make check-version      # Show current version
make bump-patch        # Bump patch version
make release           # Full release process
make build             # Build packages
make publish           # Upload to PyPI

# GitHub Actions
# Go to Actions → Release → Run workflow
```
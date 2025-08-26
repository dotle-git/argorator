.PHONY: help bump-patch bump-minor bump-major bump build clean test install dev-install publish-test publish check-version tag release

# Default target
help:
	@echo "Argorator Release Management"
	@echo "==========================="
	@echo ""
	@echo "Version Bumping:"
	@echo "  make bump-patch    - Bump patch version (0.1.0 -> 0.1.1)"
	@echo "  make bump-minor    - Bump minor version (0.1.0 -> 0.2.0)"
	@echo "  make bump-major    - Bump major version (0.1.0 -> 1.0.0)"
	@echo "  make bump v=X.Y.Z  - Set custom version"
	@echo ""
	@echo "Building & Testing:"
	@echo "  make build         - Build distribution packages"
	@echo "  make clean         - Clean build artifacts"
	@echo "  make test          - Run tests"
	@echo "  make install       - Install package locally"
	@echo "  make dev-install   - Install package in development mode"
	@echo ""
	@echo "Publishing:"
	@echo "  make publish-test  - Upload to TestPyPI"
	@echo "  make publish       - Upload to PyPI"
	@echo "  make tag           - Create git tag for current version"
	@echo "  make release       - Full release (bump patch, tag, build, publish)"
	@echo ""
	@echo "Utilities:"
	@echo "  make check-version - Display current version"

# Get current version
VERSION := $(shell grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')

# Version checking
check-version:
	@echo "Current version: $(VERSION)"
	@echo "pyproject.toml: $(shell grep '^version = ' pyproject.toml)"
	@echo "__init__.py:    $(shell grep '^__version__ = ' src/argorator/__init__.py)"

# Version bumping
bump-patch:
	@python3 scripts/bump_version.py patch

bump-minor:
	@python3 scripts/bump_version.py minor

bump-major:
	@python3 scripts/bump_version.py major

bump:
	@if [ -z "$(v)" ]; then \
		echo "Error: Please specify version with v=X.Y.Z"; \
		exit 1; \
	fi
	@python3 scripts/bump_version.py $(v)

# Building
build: clean
	@echo "Building distribution packages..."
	@python3 -m pip install --upgrade build
	@python3 -m build

clean:
	@echo "Cleaning build artifacts..."
	@rm -rf build/ dist/ *.egg-info src/*.egg-info
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete

# Testing
test:
	@echo "Running tests..."
	@python3 -m pytest

# Installation
install:
	@echo "Installing package..."
	@pip install .

dev-install:
	@echo "Installing package in development mode..."
	@pip install -e .

# Publishing
publish-test: build
	@echo "Publishing to TestPyPI..."
	@echo "Make sure you have configured your TestPyPI credentials"
	@python3 -m pip install --upgrade twine
	@python3 -m twine upload --repository testpypi dist/*

publish: build
	@echo "Publishing to PyPI..."
	@echo "Make sure you have configured your PyPI credentials"
	@python3 -m pip install --upgrade twine
	@python3 -m twine upload dist/*

# Git operations
tag:
	@echo "Creating git tag v$(VERSION)..."
	@git tag -a "v$(VERSION)" -m "Release version $(VERSION)"
	@echo "Tag created. Push with: git push origin v$(VERSION)"

# Combined operations
release: bump-patch
	@echo "Starting release process..."
	@NEW_VERSION=$$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/'); \
	echo "New version: $$NEW_VERSION"; \
	git add pyproject.toml src/argorator/__init__.py; \
	git commit -m "Bump version to $$NEW_VERSION"; \
	git tag -a "v$$NEW_VERSION" -m "Release version $$NEW_VERSION"; \
	echo ""; \
	echo "Release prepared! Next steps:"; \
	echo "1. Review changes: git show"; \
	echo "2. Push changes: git push && git push --tags"; \
	echo "3. Build and publish: make build && make publish"

# Quick release shortcuts
quick-patch: bump-patch tag
	@echo "Patch version bumped and tagged. Ready to push!"

quick-minor: bump-minor tag
	@echo "Minor version bumped and tagged. Ready to push!"

quick-major: bump-major tag
	@echo "Major version bumped and tagged. Ready to push!"
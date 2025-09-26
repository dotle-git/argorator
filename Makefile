# Argorator Development Makefile

.PHONY: help install install-dev test test-verbose test-coverage clean format lint type-check

# Default target
help:
	@echo "Argorator Development Commands:"
	@echo "  make install       - Install production dependencies"
	@echo "  make install-dev    - Install all dependencies (production + dev)"
	@echo "  make test          - Run tests"
	@echo "  make test-verbose  - Run tests with verbose output"
	@echo "  make test-coverage  - Run tests with coverage report"
	@echo "  make format        - Format code with black"
	@echo "  make lint          - Lint code with flake8"
	@echo "  make type-check    - Type check with mypy"
	@echo "  make clean         - Clean up build artifacts"

# Install production dependencies
install:
	pip install -e .

# Install all dependencies including dev tools
install-dev:
	pip install -e .[dev]

# Run tests
test:
	PYTHONPATH=/workspace/src python3 -m pytest tests/ -q

# Run tests with verbose output
test-verbose:
	PYTHONPATH=/workspace/src python3 -m pytest tests/ -v

# Run tests with coverage
test-coverage:
	PYTHONPATH=/workspace/src python3 -m pytest tests/ --cov=src/argorator --cov-report=html --cov-report=term

# Format code
format:
	python3 -m black src/ tests/

# Lint code
lint:
	python3 -m flake8 src/ tests/

# Type check
type-check:
	python3 -m mypy src/argorator/

# Clean up
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
#!/bin/bash
# Argorator Development Setup Script

set -e  # Exit on any error

echo "🚀 Setting up Argorator development environment..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9 or later."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
REQUIRED_VERSION="3.9"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python $REQUIRED_VERSION or later is required. Found: $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION detected"

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip."
    exit 1
fi

echo "✅ pip3 is available"

# Install dependencies
echo "📦 Installing dependencies..."

# Try to install with --break-system-packages if needed
if pip3 install -e .[dev] --break-system-packages 2>/dev/null; then
    echo "✅ Dependencies installed successfully"
elif pip3 install -e .[dev]; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    echo "💡 Try running: pip3 install -e .[dev] --break-system-packages"
    exit 1
fi

# Verify installation
echo "🧪 Verifying installation..."

# Test imports
if python3 -c "import argorator; print('✅ Argorator imports successfully')" 2>/dev/null; then
    echo "✅ Package imports work"
else
    echo "❌ Package import failed"
    exit 1
fi

# Run tests
echo "🧪 Running tests..."
if PYTHONPATH=/workspace/src python3 -m pytest tests/ -q; then
    echo "✅ All tests pass"
else
    echo "⚠️  Some tests failed, but dependencies are installed"
fi

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "Next steps:"
echo "  • Run tests: PYTHONPATH=/workspace/src python3 -m pytest tests/"
echo "  • Run with coverage: PYTHONPATH=/workspace/src python3 -m pytest tests/ --cov=src/argorator"
echo "  • Format code: black src/ tests/"
echo "  • Lint code: flake8 src/ tests/"
echo ""
echo "Or use the Makefile:"
echo "  • make test"
echo "  • make test-coverage"
echo "  • make format"
echo "  • make lint"
#!/usr/bin/env python3
"""
Development setup script for Argorator.
Automatically installs dependencies and sets up the development environment.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Command: {cmd}")
        print(f"   Error: {e.stderr}")
        return False


def install_dependencies():
    """Install project dependencies."""
    print("🚀 Setting up Argorator development environment...")
    
    # Check if we're in a virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    
    if not in_venv:
        print("⚠️  Warning: Not in a virtual environment. Consider creating one:")
        print("   python3 -m venv venv")
        print("   source venv/bin/activate")
        print()
    
    # Install the project in development mode
    if not run_command("pip install -e . --break-system-packages", "Installing project in development mode"):
        return False
    
    # Install development dependencies
    if not run_command("pip install -e .[dev] --break-system-packages", "Installing development dependencies"):
        return False
    
    return True


def verify_installation():
    """Verify that the installation works."""
    print("\n🧪 Verifying installation...")
    
    # Test imports
    try:
        import argorator
        print("✅ Argorator package imports successfully")
    except ImportError as e:
        print(f"❌ Failed to import argorator: {e}")
        return False
    
    # Test pytest
    if not run_command("python3 -m pytest --version", "Checking pytest installation"):
        return False
    
    # Run tests
    print("\n🧪 Running test suite...")
    if not run_command("PYTHONPATH=/workspace/src python3 -m pytest tests/ -q", "Running tests"):
        print("⚠️  Some tests failed, but dependencies are installed")
        return True
    
    return True


def main():
    """Main setup function."""
    # Change to project root
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    print("=" * 60)
    print("🔧 Argorator Development Setup")
    print("=" * 60)
    
    if not install_dependencies():
        print("\n❌ Setup failed during dependency installation")
        sys.exit(1)
    
    if not verify_installation():
        print("\n❌ Setup verification failed")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("🎉 Setup completed successfully!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Run tests: PYTHONPATH=/workspace/src python -m pytest tests/")
    print("2. Run with coverage: PYTHONPATH=/workspace/src python -m pytest tests/ --cov=src/argorator")
    print("3. Format code: black src/ tests/")
    print("4. Lint code: flake8 src/ tests/")


if __name__ == "__main__":
    main()
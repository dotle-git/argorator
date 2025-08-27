#!/usr/bin/env python3
"""
Version bumping script for argorator package.
Automatically updates version in both pyproject.toml and src/argorator/__init__.py
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Tuple


def parse_version(version_str: str) -> Tuple[int, int, int]:
    """Parse a semantic version string into major, minor, patch components."""
    match = re.match(r'^(\d+)\.(\d+)\.(\d+)(?:-.*)?$', version_str)
    if not match:
        raise ValueError(f"Invalid version format: {version_str}")
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def bump_version(version_str: str, bump_type: str) -> str:
    """Bump version based on type (major, minor, patch)."""
    major, minor, patch = parse_version(version_str)
    
    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")
    
    return f"{major}.{minor}.{patch}"


def update_pyproject_toml(file_path: Path, new_version: str) -> None:
    """Update version in pyproject.toml file."""
    content = file_path.read_text()
    
    # Update version line
    updated_content = re.sub(
        r'^version = "[^"]*"',
        f'version = "{new_version}"',
        content,
        flags=re.MULTILINE
    )
    
    if updated_content == content:
        raise ValueError("Could not find version line in pyproject.toml")
    
    file_path.write_text(updated_content)
    print(f"Updated {file_path} with version {new_version}")


def update_init_py(file_path: Path, new_version: str) -> None:
    """Update version in __init__.py file."""
    content = file_path.read_text()
    
    # Update __version__ line
    updated_content = re.sub(
        r'^__version__ = "[^"]*"',
        f'__version__ = "{new_version}"',
        content,
        flags=re.MULTILINE
    )
    
    if updated_content == content:
        raise ValueError("Could not find __version__ line in __init__.py")
    
    file_path.write_text(updated_content)
    print(f"Updated {file_path} with version {new_version}")


def get_current_version() -> str:
    """Get current version from pyproject.toml."""
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        raise FileNotFoundError("pyproject.toml not found")
    
    content = pyproject_path.read_text()
    match = re.search(r'^version = "([^"]*)"', content, re.MULTILINE)
    if not match:
        raise ValueError("Could not find version in pyproject.toml")
    
    return match.group(1)


def main():
    parser = argparse.ArgumentParser(description="Bump version for argorator package")
    parser.add_argument(
        "bump_type",
        choices=["major", "minor", "patch"],
        help="Type of version bump to perform"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making changes"
    )
    parser.add_argument(
        "--version",
        help="Set specific version instead of bumping"
    )
    
    args = parser.parse_args()
    
    try:
        # Get current version
        current_version = get_current_version()
        print(f"Current version: {current_version}")
        
        # Calculate new version
        if args.version:
            new_version = args.version
            # Validate the provided version
            parse_version(new_version)
        else:
            new_version = bump_version(current_version, args.bump_type)
        
        print(f"New version: {new_version}")
        
        if args.dry_run:
            print("Dry run - no files would be modified")
            return
        
        # Update files
        pyproject_path = Path("pyproject.toml")
        init_py_path = Path("src/argorator/__init__.py")
        
        if not pyproject_path.exists():
            raise FileNotFoundError("pyproject.toml not found")
        if not init_py_path.exists():
            raise FileNotFoundError("src/argorator/__init__.py not found")
        
        update_pyproject_toml(pyproject_path, new_version)
        update_init_py(init_py_path, new_version)
        
        print(f"\nSuccessfully bumped version from {current_version} to {new_version}")
        print("\nNext steps:")
        print(f"1. git add pyproject.toml src/argorator/__init__.py")
        print(f"2. git commit -m 'Bump version to {new_version}'")
        print(f"3. git tag v{new_version}")
        print(f"4. git push origin main --tags")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
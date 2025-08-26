#!/usr/bin/env python3
"""
Version bump utility for argorator package.

This script updates the version in both pyproject.toml and __init__.py files.
Supports major, minor, and patch version bumps, as well as custom version strings.
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Tuple


def parse_version(version_str: str) -> Tuple[int, int, int]:
    """Parse version string into major, minor, patch tuple."""
    match = re.match(r'^(\d+)\.(\d+)\.(\d+)', version_str)
    if not match:
        raise ValueError(f"Invalid version format: {version_str}")
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def bump_version(current_version: str, bump_type: str) -> str:
    """Bump version based on bump type."""
    major, minor, patch = parse_version(current_version)
    
    if bump_type == 'major':
        return f"{major + 1}.0.0"
    elif bump_type == 'minor':
        return f"{major}.{minor + 1}.0"
    elif bump_type == 'patch':
        return f"{major}.{minor}.{patch + 1}"
    else:
        # Custom version provided
        return bump_type


def update_pyproject_toml(file_path: Path, new_version: str) -> bool:
    """Update version in pyproject.toml."""
    try:
        content = file_path.read_text()
        updated_content = re.sub(
            r'^version\s*=\s*"[^"]+"',
            f'version = "{new_version}"',
            content,
            flags=re.MULTILINE
        )
        
        if content != updated_content:
            file_path.write_text(updated_content)
            return True
        return False
    except Exception as e:
        print(f"Error updating pyproject.toml: {e}")
        return False


def update_init_py(file_path: Path, new_version: str) -> bool:
    """Update version in __init__.py."""
    try:
        content = file_path.read_text()
        updated_content = re.sub(
            r'^__version__\s*=\s*"[^"]+"',
            f'__version__ = "{new_version}"',
            content,
            flags=re.MULTILINE
        )
        
        if content != updated_content:
            file_path.write_text(updated_content)
            return True
        return False
    except Exception as e:
        print(f"Error updating __init__.py: {e}")
        return False


def get_current_version(pyproject_path: Path) -> str:
    """Get current version from pyproject.toml."""
    try:
        content = pyproject_path.read_text()
        match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
        if match:
            return match.group(1)
        raise ValueError("Version not found in pyproject.toml")
    except Exception as e:
        print(f"Error reading current version: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Bump version for argorator package",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Bump patch version (e.g., 0.1.0 -> 0.1.1)
  python scripts/bump_version.py patch

  # Bump minor version (e.g., 0.1.0 -> 0.2.0)
  python scripts/bump_version.py minor

  # Bump major version (e.g., 0.1.0 -> 1.0.0)
  python scripts/bump_version.py major

  # Set custom version
  python scripts/bump_version.py 1.2.3

  # Dry run to see what would change
  python scripts/bump_version.py patch --dry-run
"""
    )
    
    parser.add_argument(
        'bump_type',
        help='Version bump type (major, minor, patch) or custom version string'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without actually modifying files'
    )
    
    args = parser.parse_args()
    
    # Find project root
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    
    # File paths
    pyproject_path = project_root / 'pyproject.toml'
    init_path = project_root / 'src' / 'argorator' / '__init__.py'
    
    # Verify files exist
    if not pyproject_path.exists():
        print(f"Error: pyproject.toml not found at {pyproject_path}")
        sys.exit(1)
    
    if not init_path.exists():
        print(f"Error: __init__.py not found at {init_path}")
        sys.exit(1)
    
    # Get current version
    current_version = get_current_version(pyproject_path)
    print(f"Current version: {current_version}")
    
    # Determine new version
    if args.bump_type in ['major', 'minor', 'patch']:
        new_version = bump_version(current_version, args.bump_type)
    else:
        # Validate custom version
        try:
            parse_version(args.bump_type)
            new_version = args.bump_type
        except ValueError:
            print(f"Error: Invalid version format: {args.bump_type}")
            print("Version must be in format X.Y.Z (e.g., 1.2.3)")
            sys.exit(1)
    
    print(f"New version: {new_version}")
    
    if args.dry_run:
        print("\nDry run - no files will be modified")
        print(f"Would update {pyproject_path}")
        print(f"Would update {init_path}")
        return
    
    # Update files
    print("\nUpdating files...")
    
    success = True
    if update_pyproject_toml(pyproject_path, new_version):
        print(f"✓ Updated {pyproject_path}")
    else:
        print(f"✗ Failed to update {pyproject_path}")
        success = False
    
    if update_init_py(init_path, new_version):
        print(f"✓ Updated {init_path}")
    else:
        print(f"✗ Failed to update {init_path}")
        success = False
    
    if success:
        print(f"\nSuccessfully bumped version to {new_version}")
        print("\nNext steps:")
        print(f"1. Commit changes: git add -A && git commit -m 'Bump version to {new_version}'")
        print(f"2. Create tag: git tag v{new_version}")
        print(f"3. Push changes: git push && git push --tags")
    else:
        print("\nError: Version bump failed")
        sys.exit(1)


if __name__ == '__main__':
    main()
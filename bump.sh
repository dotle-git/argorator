#!/bin/bash
# Convenient wrapper script for version bumping

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Help function
show_help() {
    echo "Usage: $0 [major|minor|patch] [--dry-run] [--version VERSION]"
    echo ""
    echo "Bump version for argorator package"
    echo ""
    echo "Arguments:"
    echo "  major|minor|patch    Type of version bump"
    echo ""
    echo "Options:"
    echo "  --dry-run           Show what would be changed without making changes"
    echo "  --version VERSION   Set specific version instead of bumping"
    echo "  --help, -h          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 patch                    # Bump patch version (0.1.0 -> 0.1.1)"
    echo "  $0 minor                    # Bump minor version (0.1.0 -> 0.2.0)"
    echo "  $0 major                    # Bump major version (0.1.0 -> 1.0.0)"
    echo "  $0 patch --dry-run          # Show what would happen"
    echo "  $0 --version 1.2.3          # Set specific version"
}

# Check if help is requested
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    show_help
    exit 0
fi

# Check if we're in the right directory
if [[ ! -f "pyproject.toml" ]]; then
    echo -e "${RED}Error: pyproject.toml not found. Please run this script from the project root.${NC}"
    exit 1
fi

# Check if bump_version.py exists
if [[ ! -f "bump_version.py" ]]; then
    echo -e "${RED}Error: bump_version.py not found. Please ensure the version bump script is present.${NC}"
    exit 1
fi

# Show current status
echo -e "${YELLOW}Current git status:${NC}"
git status --porcelain

if [[ $(git status --porcelain | wc -l) -ne 0 ]]; then
    echo -e "${YELLOW}Warning: You have uncommitted changes. Consider committing them first.${NC}"
    echo ""
fi

# Run the Python version bump script
echo -e "${GREEN}Running version bump...${NC}"
python3 bump_version.py "$@"

# If it's not a dry run and the script succeeded, offer to create git commands
if [[ $? -eq 0 && "$*" != *"--dry-run"* ]]; then
    echo ""
    echo -e "${GREEN}Version bump completed successfully!${NC}"
    echo ""
    
    # Get the new version
    NEW_VERSION=$(python3 -c "
import re
from pathlib import Path
content = Path('pyproject.toml').read_text()
match = re.search(r'^version = \"([^\"]*)\"', content, re.MULTILINE)
print(match.group(1) if match else 'unknown')
")
    
    echo -e "${YELLOW}Suggested next steps:${NC}"
    echo "1. Review the changes:"
    echo "   git diff"
    echo ""
    echo "2. Commit and tag the release:"
    echo "   git add pyproject.toml src/argorator/__init__.py"
    echo "   git commit -m 'Bump version to $NEW_VERSION'"
    echo "   git tag v$NEW_VERSION"
    echo "   git push origin main --tags"
    echo ""
    
    read -p "Would you like to run these git commands automatically? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}Running git commands...${NC}"
        
        git add pyproject.toml src/argorator/__init__.py
        git commit -m "Bump version to $NEW_VERSION"
        git tag "v$NEW_VERSION"
        
        echo ""
        echo -e "${GREEN}Changes committed and tagged successfully!${NC}"
        echo -e "${YELLOW}Don't forget to push:${NC} git push origin main --tags"
    fi
fi
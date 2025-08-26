#!/usr/bin/env python3
"""
Entry point script for argorator - simulates what pip would install
"""

import sys
import os

# Add the package to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from argorator.main import main

if __name__ == "__main__":
    sys.exit(main())
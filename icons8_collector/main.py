"""
Main entry point for Icons8 Collector.

This module provides backwards compatibility for direct execution.
The primary entry point is now icons8_collector.cli:main
"""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())

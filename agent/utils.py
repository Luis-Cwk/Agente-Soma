"""
SomaAgent — Utility Functions
"""
import sys


def info_print(*args, **kwargs):
    """Print with immediate flush to ensure real-time log capture."""
    print(*args, **kwargs)
    sys.stdout.flush()


def debug_print(*args, **kwargs):
    """Debug print with immediate flush."""
    print(*args, **kwargs)
    sys.stdout.flush()

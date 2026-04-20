"""Shared geometry type aliases.

This module intentionally avoids the name ``types.py`` so it does not shadow
Python's standard-library ``types`` module when files in this package are run
directly.
"""

Color = tuple[int, int, int]
Point = tuple[float, float]

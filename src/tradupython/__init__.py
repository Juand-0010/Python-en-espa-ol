"""Explicaciones legibles en español para código Python."""

from .translator import TranslationError, explain, explain_file, translate

__version__ = "0.2.1"

__all__ = ["TranslationError", "explain", "explain_file", "translate", "__version__"]

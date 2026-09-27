"""Public package interface for lyricsync."""

from .parser import LyricParser
from .player import LyricPlayer

__all__ = ["LyricParser", "LyricPlayer"]

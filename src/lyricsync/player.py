"""Playback-time lookup of the active lyric line."""

from __future__ import annotations

from bisect import bisect_right
from typing import Dict, Iterable, List, Optional


class LyricPlayer:
    """Resolves a playback position to the lyric line currently being sung.

    Lookups are O(log n), so ``get_lyric_at_time`` is safe to call on every
    tick of a playback loop.
    """

    def __init__(self, lyrics: Optional[Iterable[Dict[str, object]]] = None) -> None:
        self.lyrics: List[Dict[str, object]] = sorted(
            lyrics or (), key=lambda entry: int(entry["time_ms"])
        )
        # Parallel key list for bisect; the key= argument needs Python 3.10+.
        self._times: List[int] = [int(entry["time_ms"]) for entry in self.lyrics]

    def get_lyric_at_time(self, current_time_ms: int) -> Dict[str, object]:
        """Return the lyric active at ``current_time_ms``.

        The result is ``{"index", "time_ms", "text"}``. Before the first line,
        or when there are no lyrics, ``index`` is ``-1``, ``text`` is empty and
        ``time_ms`` echoes the requested time.
        """
        index = bisect_right(self._times, current_time_ms) - 1
        if index < 0:
            return {"index": -1, "time_ms": current_time_ms, "text": ""}

        entry = self.lyrics[index]
        return {
            "index": index,
            "time_ms": self._times[index],
            "text": str(entry["text"]),
        }

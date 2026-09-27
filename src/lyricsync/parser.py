"""Parsing for LRC synchronized lyric files."""

from __future__ import annotations

import re
from typing import Dict, List, Match

_TIMESTAMP_RE = re.compile(
    r"\[(?P<minutes>\d{1,2}):(?P<seconds>\d{2})(?:\.(?P<fraction>\d{1,3}))?\]"
)


def _match_to_ms(match: Match[str]) -> int:
    minutes = int(match["minutes"])
    seconds = int(match["seconds"])
    # "[00:01.5]" means 500 ms and "[00:01.05]" means 50 ms, so right-pad to millis.
    millis = int((match["fraction"] or "").ljust(3, "0"))
    return (minutes * 60 + seconds) * 1000 + millis


class LyricParser:
    """Turns LRC text into time-ordered lyric entries."""

    @staticmethod
    def parse_time(time_str: str) -> int:
        """Convert an LRC timestamp such as ``[mm:ss.xx]`` to milliseconds."""
        match = _TIMESTAMP_RE.fullmatch(time_str.strip())
        if match is None:
            raise ValueError(f"Invalid LRC timestamp: {time_str!r}")
        return _match_to_ms(match)

    @staticmethod
    def parse_lrc(lrc_text: str) -> List[Dict[str, object]]:
        """Parse LRC content into entries of ``{"time_ms", "text"}``, sorted by time.

        A line carrying several timestamps (``[00:12.00][01:30.00]Chorus``)
        yields one entry per timestamp. Lines without a timestamp, including
        metadata tags like ``[ar:Artist]``, are skipped.
        """
        entries: List[Dict[str, object]] = []

        for line in lrc_text.splitlines():
            stamps = list(_TIMESTAMP_RE.finditer(line))
            if not stamps:
                continue

            text = _TIMESTAMP_RE.sub("", line).strip()
            entries.extend({"time_ms": _match_to_ms(m), "text": text} for m in stamps)

        entries.sort(key=lambda entry: entry["time_ms"])
        return entries

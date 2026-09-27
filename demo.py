"""Real-time lyric playback demo.

Usage:
    python demo.py                 # plays the built-in placeholder track
    python demo.py song.lrc        # plays your own LRC file
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from lyricsync import LyricParser, LyricPlayer  # noqa: E402

TICK_SECONDS = 0.05
DURATION_MS = 20_000

# Built-in sample track. Pass an .lrc file on the command line to play something else.
DEFAULT_LRC = """\
[ti:Show Body]
[ar:Dekee]
[00:00.00]Yeah, your body vibrating to the baseline
[00:02.50]Girl, you're the only one on my mind
[00:05.00]The way you move, you got me hypnotized
[00:07.50]Look into my eyes, no more compromise
[00:10.00]Slow whine for me, make you take your time
[00:12.50]I swear to God, your love is sublime
[00:15.00]Another banger for my special lady
[00:17.50]Oh my baby, you drive me crazy
"""


def format_ms(ms: int) -> str:
    minutes, rest = divmod(max(ms, 0), 60_000)
    return f"{minutes:02d}:{rest / 1000:05.2f}"


def play(player: LyricPlayer, duration_ms: int = DURATION_MS) -> None:
    start = time.monotonic()
    next_tick = start
    current_index = None

    while True:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        if elapsed_ms > duration_ms:
            break

        lyric = player.get_lyric_at_time(elapsed_ms)
        if lyric["index"] != current_index:
            current_index = lyric["index"]
            if current_index >= 0:
                print(f"[{format_ms(elapsed_ms)}] {lyric['text']}", flush=True)

        # Schedule against absolute ticks so sleep jitter doesn't accumulate.
        next_tick += TICK_SECONDS
        time.sleep(max(0.0, next_tick - time.monotonic()))

    print(f"[{format_ms(duration_ms)}] -- stopped --")


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate real-time lyric playback.")
    parser.add_argument("lrc_file", nargs="?", type=Path, help="path to an .lrc file")
    args = parser.parse_args()

    lrc_text = args.lrc_file.read_text(encoding="utf-8-sig") if args.lrc_file else DEFAULT_LRC
    player = LyricPlayer(LyricParser.parse_lrc(lrc_text))

    try:
        play(player)
    except KeyboardInterrupt:
        print("\n-- interrupted --")


if __name__ == "__main__":
    main()

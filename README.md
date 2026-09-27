# lyricsync

`lyricsync` is a reusable Python library for parsing synchronized lyric files such as `.lrc` and tracking playback time to return the current lyric line in real time.

## Features

- Parse `.lrc` timestamps like `[mm:ss.xx]` and `[mm:ss.xxx]`
- Convert timestamps to total milliseconds accurately
- Extract lyric text and timestamps into a sortable list
- Look up the active lyric line for a given playback time in O(log n), fast enough to call on every tick of a playback loop

## Installation

```bash
pip install hatch
hatch build
```

## Example

This simulates a playback loop that checks the clock every 100 ms and prints each lyric as it becomes active:

```python
import time

from lyricsync import LyricParser, LyricPlayer

lrc_text = """
[00:00.00]Hello there
[00:02.00]I am a lyric
[00:04.00]running in real time
[00:06.00]with lyricsync
"""

player = LyricPlayer(LyricParser.parse_lrc(lrc_text))

start = time.monotonic()
current_index = -1

while (elapsed_ms := int((time.monotonic() - start) * 1000)) <= 7000:
    lyric = player.get_lyric_at_time(elapsed_ms)
    if lyric["index"] != current_index:
        current_index = lyric["index"]
        print(f"[{lyric['time_ms'] / 1000:5.2f}s] {lyric['text']}")
    time.sleep(0.1)
```

Output:

```text
[ 0.00s] Hello there
[ 2.00s] I am a lyric
[ 4.00s] running in real time
[ 6.00s] with lyricsync
```

`get_lyric_at_time` returns a dict with `index`, `time_ms` and `text`. Before the first line, `index` is `-1` and `text` is empty.

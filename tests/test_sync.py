import pytest

from lyricsync import LyricParser, LyricPlayer

SAMPLE_LRC = """\
[00:00.00]Hello
[00:03.12]world
[00:06.50]from lyricsync
"""


@pytest.fixture
def player():
    return LyricPlayer(LyricParser.parse_lrc(SAMPLE_LRC))


class TestParseTime:
    @pytest.mark.parametrize(
        ("timestamp", "expected_ms"),
        [
            ("[00:03.12]", 3120),
            ("[01:02.345]", 62345),
            ("[00:01.5]", 1500),
            ("[00:01.05]", 1050),
            ("[02:00]", 120000),
            ("  [00:00.00]  ", 0),
        ],
    )
    def test_converts_to_milliseconds(self, timestamp, expected_ms):
        assert LyricParser.parse_time(timestamp) == expected_ms

    @pytest.mark.parametrize("timestamp", ["", "00:03.12", "[0:3.12]", "[ar:Artist]", "[00:03.1234]"])
    def test_rejects_malformed_input(self, timestamp):
        with pytest.raises(ValueError, match="Invalid LRC timestamp"):
            LyricParser.parse_time(timestamp)


class TestParseLrc:
    def test_parses_lines_in_order(self):
        assert LyricParser.parse_lrc(SAMPLE_LRC) == [
            {"time_ms": 0, "text": "Hello"},
            {"time_ms": 3120, "text": "world"},
            {"time_ms": 6500, "text": "from lyricsync"},
        ]

    def test_empty_input(self):
        assert LyricParser.parse_lrc("") == []

    def test_skips_metadata_tags(self):
        lrc = """\
[ar:Some Artist]
[ti:Some Title]
[al:Some Album]
[by:Someone]
[offset:+250]
[length:03:45]

[00:01.00]First line
"""
        assert LyricParser.parse_lrc(lrc) == [{"time_ms": 1000, "text": "First line"}]

    def test_skips_untimed_lines(self):
        lrc = "just some text\n[00:01.00]Timed\n# a comment\n"
        assert LyricParser.parse_lrc(lrc) == [{"time_ms": 1000, "text": "Timed"}]

    def test_multiple_timestamps_on_one_line_expand_to_separate_entries(self):
        lrc = "[00:10.00][00:30.00]Chorus\n[00:20.00]Verse\n"
        assert LyricParser.parse_lrc(lrc) == [
            {"time_ms": 10000, "text": "Chorus"},
            {"time_ms": 20000, "text": "Verse"},
            {"time_ms": 30000, "text": "Chorus"},
        ]

    def test_sorts_out_of_order_lines(self):
        lrc = "[00:05.00]Second\n[00:01.00]First\n"
        assert [e["text"] for e in LyricParser.parse_lrc(lrc)] == ["First", "Second"]

    def test_duplicate_timestamps_keep_file_order(self):
        lrc = "[00:02.00]Lead vocal\n[00:02.00]Backing vocal\n[00:01.00]Intro\n"
        assert LyricParser.parse_lrc(lrc) == [
            {"time_ms": 1000, "text": "Intro"},
            {"time_ms": 2000, "text": "Lead vocal"},
            {"time_ms": 2000, "text": "Backing vocal"},
        ]

    def test_timestamp_with_empty_text(self):
        assert LyricParser.parse_lrc("[00:04.00]\n") == [{"time_ms": 4000, "text": ""}]


class TestLyricPlayer:
    @pytest.mark.parametrize(
        ("time_ms", "expected"),
        [
            (-1, {"index": -1, "time_ms": -1, "text": ""}),
            (0, {"index": 0, "time_ms": 0, "text": "Hello"}),
            (1500, {"index": 0, "time_ms": 0, "text": "Hello"}),
            (3119, {"index": 0, "time_ms": 0, "text": "Hello"}),
            (3120, {"index": 1, "time_ms": 3120, "text": "world"}),
            (100000, {"index": 2, "time_ms": 6500, "text": "from lyricsync"}),
        ],
    )
    def test_lookup(self, player, time_ms, expected):
        assert player.get_lyric_at_time(time_ms) == expected

    def test_no_lyrics(self):
        assert LyricPlayer().get_lyric_at_time(500) == {"index": -1, "time_ms": 500, "text": ""}

    def test_sorts_unsorted_input(self):
        player = LyricPlayer([{"time_ms": 2000, "text": "b"}, {"time_ms": 1000, "text": "a"}])
        assert player.get_lyric_at_time(1500)["text"] == "a"

    def test_does_not_mutate_input(self):
        lyrics = [{"time_ms": 2000, "text": "b"}, {"time_ms": 1000, "text": "a"}]
        LyricPlayer(lyrics)
        assert [e["text"] for e in lyrics] == ["b", "a"]

    @pytest.mark.parametrize("time_ms", [2000, 2001, 2999])
    def test_duplicate_timestamps_resolve_to_last_entry(self, time_ms):
        lyrics = LyricParser.parse_lrc("[00:01.00]Intro\n[00:02.00]Lead\n[00:02.00]Backing\n[00:03.00]Outro\n")
        player = LyricPlayer(lyrics)
        assert player.get_lyric_at_time(time_ms) == {"index": 2, "time_ms": 2000, "text": "Backing"}

    def test_playback_steps_through_every_line(self, player):
        seen = []
        for time_ms in range(-500, 8000, 100):
            text = player.get_lyric_at_time(time_ms)["text"]
            if text and (not seen or seen[-1] != text):
                seen.append(text)
        assert seen == ["Hello", "world", "from lyricsync"]

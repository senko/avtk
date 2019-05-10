from os.path import getsize

import pytest

from avtk.backends.ffmpeg.exceptions import NoMediaError
from avtk.backends.ffmpeg.probe import MediaInfo

from .utils import asset_path


def test_probe_raises_value_error_if_no_file():
    with pytest.raises(NoMediaError):
        MediaInfo('/nonexistent')


def test_probe_raises_value_error_if_not_a_regular_file():
    with pytest.raises(NoMediaError):
        MediaInfo('/dev/null')


def test_probe_raises_value_error_if_not_a_media_file():
    with pytest.raises(NoMediaError):
        MediaInfo(__file__)


def test_probe_video():
    path = asset_path('video', 'sintel.mkv')

    mi = MediaInfo(path)

    assert mi.format.size == getsize(path)
    assert mi.format.duration.total_seconds() == pytest.approx(5.0, abs=0.1)
    assert 'matroska' in mi.format.name
    assert mi.format.bit_rate / 1000000 == pytest.approx(2.650, abs=0.1)

    assert len(mi.video_streams) == 1
    assert len(mi.audio_streams) == 1
    assert len(mi.subtitle_streams) == 10

    langs = [s.language for s in mi.subtitle_streams]
    langs.sort()
    assert langs == ['dut', 'eng', 'fre', 'ger', 'ita', 'pol', 'por', 'rus', 'spa', 'vie']

    v = mi.video_streams[0]
    assert v.codec.name == 'h264'
    assert v.width == 1920
    assert v.height == 818
    assert v.frame_rate == 24

    a = mi.audio_streams[0]
    assert a.codec.name == 'ac3'
    assert a.bit_rate == 640000
    assert a.sample_rate == 48000
    assert a.channels == 6


def test_probe_image():
    path = asset_path('image', 'evil-frank.png')

    mi = MediaInfo(path)

    assert mi.format.size == getsize(path)
    assert 'png' in mi.format.name
    assert mi.format.duration is None

    assert len(mi.video_streams) == 1
    assert not mi.has_audio
    assert not mi.has_subtitles

    v = mi.video_streams[0]
    assert v.codec.name == 'png'
    assert v.frame_rate is None
    assert v.width == 320
    assert v.height == 180


def test_mp3_audio():
    path = asset_path('audio', 'stereo.mp3')

    mi = MediaInfo(path)

    assert mi.format.size == getsize(path)
    assert 'mp3' in mi.format.name
    assert mi.format.duration.total_seconds() == pytest.approx(5.0, abs=0.1)
    assert 127 <= mi.format.bit_rate / 1000 <= 129

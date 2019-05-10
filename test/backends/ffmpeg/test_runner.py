import os
from os.path import dirname, join, abspath

import pytest

from avtk.backends.ffmpeg.exceptions import NoMediaError
from avtk.backends.ffmpeg.run import ffmpeg, ffprobe


@pytest.fixture
def fake_ffprobe():
    os.environ['FFPROBE_PATH'] = abspath(join(dirname(__file__), 'fake_ffprobe.sh'))
    yield
    del os.environ['FFPROBE_PATH']


@pytest.fixture
def fake_ffmpeg():
    os.environ['FFMPEG_PATH'] = abspath(join(dirname(__file__), 'fake_ffmpeg.sh'))
    yield
    del os.environ['FFMPEG_PATH']


@pytest.fixture
def nonexistent_ffprobe():
    os.environ['FFPROBE_PATH'] = abspath(join(dirname(__file__), 'nonexistent_ffprobe.sh'))
    yield
    del os.environ['FFPROBE_PATH']


@pytest.fixture
def nonexistent_ffmpeg():
    os.environ['FFMPEG_PATH'] = abspath(join(dirname(__file__), 'nonexistent_ffmpeg.sh'))
    yield
    del os.environ['FFMPEG_PATH']


def test_run_system_ffprobe():
    result = ffprobe(['-version'], parse_json=False)
    assert result.startswith('ffprobe version')


def test_run_custom_ffprobe_no_json(fake_ffprobe):
    result = ffprobe([], parse_json=False)
    assert result == '{"status": "ok"}\n'


def test_run_custom_ffprobe_json(fake_ffprobe):
    result = ffprobe([])
    assert result == dict(status='ok')


def test_run_custom_ffprobe_error(fake_ffprobe):
    with pytest.raises(NoMediaError):
        ffprobe(['error'])


def test_run_nonexistent_ffprobe(nonexistent_ffprobe):
    with pytest.raises(ValueError):
        ffprobe([])


def test_run_nonexistent_ffmpeg(nonexistent_ffmpeg):
    with pytest.raises(ValueError):
        ffmpeg([])


def test_run_system_ffmpeg():
    result = ffmpeg(['-version'])
    assert result.startswith('ffmpeg version')


def test_run_custom_ffmpeg(fake_ffmpeg):
    result = ffmpeg([])
    assert result == 'FFMPEG\n'

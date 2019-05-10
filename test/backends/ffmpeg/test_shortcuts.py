from tempfile import mkstemp
from os import unlink, fdopen

import pytest

from avtk.backends.ffmpeg.shortcuts import get_thumbnail, extract_audio, remove_audio
from avtk.backends.ffmpeg.probe import MediaInfo

from .utils import asset_path, compare_images

video_path = asset_path('video', 'sintel.mkv')
thumb_path = asset_path('image', 'sintel@2s.png')


@pytest.fixture
def tmpfile():
    fd, path = mkstemp()
    yield fdopen(fd, 'wb'), path
    unlink(path)


@pytest.mark.slow
def test_get_thumbnail_png(tmpfile):
    fp, path = tmpfile
    fp.write(get_thumbnail(video_path, 2, fmt='png'))
    fp.close()
    diff = compare_images(thumb_path, path)
    assert diff < 0.5


@pytest.mark.slow
def test_get_thumbnail_jpg(tmpfile):
    fp, path = tmpfile
    fp.write(get_thumbnail(video_path, 2, fmt='jpg'))
    fp.close()
    diff = compare_images(thumb_path, path)
    assert diff < 0.5


@pytest.mark.slow
def test_get_thumbnail_gif(tmpfile):
    fp, path = tmpfile
    fp.write(get_thumbnail(video_path, 2, fmt='gif'))
    fp.close()
    diff = compare_images(thumb_path, path)
    assert diff < 1.0


@pytest.mark.slow
def test_get_thumbnail_tiff(tmpfile):
    fp, path = tmpfile
    fp.write(get_thumbnail(video_path, 2, fmt='tiff'))
    fp.close()
    diff = compare_images(thumb_path, path)
    assert diff < 1.0


@pytest.mark.slow
def test_get_thumbnail_bmp(tmpfile):
    fp, path = tmpfile
    fp.write(get_thumbnail(video_path, 2, fmt='bmp'))
    fp.close()
    diff = compare_images(thumb_path, path)
    assert diff < 1.0


@pytest.mark.slow
def test_extract_audio_copy(tmpfile):
    fp, path = tmpfile
    extract_audio(video_path, path, fmt='mp4')

    original = MediaInfo(video_path)
    mi = MediaInfo(path)

    assert 'mp4' in mi.format.name
    assert len(mi.streams) == 1
    assert mi.has_audio
    assert not mi.has_video
    assert not mi.has_subtitles

    diff = abs(mi.format.duration.total_seconds() - original.format.duration.total_seconds())
    assert diff == pytest.approx(0, abs=0.1)


@pytest.mark.slow
def test_extract_audio_downmix(tmpfile):
    fp, path = tmpfile
    extract_audio(video_path, path, codec='libopus', fmt='ogg', channels=2)

    original = MediaInfo(video_path)
    mi = MediaInfo(path)

    assert mi.format.name == 'ogg'
    assert len(mi.streams) == 1
    assert mi.has_audio
    assert not mi.has_video
    assert not mi.has_subtitles

    diff = abs(mi.format.duration.total_seconds() - original.format.duration.total_seconds())
    assert diff == pytest.approx(0, abs=0.1)


@pytest.mark.slow
def test_remove_audio(tmpfile):
    fp, path = tmpfile
    remove_audio(video_path, path, fmt='matroska')

    original = MediaInfo(video_path)
    mi = MediaInfo(path)

    assert 'matroska' in mi.format.name
    assert len(mi.streams) == 1
    assert mi.has_video
    assert not mi.has_audio
    assert not mi.has_subtitles

    diff = abs(mi.format.duration.total_seconds() - original.format.duration.total_seconds())
    assert diff == pytest.approx(0, abs=0.1)

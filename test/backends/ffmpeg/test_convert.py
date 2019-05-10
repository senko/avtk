from datetime import timedelta
from decimal import Decimal

import pytest

from avtk.backends.ffmpeg.convert import (
    FFmpeg, Input, Output, Format,
    Audio, NoAudio, CopyAudio,
    Video, NoVideo, CopyVideo
)

from avtk.backends.ffmpeg.exceptions import NoMediaError
from .utils import asset_path


def test_simple_single_input_output():
    in_path = asset_path('video', 'sintel.mkv')
    f = FFmpeg(in_path, 'output.mp4')
    assert f.get_args() == ['-i', in_path, 'output.mp4']


def test_simple_multiple_input_output():
    in1_path = asset_path('video', 'sintel.mkv')
    in2_path = asset_path('audio', 'stereo.mp3')

    f = FFmpeg([in1_path, in2_path], ['out1.mp4', 'out2.mp4'])
    assert f.get_args() == ['-i', in1_path, '-i', in2_path, 'out1.mp4', 'out2.mp4']


def test_nonexistent_input_fails():
    with pytest.raises(NoMediaError):
        FFmpeg('nonexistent.mp4', 'output.mp4')


def test_input_seek_timedelta():
    in_path = asset_path('video', 'sintel.mkv')
    f = FFmpeg(Input(in_path, seek=timedelta(seconds=3.14)), 'output.mp4')
    assert f.get_args() == ['-ss', '3.14', '-i', in_path, 'output.mp4']


def test_input_seek_seconds():
    in_path = asset_path('video', 'sintel.mkv')
    f = FFmpeg(Input(in_path, seek=3), 'output.mp4')
    assert f.get_args() == ['-ss', '3.0', '-i', in_path, 'output.mp4']


def test_input_duration_timedelta():
    in_path = asset_path('video', 'sintel.mkv')
    f = FFmpeg(Input(in_path, duration=timedelta(seconds=3.14)), 'output.mp4')
    assert f.get_args() == ['-t', '3.14', '-i', in_path, 'output.mp4']


def test_input_duration_decimal():
    in_path = asset_path('video', 'sintel.mkv')
    f = FFmpeg(Input(in_path, duration=Decimal('3.14')), 'output.mp4')
    assert f.get_args() == ['-t', '3.14', '-i', in_path, 'output.mp4']


def test_specific_output_format():
    in_path = asset_path('video', 'sintel.mkv')
    f = FFmpeg(in_path, Output('output.ogv', fmt=Format('ogg')))
    assert f.get_args() == ['-i', in_path, '-f', 'ogg', 'output.ogv']


def test_unsupported_format_fails():
    in_path = asset_path('video', 'sintel.mkv')
    with pytest.raises(ValueError):
        FFmpeg(in_path, Output('output.mp4', fmt=Format('unsupported')))


def test_video_simple():
    in_path = asset_path('video', 'sintel.mkv')
    f = FFmpeg(in_path, Output('output.ogv', streams=[Video('libtheora')]))
    assert f.get_args() == ['-i', in_path, '-c:v', 'libtheora', 'output.ogv']


def test_no_video():
    in_path = asset_path('video', 'sintel.mkv')
    f = FFmpeg(in_path, Output('output.ogg', streams=[NoVideo]))
    assert f.get_args() == ['-i', in_path, '-vn', 'output.ogg']


def test_copy_video():
    in_path = asset_path('video', 'sintel.mkv')
    f = FFmpeg(in_path, Output('output.ogg', streams=[CopyVideo]))
    assert f.get_args() == ['-i', in_path, '-c:v', 'copy', 'output.ogg']


def test_video_scale():
    in_path = asset_path('video', 'sintel.mkv')
    f = FFmpeg(in_path, Output('output.ogv', streams=[Video('libtheora', scale=(320, 240))]))
    assert f.get_args() == ['-i', in_path, '-c:v', 'libtheora', '-vf', 'scale=320:240', 'output.ogv']


def test_video_frames():
    in_path = asset_path('video', 'sintel.mkv')
    f = FFmpeg(in_path, Output('output.ogv', streams=[Video('libtheora', frames=1)]))
    assert f.get_args() == ['-i', in_path, '-c:v', 'libtheora', '-frames:v', '1', 'output.ogv']


def test_video_bitrate():
    in_path = asset_path('video', 'sintel.mkv')
    f = FFmpeg(in_path, Output('output.ogv', streams=[Video('libtheora', bit_rate='2000k')]))
    assert f.get_args() == ['-i', in_path, '-c:v', 'libtheora', '-b:v', '2000k', 'output.ogv']


def test_video_extra():
    in_path = asset_path('video', 'sintel.mkv')
    f = FFmpeg(in_path, Output('output.ogv', streams=[Video('libx264', extra=['-crf', '23', '-preset', 'veryslow'])]))
    assert f.get_args() == ['-i', in_path, '-c:v', 'libx264', '-crf', '23', '-preset', 'veryslow', 'output.ogv']


def test_audio_simple():
    in_path = asset_path('audio', 'stereo.mp3')
    f = FFmpeg(in_path, Output('output.ogg', streams=[Audio('vorbis')]))
    assert f.get_args() == ['-i', in_path, '-c:a', 'vorbis', 'output.ogg']


def test_no_audio():
    in_path = asset_path('audio', 'stereo.mp3')
    f = FFmpeg(in_path, Output('output.ogg', streams=[NoAudio]))
    assert f.get_args() == ['-i', in_path, '-an', 'output.ogg']


def test_copy_audio():
    in_path = asset_path('audio', 'stereo.mp3')
    f = FFmpeg(in_path, Output('output.ogg', streams=[CopyAudio]))
    assert f.get_args() == ['-i', in_path, '-c:a', 'copy', 'output.ogg']


def test_audio_downmix():
    in_path = asset_path('audio', 'stereo.mp3')
    f = FFmpeg(in_path, Output('output.ogg', streams=[Audio('vorbis', channels=1)]))
    assert f.get_args() == ['-i', in_path, '-c:a', 'vorbis', '-ac', '1', 'output.ogg']


def test_audio_bitrate():
    in_path = asset_path('audio', 'stereo.mp3')
    f = FFmpeg(in_path, Output('output.ogg', streams=[Audio('vorbis', bit_rate='128k')]))
    assert f.get_args() == ['-i', in_path, '-c:a', 'vorbis', '-b:a', '128k', 'output.ogg']

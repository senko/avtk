"""
Convenience shortcut functions
==============================

The module :mod:`avtk.backends.ffmpeg.shortcuts` contains convenience helpers for often-used
functionality of the ffmpeg backend.

These functions are just wrappers around the lower-level FFmpeg and Probe modules.

"""

from .probe import MediaInfo

from .convert import (
    FFmpeg, Input, Output, Format,
    Audio, NoAudio, CopyAudio,
    Video, NoVideo, CopyVideo,
    NoSubtitles, CopySubtitles,
    H264, H265, AAC, MP4, VP9, Opus, WebM, Ogg
)

THUMBNAIL_FORMATS = ['png', 'jpg', 'gif', 'tiff', 'bmp']  #: Supported thumbnail formats


def inspect(source):
    """
    Inspects a media file and returns information about it.

    See the :class:`~avtk.backends.ffmpeg.probe.MediaInfo` documentation for a detailed
    description of the returned information.

    :param str source: Local file path or stream URL to inspect
    :returns: Information about the inspected file or stream
    :rtype: :class:`~avtk.backend.ffmpeg.probe.MediaInfo`
    :raises NoMediaError: if source doesn't exist or is of unknown format

    Example::

        >>> from avtk.backends.ffmpeg.shortcuts import inspect

        >>> info = inspect('test-media/video/sintel.mkv')
        >>> info.format.duration
        datetime.timedelta(seconds=5, microseconds=24000)
        >>> info.format.bit_rate
        2657539
        >>> info.has_video
        True
        >>> info.video_streams[0].codec
        <Codec(name=h264, type=video)>
        >>> info.has_audio
        True
        >>> info.audio_streams[0].codec
        <Codec(name=ac3, type=audio)>
        >>> info.has_subtitles
        True
    """

    return MediaInfo(source)


def get_thumbnail(source, seek, fmt='png'):
    """
    Extracts a thumbnail from a video file.

    :param str source: file path
    :param seek: position (in seconds) from which to get the thumbnail
    :type seek: *timedelta*, *int* or *float*
    :param str fmt: output image format (one of :data:`THUMBNAIL_FORMATS`)
    :returns: thumbnail data as a binary string in the specified format
    :rtype: bytes
    :raises ValueError: if image format is not supported
    :raises NoMediaError: if source doesn't exist or is of unknown format

    Example::

        from avtk.backends.ffmpeg.shortcuts import get_thumbnail

        png_data = get_thumbnail('test-media/video/sintel.mkv', timedelta(seconds=2))
        with open('/tmp/thumb.png', 'wb') as fp:
            fp.write(png_data)
    """

    if fmt not in THUMBNAIL_FORMATS:
        raise ValueError("image format %s is not supported" % fmt)

    extra = None

    if fmt == 'jpg':
        fmt = 'mjpeg'
    elif fmt == 'tiff':
        extra = ['-pix_fmt', 'rgb24']

    return FFmpeg(
        Input(source, seek=seek),
        Output(
            '-',
            streams=[
                Video(fmt, frames=1, extra=extra)
            ],
            fmt='image2'
        )
    ).run(text=False)


def extract_audio(source, output, fmt=None, codec=None, channels=None):
    """
    Extracts audio from the source media file and saves it to a separate output file.

    If codec is not specified, audio data will be copied directly from the input file, preserving
    quality. If the codec is specified, audio will be re-encoded. The transcode process is slower
    than pure copy and some quality loss is unavoidable.

    Note that the *codec* parameter is actually an encoder name, and should be one of the supported
    encoders from :func:`~avtk.backends.ffmpeg.cap.get_available_encoders()`. The somewhat-confusing *codec* name
    for the parameter is kept to be consistent with ffmpeg naming.

    :param str source: input file path or stream URL
    :param str output: output file path
    :param str fmt: output file format (optional, default: guess from output file name)
    :param str codec: output file codec (optional, default: copy from input)
    :param int channels: downmix to specified number of channels (optional)
    :raises NoMediaError: if source doesn't exist or is of unknown format

    Example::

        from avtk.backends.ffmpeg.shortcuts import extract_audio

        extract_audio('test-media/video/sintel.mkv', '/tmp/output.ogg', codec='libopus', channels=2)
    """

    audio_stream = Audio(codec, channels=channels) if codec is not None else CopyAudio

    return FFmpeg(
        source,
        Output(
            output,
            streams=[
                NoVideo,
                NoSubtitles,
                audio_stream
            ],
            fmt=Format(fmt) if fmt else None,
            # '-sn' doesn't completely remove all subtitles if chapters are present
            extra=['-map_chapters', '-1']
        )
    ).run()


def remove_audio(source, output, fmt=None, remove_subtitles=True):
    """
    Creates an output video file from the source with all audio streams removed.

    :param str source: input file path or stream URL
    :param str output: output file path
    :param str fmt: output file format (optional, default: guess from output file name)
    :param bool remove_subtitles: whether to remove subtitle streams as well (optional, default: True)
    :raises NoMediaError: if source doesn't exist or is of unknown format

    Example::

        from avtk.backends.ffmpeg.shortcuts import remove_audio

        remove_audio('test-media/video/sintel.mkv', '/tmp/silent.mkv')
    """

    subtitle_stream = NoSubtitles if remove_subtitles else CopySubtitles

    return FFmpeg(
        source,
        Output(
            output,
            streams=[
                CopyVideo,
                subtitle_stream,
                NoAudio
            ],
            fmt=Format(fmt) if fmt else None,
            # '-sn' doesn't completely remove all subtitles if chapters are present
            extra=['-map_chapters', '-1']
        )
    ).run()


def convert_to_h264(source, output, preset=None, crf=None, video_bitrate=None, audio_bitrate=None, **kwargs):
    """
    Converts a video file to MP4 format using H264 for video and AAC for audio.

    See https://trac.ffmpeg.org/wiki/Encode/H.264 for tips on H.264 encoding with ffmpeg, and for description
    of CRF and preset parameters.

    :param str source: input file path or stream URL
    :param str output: output file path
    :param str preset: encoder preset (quality / encoding speed tradeoff) - optional
    :param str crf: constant rate factor (determines target quality) - optional
    :param video_bitrate: target video bitrate - optional
    :type video_bitrate: int or str
    :param audio_bitrate: target audio bitrate - optional
    :type audio_bitrate: int or str
    :param tuple scale: resize output to specified size (width, height) - optional
    :param list(str) extra: additional ffmpeg command line arguments - optional
    :raises NoMediaError: if source doesn't exist or is of unknown format

    If *scale* is set, either width or height may be ``-1`` to use the optimal size for preserving aspect ratio,
    or ``0`` to keep the original size.

    Bitrates should be specified as integers or as strings in 'NUMk' or 'NUMm' format.

    Example::

        from avtk.backends.ffmpeg.shortcuts import convert_to_h264

        convert_to_h264(
            'test-media/video/sintel.mkv',
            '/tmp/out.mkv',
            preset='fast',
            crf=23,
            video_bitrate='2m',
            audio_bitrate='128k'
        )
    """

    return FFmpeg(
        source,
        Output(
            output,
            streams=[
                H264(preset=preset, crf=crf, bit_rate=video_bitrate, **kwargs),
                AAC(channels=2, bit_rate=audio_bitrate),
                NoSubtitles
            ],
            fmt=MP4(faststart=True)
        )
    ).run()


def convert_to_webm(source, output, crf=None, audio_bitrate=None, **kwrags):
    """
    Converts a video file to WebM format using VP9 for video and Opus for audio.

    Uses a single-pass constant quality encode process for VP9. See https://trac.ffmpeg.org/wiki/Encode/VP9 for
    tips on VP9 encoding with ffmpeg, and for description of the CRF parameter.

    :param str source: input file path or stream URL
    :param str output: output file path
    :param str crf: constant rate factor (determines target quality) - optional, default is 31
    :param audio_bitrate: target audio bitrate - optional
    :type audio_bitrate: int or str
    :param tuple scale: resize output to specified size (width, height) - optional
    :param list(str) extra: additional ffmpeg command line arguments - optional
    :raises NoMediaError: if source doesn't exist or is of unknown format

    If *scale* is set, either width or height may be ``-1`` to use the optimal size for preserving aspect ratio,
    or ``0`` to keep the original size.

    Audio bitrate should be specified as integer or as string in 'NUMk' format.

    Example::

        from avtk.backends.ffmpeg.shortcuts import convert_to_webm

        convert_to_webm(
            'test-media/video/sintel.mkv',
            '/tmp/out.webm',
            crf=31,
            audio_bitrate='128k'
        )
    """

    return FFmpeg(
        source,
        Output(
            output,
            streams=[
                VP9(crf=crf),
                Opus(channels=2, bit_rate=audio_bitrate),
                NoSubtitles
            ],
            fmt=WebM()
        )
    ).run()


def convert_to_hevc(source, output, preset=None, crf=None, video_bitrate=None, audio_bitrate=None, **kwargs):
    """
    Converts a video file to MP4 format using H.265 (HEVC) for video and AAC for audio.

    Uses a single-pass constant quality encode process for HEVC. See https://trac.ffmpeg.org/wiki/Encode/H.265 for
    tips on HEVC encoding with ffmpeg, and for description of the CRF and preset parameters.

    :param str source: input file path or stream URL
    :param str output: output file path
    :param str preset: encoder preset (quality / encoding speed tradeoff) - optional
    :param str crf: constant rate factor (determines target quality) - optional
    :param audio_bitrate: target audio bitrate - optional
    :type audio_bitrate: int or str
    :param tuple scale: resize output to specified size (width, height) - optional
    :param list(str) extra: additional ffmpeg command line arguments - optional
    :raises NoMediaError: if source doesn't exist or is of unknown format

    If *scale* is set, either width or height may be ``-1`` to use the optimal size for preserving aspect ratio,
    or ``0`` to keep the original size.

    Bitrates should be specified as integers or as strings in 'NUMk' or 'NUMm' format.

    Example::

        from avtk.backends.ffmpeg.shortcuts import convert_to_hevc

        convert_to_hevc(
            'test-media/video/sintel.mkv',
            '/tmp/out.mp4'
        )
    """

    return FFmpeg(
        source,
        Output(
            output,
            streams=[
                H265(preset=preset, crf=crf, bit_rate=video_bitrate, **kwargs),
                AAC(channels=2, bit_rate=audio_bitrate),
                NoSubtitles
            ],
            fmt=MP4(faststart=True)
        )
    ).run()


def convert_to_aac(source, output, bit_rate=None, **kwargs):
    """
    Converts a media file to audio MP4 using AAC codec.

    :param str source: input file path or stream URL
    :param str output: output file path
    :param bit_rate: target audio bitrate - optional
    :type bit_rate: int or str
    :param int channels: number of channels to downmix to - optional
    :raises NoMediaError: if source doesn't exist or is of unknown format

    Bit rate should be specified as integers or as strings in 'NUMk' or 'NUMm' format.

    Example::

        from avtk.backends.ffmpeg.shortcuts import convert_to_aac

        convert_to_aac(
            'test-media/audio/stereo.mp3',
            '/tmp/out.aac',
            bit_rate='96k'
        )
    """

    return FFmpeg(
        source,
        Output(
            output,
            streams=[
                AAC(**kwargs),
                NoVideo,
                NoSubtitles
            ],
            fmt=MP4(faststart=True)
        )
    ).run()


def convert_to_opus(source, output, bit_rate=None, **kwargs):
    """
    Converts a media file to Opus-encoded Ogg file.

    :param str source: input file path or stream URL
    :param str output: output file path
    :param bit_rate: target audio bitrate - optional
    :type bit_rate: int or str
    :param int channels: number of channels to downmix to - optional
    :raises NoMediaError: if source doesn't exist or is of unknown format

    Bit rate should be specified as integers or as strings in 'NUMk' or 'NUMm' format.

    Example::

        from avtk.backends.ffmpeg.shortcuts import convert_to_opus

        convert_to_opus(
            'test-media/audio/stereo.mp3',
            '/tmp/out.ogg',
            bit_rate='96k'
        )
    """

    return FFmpeg(
        source,
        Output(
            output,
            streams=[
                Opus(**kwargs),
                NoVideo,
                NoSubtitles
            ],
            fmt=Ogg()
        )
    ).run()

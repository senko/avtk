"""
Converting media files
======================

This module contains wrappers for the ``ffmpeg`` command-line utility. The aim is to expose most-often
used functionality in a concise and Pythonic way, while still allowing passing extra options unsupported
by AVTK to the underlying ffmpeg invocation.

Synopsis::

    FFmpeg(inputs, outputs).run()

Inputs and outputs can either be lists (in case of multiple inputs or outputs), or a single item (in case
of single input or output).

Input can be either a string (input file path or stream URL), or an instance of :class:`Input`. Output can
either be a string (output file path) or an instance of :class:`Output` specifying the format, codecs to use
and other options.

Examples::

    # Convert MP4 to MKV with default codecs and options
    FFmpeg('input.mp4', 'output.mkv').run()

    # Convert 1 minute of input video starting at 5min mark into 1080p HEVC video
    # with 160kbit AAC audio, stripping any subtitles
    FFmpeg(
        Input('input.mkv', seek=300, duration=60),
        Output('output.mp4',
            Video('libx265', scale=(-1, 1080), preset='veryfast', crf=20),
            Audio('aac', bit_rate='160k'),
            NoSubtitles
        )
    ).run()

    # Split video into separate video and audio files
    FFmpeg(['input.mp4', [
        Output('video.mp4', streams=[H264(), NoAudio]),
        Output('audio.m4a', streams=[AAC(), NoVideo])
    ]).run()

Stream, format, input and output definitions all take an optional *extra* parameter - a list of strings
that are passed directly to ffmpeg in appropriate places. This allows you to use all functionality of ffmpeg
without explicit support in AVTK.
"""

from datetime import timedelta
from decimal import Decimal
from urllib.parse import urlparse
import os.path

from .cap import get_available_formats, get_available_encoders, Codec
from .exceptions import NoMediaError
from .run import ffmpeg


class Duration:
    """
    Helper class for parsing duration and time values - don't use it directly.

    Supported duration types: *timedelta*, *Decimal*, *float*, *int*

    Examples::

        Duration(timedelta(seconds=3.14))
        Duration('5.25')
        Duration(60.5)
        Duration(3600)
    """

    def __init__(self, val):
        if isinstance(val, Duration):
            self.duration = val.duration
        if isinstance(val, timedelta):
            self.duration = val
        elif isinstance(val, Decimal):
            self.duration = timedelta(microseconds=int(1000000 * val))
        else:
            self.duration = timedelta(seconds=val)

    def __str__(self):
        return str(self.duration.total_seconds())


class Stream:
    """
    Output stream definition - base class

    Don't use this class directly. Instead use :class:`Video`, :class:`Audio` or :class:`Subtitle`
    subclass, or one of the convenience helper classes for specific codecs.
    """

    def __init__(self, encoder):
        self._check_encoder(encoder)
        self.encoder = encoder

    def _check_encoder(self, name):
        if name in [None, 'copy']:
            return

        encoders = get_available_encoders()
        if name not in encoders:
            raise ValueError("unsupported encoder %s" % name)

        c = encoders[name]

        if c.type != self.stream_type:
            raise ValueError("%s encoder %s can't be used for %s stream" % (
                c.type,
                name,
                self.stream_type
            ))

    def __str__(self):
        return ' '.join(self.get_args())


class Video(Stream):
    """
    Output video stream definition

    :param str encoder: encoder to use
    :param tuple scale: resize output to specified size (width, height) - optional
    :param bit_rate: target video bitrate - optional
    :type bit_rate: int or str
    :param int frames: number of frames to output - optional
    :param list(str) extra: additional ffmpeg command line arguments for the stream - optional

    Use :func:`avtk.backends.ffmpeg.cap.get_available_encoders` to get information on supported encoders. You
    can also use *None* to disable the video stream (see :data:`NoVideo`), or ``copy`` to copy the video
    stream without re-encoding (see :data:`CopyVideo`).

    If *scale* is set, either width or height may be ``-1`` to use the optimal size for preserving aspect ratio,
    or ``0`` to keep the original size.

    Bitrates should be specified as integers or as strings in 'NUMk' or 'NUMm' format.

    Examples::

        # Encode to 480p H.264 at 2mbps, keeping aspect ratio
        Video('libx264', scale=(-1:480), bit_rate='2m')

        # Convert only one frame to PNG
        Video('png', frames=1)

        # Passthrough (copy video stream from input to output)
        Video('copy')
        # or
        CopyVideo

        # Disable (ignore) video streams
        NoVideo
    """

    stream_type = Codec.TYPE_VIDEO

    def __init__(self, encoder, scale=None, bit_rate=None, frames=None, extra=None):
        super().__init__(encoder)
        self.scale = scale  # (w, h) tuple, either may be -1 to autocalc aspect
        self.bit_rate = bit_rate
        self.frames = frames
        self.extra = extra

    def get_args(self):
        if self.encoder is None:
            return ['-vn']

        args = ['-c:v', self.encoder]

        if self.scale:
            args.extend([
                '-vf',
                'scale=%s' % ('%d:%d' % self.scale if isinstance(self.scale, tuple) else self.scale)
            ])

        if self.bit_rate:
            args.extend(['-b:v', str(self.bit_rate)])

        if self.frames:
            args.extend(['-frames:v', str(self.frames)])

        if self.extra:
            args.extend(self.extra)

        return args


class H264(Video):
    """
    Video stream using H.264 (AVC) codec and libx264 encoder

    :param str preset: encoder preset (quality / encoding speed tradeoff) - optional
    :param str crf: constant rate factor (determines target quality) - optional
    :param tuple scale: resize output to specified size (width, height) - optional
    :param bit_rate: target video bitrate - optional
    :type bit_rate: int or str
    :param int frames: number of frames to output - optional
    :param list(str) extra: additional ffmpeg command line arguments for the stream - optional

    See https://trac.ffmpeg.org/wiki/Encode/H.264 for tips on H.264 encoding with ffmpeg, and for description
    of CRF and preset parameters.

    Examples::

        # Encode to high quality 1080p, taking as much time as needed
        H264(preset='veryslow', crf=18)
    """

    def __init__(self, preset=None, crf=None, **kwargs):
        extra = []
        if preset:
            extra.extend(['-preset', preset])
        if crf:
            extra.extend(['-crf', str(crf)])

        super().__init__('libx264', extra=extra, **kwargs)


class H265(Video):
    """
    Video stream using H.265 (HEVC) codec and libx265 encoder

    :param str preset: encoder preset (quality / encoding speed tradeoff) - optional
    :param str crf: constant rate factor (determines target quality) - optional
    :param tuple scale: resize output to specified size (width, height) - optional
    :param bit_rate: target video bitrate - optional
    :type bit_rate: int or str
    :param int frames: number of frames to output - optional
    :param list(str) extra: additional ffmpeg command line arguments for the stream - optional

    Uses a single-pass constant quality encode process for HEVC. See https://trac.ffmpeg.org/wiki/Encode/H.265 for
    tips on HEVC encoding with ffmpeg, and for description of the CRF and preset parameters.

    Example::

        # Encode to high quality, taking as much time as needed
        H265(preset='veryslow', crf=20)
    """

    def __init__(self, preset=None, crf=None, **kwargs):
        extra = []
        if preset:
            extra.extend(['-preset', preset])
        if crf:
            extra.extend(['-crf', str(crf)])

        super().__init__('libx265', extra=extra, **kwargs)


class VP9(Video):
    """
    Video stream using VP9 codec and libvpx-vp9 encoder

    :param str crf: constant rate factor (determines target quality) - optional, default is 31
    :param tuple scale: resize output to specified size (width, height) - optional
    :param int frames: number of frames to output - optional
    :param list(str) extra: additional ffmpeg command line arguments for the stream - optional

    Uses a single-pass constant quality encode process for VP9. See https://trac.ffmpeg.org/wiki/Encode/VP9 for
    tips on VP9 encoding with ffmpeg, and for description of the CRF parameter.

    Example::

        # Encode using default parameters (CRF of 31)
        VP9()
    """

    def __init__(self, crf=None, **kwargs):
        if crf is None:
            crf = 31

        # Uses constanct quality mode: https://trac.ffmpeg.org/wiki/Encode/VP9#constantq
        extra = ['-crf', str(crf), '-b:v', '0', '-quality', 'good']
        super().__init__('libvpx-vp9', extra=extra, **kwargs)


class AV1(Video):
    """
    Video stream using AV1 codec and libaom-av1 encoder

    Based on AV1 wiki guide: https://trac.ffmpeg.org/wiki/Encode/AV1

    .. warning::

        Uses an extremely slow and unoptimized reference AV1 encoder implementation. You
        probably don't want to use this.
    """

    def __init__(self, crf=None, **kwargs):
        if crf is None:
            crf = 30

        # Based on AV1 wiki guide: https://trac.ffmpeg.org/wiki/Encode/AV1#ConstantQuality
        extra = ['-crf', str(crf), '-b:v', '0', '-strict', 'experimental']
        super().__init__('libaom-av1', extra=extra, **kwargs)


class Audio(Stream):
    """
    Output audio stream definition

    :param str encoder: encoder to use
    :param int channels: number of channels to downmix to - optional
    :param bit_rate: target audio bitrate - optional
    :type bit_rate: int or str
    :param list(str) extra: additional ffmpeg command line arguments for the stream - optional

    Use :func:`avtk.backends.ffmpeg.cap.get_available_encoders` to get information on supported encoders. You
    can also use *None* to disable the audio streams (see :data:`NoAudio`), or ``copy`` to copy the stream
    without re-encoding (see :data:`CopyAudio`).

    Bitrates should be specified as integers or as strings in 'NUMk' format.

    Examples::

        # Encode to AAC at 256kbps, while downmixing to stereo
        Audio('aac', channels=2, bit_rate='256k')

        # Passthrough (copy audio stream directly to output)
        Audio('copy')
        # or
        CopyAudio

        # Disable (ignore) audio stream
        NoAudio
    """

    stream_type = Codec.TYPE_AUDIO

    def __init__(self, encoder, channels=None, bit_rate=None, extra=None):
        super().__init__(encoder)
        self.channels = channels
        self.bit_rate = bit_rate
        self.extra = extra

    def get_args(self):
        if self.encoder is None:
            return ['-an']

        args = ['-c:a', self.encoder]
        if self.channels:
            args.extend(['-ac', str(self.channels)])

        if self.bit_rate:
            args.extend(['-b:a', str(self.bit_rate)])

        if self.extra:
            args.extend(self.extra)

        return args


class AAC(Audio):
    """
    Audio stream using AAC

    :param int channels: number of channels to downmix to - optional
    :param bit_rate: target audio bitrate - optional
    :type bit_rate: int or str
    :param list(str) extra: additional ffmpeg command line arguments for the stream - optional
    """

    def __init__(self, **kwargs):
        super().__init__('aac', **kwargs)


class Opus(Audio):
    """
    Audio stream using Opus codec and libopus encoder

    :param int channels: number of channels to downmix to - optional
    :param bit_rate: target audio bitrate - optional
    :type bit_rate: int or str
    :param list(str) extra: additional ffmpeg command line arguments for the stream - optional
    """

    def __init__(self, **kwargs):
        super().__init__('libopus', **kwargs)


class Subtitle(Stream):
    """
    Output subtitle stream definition

    Use :func:`avtk.backends.ffmpeg.cap.get_available_encoders` to get information on supported encoders. You
    can also use *None* to disable the subtitle streams (see :data:`NoSubtitles`), or ``copy`` to copy the stream
    without converting (see :data:`CopySubtitles`).
    """

    stream_type = Codec.TYPE_SUBTITLE

    def get_args(self):
        if self.encoder is None:
            return ['-sn']

        return ['-c:s', self.encoder]


NoVideo = Video(None)  #: Disable video
CopyVideo = Video('copy')  #: Dopy video without re-encoding
NoAudio = Audio(None)  #: Disable audio
CopyAudio = Audio('copy')  #: Copy audio without re-encoding
NoSubtitles = Subtitle(None)  #: Disable subtitles
CopySubtitles = Subtitle('copy')  #: Copy subtitles


class Input:
    """
    Define input source

    :param str source: input file path or stream URL
    :param seek: seek in source before processing - optional
    :type seek: see :class:`Duration`
    :param duration: how much of source to process - optional
    :type duration: see :class:`Duration`
    :param list(str) extra: additional ffmpeg command line arguments for the input - optional
    :raises NoMediaError: if source doesn't exist

    Source can either be a local file, capture device or network stream
    supported by the underlying ``ffmpeg`` tool.

    Examples::

        # Use local file, seek to 2min mark and process 5 minutes
        Input('test-media/video/sintel.mkv', seek=120, duration=300)

        # Process one minute of an internet radio stream
        Input('https://example.radio.fm/stream.aac', duration=60)
    """

    def __init__(self, source, seek=None, duration=None, extra=None):
        self.source = source
        self.seek = Duration(seek) if seek else None
        self.duration = Duration(duration) if duration else None
        self.extra = extra

        url = urlparse(source)
        if url.scheme in ['', 'file']:
            if not os.path.isfile(url.path):
                raise NoMediaError('Source file not found: ' + url.path)

    def get_args(self):
        args = []

        if self.seek:
            args.extend(['-ss', str(self.seek)])

        if self.duration:
            args.extend(['-t', str(self.duration)])

        if self.extra:
            args.extend(self.extra)

        args.extend(['-i', self.source])

        return args

    def __str__(self):
        return ' '.join(self.get_args())


class Format:
    """
    Output container format definition

    :param str name: format name
    :param list(str) extra: additional ffmpeg command line arguments for the input - optional

    Use :func:`avtk.backends.ffmpeg.cap.get_available_formats` to get information on supported formats.
    """

    def __init__(self, name, extra=None):
        if name not in get_available_formats():
            raise ValueError("unsupported format %s" % name)

        self.name = name
        self.extra = extra

    def get_args(self):
        args = ['-f', self.name]
        if self.extra:
            args.extend(self.extra)
        return args


class MP4(Format):
    """
    MP4 output format

    :param bool faststart: place the *moov atom* metadata at the beginning - optional, default *False*

    This option is required if you want to support playback of incomplete MP4 file (that is, start playback
    before the entire file is downloaded).
    """

    def __init__(self, faststart=False):
        extra = []
        if faststart:
            extra.extend(['-movflags', 'faststart'])

        super().__init__('mp4', extra)


class WebM(Format):
    """WebM output format"""

    def __init__(self):
        super().__init__('webm')


class Matroska(Format):
    """Matroska (MKV) output format"""

    def __init__(self):
        super().__init__('matroska')


class Ogg(Format):
    """Ogg output format"""

    def __init__(self):
        super().__init__('ogg')


class Output:
    """
    Defines an output to the transcoding process.

    :param str target: output file path
    :param streams: output stream definitions - optional
    :type streams: :class:`Stream` or *None*
    :param fmt: output format - optional
    :param fmt: :class:`Format`, *str* or *None*
    :param list(str) extra: additional ffmpeg command line arguments for the output - optional

    If streams are not specified, all input streams will be transcoded using default codecs
    for the specified format.

    If format is not specified, it is guessed from the output file name. If specified, it can
    either be a format name or an instance of :class:`Format`.
    """

    def __init__(self, target, streams=None, fmt=None, extra=None):
        self.target = target
        self.streams = [] if streams is None else streams
        self.extra = extra

        if fmt is None:
            self.format = None
        elif isinstance(fmt, Format):
            self.format = fmt
        else:
            self.format = Format(fmt)

    def get_args(self):
        args = []

        for s in self.streams:
            args.extend(s.get_args())

        if self.format:
            args.extend(self.format.get_args())

        if self.extra:
            args.extend(self.extra)

        args.append(self.target)
        return args

    def __str__(self):
        return ' '.join(self.get_args())


class FFmpeg:
    """
    Convert audio/video

    :param inputs: one or more inputs
    :type inputs: :class:`Input`, *str*, list(:class:`Input`) or *list(str)*
    :param outputs: one or more outputs
    :type outputs: :class:`Output`, *str*, list(:class:`Output`) or *list(str)*

    Input(s) and output(s) can either be specified as strings representing input and output
    files respectively, or as :class:`Input` and :class:`Output` objects with all the configuration
    exposed by those classes.

    If only one input is used, it can be specified directly. If multiple inputs are used, specify
    a list of inputs. Likewise for outputs.

    Examples::

        # Convert input to output
        FFmpeg('input.mp4', 'output.mkv').run()

        # Combine audio and video
        FFmpeg(['video.mp4', 'audio.m4a'], 'output.mkv').run()

        # Split audio and video
        FFmpeg(['input.mp4', [
            Output('video.mp4', streams=[H264(), NoAudio]),
            Output('audio.m4a', streams=[AAC(), NoVideo])
        ]).run()
    """

    def __init__(self, inputs, outputs):
        if not isinstance(inputs, list):
            inputs = [inputs]
        self.inputs = [(i if isinstance(i, Input) else Input(i)) for i in inputs]

        if not isinstance(outputs, list):
            outputs = [outputs]
        self.outputs = [(o if isinstance(o, Output) else Output(o)) for o in outputs]

    def get_args(self):
        """
        Builds ffmpeg command line arguments

        :returns: ffmpeg command line arguments for the specified process
        :rtype: list of strings

        Example::

            >>> FFmpeg(['input.mp4', [
            ...     Output('video.mp4', streams=[H264(), NoAudio]),
            ...     Output('audio.m4a', streams=[AAC(), NoVideo])
            ... ]).get_args()
            [
                '-i', 'input.mp4',
                '-c:v', 'libx264', '-an', 'video.mp4',
                '-c:a', 'aac', '-vn', 'audio.m4a'
            ]
        """

        args = []
        for i in self.inputs:
            args.extend(i.get_args())
        for o in self.outputs:
            args.extend(o.get_args())
        return args

    def run(self, text=True):
        """
        Runs the conversion process

        Uses :meth:`get_args` to build the command line and runs it using :func:`avtk.backends.ffmpeg.run.ffmpeg`.

        :param bool text: whether to return the output as text - optional, default true
        :returns: output (stdout) from ``ffmpeg`` invocation
        :rtype: *str* if *text=True* (default), *bytes* if *text=False*
        """

        return ffmpeg(self.get_args(), text=text)

    def __str__(self):
        return ' '.join(self.get_args())

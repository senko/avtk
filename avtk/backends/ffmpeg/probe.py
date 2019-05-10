"""
Inspecting media files
======================

A wrapper around ffprobe that gathers and makes available information about the inspected media
file or stream in a Pythonic way.
"""

from datetime import timedelta
from decimal import Decimal
from fractions import Fraction
import os.path
from urllib.parse import urlparse

from .cap import Codec as CodecCapability
from .run import ffprobe
from .exceptions import NoMediaError


def _parse_duration(val):
    return timedelta(microseconds=int(Decimal(val) * 1000000))


class MediaInfo:
    """
    Represents all available information about the inspected media file or stream.

    :Attributes:
        * raw (*dict*) - raw ``ffprobe`` JSON output
        * format (:class:`Format`) - container (format) information
        * streams (list(:class:`Stream`)) - audio, video and subtitle streams information

    The :func:`avtk.backends.ffmpeg.shortcuts.inspect` function is a simple wrapper around the
    MediaInfo constructor.

    Example::

        >>> info = MediaInfo(test-media/video/sintel.mkv')
    """

    def __init__(self, source):
        self.raw = self._probe(source)
        self.format = Format(self.raw['format'])
        self.streams = [Stream._parse(stream) for stream in self.raw['streams']]

    @staticmethod
    def _probe(source):
        url = urlparse(source)
        if url.scheme in ['', 'file']:
            if not os.path.isfile(url.path):
                raise NoMediaError('Source file not found: ' + url.path)

        return ffprobe(['-show_format', '-show_streams', source])

    @property
    def audio_streams(self):
        """
        List of audio streams in the media object"""
        return [s for s in self.streams if isinstance(s, AudioStream)]

    @property
    def video_streams(self):
        """List of video streams in the media object"""
        return [s for s in self.streams if isinstance(s, VideoStream)]

    @property
    def subtitle_streams(self):
        """List of subtitle streams in the media objects"""
        return [s for s in self.streams if isinstance(s, SubtitleStream)]

    @property
    def has_audio(self):
        """Whether there is at least one audio stream present"""
        return len(self.audio_streams) > 0

    @property
    def has_video(self):
        """Whether there is at least one video stream present"""
        return len(self.video_streams) > 0

    @property
    def has_subtitles(self):
        """Whether there is at least one subtitles stream present"""
        return len(self.subtitle_streams) > 0


class Codec:
    """
    Information about the codec used in a stream.

    :Attributes:
        * name (*str*) - codec (short) name
        * type (*str*) - codec type, one of :data:`TYPE_AUDIO`, :data:`TYPE_VIDEO`,
          :data:`TYPE_SUBTITLE` or :data:`TYPE_DATA`
        * description (*str*) - codec description (long name)
        * profile (*str* or *None*) - profile used, if applicable
    """

    TYPE_AUDIO = CodecCapability.TYPE_AUDIO  #: Audio codec
    TYPE_VIDEO = CodecCapability.TYPE_VIDEO  #: Video codec
    TYPE_SUBTITLE = CodecCapability.TYPE_SUBTITLE  #: Subtitles codec
    TYPE_DATA = 'data'  #: Raw (unknown) data

    def __init__(self, raw):
        self.type = raw['codec_type']
        self.name = raw['codec_name']
        self.description = raw['codec_long_name']
        self.profile = raw.get('profile')

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<Codec(name=%s, type=%s)>' % (self.name, self.type)


class Stream:
    """
    Information about a stream in a media file.

    This is a base class handling information common to most stream types. Streams returned in
    :class:`MediaInfo` object will be one of the subclasses holding more information.

    :Subclasses:
        * :class:`VideoStream` - for video streams
        * :class:`AudioStream` - for audio streams
        * :class:`SubtitleStream` - for subtitle streams
        * :class:`DataStream` - raw or unrecognized data

    :Attributes:
        * codec (:class:`Codec`) - codec used in this stream
        * index (*int*) - 0-based index of this stream in the container
        * time_base (*Fraction*) - unit of time for timestamp calculations
        * nb_frames (*int* or *None*) - total number of frames in the stream
        * start_time (*timedelta* or *None*) - start timestamp of the stream
        * duration (*timedelta* or *None*) - duration of the stream
        * duration_ts (*int* or *None*) - duration in *time_base* units
        * bit_rate (*int* or *None*) - bit rate of the stream
        * tags (*dict*) - stream tags, if any
    """

    def __init__(self, raw):
        self.codec = Codec(raw)
        self.index = raw['index']

        self.time_base = Fraction(raw['time_base'])
        self.nb_frames = int(raw['nb_frames']) if 'nb_frames' in raw else None
        self.start_time = _parse_duration(raw['start_time']) if 'start_time' in raw else None
        self.duration = _parse_duration(raw['duration']) if 'duration' in raw else None
        self.duration_ts = int(raw['duration_ts']) if 'duration_ts' in raw else None
        self.bit_rate = int(raw['bit_rate']) if 'bit_rate' in raw else None
        self.tags = raw.get('tags', {})

    @staticmethod
    def _parse(raw):
        ctype = raw.get('codec_type')
        if ctype == Codec.TYPE_VIDEO:
            return VideoStream(raw)
        elif ctype == Codec.TYPE_AUDIO:
            return AudioStream(raw)
        elif ctype == Codec.TYPE_SUBTITLE:
            return SubtitleStream(raw)
        elif ctype == Codec.TYPE_DATA:
            return DataStream(raw)
        else:
            raise NoMediaError("unsupported codec type '%s'" % ctype)

    def __str__(self):
        return str(self.codec)


class VideoStream(Stream):
    """
    Holds video-specific information about a stream.

    :Attributes:
        * width (*int*) - display width, in pixels
        * height (*int*) - display height, in pixels
        * display_aspect_ratio (*str*) - aspect ratio, in 'W:H' format
        * pix_fmt (*str*) - image pixel format name
        * has_b_frames (*int*) - how many frames might need reordering for B-frame decoding
          or 0 if B-frames are not used

    For a list of all known pixel formats and more information about them, run ``ffmpeg -pix_fmts``.
    """

    def __init__(self, raw):
        super().__init__(raw)

        self.width = raw['width']
        self.height = raw['height']
        self.display_aspect_ratio = raw['display_aspect_ratio']
        self.pix_fmt = raw['pix_fmt']
        self.has_b_frames = raw['has_b_frames']

        try:
            self.frame_rate = Fraction(raw['avg_frame_rate'])
        except ZeroDivisionError:
            self.frame_rate = None

    def __repr__(self):
        return '<Video(codec=%s, size=%dx%d, fps=%s)>' % (
            repr(self.codec),
            self.width,
            self.height,
            str(self.frame_rate) if self.frame_rate else 'n/a',
        )


class AudioStream(Stream):
    """
    Holds video-specific information about a stream.

    :Attributes:
        * channels (*int*) - number of channels
        * channel_layout (*str*) - channel layout
        * sample_fmt (*str*) - sample format
        * sample_rate (*int*) - audio sample rate in Hz

    For a list of all known channel names and standard layouts, run ``ffmpeg -layouts``. To get a list of
    all known sample formats, run ``ffmpeg -sample_fmts``.
    """

    def __init__(self, raw):
        super().__init__(raw)

        self.channels = raw['channels']
        self.channel_layout = raw.get('channel_layout')
        self.sample_fmt = raw['sample_fmt']
        self.sample_rate = int(raw['sample_rate'])

    def __repr__(self):
        return '<Audio(codec=%s, sample_rate=%s, bit_rate=%s)' % (
            repr(self.codec),
            (str(self.sample_rate) + 'Hz') if self.sample_rate else 'n/a',
            "%dkbps" % int(self.bit_rate / 1000) if self.bit_rate else 'n/a'
        )


class SubtitleStream(Stream):
    """
    Holds information about a subtitle stream.

    :Attributes:
        * language (*str*) - language
    """

    def __init__(self, raw):
        super().__init__(raw)

        self.language = self.tags.get('language')

    def __str__(self):
        return self.language

    def __repr__(self):
        return '<Subtitles(lang=%s)>' % self.language


class DataStream(Stream):
    """
    Holds information about unknown or raw data stream.

    :Attributes:
        * raw (*dict*) - raw data parsed from ``ffprobe``
    """

    def __init__(self, raw):
        super().__init__(raw)
        self.raw = raw

    def __str__(self):
        return repr(self.raw)

    def __repr__(self):
        return '<Data>'


class Format:
    """
    Information about the container format.

    :Attributes:
        * name (*str*) - format name, or multiple comma-separated format names (aliases)
        * names (*list(str)*) - list of format names
        * description (*str*) - format description (long name)
        * start_time (*timedelta* or *None*) - start timestamp of the entire media object
        * duration (*timedelta* or *None*) - duration of the entire media object
        * size (*int* or *None*) - size in bytes, if known
        * bit_rate (*int* or *None*) - bit rate of the entire media object
        * tags (*dict*) - stream tags, if any
    """

    def __init__(self, raw):
        self.name = raw['format_name']
        self.names = self.name.split(',')
        self.description = raw['format_long_name']

        self.start_time = _parse_duration(raw['start_time']) if 'start_time' in raw else None
        self.duration = _parse_duration(raw['duration']) if 'duration' in raw else None
        self.size = int(raw['size']) if 'size' in raw else None
        self.bit_rate = int(raw['bit_rate']) if 'bit_rate' in raw else None
        self.tags = raw.get('tags', {})

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<Format(format=%s, duration=%s, bitrate=%s)>' % (
            self.name,
            str(self.duration) if self.duration else 'n/a',
            "%dkbps" % int(self.bit_rate / 1000) if self.bit_rate else 'n/a'
        )

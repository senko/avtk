"""
Codecs, encoders and formats support in FFmpeg
==============================================

The :mod:`avtk.backends.ffmpeg.cap` module can be used to discover versions
of the available ``ffmpeg`` and ``ffprobe`` command-line tools, and list codecs, encoders
and formats they support.

Example usage::

    >>> from avtk.backends.ffmpeg import cap

    >>> cap.get_ffmpeg_version()
    '4.1.2'
    >>> cap.get_ffprobe_version()
    '4.1.2'
    >>> 'vp9' in cap.get_available_codecs()
    True
    >>> 'libx264' in cap.get_availble_encoders()
    True
    >>> 'webm' in cap.get_available_formats()
    True

"""
import re

from .run import ffmpeg, ffprobe


_ffmpeg_version = None
_ffprobe_version = None
_available_codecs = None
_available_formats = None
_available_encoders = None


class Codec:
    """
    Describes a codec known to FFmpeg

    This doesn't mean it can be encoded or decoded. For encoding support, look at :class:`Encoder`.

    Attributes:

    * ``name`` - Codec (short) name
    * ``description`` - Codec description (long name)
    * ``type`` - Codec type, one of :attr:`TYPE_AUDIO`, :attr:`TYPE_VIDEO` or :attr:`TYPE_SUBTITLE`
    * ``can_encode`` - Whether ffmpeg can encode to this codec
    * ``can_decode`` - Whether ffmpeg can decode this codec
    * ``can_all_i`` - Whether the codec is all-intra (can have only I frames)
    * ``lossy`` - Whether the codec supports lossy encoding
    * ``lossless`` - Whether the codec supports lossless encoding
    """

    TYPE_AUDIO = 'audio'  #: Audio codec
    TYPE_VIDEO = 'video'  #: Video codec
    TYPE_SUBTITLE = 'subtitle'  #: Subtitle codec

    def __init__(self, name, type, can_encode, can_decode, can_all_i, lossy, lossless, desc):
        self.name = name
        self.type = type
        self.can_encode = can_encode
        self.can_decode = can_decode
        self.can_all_i = can_all_i
        self.lossy = lossy
        self.lossless = lossless
        self.description = desc

    def __str__(self):
        return self.name

    def __repr__(self):
        cap = []
        if self.can_encode:
            cap.append('enc')
        if self.can_decode:
            cap.append('dec')
        return '<Codec(name=%s, type=%s, cap=%s)>' % (self.name, self.type, ','.join(cap))

    @classmethod
    def parse(cls, line):
        parts = re.split(r'\s+', line.strip(), 2)
        if len(parts) != 3:
            return None

        if 'V' in parts[0]:
            type = cls.TYPE_VIDEO
        elif 'A' in parts[0]:
            type = cls.TYPE_AUDIO
        elif 'S' in parts[0]:
            type = cls.TYPE_SUBTITLE
        else:
            return None

        return cls(
            parts[1],
            type,
            'E' in parts[0],
            'D' in parts[0],
            'I' in parts[0],
            'L' in parts[0],
            'S' in parts[0],
            parts[2]
        )


class Encoder:
    """
    Describes an available encoder

    Attributes:

    * ``name`` - Encoder name
    * ``description`` - Encoder description
    * ``type`` - Encoder type, one of :attr:`Codec.TYPE_AUDIO`, :attr:`Codec.TYPE_VIDEO` or :attr:`Codec.TYPE_SUBTITLE`
    """

    def __init__(self, name, type, desc):
        self.name = name
        self.type = type
        self.description = desc

    def __str__(self):
        return self.name

    @classmethod
    def parse(cls, line):
        parts = re.split(r'\s+', line.strip(), 2)
        if len(parts) != 3:
            return None

        if 'V' in parts[0]:
            type = Codec.TYPE_VIDEO
        elif 'A' in parts[0]:
            type = Codec.TYPE_AUDIO
        elif 'S' in parts[0]:
            type = Codec.TYPE_SUBTITLE
        else:
            return None

        return cls(
            parts[1],
            type,
            parts[2]
        )


class Format:
    """
    Describes a format known to FFmpeg

    Attributes:

    * ``name`` - Format name
    * ``description`` - Format description (long name)
    * ``can_mux`` - Whether ffmpeg can mux (pack) to this format
    * ``can_demux`` - Whether ffmpeg can demux (unpack) this format
    """

    def __init__(self, name, can_mux, can_demux, desc):
        self.name = name
        self.can_mux = can_mux
        self.can_demux = can_demux
        self.description = desc

    def __str__(self):
        return self.name

    @classmethod
    def parse(cls, line):
        parts = re.split(r'\s+', line.strip(), 2)
        if len(parts) != 3:
            return None

        return cls(
            parts[1],
            'E' in parts[0],
            'D' in parts[0],
            parts[2]
        )

    def __repr__(self):
        cap = []
        if self.can_mux:
            cap.append('mux')
        if self.can_demux:
            cap.append('demux')
        return '<Format(name=%s, cap=%s)>' % (self.name, ','.join(cap))


def _ffmpeg_list(what, cls):
    output = ffmpeg(['-' + what], quick=True)
    if output is None:
        return None

    items = {}
    parse_lines = False

    for line in output.split('\n'):
        line = line.strip()
        if line.startswith('--'):
            parse_lines = True
            continue

        if parse_lines is False:
            continue

        item = cls.parse(line)
        if item:
            items[item.name] = item

    return items


def get_available_codecs():
    """
    Discovers and returns a list of available codecs.

    Result is cached between runs so the results will only be discovered once.

    :return: A list of available codecs
    :rtype: list(:class:`Codec`)
    :raises ValueError: if ``ffmpeg`` utility cannot be found
    """

    global _available_codecs

    if _available_codecs is None:
        _available_codecs = _ffmpeg_list('codecs', Codec)

    return _available_codecs


def get_available_formats():
    """
    Discovers and returns a list of available formats

    Result is cached between runs so the results will only be discovered once.

    :return: A list of available formats
    :rtype: list(:class:`Format`)
    :raises ValueError: if ``ffmpeg`` utility cannot be found
    """

    global _available_formats

    if _available_formats is None:
        _available_formats = _ffmpeg_list('formats', Format)

    return _available_formats


def get_available_encoders():
    """
    Discovers and returns a list of available encoders

    Result is cached between runs so the results will only be discovered once.

    :return: A list of available encoders
    :rtype: list(:class:`Encoder`)
    :raises ValueError: if ``ffmpeg`` utility cannot be found
    """

    global _available_encoders

    if _available_encoders is None:
        _available_encoders = _ffmpeg_list('encoders', Encoder)

    return _available_encoders


def get_ffmpeg_version():
    """
    Returns version of installed ffmpeg tool

    :return: FFmpeg version in 'x.y.z' format
    :rtype: str
    :raises ValueError: if ``ffmpeg`` utility cannot be found
    """

    global _ffmpeg_version

    if _ffmpeg_version is None:
        output = ffmpeg(['-version'])
        _ffmpeg_version = output.split(' ', 3)[2]

    return _ffmpeg_version


def get_ffprobe_version():
    """
    Returns version of installed ffprobe tool

    :return: FFprobe version in 'x.y.z' format
    :rtype: str
    :raises ValueError: if ``ffprobe`` utility cannot be found
    """

    global _ffprobe_version

    if _ffprobe_version is None:
        output = ffprobe(['-version'], parse_json=False)
        return output.split(' ', 3)[2]

    return _ffprobe_version

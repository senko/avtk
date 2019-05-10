AVTK - Python Audio/Video Toolkit
=================================

AVTK provides functionality for inspecting and manipulating audio and video contents in an easy to use manner.

Current version supports working with local files using the `FFmpeg <https://ffmpeg.org/>`_ command line tools
(``ffmpeg`` and ``ffprobe``). Future versions will support various online video providers by wrapping their
respective low-level SDKs.

AVTK aims to make it easy to most of the things you might want to do with audio and video, while allowing you
to use the underlying tools and libraries for edge cases where you need full low-level functionality.

**WARNING:** AVTK is still in beta phase - bugs, missing documentation and frequent API changes are likely. Please
report bugs, suggest use cases and feature ideas, and any other feedback you might have, to GitHub issues.

Resources
---------

* Python Package Index: https://pypi.org/project/avtk/
* Documentation: https://avtk.readthedocs.io/en/latest/
* Source code: https://github.com/senko/avtk/
* Bug and feature tracker: https://github.com/senko/avtk/issues

Quickstart
----------

Install from Python Package Index::

    pip install avtk

Make sure you have the ``ffmpeg`` and ``ffprobe`` tools available on the system. For detailed installation instructions
please see the :doc:`install` page in the documentation.

Examples
--------

Converting a video::

    >>> from avtk.backends.ffmpeg.shortcuts import convert_to_webm

    >>> convert_to_webm('test-media/video/sintel.mkv', '/tmp/output.webm')

Creating a thumbnail::

    >>> from datetime import timedelta
    >>> from avtk.backends.ffmpeg.shortcuts import get_thumbnail

    >>> png_data = get_thumbnail('test-media/video/sintel.mkv', timedelta(seconds=2))

Inspecting a media file::

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

For more examples, see the :mod:`avtk.backends.ffmpeg.shortcuts` documentation.

Bugs and feature requests
-------------------------

To report a bug or suggest a feature, please use the `GitHub issue tracker <https://github.com/senko/avtk/issues>`_.

When reporting a bug, please include a detailed description, any logging output and exception tracebacks, and
media files (direcly or links to) which caused the problem.

When suggesting a feature, please explain both the feature (how it would work and what it would do) and rationale
(why it is needed, especially if the same can be combined with the existing API).

If contributing code, either bugfixes or feature implementation, please include tests for the new or fixed
functionality, and update documentation accordingly.

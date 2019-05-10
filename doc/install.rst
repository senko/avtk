Installation
============

The recommended way to install AVTK is from the Python Package Index::

    pip install avtk

If you're contributing to the project or want to check out the latest source code, you can install directly from
GitHub::

    pip install git+https://github.com/senko/avtk.git

Or you can manually download the source code and run ``setup.py`` to install::

    python setup.py build
    python setup.pby install

Requirements
~~~~~~~~~~~~

AVTK depends on the `FFmpeg <https://ffmpeg.org>`_ command-line tools for manipulating local media files. Follow
the `official installation instructions <https://ffmpeg.org/download.html>`_ to install FFmpeg.

Note that due to licensing and patent issues, the pre-built ffmpeg package on your operating system may have limited
or no support for certain codecs, formats or protocols. If you're unsure, we recomend you download a static build
that comes with most functionality out of the box.


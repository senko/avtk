AVTK - Python Audio/Video Toolkit
=================================

AVTK provides functionality for inspecting and manipulating audio and video contents in an easy to use manner.

Here's a quick example::

    >>> from avtk.backends.ffmpeg.shortcuts import convert_to_webm

    >>> convert_to_webm('test-media/video/sintel.mkv', '/tmp/output.webm')

Contents
--------

.. toctree::
   :maxdepth: 2

   Overview <overview>
   install
   ffmpeg/index
   support

Licence
-------

.. include:: ../LICENSE

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

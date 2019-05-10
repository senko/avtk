#!/usr/bin/env python

import setuptools

from avtk import VERSION, AUTHOR, AUTHOR_EMAIL

long_description = """
AVTK provides functionality for inspecting and manipulating audio and video contents in an easy to use manner.

Current version supports working with local files using the [FFmpeg](https://ffmpeg.org/) command line tools
(ffmpeg and ffprobe). Future versions will support various online video providers by wrapping their
respective low-level SDKs.

AVTK aims to make it easy to most of the things you might want to do with audio and video, while allowing you
to use the underlying tools and libraries for edge cases where you need full low-level functionality.

WARNING: AVTK is still in beta phase - bugs, missing documentation and frequent API changes are likely. Please
report bugs, suggest use cases and feature ideas, and any other feedback you might have, to GitHub issues.
"""

with open("README.rst", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="avtk",
    version=VERSION,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    description="Audio/Video toolkit",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/senko/avtk",
    packages=setuptools.find_packages(exclude=["test", "test.*"]),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)

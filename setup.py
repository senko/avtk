#!/usr/bin/env python

import setuptools

from avtk import VERSION, AUTHOR, AUTHOR_EMAIL


with open("README.rst", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="avtk",
    version=VERSION,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    description="Audio/Video toolkit",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="https://github.com/senko/avtk",
    packages=setuptools.find_packages(exclude=["test", "test.*"]),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)

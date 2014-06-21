#!/usr/bin/env python

# Copyright 2013 Sean Kelleher. All rights reserved.
# Use of this source code is governed by a GPL
# license that can be found in the LICENSE file.

from setuptools import setup

setup(
    name='Pygme',
    version="0.1",
    description="Python Gameboy Emuator",
    classifiers=[
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python",
    ],
    author="Sean Kelleher",
    author_email='ezanmoto@gmail.com',
    license="GPL",
    packages=[
        'pygme',
        'pygme.cpu',
        'pygme.cpu.test',
        'pygme.lcd',
        'pygme.lcd.driver',
        'pygme.lcd.driver.test',
        'pygme.memory',
        'pygme.memory.test',
    ],
)

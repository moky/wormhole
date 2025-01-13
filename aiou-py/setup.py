#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
    AIOU
    ~~~~

    Async I/O Utils
"""

import io

from setuptools import setup, find_packages

__version__ = '1.0.1'
__author__ = 'Albert Moky'
__contact__ = 'albert.moky@gmail.com'

with io.open('README.md', 'r', encoding='utf-8') as fh:
    readme = fh.read()

setup(
    name='aiou',
    version=__version__,
    url='https://github.com/moky/wormhole/',
    license='MIT',
    author=__author__,
    author_email=__contact__,
    description='Async I/O Utils',
    long_description=readme,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    install_requires=[

        'aiofiles',         # 23.2.1

        'redis',            # 3.5.3

        # 'async-timeout',  # 4.0.2
        # 'attrs',          # 23.2.0
        # 'multidict',      # 6.0.5
        'yarl',             # 1.9.4
        # 'frozenlist',     # 1.3.3
        'aiohttp',          # 3.8.6

    ]
)

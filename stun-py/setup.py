#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
    STUN
    ~~~~

    Session Traversal Utilities for NAT
"""

from setuptools import setup, find_packages

__version__ = '0.1.12'
__author__ = 'Albert Moky'
__contact__ = 'albert.moky@gmail.com'

with open('README.md', 'r') as fh:
    readme = fh.read()

setup(
    name='stun',
    version=__version__,
    url='https://github.com/moky/wormhole/',
    license='MIT',
    author=__author__,
    author_email=__contact__,
    description='Session Traversal Utilities for NAT',
    long_description=readme,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    install_requires=[
        'udp>=0.2.5'
    ]
)

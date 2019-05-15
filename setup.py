#!/usr/bin/env python
# coding: utf-8

from setuptools import setup

setup(
    name='wt',
    version='0.0.2',
    author='brookai',
    author_email='kaiziwangzi@gmail.com',
    url='https://github.com/kaiziwangzi',
    description=u'自动记录周报并发送到邮箱',
    packages=['wt'],
    install_requires=[],
    classifiers=[
        'Programming Language :: Python :: 3.6',
        ],
    entry_points={
        'console_scripts': [
            'wt=wt:add'
        ]
    }
)
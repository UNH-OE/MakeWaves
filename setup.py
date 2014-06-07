#!/usr/bin/env python
# coding=utf-8

from distutils.core import setup
import os

icons = os.listdir("makewaves/icons")
icons = ["makewaves/icons/" + i for i in icons]

setup(
    name='MakeWaves',
    version='0.0.1',
    author='Pete Bachant',
    author_email='petebachant@gmail.com',
    packages=['makewaves'],
    scripts=['scripts/makewaves-script.pyw', 'scripts/makewaves.bat'],
    data_files=[('Lib/site-packages/makewaves/icons', icons)],
    url='https://github.com/petebachant/MakeWaves.git',
    license='LICENSE',
    description='Python package and app for wavemaking in the UNH tow/wave tank.',
    long_description=open('README.md').read()
)

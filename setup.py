#!/usr/bin/env python

import codecs
import os

from setuptools import setup, find_packages


def read(fname):
    file_path = os.path.join(os.path.dirname(__file__), fname)
    return codecs.open(file_path, encoding='utf-8').read()


setup(
    name='pytest-influxdb-plugin',
    version='0.1.0',
    author='Ilya Dunin',
    author_email='ilya.mirea@gmail.com',
    maintainer='Ilya Dunin',
    maintainer_email='ilya.mirea@gmail.com',
    license='MIT',
    url='https://github.com/ivdunin/pytest-influxdb-plugin',
    description='A plugin to send metrics into Influxdb',
    long_description=read('README.md'),
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    keywords='pytest, plugin, testing, metrics, statistics, InfluxDB, database, time-series',
    python_requires='>=3.7',
    install_requires=[
        'influxdb>=5.3',
        'pytest>=6.2.0'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: Pytest',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Testing',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License',
    ],
    entry_points={
        'pytest11': [
            'influxdb-plugin = pytest_influxdb_plugin.plugin',
        ],
    },
)

#!/usr/bin/env python3

from setuptools import setup, find_packages
import os

# Get the long description from the README file
with open(os.path.join(os.path.dirname(__file__), 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='ovpn_bot',
    version='0.1.0',
    description='A Telegram bot for OpenVPN server monitoring',
    long_description=long_description,
    url='https://github.com/totekuh/pyopenvpn-monitor',
    author='totekuh',  # Optional
    author_email='totekuh@protonmail.com',  # Optional
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: System Administrators',
        'Topic :: System :: Networking :: Monitoring',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
    ],
    keywords='openvpn, monitoring, telegram-bot',
    python_requires='>=3.7, <4',
    install_requires=[
        'python-telegram-bot==13.7',
        'openvpn-status',
        'python-dotenv'
    ],
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    entry_points={
        'console_scripts': [
            'ovpn-monitor=ovpn_monitor.bot:main',
        ],
    },
    project_urls={
        'Bug Reports': 'https://github.com/totekuh/pyopenvpn-monitor/issues',
        'Source': 'https://github.com/totekuh/pyopenvpn-monitor/',
    },
)

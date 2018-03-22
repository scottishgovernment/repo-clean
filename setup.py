#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""The setup script."""

from setuptools import setup, find_packages

with open('README.md') as readme_file:
    readme = readme_file.read()

requirements = []

setup_requirements = []

test_requirements = [
    'pytest',
    'pytest-runner',
]

setup(
    author="Rachel Willmer",
    author_email='rachel.willmer@gov.scot',
    classifiers=[
        "Programming Language :: Python :: 3.5",
    ],
    description="Tool to delete old build artefacts from Nexus repo",
    entry_points={
        'console_scripts': ['repo-clean=repo_clean.cli:main'],
    },
    include_package_data=True,
    install_requires=[
        'lxml',
        'click',
        'requests',
        'pyyaml',
    ],
    name='repo_clean',
    packages=['infra', 'repo_clean'],
    package_dir={
        'repo_clean': '.',
        'infra': 'infra'
    },
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='http://stash.digital.gov.uk/projects/MGV/repos/deploy-pipeline/',
    version='0.1.0',
)

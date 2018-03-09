from setuptools import setup

setup(
    name='pipeline',
    version='0.1',
    description="Utilities for managing the Scot Gov deployment pipeline",
    author="Rachel Willmer",
    author_email="Rachel.Willmer@gov.scot",
    scripts=['bin/purge_nexus.py'],
    packages=['infra'],
    python_requires='~=3.5',
    classifiers=[
        "Programming Language :: Python :: 3.5",
    ],
    url='http://stash.digital.gov.uk/projects/MGV/repos/deploy-pipeline/',
    install_requires=[
        'lxml',
        'pyyaml',
        'requests',
        'setuptools',
    ])
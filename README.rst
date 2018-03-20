==========
Repo Clean
==========

Repo Clean provides a tool to clean the Nexus repository of old artifacts which
have not been used by a build in the last 3 months.


Features
--------

* TODO

Install
-------

Install pipenv

$ pip3 install pipenv

Install python packages

$ pipenv install
$ pipenv install --dev

Create a .env file containing the following.
In development, you would point NEXUS to a local VM.

PYTHONPATH=$PYTHONPATH:repo_clean:.
JENKINS='jenkins.digital.gov.uk'
NEXUS='nexus.digital.gov.uk'
NEXUS_USER='admin'
NEXUS_PASSWORD='****'

Makefile
--------

The Makefile contains these standard commands

$ make run
$ make dryrun
$ make test
$ make dist

Note that when you run the script, it will not appear to be reducing the disk
size whilst running; the blobstore compaction is the last action in the script.

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage

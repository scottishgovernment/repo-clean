# Repo Clean

### configure

Install pipenv

$ pip install pipenv

Install python packages

$ pipenv install
$ pipenv install --dev

Create a .env file

JENKINS='jenkins.digital.gov.uk'
NEXUS='nexus.digital.gov.uk' # or <newserver> if testing
NEXUS_USER='admin'
NEXUS_PASSWORD='****'

### Makefile

The Makefile contains these standard commands

$ make run
$ make dryrun
$ make test
$ make dist

## Developers

See DEV.md for a taxonomy of the terms used inside the code.

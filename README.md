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

### run

Either (a) enter into the virtual env, and then run it ...

$ pipenv shell
$ ./bin/purge_nexus.py

... or (b) run directly

$ pipenv run ./bin/purge_nexus.py

Use the --dryrun option to be prompted with the list of artefacts to be purged
before going ahead with the purge.

### test

There exists a basic test harness.

To run tests:

$ PIPENV_DOTENV_LOCATION=`pwd`/env.test pipenv run pytest

or

$ cd tests; ./test.sh

or

$ make test

### build

$ make dist


## Developers

See DEV.md for a taxonomy of the terms used inside the code.

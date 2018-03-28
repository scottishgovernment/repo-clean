# Repo Clean

Repo Clean provides a tool to clean the Nexus repository of old artifacts which
have not been used by a build in the last 3 months.

## Building on Jenkins

A package can be built in one of two different ways:

* Using debian packaging tools using dependencies installed on the system;
* Using debian packaging tools running within a Docker container. This
  option is used to verify that all build dependencies are specified in the
  debian/control file, and should be used for CI.

If not building within a container, the build dependencies need to be installed
first. To install these and then build a package, run:

    sudo apt-get install -y --no-install-recommends devscripts equivs
    sudo mk-build-deps -i
    ./build

On subsequent builds, only the `./build` step is required.

To build a debian package in a Docker container, run `./build --ci`.

The build script supports the following options:

* `-v`: Specifies the version of the binary to build, e.g. `-v 1.0.0`.
* `--ci`: Specifies that the package should be built in a Docker container.

## Developing on OSX

Install pipenv

    pip3 install pipenv

Install python packages

    pipenv install
    pipenv install --dev

Create a .env file containing the following. In development, you would point
NEXUS to a local VM.

    PYTHONPATH=$PYTHONPATH:repo_clean:.
    JENKINS='jenkins.digital.gov.uk'
    NEXUS='nexus.digital.gov.uk'
    NEXUS_USER='admin'
    NEXUS_PASSWORD='****'

### Makefile

The Makefile contains these standard commands

    make run
    make dry-run
    make test
    make dist

Note that when you run the script, it will not appear to be reducing the disk
size whilst running; the blobstore compaction is the last action in the script.

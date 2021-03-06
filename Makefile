.PHONY: clean clean-test clean-pyc clean-build docs help
.DEFAULT_GOAL := help

define BROWSER_PYSCRIPT
import os, webbrowser, sys

try:
	from urllib import pathname2url
except:
	from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

BROWSER := python -c "$$BROWSER_PYSCRIPT"

PYRUN := pipenv run

help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

run: ## run repo_clean
	pipenv install
	$(PYRUN) python cli.py

dry-run: ## do a dry-run of repo_clean
	pipenv install
	$(PYRUN) python cli.py --dry-run

test: ## run the tests
	pipenv install --dev
	PIPENV_DOTENV_LOCATION=`pwd`/env.test pipenv run pytest


clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts

clean-build: ## remove build artifacts
	# The directory name is build-py, rather than build.
	# This is to avoid conflict with build script convention in JENKINS
	# This directory name is set in setup.cfg
	rm -fr build-py/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	rm -f .coverage
	rm -fr htmlcov/

lint: ## check style with flake8
	$(PYRUN) flake8 infra tests

coverage: ## check code coverage quickly with the default Python
	$(PYRUN) coverage run --source infra -m pytest
	$(PYRUN) coverage report -m
	$(PYRUN) coverage html
	$(BROWSER) htmlcov/index.html

# docs: ## generate Sphinx HTML documentation, including API docs
# 	rm -f docs/infra.rst
# 	rm -f docs/modules.rst
# 	$(PYRUN) sphinx-apidoc -o docs/ infra
# 	$(MAKE) -C docs clean
# 	$(MAKE) -C docs html
# 	$(BROWSER) docs/_build/html/index.html

# servedocs: docs ## compile the docs watching for changes
# 	watchmedo shell-command -p '*.rst' -c '$(MAKE) -C docs html' -R -D .

# release: clean ## package and upload a release
# 	twine upload dist/*

dist: clean ## builds source and wheel package
	$(PYRUN) python setup.py sdist
	$(PYRUN) python setup.py bdist_wheel
	ls -l dist

install: clean ## install the package to the active Python's site-packages
	$(PYRUN) python setup.py install

# eof

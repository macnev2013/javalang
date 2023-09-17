VENV_BIN ?= python3 -m venv
VENV_DIR ?= .venv
PIP_CMD ?= pip3

ifeq ($(OS), Windows_NT)
	VENV_ACTIVATE = $(VENV_DIR)/Scripts/activate
else
	VENV_ACTIVATE = $(VENV_DIR)/bin/activate
endif

VENV_RUN = . $(VENV_ACTIVATE)

$(VENV_ACTIVATE): setup.py	# Create virtual environment
	test -d $(VENV_DIR) || $(VENV_BIN) $(VENV_DIR)
	$(VENV_RUN); $(PIP_CMD) install --upgrade pip setuptools wheel twine
	touch $(VENV_ACTIVATE)

usage:
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/:.*##\s*/##/g' | awk -F'##' '{ printf "%-25s %s\n", $$1, $$2 }'

venv: $(VENV_ACTIVATE)		## Create virtual environment

install: venv			## Install developer requirements into venv
	$(VENV_RUN); $(PIP_CMD) install $(PIP_OPTS) -r requirements.txt

install-dev: venv install
	$(VENV_RUN); $(PIP_CMD) install $(PIP_OPTS) -r requirements-dev.txt

test: venv					## Run tests
	$(VENV_RUN); python -m pytest -sv

dist: venv clean					## Build source and wheel package
	$(VENV_RUN); python setup.py sdist bdist_wheel

publish: venv dist			## Publish to PyPI
	$(VENV_RUN); twine upload dist/*

clean:						## Clean up build artifacts
	rm -rf dist build *.egg-info
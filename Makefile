# This file is used only to ease development by providing easy to
# use command shortcuts.
#
# While tox aims as testing with exclusive use of virtualenvs, Makefile
# is not limited to that is unaware of virtualenvs. This is by design, as
# it allows use on almost any setup (roo/non-root, venv/no venv)
all: lint docs
.PHONY: all lint docs

lint:
	tox -eansible-lint,pep8

docs:
	tox -edocs

install:
	pip install -U pip
	pip install -U setuptools
	pip install .

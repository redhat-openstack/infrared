# This file is used only to ease development by providing easy to
# use command shortcuts like:
# make lint
all: lint docs
.PHONY: all lint docs

lint:
	tox -eansible-lint,pep8

docs:
	tox -edocs

install:
	pip install .

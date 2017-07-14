# This file is used only to ease development by providing easy to
# use command shortcuts like:
# make lint
all: lint
.PHONY: all lint

lint:
	tox -eansible-lint

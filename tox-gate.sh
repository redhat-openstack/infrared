#!/bin/bash
set -x
export TOXENV="pep8,py27,cli,ansible-lint,any-errors-fatal,conflicts,plugin-registry"

# disabled parallel execution due to https://github.com/pypa/pip/issues/5345
# which detox >/dev/null || pip install --user detox
# python -m detox

python -m tox

if [[ ! -z $(git status -s) ]]; then
    ANSI_RED="\033[01;31m"
    ANSI_NORMAL="\033[0m"
    >&2 git status
    >&2 echo -e "${ANSI_RED}====== ^^ Failed: Modified files on disk, avoid them or update .gitignore file. ^^ ======${ANSI_NORMAL}"
    exit 1
fi

#!/bin/bash
set -x
export TOXENV="pep8,py27,cli,ansible-lint,any-errors-fatal,conflicts,plugin-registry"

# disabled parallel execution due to https://github.com/pypa/pip/issues/5345
# which detox >/dev/null || pip install --user detox
# python -m detox

python -m tox

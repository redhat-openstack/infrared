#!/bin/bash
set -x
RUN_ENVS="pep8 py27 cli ansible-lint any-errors-fatal"
if which python3.5 &> /dev/null; then
    RUN_ENVS="${RUN_ENVS} py35"
fi


FAILED=""
run_tox() {
    tox -e$1 &> .tox_$1_out &
}

verify_tox() {
    echo -e "\033[01;33m_________ output of $1: _________\033[0m"
    cat .tox_$1_out
    if ! tail -n2 .tox_$1_out | grep -q "$1: commands succeeded"; then
        FAILED="${FAILED} $1"
        echo -e "\033[01;31m====== ^^ end of failed $1 ^^ ======\033[0m"
    else
        echo -e "\033[01;33m====== ^^ end of $1 ^^ ======\033[0m"
    fi
}

for tEnv in ${RUN_ENVS}; do run_tox ${tEnv}; done
wait
set +x
for tEnv in ${RUN_ENVS}; do verify_tox ${tEnv} || exit 1; done
if [[ ! -z "$FAILED" ]]; then
    echo -e "\033[01;31m==== Failed: $FAILED ====\033[0m" >&2
    exit 1
fi

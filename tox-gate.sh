#!/bin/bash
set -x
RUN_ENVS="pep8 py27 cli ansible-lint any-errors-fatal conflicts plugin-registry"

FAILED=""
run_tox() {
    tox -e$1 &> .tox_$1_out &
}

verify_tox() {
    if ! tail -n2 .tox_$1_out | grep -q "$1: commands succeeded"; then
        FAILED="${FAILED} $1"
    else
        echo -e "\033[01;33m_________ output of $1: _________\033[0m"
        # failed outputs printed at the end
        cat .tox_$1_out
        echo -e "\033[01;33m====== ^^ end of $1 ^^ ======\033[0m"
    fi
}
print_failed() {
    for tEnv in ${FAILED}; do
        echo -e "\033[01;33m_________ output of ${tEnv}: _________\033[0m"
        cat .tox_${tEnv}_out;
        echo -e "\033[01;31m====== ^^ end of failed ${tEnv} ^^ ======\033[0m"
    done
}

for tEnv in ${RUN_ENVS}; do run_tox ${tEnv}; done
wait
set +x
for tEnv in ${RUN_ENVS}; do verify_tox ${tEnv} || exit 1; done
if [[ ! -z "$FAILED" ]]; then
    print_failed
    echo -e "\033[01;31m==== Failed: $FAILED ====\033[0m" >&2
    exit 1
fi

if [[ ! -z $(git status -s) ]]; then
    git status
    echo -e "\033[01;31m====== ^^ Failed: Modified files on disk, avoid them or update .gitignore file. ^^ ======\033[0m"
    exit 1
fi

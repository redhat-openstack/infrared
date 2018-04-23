#!/bin/bash

function help() {
    echo "$(basename "$0") [ -b ] [ -t ] -- script to generate release nodes between two git branches or commits"
    echo "where:"
    echo "    -h/--help         show this help text"
    echo "    -b/--between      provide option to specify branches/commits, default value: stable master"
    echo "    -t/--tags         provide options to filter notes based on commit tags, default value: BUGFIX,NEWFEATURE,APICHANGE,ANSIBLE_BUMP"
    echo ""
    echo "Example: ./$(basename "$0") -b stable master -t NEWFEATURE,APICHANGE"

    exit 0
}

print_underlined () {
    tag=$1
    echo ${tag}

    i=${#tag}
    while [[ i -gt 0 ]]; do
        printf "="
        (( i = $i - 1 ))
    done
    printf "\n\n"
}

for i in "$@"
do
case $i in
    -b|--between)
    FROM="$2"
    TO="$3"
    shift
    shift
    shift
    ;;
    -t|--tags)
    TAGS="$2"
    shift # past argument
    shift # past value
    ;;
    -h|--help)
    help
    ;;
esac
done

FROM=${FROM:-'stable'}
TO=${TO:-'master'}
TAGS=${TAGS:='BUGFIX,NEWFEATURE,APICHANGE,ANSIBLE_BUMP'}

for tag in `echo ${TAGS} | tr "," "\n"`; do
    count=$(git log ${FROM}..${TO} --pretty='%h %s' | awk -v tag="[$tag]" '$2 == tag { print $1 }'|wc -l)
    if [[ $count -gt 0 ]]; then
        print_underlined ${tag}
    fi;
    for commit in `git log ${FROM}..${TO} --pretty='%h %s' | awk -v tag="[$tag]" '$2 == tag { print $1 }'`; do
        commit_author=$(git show -s --format='%an' $commit)
        commit_date=$(git show -s --format='%aD' $commit)
        commit_subject=$(git show -s --format='%s' $commit)
        commit_body=$(git show -s --format='%b' $commit | grep -vE 'Change-Id|cherry picked from commit')

        echo "* __${commit_subject}__"
        echo "    [${commit_author}] - ${commit_date}"
        echo "    "
        echo "${commit_body}" | sed 's/^/    /'
        echo ""

    done
done
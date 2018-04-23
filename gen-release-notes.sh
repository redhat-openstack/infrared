#!/bin/bash

function help() {
    echo "$(basename "$0") [ -b ] [ -t ] -- script to generate release nodes between two git branches or commits"
    echo "where:"
    echo "    -h/--help         show this help text"
    echo "    -b/--between      provide option to specify branches/commits, default value: stable master"
    echo "    -v/--version      specify version, which will be used in release notes"
    echo "    -f/--flags        provide options to filter notes based on commit flags, default value: BUGFIX,NEWFEATURE,APICHANGE,ANSIBLE_BUMP"
    echo ""
    echo "Example: ./$(basename "$0") -b stable master -t NEWFEATURE,APICHANGE"

    exit 0
}

print_underlined () {
    text=$1
    echo ${text}

    i=${#text}
    while [[ i -gt 0 ]]; do
        printf $2
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
    -v|--version)
    VERSION="$2"
    shift # past argument
    shift # past value
    ;;
    -f|--flags)
    FLAGS="$2"
    shift # past argument
    shift # past value
    ;;
    -h|--help)
    help
    ;;
esac
done

if [[ -z "$VERSION" ]]; then
    echo "Please provide version, for help use -h/--help"
    exit
fi;

# Check if values are provided by cli, or set them to default
FROM=${FROM:-'stable'}
TO=${TO:-'master'}
FLAGS=${FLAGS:='BUGFIX,NEWFEATURE,APICHANGE,ANSIBLE_BUMP'}

# Check if there is commit with flags before printing the version
all_flags=$(echo "[$FLAGS]" | sed 's/,/] [/g')
commits_with_flags=$(git log ${FROM}..${TO} --pretty='%h %s' | awk -v flags="$all_flags" 'BEGIN{ split(flags, parts); for (i in parts) dict[parts[i]]=""}  $2 in dict' | wc -l)
if [[ commits_with_flags -gt 0 ]]; then
    print_underlined ${VERSION} '='
fi;

# Process flags one by one, and print commit info
for flag in `echo ${FLAGS} | tr "," "\n"`; do
    count=$(git log ${FROM}..${TO} --pretty='%h %s' | awk -v flag="[$flag]" '$2 == flag { print $1 }'|wc -l)
    if [[ $count -gt 0 ]]; then
        print_underlined ${flag} '-'
    fi;
    for commit in `git log ${FROM}..${TO} --pretty='%h %s' | awk -v flag="[$flag]" '$2 == flag { print $1 }'`; do
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
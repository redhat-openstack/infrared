#!/bin/bash
set -euxo pipefail
export TOXENV="pep8,py,cli,ansible-lint,any-errors-fatal,conflicts,plugin-registry"

# disabled parallel execution due to https://github.com/pypa/pip/issues/5345
# which detox >/dev/null || pip install --user detox
# python -m detox

python -m tox

ANSI_RED="\033[01;31m"
ANSI_NORMAL="\033[0m"

if [[ ! -z $(git status -s) ]]; then
    >&2 git status
    >&2 echo -e "${ANSI_RED}====== ^^ Failed: Modified files on disk, avoid them or update .gitignore file. ^^ ======${ANSI_NORMAL}"
    exit 1
fi

# verify that there is CommitMessage Body provided
# ideally reason why the change is done should be there
# just linking to somewhere else is not good enough for commit history
# while linking for more details is good, at least basic info should be here
# (external refs do disappear/change over time too for ex.)
# ... this is done as last here, so that any technical issues are pointed out first

# list of what meta-keywords to exclude based on last 255 commits
# when this was added, more to be added later based on practical experience
commitMsg_excludeLines="Change-Id|Related|Related-Bug|Related-Change|Related-To|Resolves|Side-change|Signed-off-by|Solves|Tested-by|CIX|JIRA"
commitMsgBody="$(git log --no-merges --pretty="%b" -1)"
commitMsgBody="$(grep -Ev "^\s*$|^(${commitMsg_excludeLines}): .*$" <<<"${commitMsg}")"
if [[ -z "${commitMsgBody}" ]]; then
    >&2 echo -e "${ANSI_RED}====== ERROR: Commit message is too short. ======${ANSI_NORMAL}"
    >&2 echo -e "${ANSI_RED}Commit message has to explain WHY the change is needed.${ANSI_NORMAL}"
    >&2 echo "(e.g. what is broken or missing, why the feature is desired etc)"
    >&2 echo ""
    >&2 echo "Providing just single title-line, just reference to ticket or such meta info is not enough."
    >&2 echo "Please write up little bit more details about the change."
    >&2 echo ""
    >&2 echo "If needed following are good guidelines about this:"
    >&2 echo " - https://cbea.ms/git-commit/ (more general, esp. see the Seven Rules)"
    >&2 echo " - https://wiki.openstack.org/wiki/GitCommitMessages (more technical, good/bad examples, external-references usually does not apply here)"
    >&2 echo ""
    exit 1
fi

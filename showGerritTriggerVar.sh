#!/bin/bash

echo -e "----
# Parameter name for the commit subject (commit message's 1st line).
\$GERRIT_CHANGE_SUBJECT = ${GERRIT_CHANGE_SUBJECT}

# Parameter name for the full commit message.
\$GERRIT_CHANGE_COMMIT_MESSAGE = ${GERRIT_CHANGE_COMMIT_MESSAGE}

# Parameter name for the branch.
\$GERRIT_BRANCH = ${GERRIT_BRANCH}

# Parameter name for the topic.
\$GERRIT_TOPIC = ${GERRIT_TOPIC}

# Parameter name for the change-id.
\$GERRIT_CHANGE_ID = ${GERRIT_CHANGE_ID}

# Parameter name for the change number.
\$GERRIT_CHANGE_NUMBER = ${GERRIT_CHANGE_NUMBER}

# Parameter name for the URL to the change.
\$GERRIT_CHANGE_URL = ${GERRIT_CHANGE_URL}

# Parameter name for the patch set number.
\$GERRIT_PATCHSET_NUMBER = ${GERRIT_PATCHSET_NUMBER}

# Parameter name for the patch set revision.
\$GERRIT_PATCHSET_REVISION = ${GERRIT_PATCHSET_REVISION}

# Parameter name for the Gerrit project name.
\$GERRIT_PROJECT = ${GERRIT_PROJECT}

# Parameter name for the refspec.
\$GERRIT_REFSPEC = ${GERRIT_REFSPEC}

# The name and email of the abandoner of the change.
\$GERRIT_CHANGE_ABANDONER = ${GERRIT_CHANGE_ABANDONER}

# The name of the abandoner of the change.
\$GERRIT_CHANGE_ABANDONER_NAME = ${GERRIT_CHANGE_ABANDONER_NAME}

# The email of the abandoner of the change.
\$GERRIT_CHANGE_ABANDONER_EMAIL = ${GERRIT_CHANGE_ABANDONER_EMAIL}

# The name and email of the owner of the change.
\$GERRIT_CHANGE_OWNER = ${GERRIT_CHANGE_OWNER}

# The name of the owner of the change.
\$GERRIT_CHANGE_OWNER_NAME = ${GERRIT_CHANGE_OWNER_NAME}

# The email of the owner of the change.
\$GERRIT_CHANGE_OWNER_EMAIL = ${GERRIT_CHANGE_OWNER_EMAIL}

# The name and email of the restorer of the change.
\$GERRIT_CHANGE_RESTORER = ${GERRIT_CHANGE_RESTORER}

# The name of the restorer of the change.
\$GERRIT_CHANGE_RESTORER_NAME = ${GERRIT_CHANGE_RESTORER_NAME}

# The email of the restorer of the change.
\$GERRIT_CHANGE_RESTORER_EMAIL = ${GERRIT_CHANGE_RESTORER_EMAIL}

# The name and email of the uploader of the patch-set.
\$GERRIT_PATCHSET_UPLOADER = ${GERRIT_PATCHSET_UPLOADER}

# The name of the uploader of the patch-set.
\$GERRIT_PATCHSET_UPLOADER_NAME = ${GERRIT_PATCHSET_UPLOADER_NAME}

# The email of the uploader of the patch-set.
\$GERRIT_PATCHSET_UPLOADER_EMAIL = ${GERRIT_PATCHSET_UPLOADER_EMAIL}

# The name and email of the person who triggered the event.
\$GERRIT_EVENT_ACCOUNT = ${GERRIT_EVENT_ACCOUNT}

# The name of the person who triggered the event.
\$GERRIT_EVENT_ACCOUNT_NAME = ${GERRIT_EVENT_ACCOUNT_NAME}

# The email of the person who triggered the event.
\$GERRIT_EVENT_ACCOUNT_EMAIL = ${GERRIT_EVENT_ACCOUNT_EMAIL}

# The refname in a ref-updated event.
\$GERRIT_REFNAME = ${GERRIT_REFNAME}

# The old revision in a ref-updated event.
\$GERRIT_OLDREV = ${GERRIT_OLDREV}

# The new revision in a ref-updated event.
\$GERRIT_NEWREV = ${GERRIT_NEWREV}

# The submitter in a ref-updated event.
\$GERRIT_SUBMITTER = ${GERRIT_SUBMITTER}

# The name of the submitter in a ref-updated event.
\$GERRIT_SUBMITTER_NAME = ${GERRIT_SUBMITTER_NAME}

# The email of the submitter in a ref-updated event.
\$GERRIT_SUBMITTER_EMAIL = ${GERRIT_SUBMITTER_EMAIL}

# The name of the Gerrit instance.
\$GERRIT_NAME = ${GERRIT_NAME}

# The host of the Gerrit instance.
\$GERRIT_HOST = ${GERRIT_HOST}

# The port number of the Gerrit instance.
\$GERRIT_PORT = ${GERRIT_PORT}

# The protocol scheme of the Gerrit instance.
\$GERRIT_SCHEME = ${GERRIT_SCHEME}

# The version of the Gerrit instance.
\$GERRIT_VERSION = ${GERRIT_VERSION}

# A hashcode of the Gerrit event object to make sure every set of parameters
# is unique (allowing jenkins to queue duplicate builds).
\$GERRIT_EVENT_HASH = ${GERRIT_EVENT_HASH}

# The type of the event.
\$GERRIT_EVENT_TYPE = ${GERRIT_EVENT_TYPE}
"

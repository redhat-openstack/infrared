#!/bin/bash
set -ex

mirror="$1"
if [[ "$mirror" =~ ^(brq|rdu2|qeos|tlv)$ ]]; then
    mirror="rhos-qe-mirror-${mirror}.usersys.redhat.com"
fi


# check that mirror is ready and responds in time

mirror_status="$(curl --max-time 3 "http://${mirror}/status" || echo "unreachable")"
echo "Mirror ${mirror} status: '$mirror_status'" >&2
if [[ "$mirror_status" != "ready" ]]; then
    echo "Skipping mirror usage as it is not ready." >&2
    exit 0
fi

# all ok, lets print out the selected mirror
echo "${mirror}"

#!/bin/bash
set -ex

mirror="$1"
if [[ "$mirror" =~ ^(brq2|rdu2|tlv2)$ ]]; then
    mirror="rhos-qe-mirror.lab.eng.${mirror}.redhat.com"
elif [[ "$mirror" =~ ^(brq|qeos|tlv)$ ]]; then
    # just backward compatibility for case when older short names are passed
    mirror="rhos-qe-mirror-${mirror}.usersys.redhat.com"
fi


# check that mirror is ready and responds in time
mirror_status=unreachable
retries=3
while [[ "$mirror_status" = "unreachable" && $retries -gt 0 ]]; do
    retries=$(( $retries - 1 ))
    mirror_status="$(curl --max-time 3 "http://${mirror}/status" || echo "unreachable")"
    [[ "$mirror_status" = "unreachable" ]] && echo "WARNING: mirror not reached, remaining $retries attempts ... " >&2
done

echo "Mirror ${mirror} status: '$mirror_status'" >&2
if [[ "$mirror_status" != "ready" ]]; then
    echo "Skipping mirror usage as it is not ready." >&2
    exit 0
fi

# all ok, lets print out the selected mirror
echo "${mirror}"

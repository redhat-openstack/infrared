#!/bin/bash
set -ex

mirror="$1"
if [[ "$mirror" =~ ^(brq|qeos|tlv)$ ]]; then
    mirror="rhos-qe-mirror-${mirror}.usersys.redhat.com"
fi


# check that mirror is ready and responds in time

mirror_status="$(curl --max-time 3 "http://${mirror}/status")"
echo "Mirror ${mirror} status: '$mirror_status'"
if [[ "$mirror_status" != "ready" ]]; then
    echo "Skipping mirror usage as it is not ready."
    exit 0
fi

mirror_ip=$(ping -c1 ${mirror}|head -n1|sed -r 's/^[^\(]+\(([^\)]+)\).*/\1/')
if [[ -z "$mirror_ip" ]]; then
    echo "Skipping mirror usage - unable to ping and get ip"
    exit 0
fi


# patch yum.repos

cd /etc/yum.repos.d

original_download_srv=$(sed -nr 's/.*(download\.lab.*redhat\.com).*/\1/p' *.repo | head -n1)
original_download_srv_alts=$(sed 's/\.lab\./.eng./' <<< "$original_download_srv")
original_download_srv_alts="$original_download_srv_alts $(sed 's/download/download-node-02/' <<< "$original_download_srv_alts")"

sed -i "s/download\.lab.*\.redhat\.com/${mirror}/" *.repo
sed -i "s/rhos-release.*\.redhat\.com/${mirror}\/rhos-release/" *.repo
sed -r -i "s/ayanami.*\.redhat.com/${mirror}\/ayanami/" *.repo
sed -i "s/pulp-read.*\.redhat\.com/${mirror}\/pulp-read/" *.repo

sed '/.* download\.lab.*redhat\.com.*/d' -i /etc/hosts
echo "$mirror_ip  $mirror $original_download_srv $original_download_srv_alts" >> /etc/hosts
echo "In case you want to disable mirror usage, also remove its entry from /etc/hosts" >> mirror-readme


# patch pip/easy_install config

pip_index_url="index_url = http://${mirror}/root/pypi/+simple"
pip_trusted_host="trusted-host = ${mirror}"
pip_use_wheel="True"

for HDIR in /root $(find /home -maxdepth 1 -type d|grep -v '/home$'); do
    [[ -d $HDIR ]] || continue

cat > $HDIR/.pydistutils.cfg <<EOF
[easy_install]
$pip_index_url
EOF

mkdir -p $HDIR/.pip;
cat > $HDIR/.pip/pip.conf <<EOF
[global]
$pip_index_url
[install]
$pip_trusted_host
use_wheel = $pip_use_wheel
EOF

chown "$(stat -c '%U' $HDIR)" -R $HDIR/.pydistutils.cfg $HDIR/.pip

done

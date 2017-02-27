#!/bin/bash

# script is invoked from within repos dir (ie /etc/yum.repos.d/)

set -ex

mirror="$1"
remote="$2"

# drop previous override to resolve ip again
sed '/.* download\.lab.*redhat\.com.*/d' -i /etc/hosts

mirror_ip=$(ping -c1 ${mirror}|head -n1|sed -r 's/^[^\(]+\(([^\)]+)\).*/\1/')
if [[ -z "$mirror_ip" ]]; then
    echo "Skipping mirror usage - unable to ping and get ip"
    exit 0
fi


# patch yum.repos

sed -i "s/download.*\.lab.*\.redhat\.com/${mirror}/" *.repo
sed -i "s/download\.eng.*\.redhat\.com/${mirror}/" *.repo
sed -i "s/rhos-release.*\.redhat\.com/${mirror}\/rhos-release/" *.repo
sed -r -i "s/ayanami.*\.redhat.com/${mirror}\/ayanami/" *.repo
sed -i "s/pulp.*\.redhat\.com/${mirror}\/pulp/" *.repo

# patch hosts to enforce communication only with mirror

if [[ "$remote" != "yes" ]]; then
    echo "$mirror_ip  $mirror download.lab.bos.redhat.com download.eng.bos.redhat.com download-node-02.eng.bos.redhat.com" >> /etc/hosts
    echo "In case you want to disable mirror usage, also remove its entry from /etc/hosts" >> mirror-readme
else
    echo "127.0.0.1   localhost localhost.localdomain localhost4 localhost4.localdomain4" >> hosts
    echo "::1         localhost localhost.localdomain localhost6 localhost6.localdomain6" >> hosts
    echo "$mirror_ip  $mirror download.lab.bos.redhat.com download.eng.bos.redhat.com download-node-02.eng.bos.redhat.com" >> hosts
    echo "In case you want to disable mirror usage, also remove its entry from /etc/hosts" >> mirror-readme
fi

# FIXME(psedlak):
# pypi mirror usage disabled atm, seems to cause issue with ansible's 'pip: virtualenv='
# not using specified venv at the end

## # patch pip/easy_install config
##
## pip_index_url="index_url = http://${mirror}/root/pypi/+simple"
## pip_trusted_host="trusted-host = ${mirror}"
## pip_use_wheel="True"
##
## for HDIR in /root $(find /home -maxdepth 1 -type d|grep -v '/home$'); do
##     [[ -d $HDIR ]] || continue
##
## cat > $HDIR/.pydistutils.cfg <<EOF
## [easy_install]
## $pip_index_url
## EOF
##
## mkdir -p $HDIR/.pip;
## cat > $HDIR/.pip/pip.conf <<EOF
## [global]
## $pip_index_url
## [install]
## $pip_trusted_host
## use_wheel = $pip_use_wheel
## EOF
##
## chown "$(stat -c '%U' $HDIR)" -R $HDIR/.pydistutils.cfg $HDIR/.pip
##
## done

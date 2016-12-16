#!/bin/bash -v

DISKNAME=/dev/vda
PARTNUM=1

SSECT=$(fdisk -l | grep ${DISKNAME}${PARTNUM} |awk {'print $3'})
FSECT=$(expr $(fdisk -l | grep "${DISKNAME}:" | awk {'print $7'}) - 1)

echo -e "d\nn\np\n1\n$SSECT\n${FSECT}\na\nw\n" | /usr/sbin/fdisk ${DISKNAME}
/usr/sbin/resizepart ${DISKNAME} ${PARTNUM} $(expr ${FSECT} - ${SSECT})
xfs_growfs /
exit $?

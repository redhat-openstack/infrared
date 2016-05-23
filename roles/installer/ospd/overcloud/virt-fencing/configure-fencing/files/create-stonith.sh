#!/bin/bash

cat $1 | while read LINE
do
  hostname=$(echo "$LINE" | cut -f1 -d\;)
  vmname=$(echo "$LINE" | cut -f2 -d\;)
  pcs stonith delete my-stonith-xvm-$hostname || /bin/true
  pcs stonith create my-stonith-xvm-$hostname fence_xvm port=$vmname pcmk_host_list=$hostname op monitor interval=30s
done

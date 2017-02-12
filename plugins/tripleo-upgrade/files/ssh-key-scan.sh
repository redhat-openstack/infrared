#!/bin/bash
for host in $(nova list | awk '$1 !~ /^\+/ && NR>3{print gensub(/.*=([0-9.]+).*/, "\\1",$12)}'); do
    grep -q ${host} ~/.ssh/known_hosts || ssh-keyscan -t rsa ${host} >> ~/.ssh/known_hosts
done
#!/bin/bash
for NODE in `nova list | grep $1 | awk -F "|" '{ print $2 }'` ;
    do upgrade-non-controller.sh --upgrade $NODE;
done
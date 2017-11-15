#!/bin/bash

GW=$(/sbin/ip route | awk '/default/ { print $3 }')
ping -D -c 10 ${GW} &> ~/Server_ping_results_UTC+3_$(date +%Y%m%d%H%M)

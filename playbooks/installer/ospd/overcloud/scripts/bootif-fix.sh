#!/usr/bin/env bash

while true;
        do find /httpboot/ -type f ! -iname "kernel" ! -iname "ramdisk" ! -iname "*.kernel" ! -iname "*.ramdisk" -exec sed -i 's|{mac|{net0/mac|g' {} +;
done

#!/bin/sh

SERVICE=selenium-grid-node
MSG="registered to the hub and ready"
TIMEOUT=15m

echo -n "Started waiting for selenium grid... "
timeout $TIMEOUT bash <<EOF
  grep -m 1 -q "$MSG" <(journalctl --since '15 second ago' -l -f -u $SERVICE)
  echo "ready (registered)."
  exit
EOF

if [[ $? == 124 ]]; then
    echo "registration node FAILED!"
    exit 1
fi

#!/bin/bash
set -e

HOST_UID=${PUID:-1000}
HOST_GID=${PGID:-1000}

echo "==> Running as PUID=$HOST_UID PGID=$HOST_GID"
echo "==> DISPLAY=$DISPLAY"

groupadd -f -g "$HOST_GID" zotero
id -u zotero &>/dev/null || useradd -u "$HOST_UID" -g "$HOST_GID" -m zotero

mkdir -p /run/dbus
dbus-daemon --system --fork 2>/dev/null || true

echo "==> Running startup tasks..."
python3 /build/startup.py

echo "==> Launching researcher-deskless..."
exec gosu "$HOST_UID" python3 /opt/launcher/launcher.py 2>&1
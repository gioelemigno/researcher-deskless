#!/bin/bash
set -e

HOST_UID=${PUID:-1000}
HOST_GID=${PGID:-1000}

echo "==> Running as PUID=$HOST_UID PGID=$HOST_GID"
echo "==> DISPLAY=$DISPLAY"

groupadd -f -g "$HOST_GID" zotero
id -u zotero &>/dev/null || useradd -u "$HOST_UID" -g "$HOST_GID" -m zotero

mkdir -p /zotero-data/profile
chown -R "$HOST_UID:$HOST_GID" /zotero-data

cat > /zotero-data/profile/user.js << EOF
user_pref("gfx.webrender.all", false);
user_pref("gfx.webrender.enabled", false);
user_pref("layers.acceleration.disabled", true);
user_pref("gfx.canvas.azure.accelerated", false);
EOF

chown "$HOST_UID:$HOST_GID" /zotero-data/profile/user.js

mkdir -p /run/dbus
dbus-daemon --system --fork 2>/dev/null || true

echo "==> Launching researcher-deskless..."
exec gosu "$HOST_UID" /launcher.sh 2>&1
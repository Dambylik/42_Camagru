#!/bin/sh
set -eu
mkdir -p /app/public/uploads
chown -R camagru:camagru /app/public/uploads
chmod 0755 /app/public/uploads
exec su -s /bin/sh camagru -c 'exec python -m backend.server'

#!/usr/bin/env sh
set -eu

TARGET="${1:-plugins/jtl_suite}"
mkdir -p "$TARGET"
cp -R "$(dirname "$0")/jtl_suite/." "$TARGET/"
rm -f "$TARGET/frontend/index.html" "$TARGET/frontend/index.ts" "$TARGET/frontend/package.json" "$TARGET/frontend/package-lock.json" "$TARGET/frontend/vite.config.js"
printf 'JTL Suite Plugin nach %s kopiert. Workspace-Integration siehe WORKSPACE_INTEGRATION.md.\n' "$TARGET"

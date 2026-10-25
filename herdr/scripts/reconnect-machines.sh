#!/usr/bin/env bash
# Reconnect saved SSH machines, giving ssh a terminal to ask for a passphrase in.
# Bound to prefix+m via [[keys.command]] type = "popup" in config.toml: herdr's
# background reconnects can't answer prompts, so a machine whose key always asks
# sits on "! auth" until this runs.
# A machine that's already connected just reports "reachable" without prompting,
# so there's no need for the slower `herdr machine status` probe first.
set -euo pipefail

ids=$(herdr machine list --json | jq -r '.[] | select(.enabled) | .id')
if [ -z "$ids" ]; then
  echo "No saved machines."
  sleep 1.5
  exit 0
fi

failed=0
for id in $ids; do
  herdr machine reconnect "$id" || failed=1
done

if [ "$failed" = 1 ]; then
  printf '\nReconnect failed; press Enter to close. '
  read -r _
fi

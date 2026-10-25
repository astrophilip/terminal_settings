#!/usr/bin/env bash
# Reconnect saved SSH machines, giving ssh a terminal to ask for a passphrase in.
# Bound to prefix+m via [[keys.command]] type = "popup" in config.toml: herdr's
# background reconnects can't answer prompts, so a machine whose key always asks
# sits on "! auth" until this runs.
# A machine that's already connected just reports "reachable" without prompting,
# so there's no need for the slower `herdr machine status` probe first.
set -euo pipefail

machines=$(herdr machine list --json)
ids=$(jq -r '.[] | select(.enabled) | .id' <<<"$machines")
if [ -z "$ids" ]; then
  echo "No saved machines."
  sleep 1.5
  exit 0
fi

# stdout goes straight to the popup via fd 3; stderr is captured so a known
# error can be explained instead of shown as herdr's raw debug output.
exec 3>&1
failed=0
pending=0
for id in $ids; do
  label=$(jq -r --arg id "$id" '.[] | select(.id == $id) | .label' <<<"$machines")
  if err=$(herdr machine reconnect "$id" 2>&1 >&3); then
    if [ -n "$err" ]; then printf '%s\n' "$err"; fi
  elif grep -q 'server is stopped or incompatible' <<<"$err"; then
    # ssh auth succeeded but nothing is serving on the remote yet, as after a
    # reboot there. herdr's background retry (~30s) reuses this authenticated
    # connection and starts the server itself.
    printf '%s: signed in; its herdr server is not running yet (normal after a\n' "$label"
    printf 'reboot). herdr will start it within about 30s.\n'
    pending=1
  else
    printf '%s\n' "$err"
    failed=1
  fi
done

# Any single key (Esc included) closes the popup.
if [ "$failed" = 1 ]; then
  printf '\nReconnect failed; press Esc to close. '
  read -rsn1 _
elif [ "$pending" = 1 ]; then
  printf '\nPress Esc to close. '
  read -rsn1 _
fi

#!/usr/bin/env bash
# Reconnect saved SSH machines in a terminal so ssh can ask for a passphrase.
# Bound to prefix+m (popup): herdr's background reconnects can't prompt, so a
# machine whose key always asks sits on "! auth" until this runs.
set -euo pipefail

machines=$(herdr machine list --json)
ids=$(jq -r '.[] | select(.enabled) | .id' <<<"$machines")
if [ -z "$ids" ]; then
  echo "No saved machines."
  sleep 1.5
  exit 0
fi

# Connected if herdr's ssh bridge to the target is running.
connected() {
  local re
  re=$(sed 's/[][\.*^$+?(){}|]/\\&/g' <<<"$1")
  pgrep -f -- "-T $re .*remote-client-bridge" >/dev/null
}

# The client retries "! auth" only every 30s; disable+enable makes it connect
# now (the 2s lets it notice the disable). setsid, as closing the popup kills
# its session.
connect_now() {
  perl -MPOSIX=setsid -e 'if (my $pid = fork) { waitpid $pid, 0; exit } setsid; fork and exit; exec @ARGV' -- bash -c \
    'herdr machine disable "$1"; sleep 2; herdr machine enable "$1"' _ "$1" \
    </dev/null >/dev/null 2>&1
}

# stdout goes straight to the popup via fd 3; stderr is captured so a known
# error can be explained instead of shown as herdr's raw debug output.
exec 3>&1
failed=0
pending=0
reconnected=0
for id in $ids; do
  label=$(jq -r --arg id "$id" '.[] | select(.id == $id) | .label' <<<"$machines")
  target=$(jq -r --arg id "$id" '.[] | select(.id == $id) | .target' <<<"$machines")
  if connected "$target"; then
    printf '%s: already connected\n' "$label"
    continue
  fi
  reconnected=1
  if err=$(herdr machine reconnect "$id" 2>&1 >&3); then
    if [ -n "$err" ]; then printf '%s\n' "$err"; fi
    connect_now "$id"
  elif grep -q 'server is stopped or incompatible' <<<"$err"; then
    # Signed in, but no remote server yet (e.g. after a reboot); the client
    # starts it when it connects.
    printf '%s: signed in; its herdr server is not running yet (normal after a\n' "$label"
    printf 'reboot). herdr will start it in a few seconds.\n'
    connect_now "$id"
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
elif [ "$reconnected" = 0 ]; then
  # Leave "already connected" up long enough to read.
  sleep 1
fi

#!/usr/bin/env bash
# Open an annotate (plannotator-tui) review of the focused agent's reply, placed where
# split-pane.sh would put a new pane: beside a lone pane, otherwise under the bottom of the
# right-hand column. plannotator-tui's own launcher only knows "split right/down of the
# agent's pane", so it is run with herdr-shim.sh standing in for herdr: the shim passes every
# call through, except the launcher's one `plugin pane open`, whose direction and target pane
# it replaces with the ones chosen here.
#
# Usage: annotate-pane.sh [--newest]   (--newest skips the reply picker)
# Meant for a herdr [[keys.command]] of type "shell", which sets HERDR_ACTIVE_PANE_ID.
set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd)

fail() {
  herdr notification show "Annotate" --body "$1" >/dev/null 2>&1 || true
  echo "annotate-pane: $1" >&2
  exit 1
}

# plannotator-tui ships inside the annotate plugin, whose install path changes per update.
plugins="${XDG_CONFIG_HOME:-$HOME/.config}/herdr/plugins.json"
tui=$(jq -r '.[] | select(.plugin_id == "annotate") | .plugin_root' "$plugins" 2>/dev/null \
      | head -n 1 | sed 's|$|/bin/plannotator-tui.exe|')
[ -x "$tui" ] || tui=$(command -v plannotator-tui || true)
[ -n "$tui" ] || fail "plannotator-tui not found: is the annotate plugin installed?"

pane="${HERDR_ACTIVE_PANE_ID:-}"
layout=$(herdr pane layout ${pane:+--pane "$pane"})
[ -n "$pane" ] || pane=$(printf '%s' "$layout" | jq -r .result.layout.focused_pane_id)
read -r count root bottom_right < <(printf '%s' "$layout" | jq -r '
  .result.layout.panes
  | length as $n
  | (min_by(.rect.x, .rect.y) | .pane_id) as $root
  | (map(.rect.x) | max) as $right
  | (map(select(.rect.x == $right)) | max_by(.rect.y) | .pane_id) as $bottom_right
  | "\($n) \($root) \($bottom_right)"')

# The review is of an agent's reply and the feedback is sent back to that agent. When the
# focused pane is not an agent (a shell, or an earlier review pane), use the tab's agent
# instead: the left-most, then top-most one. Otherwise the feedback only reaches the clipboard.
agents=$(herdr agent list | jq -c '[.result.agents[].pane_id]')
agent=$(printf '%s' "$layout" | jq -r --arg pane "$pane" --argjson agents "$agents" '
  .result.layout.panes
  | map(select(.pane_id as $id | $agents | index($id)))
  | if any(.pane_id == $pane) then $pane
    else (sort_by(.rect.x, .rect.y) | first | .pane_id) // $pane end')
pane="$agent"
export HERDR_ACTIVE_PANE_ID="$pane"

if [ "$count" -le 1 ]; then
  export ANNOTATE_PANE_DIRECTION=right ANNOTATE_PANE_TARGET="$root"
else
  export ANNOTATE_PANE_DIRECTION=down ANNOTATE_PANE_TARGET="$bottom_right"
fi

export HERDR_ENV=1
export HERDR_REAL_BIN="${HERDR_BIN_PATH:-$(command -v herdr)}"
export HERDR_BIN_PATH="$here/herdr-shim.sh"
if ! err=$("$tui" herdr last --placement split --deliver-to "$pane" "$@" 2>&1 >/dev/null); then
  fail "${err:-plannotator-tui failed}"
fi

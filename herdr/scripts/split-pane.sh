#!/usr/bin/env bash
# Split the current herdr tab into a fixed shape: the first split puts a new pane to the
# right of the only pane; every later split stacks a new pane under the bottom of the
# right-hand column, leaving the left pane alone. Prints the new pane's id.
#
# Usage: split-pane.sh [PANE_ID] [extra `herdr pane split` options, e.g. --cwd DIR]
# PANE_ID picks the tab (default: the focused pane's tab).
set -euo pipefail

pane="${1:-}"
[ $# -gt 0 ] && shift

layout=$(herdr pane layout ${pane:+--pane "$pane"})
read -r count target < <(printf '%s' "$layout" | jq -r '
  .result.layout.panes
  | length as $n
  | (map(.rect.x) | max) as $right
  | (map(select(.rect.x == $right)) | max_by(.rect.y) | .pane_id) as $bottom_right
  | "\($n) \($bottom_right)"')

if [ "$count" -le 1 ]; then
  herdr pane split ${pane:+--pane "$pane"} --direction right --focus "$@"
else
  herdr pane split --pane "$target" --direction down --focus "$@"
fi | jq -r .result.pane.pane_id

#!/usr/bin/env bash
# Show an image in a new herdr pane, placed like split-pane.sh (beside a lone pane, otherwise
# under the bottom of the right-hand column), without taking focus from the calling pane.
# The pane runs image-view.py, which closes the pane on q.
# Prints the new pane's id.
#
# Usage: show-image.sh IMAGE
# Run from inside a herdr pane (the image opens in that pane's tab). Needs chafa and python3.
set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd)

[ $# -eq 1 ] || { echo "usage: show-image.sh IMAGE" >&2; exit 2; }
[ "${HERDR_ENV:-}" = 1 ] || { echo "show-image: not inside herdr" >&2; exit 1; }
[ -f "$1" ] || { echo "show-image: no such file: $1" >&2; exit 1; }
command -v chafa >/dev/null || { echo "show-image: chafa is not installed" >&2; exit 1; }

image="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
p=$(bash "$here/split-pane.sh" "${HERDR_PANE_ID:-}" --no-focus)
# Wait for the shell prompt so the command isn't echoed twice.
herdr pane wait-output "$p" --regex '\S' --timeout 5000 >/dev/null
herdr pane run "$p" "python3 $(printf '%q' "$here/image-view.py") $(printf '%q' "$image") --close-pane" >/dev/null
echo "$p"

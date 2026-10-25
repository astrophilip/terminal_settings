#!/usr/bin/env bash
# Open ipython in a side pane at ~45% width (55-45 split).
# Bound to prefix+i via [[keys.command]] type = "shell" in config.toml.
# --ratio is the ORIGINAL pane's share, so 0.55 leaves the new pane 45%.
set -euo pipefail

pane=$(herdr pane split --direction right --ratio 0.55 | jq -r '.result.pane.pane_id')
herdr pane run "$pane" ipython

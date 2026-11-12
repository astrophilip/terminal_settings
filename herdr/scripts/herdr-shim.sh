#!/usr/bin/env bash
# Stand-in for the herdr binary, used by annotate-pane.sh through HERDR_BIN_PATH. Every call
# goes straight to the real herdr (HERDR_REAL_BIN), except `plugin pane open`, whose
# --direction and --target-pane are replaced with ANNOTATE_PANE_DIRECTION and
# ANNOTATE_PANE_TARGET so the review pane opens where annotate-pane.sh decided.
# With ANNOTATE_PANE_DRY_RUN set to a file path, the rewritten command is appended there
# instead of run.
real="${HERDR_REAL_BIN:-herdr}"

if [ "${1:-}" = plugin ] && [ "${2:-}" = pane ] && [ "${3:-}" = open ] \
   && [ -n "${ANNOTATE_PANE_DIRECTION:-}" ] && [ -n "${ANNOTATE_PANE_TARGET:-}" ]; then
  args=()
  skip=0
  for arg in "$@"; do
    if [ "$skip" = 1 ]; then skip=0; continue; fi
    case "$arg" in
      --direction|--target-pane) skip=1; continue ;;
    esac
    args+=("$arg")
  done
  args+=(--direction "$ANNOTATE_PANE_DIRECTION" --target-pane "$ANNOTATE_PANE_TARGET")
  if [ -n "${ANNOTATE_PANE_DRY_RUN:-}" ]; then
    { printf '%q ' "$real" "${args[@]}"; echo; } >> "$ANNOTATE_PANE_DRY_RUN"
    exit 0
  fi
  exec "$real" "${args[@]}"
fi

exec "$real" "$@"

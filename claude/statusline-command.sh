#!/usr/bin/env bash
# Claude Code status line:
#   <context %>  <user> in <dir> on <branch> where <git state>  $<mtd> mtd, $<ytd> ytd
#
# Git state: ✗ untracked or unstaged changes, + staged changes, ↑ commits to
# push, ✓ clean. The cost segment is an estimate built by cost-refresh.py.
#
# Needs bash, jq and git. The cost segment also needs python3, plus
# cost-refresh.py and pricing.json in the same directory as this script.

config_dir="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

# Solarized accent colors (24-bit)
solarized_base=$'\033[38;2;147;161;161m'
solarized_yellow=$'\033[38;2;181;137;0m'
solarized_orange=$'\033[38;2;203;75;22m'
solarized_red=$'\033[38;2;220;50;47m'
solarized_magenta=$'\033[38;2;211;54;130m'
solarized_cyan=$'\033[38;2;42;161;152m'
solarized_green=$'\033[38;2;133;153;0m'
color_reset=$'\033[0m'

# Modification time in epoch seconds, or 0 if missing (GNU stat, then BSD/macOS stat)
mtime() { stat -c %Y "$1" 2>/dev/null || stat -f %m "$1" 2>/dev/null || echo 0; }

input=$(cat)
cwd=$(jq -r '.workspace.current_dir' <<<"$input")

# current_usage is null before the first API call and right after /compact; in that
# window used_percentage is reported as 0, so gate on current_usage rather than on
# the percentage itself, otherwise a stale "0%" is shown.
context_pct=$(jq -r '
  if .context_window.current_usage == null then empty
  else (.context_window.used_percentage // empty) end' <<<"$input")

transcript_path=$(jq -r '.transcript_path // empty' <<<"$input")

# Cost cache. The status line never computes cost itself: it sources a small
# shell fragment and, when that is stale, starts a background refresh whose
# result shows up on a later redraw. A mkdir lock keeps rapid redraws from
# starting several refreshers at once.
cost_refresh="$script_dir/cost-refresh.py"
cost_stale_after=15   # seconds

if [ -n "$transcript_path" ] && [ -f "$cost_refresh" ] && command -v python3 >/dev/null; then
  cost_cache_dir="$config_dir/cost-cache"
  cost_session_id=$(basename "${transcript_path%.jsonl}")
  cost_cache_sh="$cost_cache_dir/${cost_session_id}.sh"
  cost_lock="$cost_cache_dir/${cost_session_id}.lock"
  now=$(date +%s)
  mkdir -p "$cost_cache_dir"

  # release a lock left behind by a killed refresher
  if [ -d "$cost_lock" ] && [ $(( now - $(mtime "$cost_lock") )) -gt 60 ]; then
    rmdir "$cost_lock" 2>/dev/null
  fi
  if [ $(( now - $(mtime "$cost_cache_sh") )) -ge "$cost_stale_after" ] && mkdir "$cost_lock" 2>/dev/null; then
    ( python3 "$cost_refresh" "$transcript_path" >/dev/null 2>&1
      rmdir "$cost_lock" 2>/dev/null ) &
    disown 2>/dev/null || true
  fi

  # shellcheck source=/dev/null
  [ -f "$cost_cache_sh" ] && . "$cost_cache_sh"
fi

prompt_username=${USER:-$(whoami)}

# Abbreviate $HOME as ~
prompt_directory="$cwd"
case "$prompt_directory" in
  "$HOME") prompt_directory="~" ;;
  "$HOME"/*) prompt_directory="~${prompt_directory#$HOME}" ;;
esac

# Usage segments. Each is omitted when its field is absent, so the line degrades
# cleanly before the first API response.
pct_color() {
  if   [ "$1" -ge 90 ]; then printf '%s' "$solarized_red"
  elif [ "$1" -ge 75 ]; then printf '%s' "$solarized_orange"
  elif [ "$1" -ge 50 ]; then printf '%s' "$solarized_yellow"
  else                       printf '%s' "$solarized_green"
  fi
}

usage=""
add_usage() { # $1 = whole percent, $2 = label
  [ -n "$usage" ] && usage+="${solarized_base},${color_reset} "
  usage+="$(pct_color "$1")${1}%${color_reset} ${solarized_base}${2}${color_reset}"
}

[ -n "$context_pct" ] && add_usage "${context_pct%.*}" "context"

output=""
[ -n "$usage" ] && output="${usage}  "
output+="${solarized_magenta}${prompt_username}${color_reset} "
output+="${solarized_base}in${color_reset} "
output+="${solarized_cyan}${prompt_directory}${color_reset}"

# Git branch and state. Porcelain v2 output is the same in every locale and git
# version; --no-optional-locks keeps the status line from taking index locks.
if git_status=$(git -C "$cwd" --no-optional-locks status --porcelain=v2 --branch 2>/dev/null); then
  read -r git_branch git_state < <(awk '
    /^# branch\.head / { head = $3 }
    /^# branch\.ab /   { ahead = substr($3, 2) + 0 }
    /^[?u] /           { dirty = 1 }
    /^[12] /           { if (substr($2, 2, 1) != ".") dirty = 1
                         if (substr($2, 1, 1) != ".") staged = 1 }
    END { print head, (dirty ? "dirty" : (staged ? "staged" : (ahead > 0 ? "ahead" : "clean"))) }
  ' <<<"$git_status")

  case "$git_state" in
    dirty)  git_color="$solarized_red";    git_message="✗" ;;
    staged) git_color="$solarized_orange"; git_message="+" ;;
    ahead)  git_color="$solarized_yellow"; git_message="↑" ;;
    *)      git_color="$solarized_green";  git_message="✓" ;;
  esac

  if [ "$git_branch" = "(detached)" ]; then
    git_branch="($(git -C "$cwd" --no-optional-locks describe --all --contains --abbrev=4 HEAD 2>/dev/null || echo HEAD))"
  fi

  output+=" ${solarized_base}on${color_reset} "
  output+="${solarized_orange}${git_branch}${color_reset} "
  output+="${solarized_base}where${color_reset} "
  output+="${git_color}${git_message}${color_reset}"
fi

# Estimated API list-price cost. Not a bill: a claude.ai subscription is not
# charged this, and transcript-derived totals run somewhat low because some
# auxiliary Claude Code requests record no usage.
if [ -n "$COST_MTD" ]; then
  output+=" "
  output+="${solarized_yellow}\$${COST_MTD}${color_reset} ${solarized_base}mtd,${color_reset} "
  output+="${solarized_orange}\$${COST_YTD}${color_reset} ${solarized_base}ytd${color_reset}"
fi

printf "%s\n" "$output"

# terminal_settings

| File | Install to |
|---|---|
| `ghostty/config.ghostty` | `~/Library/Application Support/com.mitchellh.ghostty/config.ghostty` |
| `windows-terminal/Fragments/terminal_settings/ghostty-palette.json` | `%LOCALAPPDATA%\Microsoft\Windows Terminal\Fragments\terminal_settings\ghostty-palette.json` |
| `windows-terminal/settings-snippet.jsonc` | merge into `%LOCALAPPDATA%\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json` |
| `herdr/config.toml` | macOS: `~/.config/herdr/config.toml` · Windows: `%APPDATA%\herdr\config.toml` |
| `codex/config-snippet.toml` | merge into `~/.codex/config.toml` (Windows: `%USERPROFILE%\.codex\config.toml`) |
| `claude/statusline-command.sh` | `~/.claude/statusline-command.sh` |
| `claude/cost-refresh.py` | `~/.claude/cost-refresh.py` (same directory as the status line script) |
| `claude/pricing.json` | `~/.claude/pricing.json` (same directory; update when API prices change) |
| `bash/.bash_profile` | `~/.bash_profile` |
| `bash/.bashrc` | `~/.bashrc` (just sources `~/.bash_profile`) |
| `bash/.bash_aliases` | `~/.bash_aliases` |
| `bash/.bash_functions` | `~/.bash_functions` |
| `bash/.bash_exports` | `~/.bash_exports` (defines the colors the prompt uses) |
| `bash/.bash_prompt` | `~/.bash_prompt` |
| `bash/.inputrc` | `~/.inputrc` |

Restart Windows Terminal after adding the fragment.

## Bash

Based on [mac-settings](https://github.com/kevinyswong/mac-settings) dotfiles, including the Solarized git-aware prompt.

Copy the files in `bash/` to your home directory (`cp -i bash/.[!.]* ~`; `-i` asks before overwriting), then open a new shell. Overwriting `~/.bash_profile` drops any blocks installers added to it, so copy those over first. Nothing needs filling in: paths use `~` or `$HOME`, and the prompt reads your user and host name from bash (`\u@\h`).

Installer-managed blocks are left out. If you use conda, run `conda init bash` after copying; it appends its block (with your install path) to `~/.bash_profile`. Homebrew is loaded from `/opt/homebrew`, its Apple Silicon location; on an Intel Mac change that line to `/usr/local/bin/brew`.

The prompt shows `user@host` in magenta locally and violet over SSH. The aliases and functions assume macOS (`ls -G`, `pmset`, `ioreg`).

For the Claude Code status line, add to `~/.claude/settings.json`:

```json
"statusLine": { "type": "command", "command": "bash ~/.claude/statusline-command.sh" }
```

If `CLAUDE_CONFIG_DIR` is set, use that directory instead of `~/.claude`. The status line needs `jq` and `git`; the cost segment also needs `python3`.

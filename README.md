# terminal_settings

| File | Install to |
|---|---|
| `ghostty/config.ghostty` | `~/Library/Application Support/com.mitchellh.ghostty/config.ghostty` |
| `windows-terminal/Fragments/terminal_settings/ghostty-palette.json` | `%LOCALAPPDATA%\Microsoft\Windows Terminal\Fragments\terminal_settings\ghostty-palette.json` |
| `windows-terminal/settings-snippet.jsonc` | merge into `%LOCALAPPDATA%\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json` |
| `herdr/config.toml` | macOS: `~/.config/herdr/config.toml` · Windows: `%APPDATA%\herdr\config.toml` |
| `claude/statusline-command.sh` | `~/.claude/statusline-command.sh` |
| `claude/cost-refresh.py` | `~/.claude/cost-refresh.py` (same directory as the status line script) |
| `claude/pricing.json` | `~/.claude/pricing.json` (same directory; update when API prices change) |

Restart Windows Terminal after adding the fragment.

For the Claude Code status line, add to `~/.claude/settings.json`:

```json
"statusLine": { "type": "command", "command": "bash ~/.claude/statusline-command.sh" }
```

If `CLAUDE_CONFIG_DIR` is set, use that directory instead of `~/.claude`. The status line needs `jq` and `git`; the cost segment also needs `python3`.

# terminal_settings

| File | Install to |
|---|---|
| `ghostty/config.ghostty` | `~/Library/Application Support/com.mitchellh.ghostty/config.ghostty` |
| `windows-terminal/Fragments/terminal_settings/ghostty-palette.json` | `%LOCALAPPDATA%\Microsoft\Windows Terminal\Fragments\terminal_settings\ghostty-palette.json` |
| `windows-terminal/settings-snippet.jsonc` | merge into `%LOCALAPPDATA%\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json` |
| `herdr/config.toml` | macOS: `~/.config/herdr/config.toml` · Windows: `%APPDATA%\herdr\config.toml` |
| `herdr/scripts/ipython-pane.sh` | `~/.config/herdr/scripts/ipython-pane.sh` (side pane bound to `prefix+i`) |
| `herdr/scripts/reconnect-machines.sh` | `~/.config/herdr/scripts/reconnect-machines.sh` (popup bound to `prefix+m`) |
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

Copy the files in `bash/` to your home directory and open a new shell. First move any installer blocks from your old `~/.bash_profile` into the new one, except conda's. The prompt shows `user@host` in magenta locally and violet over SSH.

The same files work on macOS and Linux. On macOS, Homebrew is loaded from `/opt/homebrew` (Apple Silicon).

`cat`, `PAGER` and `MANPAGER` use [bat](https://github.com/sharkdp/bat) if it's installed (`brew install bat` or `apt install bat`; Debian and Ubuntu name it `batcat`, which is picked up too), otherwise `cat` and `less`. Git always uses `less`.

Don't run `conda init bash`: its block adds about 0.5s to every new shell. Instead, `~/.bash_profile` finds conda in the usual places (add yours to the list if it lives elsewhere) and activates `base` directly. `conda activate` and `conda deactivate` work as usual. If shells get slow again, check `$CONDA_PREFIX/etc/conda/activate.d/`; conda's compiler packages, for example, add about 0.5s.

## Claude Code status line

Add to `~/.claude/settings.json`:

```json
"statusLine": { "type": "command", "command": "bash ~/.claude/statusline-command.sh" }
```

If `CLAUDE_CONFIG_DIR` is set, use it instead of `~/.claude` here and in the table. Needs `jq` and `git`; the cost segment also needs `python3`.

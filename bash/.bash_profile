# Homebrew, on macOS only (Apple Silicon location). Loaded first so the files below can
# find brew-installed tools such as bat.
if [[ $OSTYPE == darwin* && -x /opt/homebrew/bin/brew ]]; then eval "$(/opt/homebrew/bin/brew shellenv)"; fi

if [ -f ~/.bash_aliases ]; then . ~/.bash_aliases; fi
if [ -f ~/.bash_functions ]; then . ~/.bash_functions; fi
if [ -f ~/.bash_exports ]; then . ~/.bash_exports; fi
if [ -f ~/.bash_prompt ]; then . ~/.bash_prompt; fi

# Append to the Bash history file, rather than overwriting it
shopt -s histappend;

# Autocorrect typos in path names when using `cd`
shopt -s cdspell;

export BASH_SILENCE_DEPRECATION_WARNING=1

# Activate conda's base env without `conda init`. The lines `conda init` adds start conda's
# Python twice per shell (once to set up the `conda` command, once for `conda activate base`),
# about 0.5s. Here conda.sh sets up the same `conda` command without starting Python, and the
# rest of the loop does what `conda activate base` would.
# The first install found wins; add yours to the list if it lives elsewhere.
for __conda_root in "$HOME/miniconda3" "$HOME/miniforge3" "$HOME/anaconda3" \
    "$HOME/opt/miniconda3" "$HOME/opt/anaconda3" /opt/miniconda3 /opt/anaconda3 /opt/conda; do
  if [ -f "$__conda_root/etc/profile.d/conda.sh" ]; then
    . "$__conda_root/etc/profile.d/conda.sh"
    export CONDA_PREFIX="$__conda_root" CONDA_DEFAULT_ENV=base CONDA_SHLVL=1 CONDA_PROMPT_MODIFIER='(base) '
    # Drop any inherited copy (e.g. herdr started from an activated shell) so
    # `conda deactivate`, which removes one entry, leaves none.
    __conda_bin=":$CONDA_PREFIX/bin:"
    PATH=":$PATH:"
    while [[ $PATH == *"$__conda_bin"* ]]; do PATH=${PATH//"$__conda_bin"/:}; done
    PATH=${PATH#:}; PATH=${PATH%:}
    export PATH="$CONDA_PREFIX/bin:$PATH"
    # Packages' activation scripts, as `conda activate` runs them. A slow one here
    # (conda's compiler packages, say) makes every new shell slow.
    for __conda_script in "$CONDA_PREFIX"/etc/conda/activate.d/*.sh; do
      if [ -f "$__conda_script" ]; then . "$__conda_script"; fi
    done
    break
  fi
done
unset __conda_root __conda_bin __conda_script

export PATH="$HOME/.local/bin:$PATH"

# Installers append their own lines below. Don't run `conda init`: conda is set up above,
# and the lines it adds would slow shell start up.

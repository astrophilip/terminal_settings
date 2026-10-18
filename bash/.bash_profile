if [ -f ~/.bash_aliases ]; then . ~/.bash_aliases; fi
if [ -f ~/.bash_functions ]; then . ~/.bash_functions; fi
if [ -f ~/.bash_exports ]; then . ~/.bash_exports; fi
if [ -f ~/.bash_prompt ]; then . ~/.bash_prompt; fi

# Append to the Bash history file, rather than overwriting it
shopt -s histappend;

# Autocorrect typos in path names when using `cd`
shopt -s cdspell;

export BASH_SILENCE_DEPRECATION_WARNING=1

# Homebrew (Apple Silicon location; Intel Macs use /usr/local/bin/brew)
if [ -x /opt/homebrew/bin/brew ]; then eval "$(/opt/homebrew/bin/brew shellenv)"; fi

export PATH="$HOME/.local/bin:$PATH"

# Installers such as `conda init bash` append their own blocks below this line.

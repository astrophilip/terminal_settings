# Navigation
alias ..="cd .."
alias ...="cd ../.."
alias ....="cd ../../.."
alias .....="cd ../../../.."

alias gst="git status"
alias gl="git log --graph --pretty=format:'%Cgreen%h%Creset -%C(blue)%d%Creset %s %Cgreen(%cr)%Creset'"
alias grep="grep --color=auto"
# bat as cat: syntax highlighting, no line numbers/header, never pages (plain `bat` still does).
# Needs bat (`brew install bat` or `apt install bat`); Debian and Ubuntu name the binary
# batcat, so `bat` is aliased to it there. Without either, cat stays the system cat.
if type -P bat >/dev/null; then
  alias cat="bat --style=plain --paging=never"
elif type -P batcat >/dev/null; then
  alias bat="batcat"
  alias cat="batcat --style=plain --paging=never"
fi
alias v="vim"
alias functions="declare -f | grep '()'"

# Colored ls: macOS (BSD) ls takes -G; GNU ls on Linux takes --color (and reads -G as --no-group).
if [[ $OSTYPE == darwin* ]]; then __ls_color="-G"; else __ls_color="--color=auto"; fi
alias ls="ls -F $__ls_color"
alias ll="ls -lhF $__ls_color"
alias la="ls -ahF $__ls_color"
alias lla="ls -lahF $__ls_color"
alias lt="ls -lahtF $__ls_color" # sort by time modified, non-ascending order
unset __ls_color

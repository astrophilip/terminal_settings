# Navigation
alias ..="cd .."
alias ...="cd ../.."
alias ....="cd ../../.."
alias .....="cd ../../../.."

alias gst="git status"
alias gl="git log --graph --pretty=format:'%Cgreen%h%Creset -%C(blue)%d%Creset %s %Cgreen(%cr)%Creset'"
alias grep="grep --color=auto"
# bat as cat: syntax highlighting, no line numbers/header, never pages (plain `bat` still does).
# Needs bat: `brew install bat`. Without it, cat stays the system cat.
if command -v bat >/dev/null; then alias cat="bat --style=plain --paging=never"; fi
alias v="vim"
alias functions="declare -f | grep '()'"

alias ls="ls -FG"
alias ll="ls -lhFG"
alias la="ls -ahFG"
alias lla="ls -lahFG"
alias lt="ls -lahtFG" # sort by time modified, non-ascending order

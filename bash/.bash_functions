# Show all tput colors
show_tput() {
  for i in {0..255}; do
    printf "$(tput setab $i)   $i   $(tput sgr0)"
  done
  printf "\n\n\n"
  unset i
}

# Show solarized colors
show_solarized() {
  printf "\e[38;2;147;161;161mbase.    rgb(147,161,161).\e[0m"
  printf "    \e[48;2;147;161;161m                      \e[0m\n"
  printf "\e[38;2;181;137;0myellow.  rgb(181,137,0).\e[0m"
  printf "      \e[48;2;181;137;0m                      \e[0m\n"
  printf "\e[38;2;203;75;22morange.  rgb(203,75,22).\e[0m"
  printf "      \e[48;2;203;75;22m                      \e[0m\n"
  printf "\e[38;2;220;50;47mred.     rgb(220,50,47).\e[0m"
  printf "      \e[48;2;220;50;47m                      \e[0m\n"
  printf "\e[38;2;211;54;130mmagenta. rgb(211,54,130).\e[0m"
  printf "     \e[48;2;211;54;130m                      \e[0m\n"
  printf "\e[38;2;108;113;196mviolet.  rgb(108,113,196).\e[0m"
  printf "    \e[48;2;108;113;196m                      \e[0m\n"
  printf "\e[38;2;38;139;210mblue.    rgb(38,139,210).\e[0m"
  printf "     \e[48;2;38;139;210m                      \e[0m\n"
  printf "\e[38;2;42;161;152mcyan.    rgb(42,161,152).\e[0m"
  printf "     \e[48;2;42;161;152m                      \e[0m\n"
  printf "\e[38;2;133;153;0mgreen.   rgb(133,153,0).\e[0m"
  printf "      \e[48;2;133;153;0m                      \e[0m\n"
  printf "\n\n"
}

# Power drawn from the adapter and used by the system, in watts (Apple laptops)
powerstats() {
  ioreg -rw0 -c AppleSmartBattery \
    | grep -oE '"(SystemPowerIn|SystemLoad)"=[0-9]+' \
    | sort -u \
    | awk -F= '{gsub(/"/,"",$1); printf "%s: %.2f W\n", $1, $2/1000}'
}

# Turn the display off now (macOS)
sleepdisplay() {
    caffeinate -u -t 3
    sleep 2
    pmset displaysleepnow
}

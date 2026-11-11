" Keep Vim's own sensible defaults (incsearch, wildmenu, mouse, ruler, filetype plugins)
unlet! skip_defaults_vim
source $VIMRUNTIME/defaults.vim

" 16 palette colors only, so highlighting follows the terminal palette
set notermguicolors
set t_Co=16
colorscheme default
set background=dark
highlight Comment ctermfg=2
highlight LineNr ctermfg=8
highlight CursorLine cterm=NONE ctermbg=0
highlight CursorLineNr cterm=NONE ctermfg=7 ctermbg=0

set laststatus=2            " always show the status line (filename, flags, position)
set number                  " line numbers
set cursorline              " highlight the current line
set tabstop=4 shiftwidth=4 expandtab
set hlsearch ignorecase     " highlight matches; case-insensitive search
set showmatch               " flash the matching bracket
set title                   " filename in the terminal title bar

" Vim only knows .bash_profile and .bash_aliases; treat the other dotfiles as bash too
autocmd BufRead,BufNewFile .bash_* set filetype=bash

map q <Nop>

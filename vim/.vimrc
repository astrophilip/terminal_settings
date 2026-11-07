""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" Colors and Fonts
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
syntax enable
" Quiet scheme built from the Ghostty palette (vim/colors/ghostty.vim)
colorscheme ghostty

set encoding=utf8

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" Appearance
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" Show the filename in the window titlebar
set title

" Visual autocomplete for command menu
set wildmenu

" Highlight current line
set cursorline

" Enable line numbers
set number

" Change tabs to 2 spaces
set tabstop=2
        
" Tabs convert to spaces
set expandtab

" Highlight searches
set hlsearch

" Ignore case of searches
set ignorecase

" Highlight dynamically as pattern is typed
set incsearch

" Optimize for fast terminal connections
set ttyfast

" When cursor is on a brace, highlights its matching brace
set showmatch

" Enable mouse in all modes
" Drawback is that to copy, need to hold OPTION.
" Otherwise, copying enters visual mode.
set mouse=a

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" Status bar. Options available at :h statusline
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" Always show status bar
set laststatus=2

" Status bar contents: file path and flags on the left, position on the right
set statusline=%1*%F                                        " file path
set statusline+=\ %2*%m                                     " modified
set statusline+=%3*%r                                       " read only
set statusline+=%0*%=                                       " right aligned items
set statusline+=Line:\ %1*%l%0*/%1*%L                       " line / total lines
set statusline+=\ %0*(%1*%p%%%0*)                           " percent through file
set statusline+=\ \ %0*Col:\ %1*%c\                        " column

" Status bar colors (User1-3) are set in the colorscheme.

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" Mappings
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" Remove vim recording
map q <Nop>

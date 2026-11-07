" Quiet colorscheme drawn from the terminal's 16-color palette (see
" ghostty/config.ghostty), so it follows whatever Ghostty is set to.
"
" Plain text stays in the terminal foreground; only the normal (0-7) slots
" are used for syntax, since the bright ones are much louder. No bold:
" Ghostty's `bold-color = bright` would swap bold text to the bright slots.
"
" The gui colors copy the Ghostty palette so the scheme also works with
" `set termguicolors` or in gvim.

set background=dark
hi clear
if exists('syntax_on')
  syntax reset
endif
let g:colors_name = 'ghostty'

let s:p = {
      \ 'fg':      ['NONE', '#c9cad2'],
      \ 'bg':      ['NONE', '#11111a'],
      \ 'black':   ['0',    '#1e1e2d'],
      \ 'red':     ['1',    '#cc6666'],
      \ 'green':   ['2',    '#9aa251'],
      \ 'yellow':  ['3',    '#d89f31'],
      \ 'blue':    ['4',    '#7191ad'],
      \ 'magenta': ['5',    '#9f81a9'],
      \ 'cyan':    ['6',    '#6ea69f'],
      \ 'white':   ['7',    '#c9cad2'],
      \ 'grey':    ['8',    '#6d7084'],
      \ 'none':    ['NONE', 'NONE'],
      \ }

" s:hi(group, fg, bg [, attr])
function! s:hi(group, fg, bg, ...) abort
  let l:attr = a:0 ? a:1 : 'NONE'
  let l:f = s:p[a:fg]
  let l:b = s:p[a:bg]
  " The real background only matters in the GUI; terminals keep their own.
  let l:guibg = a:bg ==# 'none' ? 'NONE' : l:b[1]
  execute 'hi' a:group
        \ 'ctermfg=' . l:f[0] 'ctermbg=' . l:b[0] 'cterm=' . l:attr
        \ 'guifg=' . l:f[1] 'guibg=' . l:guibg 'gui=' . l:attr
endfunction

" --- Editor UI ---------------------------------------------------------
call s:hi('Normal',       'fg',      'none')
if has('gui_running')
  call s:hi('Normal',     'fg',      'bg')
endif
call s:hi('LineNr',       'grey',    'none')
call s:hi('CursorLineNr', 'white',   'black')
call s:hi('CursorLine',   'none',    'black')
call s:hi('CursorColumn', 'none',    'black')
call s:hi('ColorColumn',  'none',    'black')
call s:hi('SignColumn',   'grey',    'none')
call s:hi('FoldColumn',   'grey',    'none')
call s:hi('Folded',       'grey',    'black')
call s:hi('VertSplit',    'black',   'none')
call s:hi('NonText',      'grey',    'none')
call s:hi('SpecialKey',   'grey',    'none')
call s:hi('EndOfBuffer',  'black',   'none')
call s:hi('Visual',       'none',    'black', 'reverse')
call s:hi('Search',       'black',   'yellow')
call s:hi('IncSearch',    'black',   'blue')
call s:hi('CurSearch',    'black',   'blue')
call s:hi('MatchParen',   'yellow',  'black', 'underline')
call s:hi('StatusLine',   'white',   'black')
call s:hi('StatusLineNC', 'grey',    'black')
call s:hi('StatusLineTerm',   'white', 'black')
call s:hi('StatusLineTermNC', 'grey',  'black')
call s:hi('TabLine',      'grey',    'black')
call s:hi('TabLineFill',  'none',    'black')
call s:hi('TabLineSel',   'white',   'none')
call s:hi('WildMenu',     'black',   'blue')
call s:hi('Pmenu',        'white',   'black')
call s:hi('PmenuSel',     'black',   'blue')
call s:hi('PmenuSbar',    'none',    'black')
call s:hi('PmenuThumb',   'none',    'grey')
call s:hi('Title',        'blue',    'none')
call s:hi('Directory',    'blue',    'none')
call s:hi('ErrorMsg',     'red',     'none')
call s:hi('WarningMsg',   'yellow',  'none')
call s:hi('ModeMsg',      'grey',    'none')
call s:hi('MoreMsg',      'green',   'none')
call s:hi('Question',     'green',   'none')
call s:hi('SpellBad',     'none',    'none', 'underline')
call s:hi('SpellCap',     'none',    'none', 'underline')
call s:hi('SpellRare',    'none',    'none', 'underline')
call s:hi('SpellLocal',   'none',    'none', 'underline')
call s:hi('DiffAdd',      'green',   'black')
call s:hi('DiffDelete',   'red',     'black')
call s:hi('DiffChange',   'none',    'black')
call s:hi('DiffText',     'yellow',  'black')

" Status line segments used by the vimrc (%1*, %2*, %3*)
call s:hi('User1',        'white',   'black')
call s:hi('User2',        'yellow',  'black')
call s:hi('User3',        'red',     'black')

" --- Syntax ------------------------------------------------------------
call s:hi('Comment',      'green',   'none')
call s:hi('String',       'yellow',  'none')
call s:hi('Character',    'yellow',  'none')
call s:hi('Constant',     'red',     'none')
call s:hi('Number',       'red',     'none')
call s:hi('Boolean',      'red',     'none')
call s:hi('Float',        'red',     'none')
call s:hi('Identifier',   'fg',      'none')
call s:hi('Function',     'blue',    'none')
call s:hi('Statement',    'magenta', 'none')
call s:hi('Operator',     'fg',      'none')
call s:hi('PreProc',      'magenta', 'none')
call s:hi('Type',         'cyan',    'none')
call s:hi('Special',      'cyan',    'none')
call s:hi('Delimiter',    'fg',      'none')
call s:hi('Underlined',   'blue',    'none', 'underline')
call s:hi('Ignore',       'grey',    'none')
call s:hi('Error',        'red',     'none', 'underline')
call s:hi('Todo',         'yellow',  'none')

" Python marks `self`, decorators and builtins; keep them calm too.
hi link pythonBuiltin     Function
hi link pythonDecorator   PreProc
hi link pythonDecoratorName PreProc

delfunction s:hi

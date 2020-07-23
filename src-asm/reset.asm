push
  # reset
liw 3, <CurrentFiles>   # cf (currentFiles)
call <CFReset>          # cf.reset (blanks FA and FB, then runs loadToCurrent())
  # file init
liw 3, <CurrentFiles>   # cf (currentFiles)
li 4, 1                 # 1 means FB here
call <CFFileInit>       # cf.fileInit(1) (sets basic values on file like hearts = 6)
pop

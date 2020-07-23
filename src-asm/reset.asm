push
  # setSpawn (manually write data to master spawn object)
liw 3, <Spawn>          # master spawn object
liw 4, 0x46303030       # location - Skyloft map ID (F000)
li 5, 0x0               # location ctd. (null terminator)
li 6, 0x1c              # layer
li 7, 0x3f              # entrance
stw 4, 0x0(3)           # location
stw 5, 0x4(3)           # location ctd. (null terminator)
stb 6, 0x23(3)          # layer
stb 7, 0x24(3)          # entrance
  # reset
liw 3, <CurrentFiles>   # cf (currentFiles)
call <CFReset>          # cf.reset (blanks FA and FB, then runs loadToCurrent())
  # file init
liw 3, <CurrentFiles>   # cf (currentFiles)
li 4, 1                 # 1 means FB here
call <CFFileInit>       # cf.fileInit(1) (sets basic values on file like hearts = 6)
pop

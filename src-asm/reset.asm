push
  # setSpawn
liw 3, 0x805B6B0C
liw 4, 0x46303030
li 5, 0x0
li 6, 0x1c
li 7, 0x3f
stw 4, 0x0(3)
stw 5, 0x4(3)
stb 6, 0x23(3)
stb 7, 0x24(3)
  # reset
liw 3, 0x8095545C       # cf (currentFiles)
call 0x80010560         # reset(cf)
  # file init
liw 3, 0x8095545C       # cf (currentFiles)
li 4, 1
call 0x8000abc0
pop

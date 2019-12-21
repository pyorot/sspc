push
liw 3, 0x8095545C       # cf (currentFiles)
call 0x8000E180         # fileSaveSelected(cf)
pop

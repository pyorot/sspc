push
liw 3, 0x8095545C       # cf (currentFiles)
call 0x8000D390         # fileLoadSelected(cf)
call 0x800C0740         # loadToCurrent()
pop

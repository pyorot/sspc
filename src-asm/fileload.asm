push
liw 3, 0x8095545C       # cf (currentFiles)
call 0x8000D390         # cf.fileLoadSelected() (copies FS → FA)
call 0x800C0740         # loadToCurrent() (copies all committable data to static "current" data)
pop

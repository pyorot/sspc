push
liw 3, <CurrentFiles>     # cf (currentFiles)
call <CFFileLoadSelected> # cf.fileLoadSelected() (copies FS → FA)
call <LoadToCurrent>      # loadToCurrent() (copies all committable data to static "current" data)
pop

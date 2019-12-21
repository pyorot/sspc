push
liw 3, 0x80000008       # dest address
lis 4, 0x80000000@h     # src address (use liw if right-half non-zero)
li 5, 8                 # size (bytes)
call 0x800043c4         # memcpy(dest, src, size)
pop

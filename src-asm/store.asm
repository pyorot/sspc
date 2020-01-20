push

# position store
liw 3, 0x805789EC       # static ptr to Link
lwz 4, 0 (3)            # r4 has Link (or nullptr)
liw 3, 0x8095545C       # r3 has cf (currentFiles), i.e. FA - 0x8
cmpwi r4, 0             # if r4 is nullptr
beq label_0             # skip copying
    lhz 6, 0xBA (4)         # Link 1θ
    lwz 7, 0xC0 (4)         # Link 1x
    lwz 8, 0xC4 (4)         # Link 1y
    lwz 9, 0xC8 (4)         # Link 1z
    sth 6, 0x5316 (3)       # FA 1θ (relative to cf = FA - 0x8)
    stw 7, 0x18 (3)         # FA 1x
    stw 8, 0x1C (3)         # FA 1y
    stw 9, 0x20 (3)         # FA 1z

# file save
label_0:                # note that r3 is cf from before
call 0x8000E180         # cf.fileSaveSelected() (copies FA → FS)

pop

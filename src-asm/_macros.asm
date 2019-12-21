.macro liw reg, word            # load literal (li) word into register
    lis \reg, \word @h          # load left half and shift
    ori \reg,\reg,\word @l      # add in right half
.endm

.macro call address             # call function at address
    liw r0, \address            # load address into r0
    mtctr r0                    # move into CTR
    bctrl                       # branch+link from CTR
.endm

.macro push                     # backup registers into new stack frame
    stwu r1,-0x80(r1)           # create frame and move stack ptr, r1
    mflr r0                     # load LR into r0
    stw r0,0x84(r1)             # store r0 (=LR) at offset 0x4 of next frame
    stmw r3,8(r1)               # store r3-r31 at offset 0x8 (to 0x7C)
.endm

.macro pop                      # restore registers from (popped) stack frame
    lmw r3,8(r1)                # load r3-r31 from frame+0x8
    lwz r0,0x84(r1)             # load frame+0x4 (=LR) into r12
    mtlr r0                     # load this into LR
    addi r1,r1,0x80             # pop stack (add size to stack ptr, r1)
.endm

# use push/pop to set aside existing register values, yielding a fresh context where
# injected code and function calls can run w/o side-effects. the preserved registers are:
# r3–r31 and LR. r0 is used to load in/out of LR, as per convention

.macro print
    sthu r14,2(r6)          # Store halfword contents of r4 to the address after the one in r3 and update it.
.endm

.macro printi char
    li r14, \char           # Store a literal char into the printing cursor and update it.
    print
.endm

.macro pushlr               # Stores register 0 on the stack, and stores the link register in r0
    stwu r1,-0x10(r1)
    stw r0,4(r1)
    mflr r0
.endm

.macro poplr                # Sets the link register to r0, then recovers r0 from the stack.
    mtlr r0
    lwz r0,4(r1)
    addi r1,r1,0x10
.endm

# Some relevant in-game struct layouts...
                                    # struct HUDElement:
.set Offset_Parent, 0xC             #   word ParentPtr;     // ptr to a HUDElement which contains this
.set Offset_Opacity, 0xB8           #   byte Opacity;       // alpha channel, 0x00 to 0xFF
.set Offset_Flags, 0xBB             #   byte Flags;         // 1 = displayed, 2 = ??, 4 = apply scaling factor

                                    # struct TextDisplay inherits HUDElement:
.set Offset_Text_Ptr, 0xD8          #   word TextPtr;       // Points to the start of the UTF16 text content.
.set Offset_Text_Index, 0xFF        #   byte TextIndex;     // Must be non-zero for the text to be displayed. Indicates which source the displayed text was copied from.
.set Offset_Text_TextLength, 0x19B  #   byte TextLength;    // Length of the string, in UTF-16 characters, not bytes. May actually be halfword.

                                    # struct Label inherits HUDElement:
.set Offset_Label_TextBg, 0x8B4     #   TextDisplay Background
.set Offset_Label_TextFg, 0xB34     #   TextDisplay Foreground

.set Offset_Label_Text_Loaded, Offset_Label_TextFg + Offset_Parent
.set Offset_Start_Print, 0x1E

.macro init_print_cursor reg
    addi \reg, r3, Offset_Start_Print
.endm

# r3 = EmptyA
# r4 = Link ptr
# r5 = Button ptr
# r6 = Printing cursor; when printing is done, it is used for # of halfwords printed
# r8 = int to convert
# f4 = value to convert
# EmptyA:
#   [0 - 0x17]      = Store floats from registers
#   [0x20 - 0x3F]   = Print result
#   [0x40 - 0x4F]   = Temporary scratch

push
main:
    liw r4, LinkHeader
    liw r3, EmptyA

    stfd f3, 0(r3)                      # Store off f3,f4,f5 in empty space.
    stfd f4, 8(r3)
    stfd f5, 0x10(r3)

    lfs f4,0xC8(r4)
    liw r5,ZButtonLabel
    bl float_out                        # Link Z on Z button

    lfs f4,0xC0(r4)
    liw r5,NunchukLabel
    bl float_out                        # Link X above Nunchuk

    lhz r8,0xBA(r4)
    liw r5,TwoButtonLabel
    bl word_out                         # Link Angle on 2 button

    lfs f4,0xC4(r4)
    liw r5,CButtonLabel
    bl float_out                        # Link Y on C button
b end

float_out:                              # Displays the value of the float in f4 on the label or group whose header ptr is in r5.
    mflr r0
    init_print_cursor r6                # Initialize the printing cursor.
    bl print_float_to_utf16_data        # Print the float, as UTF16 in decimal, to the empty space.
    bl print_end                        # Finish printing. This stores the number of characters printed in r6.
    bl print_data_to_label              # Copies the printed data and # of characters printed to the label, and enables it if possible.
    mtlr r0
blr

print_end:
    init_print_cursor r8
    sub r6,r6,r8                        # Get the return value (bytes written) by subtracting the starting address from the current address
    srwi r6,r6,1                        # Store the return value in halfwords by dividing by two.
blr

word_out:                               # Displays the value of the word in r8 on the label whose header ptr is in r5.
    mflr r0
    init_print_cursor r6                # Initialize the printing cursor.
    li r12,1                            # We want trailing zeroes, not leading zeroes, for this.
    bl print_word_to_utf16_data         # Print the word, as UTF16 in decimal, to the empty space.
    bl print_end                        # Finish printing. This stores the number of characters printed in r6.
    mtlr r0
# Fallthrough: let print_data_to_label return to main.

print_data_to_label:                    # Prints the UTF16 string, starting at EmptyA+0x20 and with length equal to the value in r6, to the label pointed to in r5.
    pushlr
        lwz r8, Offset_Label_Text_Loaded(r5)
        cmpw r8,r5
        bne _print_data_to_label_end    # Assert label text has the label set as parent, to ensure it's hud data.
        li r7,3
        mtctr r7
        li r9,0xFF
        _enable_parent:
            cmpwi r8,0
            beq _end_parent_loop
            bl enable_hudelement
        bdnz _enable_parent
        _end_parent_loop:

        addi r8,r5,Offset_Label_TextFg  # Store the foreground text and enable it.
        bl print_data_to_text
        
        addi r8,r5,Offset_Label_TextBg  # Store the background text and enable it.
        li r9,0x40
        bl print_data_to_text
        _print_data_to_label_end:
    poplr
blr

print_data_to_text:                     # Prints the UTF16 string, starting at EmptyA+0x20 and with length equal to the value in r6, to the text whose header is pointed to in r8.
    lwz r10,Offset_Text_Ptr(r8)          # Load the pointer to the text content.
    cmpwi r10,0
    beq _end_enable_hudelement
    
    lmw r24,0x20(r3)                    # Brief memcpy from the printing space to the text pointer.
    stmw r24,0(r10)
    
    stb r6,Offset_Text_TextLength(r8)   # Set text length

    li r10,1
    stb r10,Offset_Text_Index(r8)        # Set text index to 1. Doesn't matter what it is as long as it's not 0.
# Fallthrough: let enable_hudelement return to caller.

enable_hudelement:                      # Enables the hud element whose pointer is in r8, via opacity and flags, and stores the element's parent in r8
    stb r9, Offset_Opacity(r8)
    lbz r10,Offset_Flags(r8)
    ori r10,r10,1
    stb r10,Offset_Flags(r8)
    lwz r8,Offset_Parent(r8)
    _end_enable_hudelement:
blr

print_word_to_utf16_data:           # Print the word in r8 as decimal UTF16 string.
    # params:   r3 = Empty space begin
    #           r6 = printing cursor
    #           r8 = word to convert
    #           r12 = 1 for trailing zeroes, 0 for leading zeroes (up to 6 places)
    # locals:   r9 = power of 10 to use for extracting digits
    #           r10 = constant 10 for use in divw instruction because there is no divwi
    #           r11 = 1 if anything has been printed
    #           r14 = pass char to print

    cmpwi r8,0                                    # if (word to convert) == 0:
    bne _print_word_to_utf16_data_nonzero
        printi 0x30                               #     print '0'
        b _print_word_to_dec_end                  #     return
    _print_word_to_utf16_data_nonzero:
    
    liw r9,0x186A0                                # r9 := 100,000 literal
    li r10,10
    li r11,0

    try_digit:                                    # do {
        cmpw r8,r9                                #     if r8 < r9 (current digit is zero) {
        bge try_digit_else
            cmpwi r11,0                           #         if r11 == 0  (haven't printed anything) {
            bne try_digit_2
            cmpwi r12,1                           #             if r12 == 1 (we don't want leading zeroes) {
            beq try_digit_compare                 #                 then skip printing this digit;
            try_digit_2:                          #         } }
            or r14,r8,r12                         #         if r6 == 0 && r7 == 0 (all remaining digits are zero and we don't want trailing zeroes) {
            cmpwi r14,0
            beq _print_word_to_dec_end            #             skip the rest of the word }
            printi 0x30                           #         print '0'
            ori r11,r11,1                         #         r11 := 1 (have now printed a digit)
            b try_digit_compare
        try_digit_else:                           #     } else {
            divw r15,r8,r9                        #         r15 = current digit
            addi r14,r15,0x30                     #         print current digit
            print
            ori r11,r11,1                         #         r11 := 1 (have now printed a digit)
            mullw r14,r15,r9
            sub r8,r8,r14                         #         subtract the leading digit before next loop
        try_digit_compare:                        #     }
        divw r9,r9,r10                            #     r9 /= 10;
    cmpwi r9,0
    bne try_digit                                 # } while (r9 != 0);
    _print_word_to_dec_end:
blr

print_float_to_utf16_data:  # Print the float in f4 as a decimal UTF16 string.
    # params:   f4 = float to print
    # locals:   r8 = temporary index and word storage
    #           r9 = temporary storage
    #           f5 = math
    #           f3 = math
    pushlr
    fabs f3,f4                  # Load its absolute value into f3 for processing
    fcmpo 7,f3,f4               # if the original value is negative, print '-'
    beq 7,_print_float_to_utf16_data_positive
        printi 0x2D
    _print_float_to_utf16_data_positive:

    fctiwz f4,f3

    li r8,0x40
    stfiwx f4,r8,r3
    lwz r8,0x40(r3)             # Convert the float to its integer part. Store the resulting word in r8.

    # Algorithm from http://mirror.informatimago.com/next/developer.apple.com/documentation/mac/PPCNumerics/PPCNumerics-157.html
    .set Magic_A, 0x80000000    # Magic dblword constant for the conversion algorithm.
    .set Magic_B, 0x43300000
    liw r14,Magic_A
    stw r14,0x44(r3)
    liw r14,Magic_B
    stw r14,0x40(r3)
    stw r14,0x48(r3)
    xoris r12,r8,0x8000
    stw r12,0x4C(r3)
    lfd f4,0x48(r3)
    lfd f5,0x40(r3)
    fsub f4,f4,f5               # The float in f4 is now the integer part of the original float.

    fsub f3,f3,f4               # Fractional part is in f3 now.

    li r12,1                    # Add trailing zeroes
    bl print_word_to_utf16_data # Print the integer part

    printi 0x2E                 # Print '.'

    liw r9,0x412e8480           # Store 1,000,000.0 literal in f4.
    stw r9,0x48(r3)
    lfd f4,0x48(r3)
    fmul f3,f4,f3               # f3 *= f4
    fctiw f4,f3                 # f4 is now 6 decimal places of the fractional part, as an integer word
    
    li r8,0x40
    stfiwx f4,r8,r3
    lwz r8,0x40(r3)             # Convert the float to its integer part. Store the resulting word in r8.
    
    li r12,0                    # Trailing zeroes unnecessary now that we're past the decimal
    bl print_word_to_utf16_data
    poplr
blr

end:
    lfd f3,0x0(r5)             # restore f3,f4,f5
    lfd f4,0x8(r5)
    lfd f5,0x10(r5)
pop

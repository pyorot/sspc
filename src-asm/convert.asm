.macro print
    sth r4,0(r3)            # Store halfword contents of r4 to the address of r3
    addi r3,r3,2            # Add 2 to r3
.endm

.macro printi char
    li r4, \char
    sth r4,0(r3)
    addi r3,r3,2
.endm

# 80001500 = base
# [0] = mode
#   code 1 = halfword to decimal: halfword at [4-5]
#   code 2 = single-precision float to decimal: float at [4-7]
# [8] = return value, 1B, # of halfwords printed
# 
# [20-3F] = output of printed chars
# [40-47] = store f3
# [48-4f] = store f4
# [50-57] = store f5
# [60-78] = scratch for word_to_float
# [80-8f] = scratch for float_to_dec
# [90-9f] = scratch for gecko code
# [a0-af] = store GR0, GR1, GR2, GR3

# r3 = pointer to current place to print
# r4 = halfword to be printed
# r5 = base address

push
main:
    liw r5, 0x80001500          # Base address
    lbz r4, 0(r5)               # Instruction code
    liw r3, 0x80001520          # Point to output
    cmpwi r4,1
    beq halfword_to_dec
    cmpwi r4,2
    beq float_to_dec
    print_error:
        liw r6, 0x00450052          # error: unknown instruction code
        liw r7, 0x0052004F
        lis r8, 0x0052
        stswi r6,r3,10
        addi r3,r3,10
        b end

halfword_to_dec:
    lhz r6, 4(r5)
    li r7,1
    bl print_word_to_dec
b end

float_to_dec:
    stfd f3, 0x40(r5)           # Store off f3,f4,f5
    stfd f4, 0x48(r5)
    stfd f5, 0x50(r5)

    lfs f4, 4(r5)               # Load the value to convert into f4
    fabs f3,f4                  # Load its absolute value into f3 for processing
    fcmpo 7,f3,f4               # if the original value is negative, print '-'
    beq 7,_normal
        printi 0x2D
     _normal:

    fctiwz f4,f3

    li r6,0x80
    stfiwx f4,r6,r5
    lwz r6,0x80(r5)             # Convert the float to its integer part. Store the resulting word in r6.
    bl word_to_float            # Stores the word in r6 in f4, converted back to float, but is now just the integer part
    fsub f3,f3,f4               # Fractional part is in f3 now.

    li r7,1                     # Add trailing zeroes
    bl print_word_to_dec        # Print the integer part

    printi 0x2E                 # Print '.'

    liw r9,0x412e8480           # Store 1,000,000.0 literal in f4.
    stw r9,0x88(r5)
    lfd f4,0x88(r5)
    fmul f3,f4,f3               # f3 *= f4
    fctiw f4,f3                 # f4 is now 6 decimal places of the fractional part, as an integer word
    
    li r6,0x80
    stfiwx f4,r6,r5
    lwz r6,0x80(r5)             # Convert the float to its integer part. Store the resulting word in r6.
    
    li r7,0                     # Trailing zeroes unnecessary now that we're past the decimal
    bl print_word_to_dec

    lfd f3,0x40(r5)             # restore f3,f4,f5
    lfd f4,0x48(r5)
    lfd f5,0x50(r5)
b end

print_word_to_dec:                                # Print the word in r6 as decimal UTF16 string.
    # params:   r3 = printing pointer
    #           r5 = base pointer
    #           r6 = word to convert
    #           r7 = 1 for trailing zeroes, 0 for leading zeroes (up to 6 places)
    # locals:   r0 = LR storage
    #           r4 = pass char to print
    #           r9 = power of 10 to use for extracting digits
    #           r10 = constant 10 for use in divw instruction because there is no divwi
    #           r11 = 1 if anything has been printed

    mflr r0
    cmpwi r6,0                                    # if r6 == 0:
    bne nonzero
        printi 0x30                               #     print '0'
        b _end_print_word_to_dec                  #     return
    nonzero:
    
    liw r9,0x186A0                                # r9 := 100,000 literal
    li r10,10
    li r11,0

    try_digit:                                    # do {
        cmpw r6,r9                                #     if r6 < r9 (current digit is zero) {
        bge try_digit_else
            cmpwi r11,0                           #         if r11 == 0  (haven't printed anything) {
            bne try_digit_2
            cmpwi r7,1                            #             if r7 == 1 (we don't want leading zeroes) {
            beq try_digit_compare                 #                 then skip printing this digit;
            try_digit_2:                          #         } }
            or r12,r6,r7                          #         if r6 == 0 && r7 == 0 (all remaining digits are zero and we don't want trailing zeroes) {
            cmpwi r12,0
            beq _end_print_word_to_dec            #             skip the rest of the word }
            printi 0x30                           #         print '0'
            ori r11,r11,1                         #         r11 := 1 (have now printed a digit)
            b try_digit_compare
        try_digit_else:                           #     } else {
            divw r12,r6,r9                        #         r12 = current digit
            addi r4,r12,0x30                      #         print current digit
            print
            ori r11,r11,1                         #         r11 := 1 (have now printed a digit)
            mullw r4,r12,r9
            sub r6,r6,r4                          #         subtract the leading digit before next loop
        try_digit_compare:                        #     }
        divw r9,r9,r10                            #     r9 /= 10;
    cmpwi r9,0
    bne try_digit                                 # } while (r9 != 0);
    _end_print_word_to_dec:
    mtlr r0
blr

word_to_float:              # converts the word in r4 to a float in f4 with the same numerical value.
    # params:   r6 = word to convert
    #           f4 = destination register
    # locals:   r5 = base ptr
    #           f5 = math
    #           r12 = tmp storage
    # algorithm from http://mirror.informatimago.com/next/developer.apple.com/documentation/mac/PPCNumerics/PPCNumerics-157.html
    liw r14,0x80000000
    stw r14,0x74(r5)
    liw r14,0x43300000
    stw r14,0x70(r5)
    stw r14,0x60(r5)
    xoris r12,r6,0x8000
    stw r12,0x64(r5)
    lfd f4,0x60(r5)
    lfd f5,0x70(r5)
    fsub f4,f4,f5
blr

end:                  # Backfill 32-byte block in which r3 is found, with zeroes.
    # params:   r3 = current print ptr
    # locals:   r6 = math
    #           r4 = null
    #           r5 = placeholder for ctr
    #           r7 = return value
    liw r6,0x80001540
    sub r6,r6,r3
    srwi r6,r6,1            # r6 >>= 1; r6 is now the # of halfwords to write
    liw r7,0x80001520       # Get the return value (bytes written) by subtracting the starting address from the current address
    sub r7,r3,r7
    srwi r7,r7,1
    stb r7,8(r5)            # Store the return value
    li r4,0                 # r4 := 0
    mfctr r5
    mtctr r6                # for i = 1 to r6:
    _print_hw_zero:
        print
    bdnz _print_hw_zero     # end for
    mtctr r5
pop

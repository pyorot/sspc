# Gecko Guide

*(An intro to Gecko and how it's used in this project. Optional reading is in italics.)*

Gecko is an assembly-like language for working directly with memory and/or triggering custom ASM. The codes are interpreted by a "codehandler" (in an emulator or loader) that runs them at least once per frame by injecting them into standard system calls – *usually OSSleepThread on Nintendont, also often Vertical Blanking Interval (once per frame), etc*. This means they carry no state between runs, and will repeat their actions each time. The exception to this is the `CC` code and [Switch](#Switch) idiom.

## Codetypes
The syntax is pairs of 4B words, usually written in hex. The codetype is the first byte of the (8B) pair. These are used in this project. Docs [here](https://geckocodes.org/index.php?arsenal=1). 

### Read/Write
**00–05; 10–15 – Write literal**  
Write literal (= constant) directly to memory.

**80; 82; 84 – GR read/write**  
Set Gecko register (GR) to literal, or copy from/to it to/from memory. These are a set of 16 4B memory locations provided by Gecko.

### Navigation
**42; 4A – Set default address**  
Set base/pointer (default) addresses (BA/PA) to literal. Memory addresses in other codes are usually interpreted as offsets relative to these, so they can fit into the 8B codes. See [Address](#Address) and [Pointer](#Pointer) idioms.

### If
**20–3F – If literal**  
Compare memory to literal (=, ≠, <, >). There is no direct way to compare GRs to literals.

**CC – On/Off**  
Detect change in if result. Persists state, so use this for codes that toggle things – see [Switch](#Switch) idiom.

**DE – Assert pointer**  
Checks that a value in the pointer address (PA) is valid. Use for safety before dereferencing; see [Pointer](#Pointer) idiom.

**E0 – Infinite end-if**  
Ends all conditional statements.

**E2 – Finite end-if**  
Ends specified number of conditional statements. A single end-if can be applied directly from an if literal by adding 1 to the mem address (note that 1B if literal doesn't exist).

### ASM
**C0 – Execute ASM**  
Run ASM instructions within the Gecko code. This and `C2` need a separate guide!

**C2 – Inject ASM**  
Inject ASM into an existing function.

## Notes

### Data sizes
Most read/write commands require choosing data size, from 1B, 2B or 4B. *The intended size of a variable is usually visible in Ghidra.*

If statements allow comparison of 2B or 4B variables.
* 4B is simpler (no mask).
* 2B is more powerful because of the *mask* you can provide, which lets you easily compare 1B or go as far as isolating bits. A mask of `0000` preserves the whole variable; `FFFF` sets it to 0.

### Branching
The implementation of if statements (20–3F; DE) is unlike structured languages. Imagine a signal ("code execution") passing through the code, that gets disabled (possibly repeatedly) if the conditional evals to false. End-ifs can be applied to clear specific quantities of disablings (E2) or all of them (E0). The CC code is different – see [Switch](#Switch) idiom.

## Idioms

### Address
Base address is usually set to `80000000`, which makes all of GC mem accessible by adding the codetype (writing e.g. `04` as `04000000`) to the address (resulting in a range of e.g. `04000000` to `05200000`). A convenient way to access Wii memory is to find (or set) a variable to `90000000`, then load that variable's *address* to the pointer address. Then BA covers GC and PA covers Wii.

*Changing BA/PA to non-`x0000000` values to use offsets is a faff imo bc of the lost direct comparison with Dolphin Memory Engine among other things.*

### Pointer
Otoh, a situation where PA must be used is to access heap data that is at risk of moving. Find a static pointer to the containing object, then:
1. load it to PA (with `4A` code);
2. validate that it's a pointer (with `DE` code);
3. dereference it with offset (in any other code).

### Flag
The executable part of memory (typically at addresses ~`80004000` to ~`80400000` or ~`80500000`) is guaranteed to not change *and* has lots of spaces left by alignment of functions. I use this to store flags and Gecko registers to back-up data, because GRs can't be compared to literals.
* Set flags with 1B writes:  
`00004204 00000001`  
`00004205 00000001`
* Check flags with 2B ifs with masks:   `28004204 00FF0100`  
`28004204 FF000001` (rsp.)  
Note that the mask and literal are on opposite halves of the 2B variable!

### Copy
Directly copying from memory to memory is not possible (copying between memory and GRs is). To alleviate that, copy to a "volatile" GR, then copy from it elsewhere. Convention: volatile GRs will be the ones counting backwards from index `E`. *Don't use `F` bc it's a special char in various GR codetypes signalling not to use a GR at all!*

For more complicated or bulk copying, find the `memcpy` function in the game and call it with `C0` ASM execution.

### Switch
The key is that a `CC` code executes regardless of all if conditional disabling of execution. It toggles off/on if and only if it's hit by an enabled signal and was on the last run hit by a disabled signal. Key example: atomic button press.

The switch idiom looks like this:
```
[conditional]       # 1. If (I)
[true payload (T)]  # 2
cc000000 00000000   # 3. Switch (S)
[conditional]       # 4. (I) again
[false payload (F)] # 5
e0000000 00000000   # 6. ∞ end-if
```
Example of conditional – if d-pad right is pressed in Skyward Sword:
```
2859CF8C 00000002
```
I is true/false (+/-) and S is on/off (+/-).  
**Statically**, this happens:
```
I+ S+: runs T, then F
I- S+: doesn't run
I+ S-: runs T
I- S-: doesn't run
```
**Dynamically**, we have this loop:  
(initial state is I- S+)  
(`→` denotes changes, `~` no change, and `:` causality)
```
# I→+ S+: S→- : forces T
# I→- S-: S~  : persists above
# I→+ S-: S→+ : forces T, then F
# I→- S+: S~  : persists above
```
(I) is typically a button-press conditional, which is great because this means T or F will only execute while trigger buttons are pressed (and their results will remain when unpressed), so have no potential lag impact on gameplay. Likewise, the same condition toggles between applying T and F, so one button can toggle something.

The key downside is that F cannot be run separately, only T then F. Fine if F overwrites the same values as T, but otherwise note side-effects and things that should be reverted.

**Note**: (I) can be replaced with multiple lines, interpreted as logical conjunction, w/o any change in the idiom.

**Warning**: if using an end-if in (I) (by incrementing the mem address), the second instance of (I) *must not* end-if (put it back to the original mem address). *The F payload is conditional on the switch; end-if would make it accessible from outside.*

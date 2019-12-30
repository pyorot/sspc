---
layout: default
permalink: /ss/pc/user
---

# User Guide
These codes are for JP Skyward Sword (SOUJ01) and use the d-pad and Wii Remote + Nunchuk buttons.

| | | 
|-|-|
| → | Store
| ← | Reload
| Z + ← | BiT Reload
| ↑ | Cutscene Skip Toggle
| Z + ↑ | Contextual Toggle

There are two settings flags:

| | |
|-|-| 
| **0 (reload spawn)** | should stored spawn values be loaded during a reload (← press)?
| **1 (contextual)** | are the contextual cheats (Z + ↑ press) active?

File notation:

| | |
|-|-|
| **FA** | currently-loaded file (at 0x80955464)
| **FB** | BiT file (at 0x8095A824‬)
| **F1/2/3** | save files loaded to RAM (at 0x809BE200‬, 0x809C35C0‬, 0x809C8980 rsp.)
| **FC** | the "current" file, which is FA during gameplay and FB on the title screen.
| **FS** | the "selected" file, which is F1/2/3 depending on which was last selected (or started) on the title screen.

*Committables* refers to data that can be committed, which includes story/inventory/scene/temp flags + other unknown temporary data. *Spawn data* refers to area (e.g. "F000"), layer and entrance.

## Codes

### → : Store
Stores your current file and spawn data. This toggles flag 0:
* if it was disabled, the store takes place, the flag is enabled, and a green potion is shown.
* if it was enabled, no store takes place, the flag is disabled, and a purple potion is shown.

*Notes:*
* Double-press → if you want to do a store but leave flag 0 unchanged.

*Psuedocode:*  
```
if flag 1 is true:  
    unset flag 1  
    show "off" potion  
else:  
    copy file: FA → FS  
    copy spawn data: static data → cheat cache  
    set flag 1  
    show "on" potion  
```

### ← : Reload
Restores your stored file (see → press), restores respawn data if flag 0 is enabled, and triggers a reload. If no file has been stored, your started save file is restored.

*Notes:*
* Don't reload during a death continue screen; it'll fade to black and softlock.
* The file doesn't reload during title screen because then FC = FB (see code below).
* Reloading with flag 0 off will reload the current area from the entrance you came through. The layer may change if your story flags were changed and stored.
* Reloading with flag 0 on into a different area occasionally leads into a partially-loaded area and softlock (I gotta look into how loading works a bit more). Keep it off for safety.

*Psuedocode:*  
```
copy file: FS → FA  
copy committables: FC → static data  
if flag 0 is true: copy spawn data: cheat cache → static data   
trigger reload  
```

### Z + ← : BiT Reload
Loads BiT (Back in Time) into the default spawn.

*Notes:*
* Running this during gameplay causes Link to die immediately (because the current file is still FA, which just got blanked – see code), and no title screen appears; press reset first!

*Psuedocode:*  
```
set spawn data: (BiT defaults) → static data  
blank FA and FB  
copy committables: FC → static data  
initialise FB  
trigger reload  
```

### ↑ : Cutscene Skip Toggle
Enables/disables cutscene skips, showing a green/purple potion respectively. These skips retain changes in story/scene flags and Link/camera position as much as possible.

*Skipped Cutscenes:*  
Exiting sparring hall  
Sheikah stone dialogue  
Zelda loftwing dialogue  
Fledge adventure pouch  
Meeting Impa  
Meeting Gorko  
Machi  
Lopsa  
Bucha  

*Psuedocode:*  
```
alternate between:  
    splice cutscene graphs; show "on" potion  
    revert cutscene graphs; show "off" potion
```

### Z + ↑ : Contextual Toggle
Enables/disables context-dependent cheats, showing a green/purple potion respectively. Flag 1 is set to whether this is enabled.

**Scaldera:**  
Forces entrance to 1 while in ET boss room (B200)  
Pastes boss health over rupee count (on FA) while Scaldera is loaded.  

*Psuedocode:*  
```
alternate between:  
    set flag 1; show "on" potion  
    unset flag 1; show "off" potion  

if flag 1:  
    ### Scaldera ###  
    if static spawn area == "B200":  
        static spawn entrance = 1  
        rupee count = boss health  
```

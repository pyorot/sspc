---
layout: default
permalink: /ss/pc/user
---

# User Guide
**Version 1.1**. These codes are for JP Skyward Sword (SOUJ01) and use the d-pad and Wii Remote + Nunchuk buttons.

| | | 
|-|-|
| → | Store
| ← | Reload
| C + ← | Direct Reload
| B + ← | BiT Reload
| ↑ | Cutscene Skip Toggle
| Z + ↑ | Contextual Toggle

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
Stores your current file and spawn data, and position + angle if Link is loaded. Shows a blue potion.

*Notes:*
* Position + angle stores will fail if Link is not loaded (e.g. during a load). It's still fine to do indirect reloads (←) w/o valid position + angle.
* This isn't useful on the title screen cos it stores FA (the selected file), not FB (BiT file).

*Psuedocode:*  
```
if Link (actor) is loaded:
    copy position + angle: Link → FA  
copy file: FA → FS  
copy spawn data: static data → cheat cache  
show blue potion  
```

### ← : Reload | C + ← : Direct Reload
Restores your stored file and respawn data (see → press), then triggers a reload. If C is held, it's a *direct* load into the stored position + angle, else it's an *indirect* load through the entrance.

*Notes:*
* Don't reload during a death continue screen; it'll fade to black and softlock.
* If no store had been done, the reload will be blocked, but the current spawn data is now invalid and has to be fixed by using a loading zone before future stores/loads work.
* Reloading into a different area can lead into an unloaded area and softlock; a different map can lead to a crash (I gotta look into how loading works a bit more). Stay in the same area for safety.

*Psuedocode:*  
```
copy file: FS → FA  
copy committables: FC → static data  
copy spawn data: cheat cache → static data   
if spawn area is valid:  
    <if C + ←> set reload type = 1  
    trigger reload  
```

### B + ← : BiT Reload
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

| Skipped Cutscenes | |
| - | - |
| Horwell | Exiting sparring hall |
| Sheikah stone text | Zelda loftwing text |
| Adventure pouch | Fi: Leaving Skyloft |
| Fi: Whirlpool | Meeting Impa |
| Meeting Gorko | Meeting Machi |
| Machi | Lopsa |
| Oolo | Bucha |
| Fi: Viewing Platform | Cube Warp |
| Fi: Skyview Complete | Ghirahim Scaldera  

*Notes:*
* If a cutscene skip messes up your position/camera/stamina meter (or anything else), that's unintentional.

*Psuedocode:*  
```
alternate between:  
    splice cutscene graphs; show "on" potion  
    revert cutscene graphs; show "off" potion
```

### Z + ↑ : Contextual Toggle
Enables/disables context-dependent cheats, showing a green/purple potion respectively. Flag 1 (in the cheats) is set to whether this is enabled.

**Scaldera:**  
Forces entrance to 1 while in ET boss room (B200).  
Pastes boss health over rupee count (on FA) while Scaldera is loaded.  

**Sidehop CS Skip:**  
Forces save prompt when reloading into Skyloft (F000) on layer 3 (Wing Ceremony), allowing for practice like in [this video](https://www.youtube.com/watch?v=VayLxTLOOkY). Do a store on the save prompt/during Zelda's text/after a sidehop, then reload.

*Psuedocode:*  
```
alternate between:  
    set flag 1; show "on" potion  
    unset flag 1; show "off" potion  

if flag 1:  
    ### Scaldera ###  
    if static spawn has area "B200":  
        static spawn entrance = 1  
        rupee count on FA = boss health  
    ### Sidehop CS Skip ###  
    if static spawn has area "F000" and layer 3:  
        reloader.savePrompt = true  
```

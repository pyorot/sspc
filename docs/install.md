---
layout: default
permalink: /ss/pc/install
---

# Installation Guide

## Console

**GCT Files**  
The GCT file format for cheats is natively supported by many common Wii game loaders, like USB Loader GX, Gecko OS and Neogamma. This guide will use Gecko OS and USB Loader GX, depending on whether the game is loaded from disc or USB drive respectively.

**Homebrew + Firmware**  
All loaders run on a **homebrewed Wii**. I recommend using [this guide](https://wii.guide) for a fresh homebrew installation.

**Japanese Game Only**  
The practice codes require a **Japanese copy** of Skyward Sword (SOUJ01). All the aforementioned loaders allow loading from a USB or SD card, so you can source an ISO of the game to use with them (verify the file integrity by comparing hashes with [this database](https://www.gametdb.com/) in Dolphin).

**Leaderboard Legality**  
Cheats and loading from USB/SD are banned for speedruns on the leaderboard (because disc loads are slower than flash loads).

### Disc Loading
Here's an ez-pz method, using Gecko OS and an SD card. Ensure the SD card is formatted with FAT32.

**File Setup**  
Place 2 things on an SD card: **Gecko OS** and the **cheat GCT** file.  
*In the following, ◯ represents your SD card drive letter, usually E, F... for removable drives like SD and USB.*

- **Gecko OS**:
  - The final version (1.9.3.1) is available [here](/files/Gecko1931.zip).
  - This is a file archive (zip file) – open and extract it to `◯:/apps/`. Don't just copy the zip file to that folder and expect it to work!
- **Cheat GCT**:
  - Place this at `◯:/codes/SOUJ01.gct`; do not rename!

Sample layout on SD card once finished:
```
SD (E:)
├───apps
│   └───Gecko1931
│       ├───boot.elf
│       ├───icon.png
│       └───meta.xml
└───codes
    └───SOUJ01.gct
```

**Usage**  
Open Gecko OS from the Homebrew Channel.  
Verify the following settings in "Config Options" (and click "Save Config" to make changes):
- Load Debugger: NO
- SD File Patcher: NO
- SD Cheats: YES

Then click "Launch Game".

### USB Loading
Here's a D: method, using USB Loader GX and a USB drive. This has been tested with the drive formatted to FAT32 but may work with NTFS.

**File Setup**  
Place 3 things on a USB drive: **USB Loader GX**, the **cheat GCT** file, and the **game** (to be explained).  
*In the following, ◯ represents your USB drive letter, usually E, F... for removable drives like SD and USB.*

- **USB Loader GX**:
  - The latest version (3.0 r-something) is available [here](https://sourceforge.net/projects/usbloadergx/files/latest/download).
  - This is a file archive (zip file) – open and extract it to `◯:/` (the `apps` folder is provided in the archive). Don't just copy the zip file to that folder and expect it to work!
- **Cheat GCT**:
  - Place this at `◯:/codes/SOUJ01.gct`; do not rename!
- **Game**:
  - Source an ISO from the interwebs. Verify it in Dolphin (see the *Japanese Game Only* paragraph above). ISOs can also be ripped from a disc by other means.
  - Pick up and run a copy of [Wii Backup Manager](http://www.wiibackupmanager.co.uk/WiiBackupManager_Build78.html), to be used to copy the ISO to the USB drive in the correct format.
    - Files → Add → Files... → (select your ISO). Select the ISO (tick check-box).
    - Drive 1 → (select `Drive (◯:)` in the drop-down box initially showing "Inactive"). Agree to creating a WBFS folder on the USB drive, if prompted.
    - Files → Transfer → WBFS File... → (select `◯:/wbfs`). Wait for transfer to complete.

Sample layout on USB drive once finished. *The WBFS file is partitioned because FAT32 has a 4GB file limit.*
```
USB (D:)
├───disc.info
├───apps
│   └───usbloader_gx
│       ├───480p fix info.txt
│       ├───boot.dol
│       ├───boot_non480pfix.dol
│       ├───icon.png
│       └───meta.xml
├───codes
│   └───SOUJ01.gct
└───wbfs
    ├───disc.info
    └───The Legend of Zelda Skyward Sword [SOUJ01]
        ├───SOUJ01.wbfs
        └───SOUJ01.wbf1
```

**Usage**  
Start Homebrew Channel, remove SD card, then open USB Loader GX *(if it's started with an SD card inserted, it'll look for cheats on the SD card)*.

Verify: (Global) Settings → Loader Settings → Ocarina: ON.

Then start the game. If the above setting is on and there's no warning when starting the game, cheats have successfully loaded.

**Troubleshooting**  
If the game is detected but fails to start, switch the USB drive to the other port. The right port (when the Wii is standing) has better hardware/driver compatibility than the left.

## Dolphin

**Version Compatibility**  
These codes are compatible with Dolphin 5.0 and the development versions of 5.0 **excluding 5.0-8985 — 5.0-11177 (inclusive)**. These versions [break the 82 Gecko codetype](https://bugs.dolphin-emu.org/issues/11887) and so the Spawn Store code. The latest monthly builds are all good.

### Setup
The INI file has format:
```
[Gecko]
$sspc | context
2859cf8c 00002008
00004205 00000001
...
8410000e 80955ec2
e0000000 80008000
$sspc | cutscene
48000000 803d2144
2859cf8c 00000008
...
```
The $ line is the name of a code, and the block of pairs of hex numbers following it before the next $ is the body of that code. These can be entered into Dolphin together or individually:

**Together**  
Right-click the Skyward Sword JP ISO → Properties → Game Config
- [latest dev versions] → Editor → User Config
- [5.0 stable] → Edit Config

Paste the whole INI file at the top, replacing the `[Gecko]` section if it exists (a section is a `[xxxxx]` tag and whatever follows it until the next such tag). Then click Close \[dev\], or save and exit \[5.0 stable\].

**Individually**  
[latest dev versions only]. Right-click the Skyward Sword JP ISO → Properties → Gecko Codes. Use the menus to add/edit codes with custom names, taking care to paste only the body of a code (single block of pairs of hex numbers) in the "Code" textbox in the Cheat Code Editor.

### Usage
Right-click the Skyward Sword JP ISO → Properties → Gecko Codes, then just check/uncheck the codes you want to activate.

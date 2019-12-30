---
layout: default
permalink: /ss/pc/install
---

# Installation Guide

## Console

**GCT Files**  
The GCT file format for cheats is natively supported by many common loaders, like Nintendont, Neogamma, Gecko OS and Swiss. This guide will use Nintendont so it can fall back to the [SMS guide](https://gct.zint.ch/guide) for troubleshooting support.

**Homebrew + Firmware**  
All loaders run on a **homebrewed Wii**. I recommend using [this guide](https://wii.guide) for a fresh homebrew installation. I also recommend installing the **latest firmware** (4.3) because it includes USB 2.0 drivers that Nintendont likely requires for USB loading.

**Japanese Game Only**  
The practice codes require a **Japanese copy** of Skyward Sword (SOUJ01). All the aforementioned loaders allow loading from a USB or SD card, so you can source an ISO of the game to use with them (verify the file integrity by comparing hashes with [this database](https://www.gametdb.com/) in Dolphin).

**Leaderboard Legality**  
Cheats and loading from USB/SD are banned for speedruns on the leaderboard (because disc loads are slower than flash loads).

### File Setup
Place 3 things on an SD card or USB drive (or both): **Nintendont**, the **game ISO** file and the **cheat GCT** file. Skip the game ISO if you want to load the game from disc instead.

*In the following, ◯ represents your drive letter, usually E, F... for removable drives like SD and USB.*

- **Nintendont**:
  - The latest version is available [here](https://share.zint.ch/nintendont/latest/Nintendont.zip) (thanks to Psychonauter for maintaining). Don't use old versions for quality-of-life reasons; specifically anything before v5 as the codes may be too long for those versions.
  - This is a file archive (zip file) – open and extract it to `◯:/apps/Nintendont`. Do not just copy the zip file to that folder and expect it to work!
- **Game ISO**:
  - Place this at `◯:/games/SOUJ01.iso`; do not rename!
- **Cheat GCT**:
  - Place this at `◯:/codes/SOUJ01.gct`; do not rename!
  - If an ISO is being used, it must be on the same drive as the GCT – whether SD or USB. Nintendont itself can be on a different drive.

### Using Nintendont
Open Nintendont from the Homebrew Channel, then select:
- to load from disc/SD/USB (depending on where the game is);
- `Cheats: On` in settings.

Then start the game.

### Troubleshooting
Check the [SMS troubleshooting guide](https://gct.zint.ch/guide#3).

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

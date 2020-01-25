---
layout: default
permalink: /ss/pc/changelog
---

# Changelog

[**Previous versions here**](https://github.com/Pyorot/sspc/tree/master/release).

## **1.1** | 2020/01/25
Changes:
* **Spawn**:
  * **Removed auto reload**: All stores now just store instead of toggling reload mode, and a reload requires a previous store.
  * **Added direct reload**: press C + ← to reload directly into the saved co-ordinates (which are now updated during stores). Useful when loading zones are not used for ages, like in Faron and dungeons.
  * **BiT reload moved to B + ←**: to prevent accidental use during Sidehop CS Skip.

* **Cutscene Skips**: now skips all (long) cutscenes up to Skyview Spring (+ Ghirahim Scaldera).

* **\[New\] Context: Sidehop CS Skip**: when in layer 3 in Skyloft, a bit is forced that triggers a save-prompt during any reload, allowing [efficient practice of this trick](https://www.youtube.com/watch?v=VayLxTLOOkY).

Elaboration:
* On auto reload: *This was intended to obviate storing, since it would reload into the most-recent spawn, but it loaded the file from the last store regardless, which was prone to stale files and layer problems. Could just not reload files in auto-reload mode, but this isn't helpful since progression in an area wouldn't be reset. In auto-reload, entrances are implicitly stored when going through a loading zone. Files should be stored then as well, which is something for a future version.*

## **1.0** | 2019/12/25
Initial release:
* **Spawn**: store (→), reload (manual and auto modes; ←), BiT reload (Z + ←).
* **Cutscene Skips**: about [half of the cutscenes up to Skyview Spring](https://github.com/Pyorot/sspc/blob/c19c7212ed5ac55022530c4e72a085609cdbd616/docs/cs%20skips.txt) + Ghirahim Scaldera (↑).
* **Context: Scaldera**: fast entrance + health display on rupees (Z + ↑).

# Control-PC CNC12 customizations (re-apply after a CNC12 upgrade)

Several files on the Windows control PC look like stock CNC12 files but are **customized
for this machine and tracked in this repo**. A CNC12 **software upgrade can silently
overwrite them** with stock versions, reverting the customization with no warning.

**After any CNC12 upgrade:** restore the customizations below and verify (see "How to tell
it reverted"). For the large files, prefer **re-applying just the customization onto the
upgraded file** over copying the old repo file wholesale, so you keep the upgrade's other
content -- see each file's "Restore" note.

## Customized files

| File | What's customized | Commits | How to tell it reverted | Restore |
|------|-------------------|---------|-------------------------|---------|
| `language.msg` | Parameter-screen labels: **P860-P863** (gear shift) and **P700** (ATC tool number handed to the PLC by mfunc6). Everything else is the stock baseline. | `dfab98c` (P860-863 + baseline), this branch (P700) | P860-P863 read "Not Used"; P700 reads "Reserved for Enduser/Integrator...". | **Re-apply both label sets onto the upgraded file** (don't overwrite it wholesale). See "language.msg" below. |
| `plcmsg.txt` | This machine's **PLC operator messages** (ATC / spindle / turret / carousel). | `e1ab3c5` (add), `4c329ee` (feed-hold interlock msgs), `96ccf68` (ATC timeout), this branch (ATC BIN OUT OF RANGE) | Custom ATC/spindle faults show blank or a stock string. | Re-merge the custom messages into the upgraded `plcmsg.txt` (diff against stock). |
| `system/MPGmacro4.mac` | Wireless MPG Aux Key 4 = **ATC Reset** (one line: `M20`). CNC12 ships a demo file here that only pops an example `M225` message. | this branch | Pressing MPG macro 4 shows "This is an example macro run from the Macro4 button..." instead of resetting the ATC. | Copy from the repo. Code must stay between `N100` and `N1000`, with no `M225` line. |
| `cncm.hom` | Full custom homing program (home order + HomeSync latch). | `b90529c` | Homing order wrong / machine-coord DRO latch gone. | Fully custom -- copy `cncm.hom` from the repo verbatim. |

Also machine-specific and tracked (part of a full re-deploy, less likely clobbered by a CNC12
upgrade): `Centroid-Acroloc-ALLIN1DC.src` + `mfunc*.mac`, the retro VCP under
`resources/vcp/`, and `resources/colors/`.

## Details

### `language.msg` -- parameter/UI labels (the general capability)

- ~97k lines, **UTF-8** (contains other-language unicode) with **LF** endings.
- Each parameter N has `@P<N>_LABEL` (short, in the list) and `@P<N>_LABEL_L` (long
  description); edit the `eng:` line. Other-language slots can stay as-is (machine runs
  English). **Any CNC12 parameter or UI label can be renamed this way.**
- **Two customizations here** (everything else is the stock baseline):
  - **P860-P863** (gear shift, commit `dfab98c`) -- CNC12 shows the 860-870 block as "Not
    Used", so these were named: `Gear Crossover RPM`, `Gear Crossover Hysteresis`,
    `Gear Shift Coast Dwell ms`, `High Gear Ratio`.
  - **P700** (enhanced ATC) -- `ATC: tool number of the last M6 (mfunc6 G10)`; the value is
    written by `mfunc6.mac` (`G10 P700 R[#4120]`) and read by the PLC for the VCP `TOOL`
    readout. Never edit the value by hand.
- **Restore after upgrade:** keep the upgraded `language.msg` and re-apply both label sets.
  The exact before/after is in `git show dfab98c -- language.msg` and in this repo's copy;
  target the `eng:` line for each `@P<n>_LABEL` / `_L` and preserve UTF-8 + LF.

### `plcmsg.txt` -- PLC operator messages

- Small (~94 lines). Format: `<msgNumber> <value> <text>` where the `.src` references each as
  a constant `value = number + 256*file` (e.g. `ATC_Lock_Released_C IS 45546 ;(2+256*174)`).
- Machine-relevant custom messages include:
  - **60-68:** LOW AIR, ATC WHILE MANUAL INDEX, MANUAL INDEX WHILE ATC, **CAROUSEL MOVE TIME
    OUT** (63), tool clamp/orient faults, **ATC BIN OUT OF RANGE** (67), **CAROUSEL MOVED BY
    HAND** (68).
  - **70-73:** spindle chiller, pot up/down, arm motor, POT NOT UP FOR CAROUSEL.
  - **101-110:** tool-change / turret / collet / spindle-lock faults.
  - **171-176:** Tool Carousel manual unlock, **Spindle not parked. Z Axis not at zero.**,
    Tool Carousel not locked, Tool Carousel locked (used by the ATC lock + spindle-park
    logic), **CAROUSEL MOVED - PRESS ATC RESET** (175) and **ATC POSITION RE-ESTABLISHED**
    (176) — the hand-moved-carousel interlock's status pair.
- **Restore after upgrade:** diff the upgraded `plcmsg.txt` against this repo's copy and
  re-add the machine's messages (the numbers above). Any custom message referenced by a
  `.src` constant that goes missing will display blank.

### `cncm.hom` -- homing program

Fully custom, 14 lines. Home order **Z+ (clear the head), X-, Y+**, then it pulses
`HomeSync_SV` (`M94 /6`, `SV_M94_M95_6`) so the PLC latches the encoder counts at machine
zero -- the VCP machine-coordinate readout measures from that latch. Copy verbatim from the
repo after an upgrade.

### Tool Library: the dummy reset tool (not a file, but lost with the library)

**Tools 199 and 200** must both be assigned the **same** bin in the Tool Library,
with H and D offsets set to **0**. They are never cut with: the VCP **ATC RESET**
button and wireless MPG macro button 4 both run `M20`, which changes to whichever
of the two CNC12 does not believe is loaded. That is the only reliable way to
clear a hand-moved carousel (CNC12 skips an M6 for the tool it believes is
loaded), and two dummies are needed because after one reset the loaded tool is
the dummy itself.
Re-create it after any tool-library restore, and export the library (F5 Export
Lib) so it can be restored.

### Machine parameters for the ATC (not a file, but reset by a re-install)

The tool changer runs CNC12's **non-random enhanced ATC**. These must be set on the
Machine Parameters screen (F1 Setup > F3 Config > F3 Parms); a CNC12 re-install or a
parameter-file restore from an old backup reverts them:

| Param | Value | Why |
|---|---|---|
| P6 | 1 | ATC installed; on-screen tool updates after M6 |
| P160 | 1 | non-random enhanced ATC: M107 sends the bin, Tool Library Bin column editable |
| P161 | 12 | number of carousel bins; the PLC's M6 bin guard limit. **Reboot after changing** |
| P164 | 1 | F2 ATC Reset key in the Tool Library |

The tool->bin map itself lives in the **Tool Library Bin column** (F1 Setup > F2 Tool >
F2 Tool Lib), saved by CNC12 in its tool library file, and is not tracked in this repo.
Export it (F5 Export Lib) after changes so it can be restored.

## After-upgrade checklist

- [ ] `language.msg`: re-apply the P860-P863 and P700 label edits onto the upgraded file.
- [ ] `plcmsg.txt`: re-merge the custom ATC/spindle messages (60-68, 70-73, 101-110, 171-176).
- [ ] `cncm.hom`: copy verbatim from the repo.
- [ ] `system/MPGmacro4.mac`: copy from the repo (a CNC12 upgrade restores the demo macro).
- [ ] Restart CNC12.
- [ ] Parameters screen: P860-P863 show the gear-shift labels, P700 the ATC tool label; P6 = 1, P160 = 1, P161 = 12, P164 = 1.
- [ ] Tool Library: Bin column editable and matches the carousel (re-import the exported library if not); tools 199 and 200 share a bin and have zero H/D offsets.
- [ ] Trigger/confirm a custom ATC message displays (e.g. a carousel timeout).
- [ ] Home the machine; confirm the machine-coordinate DRO latch works.
- [ ] Re-copy `resources/vcp/` if the VCP theme reverted.

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
| `language.msg` | Parameter-screen labels: **P860-P863** (gear shift) and **P701-P712** (ATC tool->bin map). Everything else is the stock baseline. | `dfab98c` (P860-863 + baseline), `75c2acb` (P701-712) | P701-P712 read "Reserved for Enduser/Integrator..." again; P860-P863 read "Not Used". | **Re-apply both label sets onto the upgraded file** (don't overwrite it wholesale). See "language.msg" below. |
| `plcmsg.txt` | This machine's **PLC operator messages** (ATC / spindle / turret / carousel). | `e1ab3c5` (add), `4c329ee` (feed-hold interlock msgs), `96ccf68` (ATC timeout) | Custom ATC/spindle faults show blank or a stock string. | Re-merge the custom messages into the upgraded `plcmsg.txt` (diff against stock). |
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
  - **P701-P712** (ATC tool->bin map, commit `75c2acb`) -- relabeled from the generic
    "Reserved for Enduser/Integrator..." to `"ATC bin <n> - tool number loaded in this
    carousel bin"` + the long map description (24 lines: `@P70n_LABEL` and `@P70n_LABEL_L`).
- **Restore after upgrade:** keep the upgraded `language.msg` and re-apply **both** label sets.
  The exact before/after is in `git show 75c2acb -- language.msg` and
  `git show dfab98c -- language.msg`; target the `eng:` line for each `@P<n>_LABEL` / `_L` and
  preserve UTF-8 + LF.

### `plcmsg.txt` -- PLC operator messages

- Small (~94 lines). Format: `<msgNumber> <value> <text>` where the `.src` references each as
  a constant `value = number + 256*file` (e.g. `ATC_Lock_Released_C IS 45546 ;(2+256*174)`).
- Machine-relevant custom messages include:
  - **60-66:** LOW AIR, ATC WHILE MANUAL INDEX, MANUAL INDEX WHILE ATC, **CAROUSEL MOVE TIME
    OUT** (63), tool clamp/orient faults.
  - **70-73:** spindle chiller, pot up/down, arm motor, POT NOT UP FOR CAROUSEL.
  - **101-110:** tool-change / turret / collet / spindle-lock faults.
  - **171-174:** Tool Carousel manual unlock, **Spindle not parked. Z Axis not at zero.**,
    Tool Carousel not locked, Tool Carousel locked. (Used by the ATC lock + spindle-park logic.)
- **Restore after upgrade:** diff the upgraded `plcmsg.txt` against this repo's copy and
  re-add the machine's messages (the numbers above). Any custom message referenced by a
  `.src` constant that goes missing will display blank.

### `cncm.hom` -- homing program

Fully custom, 14 lines. Home order **Z+ (clear the head), X-, Y+**, then it pulses
`HomeSync_SV` (`M94 /6`, `SV_M94_M95_6`) so the PLC latches the encoder counts at machine
zero -- the VCP machine-coordinate readout measures from that latch. Copy verbatim from the
repo after an upgrade.

## After-upgrade checklist

- [ ] `language.msg`: re-apply the P701-P712 label edits onto the upgraded file.
- [ ] `plcmsg.txt`: re-merge the custom ATC/spindle messages (60-66, 70-73, 101-110, 171-174).
- [ ] `cncm.hom`: copy verbatim from the repo.
- [ ] Restart CNC12.
- [ ] Parameters screen: P701-P712 show the ATC bin labels (not "Reserved...").
- [ ] Trigger/confirm a custom ATC message displays (e.g. a carousel timeout).
- [ ] Home the machine; confirm the machine-coordinate DRO latch works.
- [ ] Re-copy `resources/vcp/` if the VCP theme reverted.

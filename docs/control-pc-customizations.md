# Control-PC CNC12 customizations (re-apply after a CNC12 upgrade)

Several files on the Windows control PC look like stock CNC12 files but are **customized
for this machine and tracked in this repo**. A CNC12 **software upgrade can silently
overwrite them** with stock versions, reverting the customization with no warning.

**After any CNC12 upgrade:** re-copy the files below from this repo to the CNC12 directory,
restart CNC12, and verify (see "How to tell it reverted").

## Customized files

| File | What's customized | How to tell it reverted | Restore |
|------|-------------------|-------------------------|---------|
| `language.msg` | CNC12 UI strings, incl. **parameter-screen labels**. **P701-P712** relabeled to the ATC tool->bin map (from the generic "Reserved for Enduser/Integrator..."). Labels are `@P<n>_LABEL` (short) + `@P<n>_LABEL_L` (long); edit the `eng:` line. | The P701-P712 parameter descriptions read "Reserved for Enduser/Integrator custom PLC and Macro use" again. | Copy `language.msg` to the CNC12 dir; restart CNC12. |
| `plcmsg.txt` | Custom **PLC operator messages** (ATC/carousel/spindle: `CAROUSEL MOVE TIME OUT`, `Spindle not parked`, `Tool Carousel manual unlock`, `Tool Carousel not locked`, ...). Keyed by message number; the `.src` references them as `value = number + 256*file`. | Custom ATC/spindle faults show blank or a stock string. | Copy `plcmsg.txt` to the CNC12 dir. |
| `cncm.hom` | Custom homing program (HomeSync latch for the machine-coordinate DRO). | Homing behaves stock / the machine-coord latch is gone. | Copy `cncm.hom` to the CNC12 dir. |

Also machine-specific and tracked (less likely to be clobbered by a CNC12 upgrade, but part
of a full re-deploy): `Centroid-Acroloc-ALLIN1DC.src` + `mfunc*.mac` (compiled/installed via
CNC12), the retro VCP under `resources/vcp/`, and `resources/colors/`.

## Editing `language.msg` (how the parameter relabeling was done)

- ~97k lines, **UTF-8** (contains other-language unicode) with **LF** endings. Edit only the
  exact `eng:` lines; preserve encoding and line endings.
- Each parameter N has two entries: `@P<N>_LABEL` (short, shown in the list) and
  `@P<N>_LABEL_L` (long description). Other-language slots can stay as-is (machine runs
  English).
- This is a general capability: **any CNC12 parameter or UI label can be renamed** by editing
  its `@..._LABEL` entry in `language.msg`.

## After-upgrade checklist

- [ ] Re-copy `language.msg`, `plcmsg.txt`, `cncm.hom` from this repo to the CNC12 directory.
- [ ] Restart CNC12.
- [ ] Parameters screen: P701-P712 show the ATC bin labels (not "Reserved...").
- [ ] Trigger/confirm a custom ATC message still displays (e.g. a carousel timeout).
- [ ] Home the machine; confirm the machine-coordinate DRO latch works.
- [ ] Re-copy `resources/vcp/` if the VCP theme reverted.

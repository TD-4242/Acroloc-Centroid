# Troubleshooting and edit workflow

Why the VCP will not load, the SVG rules that trip people up, the field-validated facts to keep
in mind, and how to verify an edit -- including without the machine.

## Edit workflow / discipline

- **Back up the skin `.vcp` before editing** (copy to `*_backup.vcp`), so reverting is trivial.
- **Change one thing at a time.** Compound edits make failures hard to isolate.
- **Restart CNC12 to reload** an edited skin or button. Edits are not hot-reloaded.
- **A button used by multiple skins** must be edited and re-checked in every skin that
  references it (this repo has `servo_mill_vcp_skin.vcp` and `servo_mill_vcp_rapid_skin.vcp`).

## Field-validated facts

From on-machine work; consistent with (and explaining) the manual's SVG advice:

1. **The renderer effectively ignores SVG `text-anchor`.** Position button text with an explicit
   `x`. *Why:* the VCP wants fonts converted to paths, so live text-anchor centering is not
   honored -- convert fonts to paths ("Object to Path") and place text by coordinate.
2. **Rendered graphic size tracks the SVG `width`/`height`/artboard.** *Why:* removing them
   shrinks the button; the manual's "copy an existing button SVG so the artboard is correct" is
   the same rule. Grid `row_span`/`column_span` scale the cell, but the SVG artboard must match.
3. **CNC12 must be restarted to reload** a skin/button change. *Why:* the VCP reads the files at
   startup.
4. **Back up the skin before editing.** *Why:* a single typo can stop the VCP from starting;
   reverting to the backup is the fastest recovery.
5. **Edits to a shared button apply to every skin.** *Why:* skins reference the same button
   folder; a change is not isolated to one skin.

## VCP will not start after an edit

Common causes (the error dialog usually names the offending button):

- Typo in an SVG filename, or the SVG is missing / in the wrong folder.
- Incompatible SVG (embedded bitmap image, or an unconverted font).
- Missing button XML file.
- Typo in the button XML or the skin XML.

A **missing button XML** is special: the graphic still shows, but the button does nothing
(the file that described its behavior is gone).

## VCP does not appear at all

- Bad skin name or path in `options.xml`, or the skin file is not where `options.xml` expects.
- A typo in the skin XML.
- The required Windows .NET framework is not installed.
- Windows is in Tablet mode (set Desktop mode).
- Windows Region is not set to United States.
- **Skewed or chopped off:** set the Windows display resolution to 1920x1080.
- **Missing lower third after a CNC12 upgrade:** a cross-version `restore report` issue -- restore
  report only works within the same CNC12 version.

## Good SVG practice

- Vectors only -- no embedded bitmaps, no live fonts. Convert bitmaps to vector first.
- **Convert all fonts to paths** ("Object to Path" in Inkscape / "create outlines" in
  Illustrator) before saving.
- Every element must have a color assigned (uncolored elements can default to invisible/white).
- Keep all art inside the artboard.
- Delete unused/hidden layers and empty (no-color, no-thickness) elements.
- If a graphic misbehaves, ungroup everything -- convoluted nested groups are a common cause.

## Verifying an edit

**Without the machine:** the "Offline Mill and Lathe Intercon" installer (CNC12 v5.04+) runs the
VCP without a control board, using the same `...\resources\vcp` layout -- good for graphics-only
checks. It cannot exercise real function/PLC behavior.

Static checks you can run against this repo before loading:

- The name in each skin `<button>` line matches a folder under `resources/vcp/Buttons/`.
- Every SVG referenced by a button XML exists in that button's folder.
- The XML is well-formed.
- Files are ASCII (this repo's controller/source convention).

Only the control PC (or the offline Intercon for graphics) confirms the button actually works.

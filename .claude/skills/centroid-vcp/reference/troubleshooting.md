# Troubleshooting and edit workflow

Why the VCP will not load, the SVG rules that trip people up, the field-validated facts to keep
in mind, and how to verify an edit -- including without the machine.

## The renderer is Svg2Xaml -- and it fails silently

The VCP renders SVGs by converting them to WPF XAML with the **Svg2Xaml** library (its assembly
doc ships inside a CNC12 report `.zip`, which is how this was confirmed). It supports only a
subset of SVG, and an unsupported feature does **not** produce an error dialog: the whole VCP
simply never appears -- CNC12 runs fine, `VirtualControlPanel.exe` starts and exits with no
message. All of the following were established by on-machine bisection (2026-07, retro skin
work):

**Crashes the VCP (silent):**

- `<filter>` and filter primitives (`feGaussianBlur`, `feMerge`, ...). Fake glows with layered
  semi-transparent shapes instead.
- Gradients with percentage / objectBoundingBox coordinates. Every `linearGradient` /
  `radialGradient` must use `gradientUnits="userSpaceOnUse"` with absolute coordinates, and no
  `%` anywhere in the gradient element.

**Renders wrong (no crash):**

- Transform *lists* -- `transform="translate(...) scale(...)"` is not applied, so the shapes
  pile up at the origin. Only a **single `matrix(...)` transform** is proven safe; better still,
  bake scale/translate into the path coordinates.
- `text-anchor` is ignored -- see the text section below.
- An SVG `font-family` that is not installed silently substitutes another font, shifting text.

**Debugging technique when the VCP will not appear:** binary-search with throwaway minimal
skins. Make copies of the skin each containing one suspect feature (one gradient style, one
filter, one transform form ...), point `options.xml` at each in turn, restart CNC12, and see
which one kills it. Tedious but definitive, and the only method that works against a silent
crash. Delete the test skins when done.

## Text and fonts

- **`text-anchor` is ignored** -- there is no live centering. Either convert text to paths
  ("Object to Path"), or keep live `<text>` but compute the left-edge `x` yourself from a
  character-advance-width table for the exact font (Arial Bold AFM widths worked; see
  `tools/vcpgen.py` `CHAR_W`). Live text is fine once positioned explicitly.
- **Only use fonts installed on the control PC.** A missing font substitutes silently and your
  computed widths are then wrong (symptom: text sits off-center, typically to the right). Plain
  Arial is safe; Arial Narrow was not present on this control PC.
- Custom fonts (e.g. DSEG7 Classic for 7-segment digits) work in skin `<plc_word>`/`<text>`
  elements but must be installed **for all users** on the Windows control PC ("Install for all
  users"), or CNC12 (which may run under a different account/elevation) will not see them.

## CNC12 rewrites the skin file

Opening the **VCP options** screen in CNC12 and saving re-serializes the active skin `.vcp` --
hand-written formatting, comments, and even values (observed: the `<background>` color reset to
`#a6a5a5`) can be clobbered. Treat the on-control-PC skin as disposable: keep the source of
truth in the repo (ideally generated), diff after touching VCP options, and re-copy.

## Windows file conventions

CNC12 runs on Windows: every file it consumes under `resources/vcp/` (`.vcp`, button `.xml`,
`.svg`, `options.xml`) should be **ASCII-only with CRLF line endings**. Enforce this in
generators/tests rather than hoping editors cooperate.

## Edit workflow / discipline

- **Back up the skin `.vcp` before editing** (copy to `*_backup.vcp`), so reverting is trivial.
- **Change one thing at a time.** Compound edits make failures hard to isolate.
- **Restart CNC12 to reload** an edited skin or button. Edits are not hot-reloaded.
- **A button used by multiple skins** must be edited and re-checked in every skin that
  references it (this repo has the generated `acroloc_retro_vcp_skin.vcp` plus the stock
  `servo_mill_vcp_skin.vcp` / `servo_mill_vcp_rapid_skin.vcp`; the retro skin uses its own
  `retro_*` button folders, so its edits do not leak into the stock skins).
- **Generated skin:** the retro skin and every `retro_*` button are emitted by
  `tools/vcpgen.py` -- edit the generator and re-run it (tests: `tools/test_vcpgen.py`), never
  the emitted files.

## Field-validated facts

From on-machine work; consistent with (and explaining) the manual's SVG advice:

1. **The renderer effectively ignores SVG `text-anchor`.** Position button text with an explicit
   `x` -- convert fonts to paths, or compute the `x` from real font metrics (see "Text and
   fonts" above).
2. **Rendered graphic size tracks the SVG `width`/`height`/artboard.** *Why:* the graphic is
   drawn at its declared size, not stretched to the cell. Grid `row_span`/`column_span` enlarge
   the *cell*, but the SVG artboard must be sized for the span (sizing numbers in
   [button-anatomy.md](button-anatomy.md)).
3. **The renderer supports only a subset of SVG, and unsupported features crash silently** --
   see "The renderer is Svg2Xaml" above. No filters; userSpaceOnUse gradients only; single
   `matrix()` transforms only.
4. **CNC12 must be restarted to reload** a skin/button change. *Why:* the VCP reads the files at
   startup.
5. **Back up the skin before editing.** *Why:* a single typo can stop the VCP from starting;
   reverting to the backup is the fastest recovery. Also note CNC12's VCP options screen
   rewrites the skin on save (see above).
6. **Edits to a shared button apply to every skin.** *Why:* skins reference the same button
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
- An SVG using an unsupported Svg2Xaml feature (filters, percentage-coordinate gradients) --
  silent, no dialog; see the Svg2Xaml section above and bisect with minimal skins.
- The required Windows .NET framework is not installed.
- Windows is in Tablet mode (set Desktop mode).
- Windows Region is not set to United States.
- **Skewed or chopped off:** set the Windows display resolution to 1920x1080.
- **Missing lower third after a CNC12 upgrade:** a cross-version `restore report` issue -- restore
  report only works within the same CNC12 version.

## Good SVG practice

- Stay inside the Svg2Xaml safe subset (top of this file): no filters, absolute userSpaceOnUse
  gradients, single `matrix()` transforms or baked coordinates, explicit text `x`.
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

# Centroid VCP Authoring Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a machine-agnostic `centroid-vcp` knowledge-base skill that lets Claude
confidently customize a Centroid CNC12 Virtual Control Panel (skin layout, buttons, graphics,
visual states, actions, and advanced displays).

**Architecture:** A `SKILL.md` (orientation + at-a-glance tables + task-playbook index) plus six
topical `reference/*.md` deep-dives, mirroring the existing `acroloc-s10` and
`centroid-plc-programming` skills. All content is grounded in the CNC12 VCP 2.0 Users Manual
and the in-repo `resources/vcp/` tree. One cross-link is added to `acroloc-s10/SKILL.md`.

**Tech Stack:** Markdown docs only. No code, no build, no PLC/macro/source changes. Verified
with shell checks (grep for required tokens, cross-link existence, ASCII-only, referenced-file
existence).

**Design spec:** `docs/superpowers/specs/2026-07-13-centroid-vcp-skill-design.md`

## Global Constraints

- **ASCII-only** in every `.md` (7-bit; no smart quotes, em dashes, or non-ASCII). Consistent
  with the repo's other skill docs. Verify each file with:
  `LC_ALL=C grep -nP "[^\x00-\x7F]" <file>` -> must print nothing.
- **Machine-agnostic:** no Acroloc-specific config (skin name we run, our custom-button list,
  our PLC-bit assignments) lives in this skill. In-repo buttons may be used only as *generic
  worked examples*. Machine specifics stay in `acroloc-s10`.
- **Cite the manual by section title, not page number** (page numbers rot across revisions).
- **Every XML/SVG snippet** either matches a real file under `resources/vcp/` or is explicitly
  labeled a generic template.
- **Follow the sibling skill house style:** open `SKILL.md` with a `## When to use / when not`
  block; keep reference files self-contained; use relative markdown links between files.
- **Commits:** this repo commits only when the user asks. Author all files first; the single
  commit is the final task and is performed only on the user's go-ahead (do not push unasked).
- **The only file changed outside `.claude/skills/centroid-vcp/`** is `acroloc-s10/SKILL.md`
  (one cross-link entry).

### Reference facts (verified against the manual + real files; use verbatim)

Button XML nodes (child of `<vcp_button>`):
- `<skin_event_num>N</skin_event_num>` -- binds the button to CNC12 function/PLC logic N; in the
  PLC this is `SV_SKIN_EVENT_N`. Max 255 skin events. Example real values (from
  `resources/vcp/Buttons/*/*.xml`): flood_coolant=22, coolant_pump=23, single_block=47,
  reset=56. Aux-key skin events (run a macro): 3,4,5,8,9,10,13,14,15,18,19,20,24,25,68,69.
- `<plc_output>` with `<number>N</number>` = PLC output/mem read-back that drives the LED.
  Either LED colors `<color_on>#RRGGBB</color_on>`/`<color_off>#RRGGBB</color_off>`, OR image
  swap `<image_on>on.svg</image_on>`/`<image_off>off.svg</image_off>` (swap on function
  activated). Deleting the whole `<plc_output>` block removes the LED.
- `<plc_input>` with `<number>`, `<image_on>`, `<image_off>` = button acts as an indicator that
  swaps image on the state of a PLC input (manual's Probe indicator example, input #7).
- `<plc_memory>` with `<number>`, `<image_on>`, `<image_off>` = same, driven by a MEM location.
- `<on_click_swap>swap.svg</on_click_swap>` = show a different image only while pressed/clicked.
- `<run><line>G0 X0 Y0</line></run>` = run one G-code line directly (CNC12 v5.08+).
  `<run><macro>C:\cncm\ncfiles\myMacro.cnc</macro></run>` = run a macro file directly. Never mix
  `<line>` and `<macro>` in one `<run>` (only the macro runs / second line ignored).
- `<app>C:\cncm\SomeApp.exe</app>` = launch an external application.
- `<switch>` with `<switch_on>`/`<switch_off>` each containing `<remove>group</remove>`,
  `<add>group</add>`, and `<image_on>`/`<image_off>` = group show/hide + image swap on press.
- `group="name"` attribute on the `<button ...>` line adds the button to a switch group.

Skin `.vcp` nodes (child of `<vcp_skin>`):
- `<button row="R" column="C">name</button>` places button folder `name` on the grid. Optional
  attributes: `row_span`, `column_span` (BIG multi-cell buttons), `group`.
- `<column_count>N</column_count>` / `<row_count>N</row_count>` set grid size (CNC12 v5.40+;
  default 6 x 14 on the stock mill). More cells => proportionally smaller buttons.
- `<background>#RRGGBB</background>` sets VCP bg color (default grey #A6A5A0); or a path line
  `<background>C:\cncm\resources\vcp\images\stainless-steel.jpg</background>` for an image bg.
- `<border>` block: `<column_span>`, `<column_start>`, `<row_span>`, `<row_start>`,
  `<fill>#RRGGBB|Transparent</fill>`, `<outline_color>`, `<outline_thickness>`. Draws
  group boxes / solid fills. May contain `<plc_word>`, `<text>`, `<group>`.
- `<image>` block: `<column_span>`, `<column_start>`, `<row_span>`, `<row_start>`,
  `<path>...svg</path>` for a static logo/icon overlay (may contain `<group>`).
- `<text>` block (inside a border): `<content>` (use `&#13;` for a newline), `<fontsize>`,
  `<color>`, `<font>`, `<horizontalalignment>`, `<verticalalignment>`.
- `<plc_word>` (inside a border or vcp_button): `<number>` (W-word, from the PLC's Word
  Definitions), `<type>Int|Float|Double|DoubleFloat</type>` (default Int), `<significant>N`
  (decimals, non-Int, default 2), `<color>` (default #000000), `<fontsize>` (default 16),
  `<font>` (default Segoe UI), `<fontstyle>normal|bold|italic|oblique</fontstyle>`,
  `<verticalalignment>top|center|bottom</verticalalignment>` (default bottom),
  `<horizontalalignment>left|right|center</horizontalalignment>` (default left),
  `<marginbottom|margintop|marginleft|marginright>N</...>`, `<percentage>true</percentage>`.
  Common stock words: W19 SpinOverride %, W31 FinalFeedOverride %, W7 TargetVoltage %,
  W54 CurrentCarouselPosition, W52 CurrentTurretPosition.
- `<on_hover>` / `<on_click>`: `<opacity>N</opacity>` + `<outline_color>#RRGGBB|Transparent`.
  Default hover = white outline; default click = black outline.
- `<hide_group>`/`<hideGroup>` with one or more `<group>name</group>` = hide groups at startup.
- Performance note: degradation starts ~1000 objects.

options.xml: the active skin is the `Skin` `VcpOption` `<Value>` (e.g. `acorn_mill_vcp_skin`).

Field-validated facts (from last session's on-machine work; the manual's SVG advice explains
them -- present them as elaborations, not contradictions):
- The renderer effectively ignores SVG `text-anchor`; position button text with an explicit `x`.
  Root practice from the manual: convert all fonts to paths ("Object to Path" in Inkscape)
  before saving a button SVG.
- Rendered button graphic size tracks the SVG `width`/`height`/artboard; the manual's advice to
  "open the existing button .svg, rename it, and modify it (so the size/artboard is correct)"
  is the same rule. Grid `row_span`/`column_span` scale the cell; the SVG artboard must match.
- CNC12 must be restarted to reload an edited skin/button.
- Back up the skin `.vcp` before editing (manual's own advice).
- A button used by more than one skin must be edited/rechecked in each skin.

Verification aids from the manual (put in troubleshooting.md):
- Offline testing: the "Offline Mill and Lathe Intercon" installer runs the VCP without a
  control board, using the same `...\resources\vcp` layout -- good for graphics-only checks.
- VCP-won't-start causes: SVG filename typo / missing SVG / incompatible SVG (embedded
  bitmap or unconverted font) / missing button XML / typo in button or skin XML. Error dialog
  names the button. Missing button XML => graphic shows but function dead.
- VCP absent / no message: bad skin name or path in options.xml; skin XML typo; .NET missing;
  Windows Tablet mode; Windows Region not USA. Skewed/chopped => set display to 1920x1080.

---

## Task 1: reference/skin-and-grid.md (the layout layer)

**Files:**
- Create: `.claude/skills/centroid-vcp/reference/skin-and-grid.md`
- Read to ground: `resources/vcp/options.xml`,
  `resources/vcp/skins/servo_mill_vcp_skin.vcp`,
  `resources/vcp/skins/servo_mill_vcp_rapid_skin.vcp`

**Interfaces:**
- Produces: the file that `SKILL.md` (Task 7) links to for "skins, the grid, move/delete a
  button." Anchors other files reference: this file owns `<button>` placement, `column_count`/
  `row_count`, and `options.xml` skin selection.

- [ ] **Step 1: Read the real skin + options files**

Run: `sed -n '1,40p' resources/vcp/skins/servo_mill_vcp_skin.vcp; cat resources/vcp/options.xml`
Confirm the actual `<button>` lines, any `<border>`/`<image>` blocks, and the `Skin` Value.

- [ ] **Step 2: Write the file** with these sections (ASCII-only):

1. **The two-layer model (short recap + link):** the skin `.vcp` places named buttons on a
   grid; each button is a folder (link to `button-anatomy.md`).
2. **Where skins live and how one is selected:** `resources/vcp/skins/*.vcp`; `options.xml`
   `Skin` VcpOption `<Value>` picks the active skin (no extension). Note this repo ships two
   skins (`servo_mill_vcp_skin.vcp`, `servo_mill_vcp_rapid_skin.vcp`).
3. **The grid:** rows x columns (stock mill 6 columns x 14 rows), `<button row="R"
   column="C">name</button>` maps a button folder to a cell. `<column_count>`/`<row_count>`
   (CNC12 v5.40+) resize the grid; more cells = smaller buttons.
4. **Move a button:** change the `row`/`column` attribute; restart CNC12. Use a real line from
   the shipped skin as the worked example.
5. **Delete a button:** remove its `<button>` line (frees the cell). Note: also remove/adjust
   any `<border>`/`<image>` that framed it.
6. **Skins that differ:** editing a button affects every skin that references it; the rapid
   skin may need the same edit. Cross-link `advanced.md` for the rapid/feed group-switch skins.
7. **Background & static overlays (pointers):** one-paragraph mention of `<background>`,
   `<border>`, `<image>`, `<text>`, `<plc_word>` living at skin level, each linking to the
   file that details it (`visual-states.md`, `advanced.md`).

- [ ] **Step 3: Verify**

Run: `LC_ALL=C grep -nP "[^\x00-\x7F]" .claude/skills/centroid-vcp/reference/skin-and-grid.md`
Expected: no output (ASCII-only).
Run: `grep -c "button row=" .claude/skills/centroid-vcp/reference/skin-and-grid.md`
Expected: >= 1 (contains a real placement example).

---

## Task 2: reference/button-anatomy.md (the button folder + XML/SVG format)

**Files:**
- Create: `.claude/skills/centroid-vcp/reference/button-anatomy.md`
- Read to ground: `resources/vcp/Buttons/coolant_pump/coolant_pump.xml` and `.svg`,
  `resources/vcp/Buttons/template.xml`, `resources/vcp/Buttons/single_block/single_block.xml`,
  `resources/vcp/Buttons/x_positive/x_positive.svg`

**Interfaces:**
- Consumes: `skin-and-grid.md` (placement).
- Produces: the canonical **button XML tag reference** table and the **create-a-new-button**
  recipe that `SKILL.md`, `visual-states.md`, and `actions.md` link to.

- [ ] **Step 1: Read the real button files**

Run: `cat resources/vcp/Buttons/coolant_pump/coolant_pump.xml resources/vcp/Buttons/coolant_pump/coolant_pump.svg`
Confirm the tag set and the SVG width/height/text layout actually shipped.

- [ ] **Step 2: Write the file** with these sections:

1. **The button folder contract:** `Buttons/<name>/` holds `<name>.xml` (behavior) + one or
   more `.svg` graphics; folder name == xml base name == default svg base name. The name in the
   skin's `<button>` line must match the folder.
2. **Button XML tag reference table** -- every `<vcp_button>` child, from the Reference facts
   block above: `skin_event_num`, `plc_output` (+`number`,`color_on`,`color_off`,`image_on`,
   `image_off`), `plc_input`, `plc_memory`, `on_click_swap`, `run`(+`line`,`macro`), `app`,
   `switch`, and the `group` attribute. Columns: tag | purpose | detailed in. Point
   visual-state tags to `visual-states.md`, action tags to `actions.md`.
3. **SVG conventions & sizing:** SVG is plain-text vectors; the renderer wants clean vectors
   only (no embedded bitmaps/fonts). **Field-validated:** size tracks the SVG width/height/
   artboard; `text-anchor` is effectively ignored -- position text with an explicit `x`, and
   convert fonts to paths ("Object to Path"). Best practice: copy an existing button SVG and
   edit it so the artboard is correct. Link SVG troubleshooting to `troubleshooting.md`.
4. **Create-a-new-button recipe (worked, using coolant_pump as the real example):**
   (a) make `Buttons/<name>/`; (b) create `<name>.svg` (copy a similar button's SVG, keep
   width/height, set text by explicit x); (c) write `<name>.xml` -- pick the function via
   `skin_event_num` (link to `actions.md` for choosing the number) and optionally an LED via
   `plc_output`; (d) place it in the skin `<button>` line (link to `skin-and-grid.md`);
   (e) restart CNC12. Show the real `coolant_pump.xml` (skin_event_num 23, plc_output 1079) as
   the finished example, labeled as a real in-repo file.
5. **Momentary vs latched vs indicator:** one short table mapping intent -> which tag set
   (bare `skin_event_num`; `+plc_output` LED; `plc_input`/`plc_memory`/image-swap indicator;
   `run`/`app` direct action).

- [ ] **Step 3: Verify**

Run: `LC_ALL=C grep -nP "[^\x00-\x7F]" .claude/skills/centroid-vcp/reference/button-anatomy.md`
Expected: no output.
Run: `grep -E "skin_event_num|plc_output|on_click_swap|<run>|<app>" .claude/skills/centroid-vcp/reference/button-anatomy.md | wc -l`
Expected: >= 5 (tag reference is present).

---

## Task 3: reference/visual-states.md (color & graphics states)

**Files:**
- Create: `.claude/skills/centroid-vcp/reference/visual-states.md`
- Read to ground: `resources/vcp/Buttons/reset/` (reset.svg, reset_tripped.svg, reset_clear.svg,
  reset.xml), `resources/vcp/Buttons/probe_indicator/`, `resources/vcp/images/` listing,
  `resources/vcp/skins/servo_mill_vcp_skin.vcp` (border/image/on_hover/on_click blocks)

**Interfaces:**
- Consumes: `button-anatomy.md` (tag reference).
- Produces: the visual-styling playbooks linked from `SKILL.md` and the create-button recipe.

- [ ] **Step 1: Ground against real files**

Run: `ls resources/vcp/Buttons/reset resources/vcp/Buttons/probe_indicator resources/vcp/images; cat resources/vcp/Buttons/reset/reset.xml`

- [ ] **Step 2: Write the file** with these sections:

1. **LED indicator color:** `plc_output`>`number` + `color_on`/`color_off` (hex). The VCP
   overlays the LED (radial gradient auto-added); LEDs are not part of the SVG. Remove the LED
   by deleting the `plc_output` block. Real example: `coolant_pump.xml` colors.
2. **Swap image while pressed:** `<on_click_swap>name_swap.svg</on_click_swap>` (transient,
   only during click).
3. **Swap image on function activated:** `plc_output` with `image_on`/`image_off` (state of the
   button's output). Real example: `reset` button (reset.svg / reset_tripped.svg).
4. **Indicator light from an input or memory:** `plc_input` and `plc_memory` with
   `image_on`/`image_off`. Real example: `probe_indicator` (probe_trip.svg / probe_clear.svg,
   input #7 in the manual).
5. **Hover / click / touch effects:** skin-level `<on_hover>`/`<on_click>` with `<opacity>` and
   `<outline_color>` (use `Transparent` to disable). Defaults: white hover outline, black click.
6. **Borders & backgrounds:** `<border>` (group boxes / solid fills; `<fill>` +
   `<outline_color>` + `<outline_thickness>` + span/start) and `<background>` (color or image;
   default #A6A5A0; image should be >= VCP size, anchored top-right, cropped).
7. **Logos & icons:** static `<image>` overlays (`<path>` to an SVG in `resources/vcp/images/`;
   `column_span`/`row_span`/`column_start`/`row_start`). Replace by editing `<path>`; delete to
   free the cells. Real files: `images/acornlogo.svg`, `images/coolant.svg`.

- [ ] **Step 3: Verify**

Run: `LC_ALL=C grep -nP "[^\x00-\x7F]" .claude/skills/centroid-vcp/reference/visual-states.md`
Expected: no output.
Run: `grep -E "on_click_swap|image_on|on_hover|<border>|<background>|<image>" .claude/skills/centroid-vcp/reference/visual-states.md | wc -l`
Expected: >= 5.

---

## Task 4: reference/actions.md (functions, macros, apps, PLC bits)

**Files:**
- Create: `.claude/skills/centroid-vcp/reference/actions.md`
- Read to ground: `resources/vcp/Buttons/flood_coolant/flood_coolant.xml`,
  `resources/vcp/Buttons/coolant_pump/coolant_pump.xml`, `resources/vcp/Buttons/m55/m55.xml`

**Interfaces:**
- Consumes: `button-anatomy.md`.
- Produces: the `skin_event_num` explanation + macro/app/PLC-bit playbooks; cross-linked from
  `button-anatomy.md` and `SKILL.md`. Links out to `centroid-plc-programming` and `acroloc-s10`.

- [ ] **Step 1: Ground against real files**

Run: `cat resources/vcp/Buttons/m55/m55.xml resources/vcp/Buttons/flood_coolant/flood_coolant.xml`

- [ ] **Step 2: Write the file** with these sections:

1. **What skin_event_num is:** the binding from a button to CNC12/PLC logic; surfaces in the
   PLC as `SV_SKIN_EVENT_N`. The full catalog lives in the PLC source (`*_plc.src`, the
   "System variables: Virtual Control Panel Events" / skin_event section); max 255. Give the
   method to find a number (grep the PLC source for `skin_event`), cross-link
   `centroid-plc-programming` for the `SV_` side and `acroloc-s10` for this machine's buttons.
   Table of common stock skin events from the manual (e.g. 3-5/8-9/...=Aux keys; 21=CoolAutoMan,
   22=CoolFlood, 23=CoolMist; 47=SingleBlock; 56=Reset; 73=WorkLight), labeled "stock Acorn
   mill -- confirm against the machine's own PLC source."
2. **Aux keys = macro buttons:** 16 Aux-key skin events map to `mfuncNN.mac` via the Wizard's
   VCP Aux Keys menu. A button with an Aux-key `skin_event_num` runs the assigned macro. To
   change behavior, edit the assigned macro (e.g. `mfunc56.mac`) rather than the button.
   Cross-link `centroid-plc-programming`/`acroloc-s10` macros.
3. **Run a macro/line directly (no Aux key):** `<run><line>...</line></run>` (one G-code line)
   or `<run><macro>path.cnc</macro></run>`; only from the main CNC12 menu; never mix line+macro.
4. **Launch an app:** `<app>path.exe</app>` (manual's Plasma Profile Manager example).
5. **Drive/read a PLC bit:** LED read-back via `plc_output`>`number` (a PLC OUT/MEM read as
   `#(60000+n)` from macros); writing a bit is done in the macro the button runs
   (`M94 /bit` set, `M95 /bit` reset). Cross-link `centroid-plc-programming` and `acroloc-s10`
   for the macro/PLC side; keep this file about the button->function wiring only.

- [ ] **Step 3: Verify**

Run: `LC_ALL=C grep -nP "[^\x00-\x7F]" .claude/skills/centroid-vcp/reference/actions.md`
Expected: no output.
Run: `grep -E "SV_SKIN_EVENT|<run>|<macro>|<app>|M94|M95" .claude/skills/centroid-vcp/reference/actions.md | wc -l`
Expected: >= 4.

---

## Task 5: reference/advanced.md (BIG buttons, PLC-word data, groups/switching)

**Files:**
- Create: `.claude/skills/centroid-vcp/reference/advanced.md`
- Read to ground: `resources/vcp/skins/servo_mill_vcp_rapid_skin.vcp` (group/switch/plc_word),
  `resources/vcp/Buttons/rapid_feed/` if present

**Interfaces:**
- Consumes: `skin-and-grid.md`, `button-anatomy.md`.
- Produces: the advanced-display playbooks linked from `SKILL.md`.

- [ ] **Step 1: Ground against real files**

Run: `grep -nE "plc_word|<group>|<switch|hide_group|row_span|column_span" resources/vcp/skins/servo_mill_vcp_rapid_skin.vcp | head -40`

- [ ] **Step 2: Write the file** with these sections:

1. **BIG (multi-cell) buttons:** add `row_span`/`column_span` to the `<button>` line; the SVG
   artboard scales to the spanned cells (link to the field-validated sizing note in
   `button-anatomy.md`). Worked example: the manual's `m55` 2x2 button.
2. **Display live data with PLC words:** `<plc_word>` inside a `<border>` (or `<vcp_button>`),
   full sub-node list from the Reference facts (number/type/significant/color/fontsize/font/
   fontstyle/alignment/margins/percentage). Where W-numbers come from (the PLC's Word
   Definitions section); common stock words (W31 feed override %, W19 spindle override %,
   W54 carousel position, W52 turret position). Note custom words require PLC edits ->
   cross-link `centroid-plc-programming`.
3. **Static text without an image:** `<text>` in a `<border>` (`content` with `&#13;` newline,
   font/size/color/alignment).
4. **Groups & switching:** `<group>` on border/image and `group=` on buttons; a button's
   `<switch>`/`<switch_on>`/`<switch_off>` with `<remove>`/`<add>`/`image_on`/`image_off`;
   `<hide_group>` at skin startup. Worked example: the stock rapid/feed override swap
   (`rapid_group`). Performance caution ~1000 objects.

- [ ] **Step 3: Verify**

Run: `LC_ALL=C grep -nP "[^\x00-\x7F]" .claude/skills/centroid-vcp/reference/advanced.md`
Expected: no output.
Run: `grep -E "row_span|plc_word|<switch|hide_group|<text>" .claude/skills/centroid-vcp/reference/advanced.md | wc -l`
Expected: >= 4.

---

## Task 6: reference/troubleshooting.md (manual troubleshooting + field-validated facts + workflow)

**Files:**
- Create: `.claude/skills/centroid-vcp/reference/troubleshooting.md`

**Interfaces:**
- Produces: the authoritative **field-validated facts** list (summarized in `SKILL.md`) + the
  edit/verify workflow. Linked from every other file for "why won't it load" questions.

- [ ] **Step 1: Write the file** with these sections:

1. **Edit workflow / discipline:** back up the skin `.vcp` first; change one thing at a time;
   restart CNC12 to reload; a button in multiple skins must be fixed in each.
2. **Field-validated facts (authoritative):** the 5 items from the Reference facts block
   (text-anchor ignored / fonts-to-paths; size from SVG width/height/artboard; restart to
   reload; back up before editing; multi-skin edits), each with the one-line "why."
3. **VCP won't start after an edit:** SVG filename typo / missing SVG / incompatible SVG
   (embedded bitmap or unconverted font) / missing button XML / XML typo. The error dialog
   names the button. Missing button XML => graphic shows, function dead.
4. **VCP absent / no message:** bad skin name or path in `options.xml`; skin XML typo; .NET
   missing; Windows Tablet mode; Windows Region not USA. Skewed/chopped => display 1920x1080.
   Missing lower third after a CNC12 upgrade => cross-version restore-report issue.
5. **Good SVG practice:** vectors only; convert fonts to paths; every element needs a color;
   keep art in the artboard; ungroup convoluted groups; delete empty/hidden layers; convert
   bitmaps to vector first.
6. **Verify without the machine:** the "Offline Mill and Lathe Intercon" installer runs the VCP
   off a control board using the same `...\resources\vcp` layout (graphics-only checks). In this
   repo, sanity checks Claude can run: button name in the skin matches a folder; referenced SVGs
   exist in the folder; XML is well-formed; ASCII-only. Note what only the control PC can
   confirm (actual function/PLC behavior).

- [ ] **Step 2: Verify**

Run: `LC_ALL=C grep -nP "[^\x00-\x7F]" .claude/skills/centroid-vcp/reference/troubleshooting.md`
Expected: no output.
Run: `grep -iE "text-anchor|artboard|restart|back up|offline" .claude/skills/centroid-vcp/reference/troubleshooting.md | wc -l`
Expected: >= 4.

---

## Task 7: SKILL.md (orientation, tables, task-playbook index)

**Files:**
- Create: `.claude/skills/centroid-vcp/SKILL.md`
- Read to match house style: `.claude/skills/teco-f510/SKILL.md`,
  `.claude/skills/centroid-plc-programming/SKILL.md`, `.claude/skills/acroloc-s10/SKILL.md`

**Interfaces:**
- Consumes: all six reference files (must exist first so links/anchors resolve).
- Produces: the skill entry point.

- [ ] **Step 1: Match the frontmatter convention**

Frontmatter with `name: centroid-vcp` and a `description:` in the sibling "Use when ..." style,
enumerating the covered tasks and ending with the machine-agnostic + source note, e.g.:
"Use when customizing a Centroid CNC12 Virtual Control Panel (VCP): moving/creating/deleting
buttons, editing button graphics and LED/image visual states, wiring a button to a
function/macro/app or PLC bit, and building big buttons or live PLC-word data displays. Covers
the skin .vcp grid, button XML/SVG format, options.xml, and troubleshooting. Generic to the
Centroid VCP -- this-machine skin/buttons live in the acroloc-s10 skill. Source: official CNC12
VCP 2.0 Users Manual + this repo's resources/vcp."

- [ ] **Step 2: Write the body** with these sections:

1. **`## When to use / when not`** -- use for VCP skin/button customization; not for PLC language
   (`centroid-plc-programming`), operating the machine (`centroid-cnc12-operating`), or our
   specific panel config (`acroloc-s10`).
2. **The two-layer mental model:** skin `.vcp` (placement) vs button folder (`<name>.xml` +
   `<name>.svg`). "Change where = skin file; change what = button folder."
3. **Button XML tag at-a-glance table:** the `<vcp_button>` children (tag -> meaning -> detailed
   in <reference file>). Grounded in the real tag set (Reference facts block).
4. **Task-playbook index table:** "I want to ..." -> reference file, covering all four areas:
   move/delete/create a button, edit graphics/LED/image state, hover/border/background/logo,
   wire a function/macro/app/PLC bit, big button, PLC-word display, "won't load". 
5. **Field-validated facts callout:** the compact 5-item list, pointing to
   `troubleshooting.md` for detail.
6. **Navigation commands:** grep the skins/buttons (e.g. list `resources/vcp/Buttons`, grep a
   button name across skins), mirroring the `acroloc-s10` "find code" style.
7. **See also:** links to the six reference files + `acroloc-s10`, `centroid-plc-programming`,
   `centroid-cnc12-operating`, and `README.md`/`CLAUDE.md`.

- [ ] **Step 3: Verify**

Run: `LC_ALL=C grep -nP "[^\x00-\x7F]" .claude/skills/centroid-vcp/SKILL.md`
Expected: no output.
Run: `awk '/^---$/{n++} n==1&&/^name:|^description:/{print} n==2{exit}' .claude/skills/centroid-vcp/SKILL.md`
Expected: prints a `name:` and `description:` line (valid frontmatter).
Run (every referenced reference file exists):
`for f in $(grep -oE "reference/[a-z-]+\.md" .claude/skills/centroid-vcp/SKILL.md | sort -u); do test -f ".claude/skills/centroid-vcp/$f" && echo "OK $f" || echo "MISSING $f"; done`
Expected: all `OK`.

---

## Task 8: Cross-link from acroloc-s10 -> centroid-vcp

**Files:**
- Modify: `.claude/skills/acroloc-s10/SKILL.md`

**Interfaces:**
- Consumes: the finished `centroid-vcp` skill.
- Produces: the machine skill's route into VCP work.

- [ ] **Step 1: Read the target section**

Run: `grep -n "Task playbooks\|### 3. Add or change an M-code macro\|## See also" .claude/skills/acroloc-s10/SKILL.md`
Choose the insertion point: a new short task entry under "Task playbooks" (e.g. "### 5. Edit the
VCP / operator panel") plus a "See also" bullet.

- [ ] **Step 2: Add the cross-link** -- a brief entry pointing VCP customization (our skin, our
buttons like `coolant_pump`, the row/col placement) to the `centroid-vcp` skill for format/how-to,
while noting this machine's specifics stay documented in `acroloc-s10`. Keep it to a few lines;
match surrounding style. Add one `## See also` bullet linking `../centroid-vcp/SKILL.md`.

- [ ] **Step 3: Verify**

Run: `grep -n "centroid-vcp" .claude/skills/acroloc-s10/SKILL.md`
Expected: >= 1 reference.
Run: `LC_ALL=C grep -nP "[^\x00-\x7F]" .claude/skills/acroloc-s10/SKILL.md`
Expected: no output (didn't introduce non-ASCII).

---

## Task 9: Final consistency review + commit

**Files:** none created; whole-skill review.

- [ ] **Step 1: Cross-link integrity** -- every relative link resolves:

Run:
`cd .claude/skills/centroid-vcp && for f in SKILL.md reference/*.md; do grep -oE "\]\(([a-zA-Z./_-]+\.md)" "$f" | sed -E 's/^\]\(//' | while read t; do (cd "$(dirname "$f")" && test -f "$t") && : || echo "BROKEN $f -> $t"; done; done; cd -`
Expected: no `BROKEN` lines.

- [ ] **Step 2: ASCII sweep across the whole skill:**

Run: `LC_ALL=C grep -rnP "[^\x00-\x7F]" .claude/skills/centroid-vcp/`
Expected: no output.

- [ ] **Step 3: Groundedness spot-check** -- confirm each "real example" filename cited in the
skill actually exists:

Run: `grep -rhoE "resources/vcp/[A-Za-z0-9_./-]+" .claude/skills/centroid-vcp/ | sort -u | while read p; do test -e "$p" && echo "OK $p" || echo "MISSING $p"; done`
Expected: all `OK` (or the only non-OK are clearly-labeled generic templates, not real-file claims).

- [ ] **Step 4: Machine-agnostic check** -- no accidental Acroloc-specific config leaked in:

Run: `grep -rinE "acroloc|W71|W72|ATC_Pos|CarouselToolID" .claude/skills/centroid-vcp/ | grep -v "acroloc-s10"`
Expected: no output (references to Acroloc appear only as cross-links to the acroloc-s10 skill).

- [ ] **Step 5: Commit (only on the user's go-ahead)**

```bash
git add .claude/skills/centroid-vcp .claude/skills/acroloc-s10/SKILL.md \
  docs/superpowers/plans/2026-07-13-centroid-vcp-skill.md
git commit -m "docs(skill): add centroid-vcp VCP authoring knowledge base

Machine-agnostic Centroid CNC12 VCP customization skill (SKILL.md + 6 reference
files) distilled from the VCP 2.0 Users Manual and this repo's resources/vcp.
Cross-linked from acroloc-s10.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Self-Review (against the spec)

- **Spec coverage:** skin/grid+move/delete (T1), button format+create (T2), visual states
  (T3), actions/macros/apps/PLC bits (T4), big buttons+PLC words+groups (T5), troubleshooting +
  field-validated facts (T6), SKILL.md orientation/index (T7), acroloc-s10 cross-link (T8),
  consistency + commit (T9). All four user-selected coverage areas map to T2-T5. The spec's
  manual-section -> file mapping matches the task-to-file mapping.
- **No placeholders:** every task names exact files to read, exact tags/values (Reference facts
  block), real in-repo example files, and concrete verify commands.
- **Type/name consistency:** file names, tag names (`skin_event_num`, `plc_output`, `plc_word`,
  `on_click_swap`, `row_span`), and skin-event values (22/23/47/56) are used identically across
  tasks and match the real button XMLs and the manual.

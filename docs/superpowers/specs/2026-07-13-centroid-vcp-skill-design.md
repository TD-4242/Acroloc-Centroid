# Centroid VCP Authoring Skill Design

- Date: 2026-07-13
- Status: designed; implementation pending
- Scope: new skill `.claude/skills/centroid-vcp/` (docs only; no PLC/macro/source changes)
- Source material: `~/Centroid_DIY/centroid_vcp_users_manual.pdf` (CNC12 VCP 2.0 Users
  Manual, rev 28) and the in-repo `resources/vcp/` tree (real skins + buttons)
- Related: [[acroloc-s10]] (this machine), `centroid-plc-programming`,
  `centroid-cnc12-operating`, `centroid-allin1dc-install`

## Goal

Create a **machine-agnostic** knowledge-base skill that lets Claude confidently make custom
changes to a Centroid CNC12 Virtual Control Panel (VCP): move/create/delete buttons, edit
button graphics and visual states, wire buttons to functions/macros/PLC bits, and build the
advanced button types (big multi-cell buttons, live PLC-word data displays).

It sits alongside `centroid-plc-programming` as general Centroid knowledge. It contains **no
Acroloc-specific configuration**; machine specifics (which skin we run, the buttons we added)
stay in `acroloc-s10`, which will cross-link to this skill.

## Why this skill

VCP customization is spread across three coupled artifact types — the skin `.vcp` file (grid
placement), per-button `Buttons/<name>/<name>.xml` + `<name>.svg`, and the PLC/macros a button
drives. The manual documents the format but is 64 pages; the repo has a working example tree
but no distilled guidance. Last session we reverse-engineered the button format the hard way
and hit undocumented renderer behavior (see "Field-validated facts"). This skill captures that
once so it is not re-derived.

## Positioning and naming

- Directory: `.claude/skills/centroid-vcp/`
- `name: centroid-vcp`
- `description:` follows the sibling convention (a "Use when ..." sentence enumerating the
  covered tasks), ending with a machine-agnostic disclaimer and source note, mirroring
  `teco-f510`: "... Generic to the Centroid VCP — this-machine skin/buttons live in the
  acroloc-s10 skill. Source: official CNC12 VCP 2.0 Users Manual + this repo's resources/vcp."
- Cross-linking:
  - This skill links **to** `acroloc-s10` for "our actual panel."
  - `acroloc-s10/SKILL.md` gains one short pointer **to** this skill (a "Edit the VCP" entry in
    its task-playbook area) so the machine skill routes VCP work here. This is the only edit
    outside the new skill directory.

## File structure

Mirrors the established SKILL.md + `reference/*.md` pattern (`acroloc-s10` has the same
footprint):

```
.claude/skills/centroid-vcp/
  SKILL.md                  orientation, the two-layer mental model, button-XML tag
                            table, task-playbook index, field-validated-facts callout
  reference/
    skin-and-grid.md        skins folder; options.xml skin selection; the row/column grid;
                            .vcp <button row= column=> placement; move & delete a button
    button-anatomy.md       Buttons/<name>/ folder; button XML tag reference; SVG
                            conventions & sizing; create-a-new-button worked recipe
    visual-states.md        LED indicator color; image swap on click/press; image swap on
                            function-activated; hover/click/touch effects; borders &
                            backgrounds; logos & icons
    actions.md              skin_event_num function map; run a macro from a button; launch
                            an app; drive/read a PLC bit (#(60000+n), M94/M95, plc_output)
    advanced.md             BIG (multi-cell) buttons; display live data with PLC words
    troubleshooting.md      manual troubleshooting + field-validated gotchas + edit workflow
```

### Manual-section -> file mapping

| Manual section (by title) | Reference file |
|---|---|
| Introduction; Button Grid Layout; VCP user editable files; How to move or delete a button | `skin-and-grid.md` |
| Button Graphics Location and Format; Create a New Button | `button-anatomy.md` |
| Change Button Graphics and VCP background; Change the LED indicator light color; Swap Image when clicked/pressed; Swap Image when function activated; Logos and Icons; Border and Backgrounds; Mouse Hover/Click and Touch effects | `visual-states.md` |
| Run a Macro from a Button, Launch an App | `actions.md` |
| Making BIG buttons; Display Data with PLC Words | `advanced.md` |
| Trouble Shooting; Special Cases | `troubleshooting.md` |

`skin_event_num` (the button-to-function binding) is documented in `actions.md`; it also
appears in the create-a-new-button recipe in `button-anatomy.md` with a pointer to
`actions.md` for the full function map.

## Content per file

Each reference file is self-contained, ASCII-only, and references the manual **by section
title, not page number** (page numbers rot across manual revisions).

### SKILL.md
- "When to use / when not" block (matches sibling skills). Not for: PLC language (-> 
  `centroid-plc-programming`), operating the machine (-> `centroid-cnc12-operating`), or our
  specific panel config (-> `acroloc-s10`).
- **The two-layer mental model:** (1) the skin `.vcp` file places named buttons on the
  row/column grid; (2) each button is a self-contained `Buttons/<name>/` folder (`<name>.xml`
  behavior + `<name>.svg` graphics). Changing *where* a button is = skin file; changing *what*
  a button is = button folder.
- **Button XML tag at-a-glance table** (tag -> meaning -> where detailed), covering the tags
  actually present in `resources/vcp/Buttons/*/*.xml` (e.g. `skin_event_num`, `plc_output`
  with `number`, image/svg refs, text, border/background). Exact tag set to be confirmed by
  reading real button XMLs during implementation.
- **Task-playbook index:** a table of "I want to ..." -> reference file + section, covering all
  four coverage areas the user selected (core button editing, visual states & styling, button
  actions, advanced display).
- A compact **field-validated-facts** callout (full list below) with the key gotchas inline
  and a pointer to `troubleshooting.md`.
- Navigation commands (grep the skins/buttons), following the `acroloc-s10` "find code" style.

### reference/skin-and-grid.md
- Where skins live (`resources/vcp/skins/*.vcp`) and how `options.xml` selects the active skin
  (the `Skin` VcpOption `Value`).
- The even row/column grid (rows 1-14, columns 1-6 in the stock mill skin) and how
  `<button row="R" column="C">name</button>` maps a button folder onto a cell.
- Worked **move a button** procedure (change the column/row attribute) and **delete a button**
  (remove/blank the line), using real lines from our skin files.
- Note: multiple skins in the repo (`servo_mill_vcp_skin.vcp`,
  `servo_mill_vcp_rapid_skin.vcp`) and that both may need the same edit.

### reference/button-anatomy.md
- The `Buttons/<name>/` folder contract: `<name>.xml` + one or more `.svg` graphics; naming
  convention (folder == xml == default svg base name).
- **Full button XML tag reference** — every tag observed in real button XMLs, with type and
  meaning, plus which are optional. Sourced by reading `resources/vcp/Buttons/*/*.xml` and the
  manual's "Button Graphics Location and Format" + "Create a New Button" sections.
- **SVG conventions & sizing**, including the field-validated rules (size from `width`/`height`;
  `text-anchor` ignored; position text with explicit `x`).
- A **create-a-new-button** worked recipe using `coolant_pump` (real, in-repo) as the example:
  make the folder, write the SVG, write the XML (function via `skin_event_num`, LED via
  `plc_output`), place it in the skin. Cross-links to `actions.md` for choosing the function
  number and to `visual-states.md` for graphics states.

### reference/visual-states.md
- **LED indicator color** (`plc_output` + the color mechanism from "Change the LED indicator
  light color").
- **Image swap on click/press** vs **image swap on function-activated** — the two distinct
  mechanisms, the extra SVG files they need (e.g. `reset`/`reset_tripped`/`reset_clear`,
  `probe_indicator`/`probe_trip`/`probe_clear` in the repo), and the XML that wires them.
- **Hover/click/touch effects**, **borders & backgrounds**, **logos & icons** (including
  changing the VCP background and the corner logo, referencing `resources/vcp/images/`).

### reference/actions.md
- **skin_event_num function map:** what the number means (it selects the CNC12 skin event /
  panel function; in the PLC it surfaces as `SV_SKIN_EVENT_N`). Provide the mapping method and
  the common/known values, cross-referencing `centroid-plc-programming` for the `SV_` side.
- **Run a macro from a button** and **launch an app** (from the manual's section), with the
  exact XML.
- **Drive/read a PLC bit from a button:** `plc_output` for the LED read-back; and the macro
  side (`#(60000+n)` reads, `M94 /bit` / `M95 /bit` writes) cross-linked to
  `centroid-plc-programming` and `acroloc-s10`.

### reference/advanced.md
- **BIG buttons:** how a button spans multiple grid cells ("Making BIG buttons"), the sizing
  interaction with the field-validated width/height rule.
- **Display data with PLC words:** the mechanism to show live PLC `W` values on the VCP, the
  XML/format, and formatting options from that manual section.

### reference/troubleshooting.md
- The manual's "Trouble Shooting" and "Special Cases" content, distilled.
- **Field-validated facts** (authoritative list; also summarized in SKILL.md):
  1. The renderer **ignores SVG `text-anchor`** — center/position text with an explicit `x`.
  2. Button **size is taken from the SVG `width`/`height`** attributes; removing them shrinks
     the button.
  3. `skin_event_num` is the button's **function binding**; it surfaces in the PLC as
     `SV_SKIN_EVENT_N`.
  4. `<plc_output><number>N</number>` sets the **LED indicator source** (a PLC output/mem
     read-back).
  5. **CNC12 must be restarted** to reload an edited skin/button.
  6. **Back up the skin `.vcp` before editing** (the manual's own advice; keep a `*_backup.vcp`).
  7. Editing a button used by more than one skin requires editing/rechecking each skin.
- Verification workflow: how to sanity-check an edit without the machine (well-formed XML,
  referenced SVGs exist, the button name in the skin matches a folder), and what can only be
  confirmed on the control PC.

## What this skill is NOT

- Not machine-specific: no Acroloc skin name, custom button list, or PLC-bit assignments live
  here (those are `acroloc-s10`). The skill uses in-repo buttons only as *generic worked
  examples*.
- Not a PLC-language or macro reference (that is `centroid-plc-programming`); it links out for
  the PLC/macro side of button actions.
- Not a transcription of all 64 manual pages — it distills to task playbooks + a tag reference,
  citing the manual by section for depth.

## Implementation notes

- Read the remaining manual pages (9-64) during implementation to fill the tag reference,
  visual-state mechanisms, actions, big-button, and PLC-word sections accurately.
- Read a representative spread of real button XMLs (simple momentary, LED toggle, image-swap,
  macro-launcher, big button) to ground the tag reference in what the renderer actually reads.
- ASCII-only markdown (consistent with existing skills); no smart quotes/em dashes.
- The only file changed outside `.claude/skills/centroid-vcp/` is `acroloc-s10/SKILL.md` (one
  cross-link entry).

## Testing / validation

No automated tests (docs). Validation:
- Internal consistency: every task in the SKILL.md index resolves to a real section in a
  reference file; every cross-link target exists.
- Groundedness: every XML/SVG snippet either matches a real file under `resources/vcp/` or is
  labeled as a generic template; every field-validated fact is traceable to last session's
  on-machine findings.
- Optional human spot-check against the control PC on the next VCP edit.

## Open questions

None.

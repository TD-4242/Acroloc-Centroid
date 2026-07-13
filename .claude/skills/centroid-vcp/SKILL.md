---
name: centroid-vcp
description: Use when customizing a Centroid CNC12 Virtual Control Panel (VCP) - moving, creating, or deleting buttons; editing button graphics and LED/image visual states; wiring a button to a function, macro, app, or PLC bit; styling with borders/backgrounds/logos; or building big buttons and live PLC-word data displays. Covers the skin .vcp grid, the button XML/SVG format, options.xml skin selection, and why the VCP will not load. Generic to the Centroid VCP - this-machine skin/buttons live in the acroloc-s10 skill. Source: official CNC12 VCP 2.0 Users Manual + this repo's resources/vcp.
---

# Centroid VCP (Virtual Control Panel) authoring

The VCP is the on-screen operator panel CNC12 draws (jog keys, spindle/coolant, overrides,
custom function buttons). It is defined by editable XML skins, per-button XML + SVG folders, and
`options.xml`, all under `resources/vcp/`. This skill is how to customize it.

## When to use / when not

Use for: moving/creating/deleting VCP buttons, changing button graphics and visual states,
styling the panel, wiring buttons to functions/macros/apps/PLC bits, big buttons, and live data
displays; and for diagnosing why the VCP will not load.

Not for:
- PLC stage language, `SV_*` variables, or M-code macro bodies -> use
  [centroid-plc-programming](../centroid-plc-programming/SKILL.md).
- Operating the machine (jogging, WCS, running jobs) -> use
  [centroid-cnc12-operating](../centroid-cnc12-operating/SKILL.md).
- This machine's actual skin, custom buttons (e.g. `coolant_pump`), and PLC-bit assignments ->
  use [acroloc-s10](../acroloc-s10/SKILL.md).

## The two-layer mental model

1. **Skin layer** -- `resources/vcp/skins/<name>.vcp` places named buttons onto a row/column grid
   and holds page-wide elements (background, borders, logos, live data).
2. **Button layer** -- each button is a folder `resources/vcp/Buttons/<name>/` with `<name>.xml`
   (behavior) and `<name>.svg` (graphic).

> Change **where** a button is -> edit the skin `.vcp`. Change **what** a button is -> edit the
> button folder. Restart CNC12 to reload either.

`options.xml` selects the active skin by name (this repo: `servo_mill_vcp_skin`).

## Button XML at a glance

Children of `<vcp_button>` (details in [button-anatomy.md](reference/button-anatomy.md)):

| Tag | Meaning | Detailed in |
|-----|---------|-------------|
| `<skin_event_num>` | Function binding (PLC `SV_SKIN_EVENT_N`) | [actions.md](reference/actions.md) |
| `<plc_output>` | LED color, or image swap on an output's state | [visual-states.md](reference/visual-states.md) |
| `<plc_input>` / `<plc_memory>` | Indicator: image swap on an input/mem bit | [visual-states.md](reference/visual-states.md) |
| `<on_click_swap>` | Graphic shown only while pressed | [visual-states.md](reference/visual-states.md) |
| `<run>` (`<line>`/`<macro>`) | Run a G-code line or macro directly | [actions.md](reference/actions.md) |
| `<app>` | Launch an external application | [actions.md](reference/actions.md) |
| `<switch>` / `group=` | Show/hide switching groups | [advanced.md](reference/advanced.md) |

## Task playbook index

| I want to... | Go to |
|--------------|-------|
| Move or delete a button; understand the grid / `options.xml` | [skin-and-grid.md](reference/skin-and-grid.md) |
| Create a new button; learn the button XML/SVG format | [button-anatomy.md](reference/button-anatomy.md) |
| Add an LED, swap graphics on state, indicator lights | [visual-states.md](reference/visual-states.md) |
| Style hover/click, borders, backgrounds, logos | [visual-states.md](reference/visual-states.md) |
| Wire a button to a function, macro, app, or PLC bit | [actions.md](reference/actions.md) |
| Make a big multi-cell button | [advanced.md](reference/advanced.md) |
| Show live PLC data or static text; group switching | [advanced.md](reference/advanced.md) |
| Figure out why the VCP will not load | [troubleshooting.md](reference/troubleshooting.md) |

## Field-validated facts (keep in mind)

From on-machine work; details in [troubleshooting.md](reference/troubleshooting.md):

- The renderer effectively ignores SVG `text-anchor` -- position text with an explicit `x` and
  convert fonts to paths ("Object to Path").
- Rendered button size tracks the SVG `width`/`height`/artboard -- keep them; copy an existing
  button SVG so the artboard is correct.
- Restart CNC12 to reload any skin/button change.
- Back up the skin `.vcp` before editing; change one thing at a time.
- A button used by more than one skin must be edited/re-checked in each skin.

## Navigating the VCP files

```bash
# List all button folders
ls resources/vcp/Buttons

# Which skins reference a button, and where it sits
grep -rn "coolant_pump" resources/vcp/skins

# What a button does (function + LED)
cat resources/vcp/Buttons/coolant_pump/coolant_pump.xml

# Which skin is active
grep -A1 "<Name>Skin</Name>" resources/vcp/options.xml
```

## See also

- [reference/skin-and-grid.md](reference/skin-and-grid.md) -- skins, grid, `options.xml`, move/delete
- [reference/button-anatomy.md](reference/button-anatomy.md) -- button folder, XML/SVG, create a button
- [reference/visual-states.md](reference/visual-states.md) -- LEDs, image swaps, borders, backgrounds, logos
- [reference/actions.md](reference/actions.md) -- skin events, macros, apps, PLC bits
- [reference/advanced.md](reference/advanced.md) -- big buttons, PLC words, text, switching
- [reference/troubleshooting.md](reference/troubleshooting.md) -- why it will not load; edit workflow
- [acroloc-s10](../acroloc-s10/SKILL.md) -- this machine's skin and custom buttons
- [centroid-plc-programming](../centroid-plc-programming/SKILL.md) -- PLC/macro side of button actions
- [centroid-cnc12-operating](../centroid-cnc12-operating/SKILL.md) -- operating the machine
- [README.md](../../../README.md), [CLAUDE.md](../../../CLAUDE.md) -- repo overview and conventions

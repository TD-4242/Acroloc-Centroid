# Button anatomy (the button folder, XML, and SVG)

This is the **button layer**: each button is a self-contained folder. The skin that places it on
the grid is the [layout layer](skin-and-grid.md).

## The button folder contract

Each button is a folder under `resources/vcp/Buttons/<name>/` containing:

- `<name>.xml` -- the button's behavior (function, LED, image swaps, actions).
- one or more `.svg` graphics -- what is drawn on screen.

The folder name, the `.xml` base name, and the default `.svg` base name all match, and they must
match the name used in the skin's `<button ...>name</button>` line.

## Button XML tag reference

Every tag below is a child of the root `<vcp_button>` element. A minimal button is just a
`skin_event_num`; the rest are optional.

| Tag | Purpose | Detailed in |
|-----|---------|-------------|
| `<skin_event_num>` | Bind the button to a CNC12 function / PLC logic N (in the PLC: `SV_SKIN_EVENT_N`). | [actions.md](actions.md) |
| `<plc_output>` (`<number>`, `<color_on>`, `<color_off>`) | LED indicator driven by a PLC output/mem read-back. | [visual-states.md](visual-states.md) |
| `<plc_output>` (`<number>`, `<image_on>`, `<image_off>`) | Swap the whole graphic on the output's on/off state. | [visual-states.md](visual-states.md) |
| `<plc_input>` (`<number>`, `<image_on>`, `<image_off>`) | Indicator: swap graphic on a PLC input's state. | [visual-states.md](visual-states.md) |
| `<plc_memory>` (`<number>`, `<image_on>`, `<image_off>`) | Indicator: swap graphic on a PLC MEM location's state. | [visual-states.md](visual-states.md) |
| `<on_click_swap>swap.svg` | Show a different graphic only while pressed. | [visual-states.md](visual-states.md) |
| `<run>` (`<line>` or `<macro>`) | Run one G-code line or a macro file directly. | [actions.md](actions.md) |
| `<app>path.exe` | Launch an external application. | [actions.md](actions.md) |
| `<switch>` (`<switch_on>`/`<switch_off>` with `<remove>`/`<add>`/`image_on`/`image_off`) | Show/hide groups + swap image on press. | [advanced.md](advanced.md) |
| `group="name"` (attribute on the skin `<button>` line) | Add the button to a switching group. | [advanced.md](advanced.md) |

Real in-repo example -- `resources/vcp/Buttons/coolant_pump/coolant_pump.xml`, a latched LED
button:

```xml
<vcp_button>
	<skin_event_num>23</skin_event_num>
	<plc_output>
		<number>1079</number>
		<color_on>#EC1C24</color_on>
		<color_off>#81151C</color_off>
	</plc_output>
</vcp_button>
```

## Intent -> tag set

| You want... | Use |
|-------------|-----|
| A momentary function button | bare `<skin_event_num>` |
| A button with an on/off LED | `<skin_event_num>` + `<plc_output>` colors |
| An indicator whose graphic reflects a bit | `<plc_output>`/`<plc_input>`/`<plc_memory>` with `image_on`/`image_off` |
| A press-only graphic change | `<on_click_swap>` |
| A button that runs a macro or a line | `<run>` (or an Aux-key `skin_event_num`) |
| A button that launches an app | `<app>` |

## SVG conventions and sizing

SVG is a plain-text vector format. The VCP renderer wants **clean vectors only** -- no embedded
bitmaps and no live fonts (see [troubleshooting.md](troubleshooting.md) for the full SVG rules).

Field-validated behavior (from on-machine work; consistent with the manual's SVG advice):

- **Rendered size tracks the SVG `width`/`height`/artboard.** Keep the `width`, `height`, and
  `viewBox` on the `<svg>` element. The manual's advice -- "open an existing button `.svg`,
  rename it, and modify it, so the size/artboard is correct" -- is the same rule. Grid
  `row_span`/`column_span` scale the *cell* ([advanced.md](advanced.md)); the SVG artboard must
  still be right.
- **`text-anchor` is effectively ignored.** Position button text with an explicit `x`, and
  convert all fonts to paths ("Object to Path" in Inkscape) before saving. This is the root
  cause the manual is getting at when it says convert fonts to lines and arcs.

Real in-repo SVG -- `resources/vcp/Buttons/coolant_pump/coolant_pump.svg` (note width/height 100,
matching viewBox, and text placed by explicit `x` rather than centering):

```xml
<svg version="1.1" xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100">
  <rect width="100" height="100" rx="6" style="fill:#252d6b"/>
  <text x="7" y="43" style="fill:#ffffff;font-family:'Arial',sans-serif;font-weight:bold;font-size:17px;">COOLANT</text>
  <text x="12" y="77" style="fill:#ffffff;font-family:'Arial',sans-serif;font-weight:bold;font-size:26px;">PUMP</text>
</svg>
```

## Create a new button (worked recipe)

Using `coolant_pump` as the real example that this repo already ships:

1. **Make the folder** `resources/vcp/Buttons/coolant_pump/`.
2. **Create the SVG** `coolant_pump.svg`. Easiest: copy a similar button's SVG so the
   artboard/size is correct, then edit fill and text. Keep `width`/`height`/`viewBox`; place
   text with explicit `x`; convert fonts to paths for anything final.
3. **Write the XML** `coolant_pump.xml`. Pick the function with `<skin_event_num>` (see
   [actions.md](actions.md) for choosing the number) and, if the button has an on/off state,
   add a `<plc_output>` LED. The shipped file uses `skin_event_num` 23 and `plc_output` 1079.
4. **Place it in the skin** with a `<button>` line ([skin-and-grid.md](skin-and-grid.md)):
   `<button row="5" column="4">coolant_pump</button>`.
5. **Restart CNC12** to load it.

A quick way to build the graphic is to copy an existing button folder, rename the folder + files
+ any internal references, then edit. See [troubleshooting.md](troubleshooting.md) if the VCP
will not start after adding the button.

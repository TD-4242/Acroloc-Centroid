# Visual states and styling

How a button shows state (LEDs, image swaps) and how the skin is styled (hover/click, borders,
backgrounds, logos). Button tags here are children of `<vcp_button>`
([button-anatomy.md](button-anatomy.md)); skin tags are children of `<vcp_skin>`
([skin-and-grid.md](skin-and-grid.md)).

## LED indicator color

The VCP overlays an LED (with an automatic radial-gradient) on the button; the LED is **not**
part of the SVG. Drive it from a PLC output/mem read-back:

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

Colors are hex. `<number>` is the PLC output/mem whose state the LED reflects (find it from the
PLC program; see [actions.md](actions.md)). To **remove** the LED entirely, delete the whole
`<plc_output>` block, leaving just the `<skin_event_num>`.

## Swap the graphic while pressed

Show a different SVG only while the button is held:

```xml
<vcp_button>
	<skin_event_num>39</skin_event_num>
	<on_click_swap>x_positive_swap.svg</on_click_swap>
</vcp_button>
```

Put the swap SVG in the same button folder.

## Swap the graphic on function activated

Instead of an LED, use two whole graphics for the on/off state of the button's output -- put
`image_on`/`image_off` inside `<plc_output>`. Real in-repo example,
`resources/vcp/Buttons/reset/reset.xml`:

```xml
<vcp_button>
	<skin_event_num>56</skin_event_num>
	<plc_output>
		<number>1107</number>
		<image_on>reset_tripped.svg</image_on>
		<image_off>reset.svg</image_off>
	</plc_output>
</vcp_button>
```

## Indicator light from an input or memory bit

A button can act purely as an indicator, swapping graphics on the state of a PLC **input**
(`<plc_input>`) or **memory** bit (`<plc_memory>`). Real in-repo example,
`resources/vcp/Buttons/probe_indicator/` (files `probe_trip.svg` / `probe_clear.svg`):

```xml
<vcp_button>
	<plc_input>
		<number>7</number>
		<image_on>probe_trip.svg</image_on>
		<image_off>probe_clear.svg</image_off>
	</plc_input>
</vcp_button>
```

`<plc_memory>` is identical but watches a MEM location instead of an input.

## Hover / click / touch feedback

Skin-level effects (children of `<vcp_skin>`). Defaults: a white outline on hover, a black
outline on click. Set the color to `Transparent` to disable.

```xml
<on_hover>
	<opacity>100</opacity>
	<outline_color>#ffffff</outline_color>
</on_hover>
<on_click>
	<opacity>100</opacity>
	<outline_color>#000000</outline_color>
</on_click>
```

## Borders and backgrounds

`<border>` draws a group box or a solid fill (to visually group related buttons). It spans a
rectangle of the grid:

```xml
<border>
	<column_span>3</column_span>
	<column_start>1</column_start>
	<fill>#00007F</fill>            <!-- or Transparent for an outline-only box -->
	<row_span>4</row_span>
	<row_start>1</row_start>
	<outline_color>#000000</outline_color>
	<outline_thickness>2</outline_thickness>
</border>
```

A `<border>` can also carry a `<plc_word>` or `<text>` (see [advanced.md](advanced.md)) and a
`<group>` for switching.

`<background>` sets the VCP background. A hex value gives a solid color (this repo uses
`#a6a5a5`; the CNC12 default is `#A6A5A0`):

```xml
<background>#a6a5a5</background>
```

A file path uses an image (`.jpg`/`.png`) as the background; the image should be at least VCP
size, is anchored top-right, and is cropped to fit:

```xml
<background>C:\cncm\resources\vcp\images\stainless-steel.jpg</background>
```

## Logos and icons (static images)

`<image>` overlays a static graphic (logo/icon) on the grid -- it is not a button. Real in-repo
images live in `resources/vcp/images/` (e.g. `acornlogo.svg`, `coolant.svg`):

```xml
<image>
	<column_span>3</column_span>
	<column_start>4</column_start>
	<row_span>1</row_span>
	<row_start>1</row_start>
	<path>C:\cncm\resources\vcp\images\acornlogo.svg</path>
</image>
```

Replace a logo by editing `<path>`; delete the whole `<image>` block to free those cells for
buttons. An `<image>` may also carry a `<group>` for switching ([advanced.md](advanced.md)).

# Advanced displays (big buttons, PLC words, text, switching)

Heavier, less-common features: multi-cell buttons, live PLC data, static text, and group
switching. Skin tags are children of `<vcp_skin>` ([skin-and-grid.md](skin-and-grid.md)); button
tags are children of `<vcp_button>` ([button-anatomy.md](button-anatomy.md)).

## BIG (multi-cell) buttons

Add `row_span` / `column_span` to the button's `<button>` line to make it span several grid
cells. Make room by deleting the buttons it will cover.

```xml
<!-- a 2x2 M55 button -->
<button row="3" column="4" row_span="2" column_span="2">m55</button>
```

The button's SVG artboard scales to the spanned area, so the SVG `width`/`height`/`viewBox` must
be correct (see the sizing note in [button-anatomy.md](button-anatomy.md)).

## Display live data with PLC words

A `<plc_word>` shows a live PLC `W` value, placed inside a `<border>` (or a `<vcp_button>`). Full
node set:

```xml
<plc_word>
	<number>31</number>                          <!-- which W word (from the PLC's Word Definitions) -->
	<type>Float</type>                           <!-- Int (default) | Float | Double | DoubleFloat -->
	<significant>5</significant>                 <!-- decimals for non-Int; default 2 -->
	<color>#000000</color>                       <!-- default #000000 -->
	<fontsize>22</fontsize>                       <!-- default 16 -->
	<font>Segoe UI</font>                         <!-- default Segoe UI; use exact list names -->
	<fontstyle>bold</fontstyle>                   <!-- normal | bold | italic | oblique -->
	<verticalalignment>bottom</verticalalignment> <!-- top | center | bottom; default bottom -->
	<horizontalalignment>center</horizontalalignment> <!-- left | right | center; default left -->
	<marginbottom>-5</marginbottom>               <!-- margintop/left/right too; integers -->
	<percentage>true</percentage>                 <!-- append a % sign -->
</plc_word>
```

`<number>` is a PLC word index, found in the PLC source's "Word Definitions" section. Common
stock words:

| W | Meaning |
|---|---------|
| W31 | Feedrate override % (`FinalFeedOverride_W`) |
| W19 | Spindle speed override % (`SpinOverride_W`) |
| W7  | Target voltage override % (`TargetVoltage_W`) |
| W54 | Current carousel position (`CurrentCarouselPosition_W`) |
| W52 | Current turret position (`CurrentTurretPosition_W`) |

Displaying a custom value means defining a new `W` and feeding it in the PLC program, then
referencing its number here -- see
[centroid-plc-programming](../../centroid-plc-programming/SKILL.md).

## Static text without an image

`<text>` displays text directly (no SVG), inside a `<border>`. Use `&#13;` for a line break.

```xml
<border>
	<column_span>2</column_span>
	<column_start>1</column_start>
	<fill>Transparent</fill>
	<row_span>1</row_span>
	<row_start>8</row_start>
	<text>
		<content>This is sample text&#13;With a new line</content>
		<fontsize>20</fontsize>
		<color>#ffffff</color>
		<font>Segoe UI</font>
		<horizontalalignment>center</horizontalalignment>
		<verticalalignment>center</verticalalignment>
	</text>
</border>
```

## Groups and switching

The switching feature lets buttons, borders, and images share the same space and appear only
when wanted (e.g. the stock rapid/feed override swap).

Define membership:

- On a border or image: a child `<group>group_name</group>`.
- On a button: a `group="group_name"` attribute on its `<button>` line.

Then a button controls the groups with `<switch>`:

```xml
<vcp_button>
	<switch>
		<switch_on>
			<remove>feed_group</remove>
			<add>rapid_group</add>
			<image_on>rapid_feed_lit.svg</image_on>
		</switch_on>
		<switch_off>
			<remove>rapid_group</remove>
			<add>feed_group</add>
			<image_off>rapid_feed.svg</image_off>
		</switch_off>
	</switch>
</vcp_button>
```

Hide groups at startup so everything is not visible at once, using a skin-level node:

```xml
<hide_group>
	<group>rapid_group</group>
</hide_group>
```

Real in-repo example: `resources/vcp/skins/servo_mill_vcp_rapid_skin.vcp` defines
`feed_group` / `rapid_group` / `linked_group`, each with a `<border>` carrying a `<plc_word>`,
switched by the rapid/feed toggle button.

Performance note: the VCP can hold many objects, but responsiveness starts to degrade around
1000 objects.

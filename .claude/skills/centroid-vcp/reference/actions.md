# Button actions (functions, macros, apps, PLC bits)

How a button *does* something: bind it to a CNC12 function, run a macro or a line of G-code,
launch an app, or reflect/drive a PLC bit. Tags here are children of `<vcp_button>`
([button-anatomy.md](button-anatomy.md)).

## skin_event_num: the function binding

`<skin_event_num>N</skin_event_num>` binds a button to a piece of logic. That logic lives in the
PLC program; the same number appears there, where it surfaces as the system variable
`SV_SKIN_EVENT_N`. When the button is pressed, CNC12 runs whatever the PLC associates with skin
event N. The maximum is 255 skin events.

```xml
<vcp_button>
	<skin_event_num>22</skin_event_num>
	<plc_output>
		<number>1078</number>
		<color_on>#EC1C24</color_on>
		<color_off>#81151C</color_off>
	</plc_output>
</vcp_button>
```

(Real in-repo `flood_coolant.xml`: skin event 22, LED output 1078.)

### Finding the right number

Every skin event is defined in the machine's PLC source. Open the PLC `.src` and search for
`skin_event` -- the "System variables: Virtual Control Panel Events" section lists each one with
its row/column note. For the `SV_` side of PLC logic, see the
[centroid-plc-programming](../../centroid-plc-programming/SKILL.md) skill. For which buttons this
machine actually uses and what they drive, see [acroloc-s10](../../acroloc-s10/SKILL.md).

Common stock Acorn-mill skin events (confirm against the machine's own PLC source before
relying on them):

| Skin event | Function |
|-----------|----------|
| 3,4,5,8,9,10,13,14,15,18,19,20,24,25,68,69 | Auxiliary keys 1-16 (run a macro) |
| 21 | Coolant Auto/Man |
| 22 | Coolant Flood |
| 23 | Coolant Mist |
| 47 | Single Block |
| 56 | Reset |
| 73 | Work Light |

## Aux keys: buttons that run a macro

Sixteen of the skin events above are **Auxiliary keys**. Each maps to a macro (`mfuncNN.mac`)
through the Wizard's "VCP Aux Keys" menu (or CNC12 parameters). A button whose `skin_event_num`
is an Aux-key event runs that assigned macro when pressed. A button can be just:

```xml
<vcp_button>
	<skin_event_num>18</skin_event_num>
</vcp_button>
```

(Real in-repo `m55.xml`: Aux key, skin event 18.) To change what such a button does, edit the
**assigned macro** (the `mfuncNN.mac` mapped to that Aux key in the Wizard), not the button. The position of a button never makes it
an Aux key -- the skin event number does. See [acroloc-s10](../../acroloc-s10/SKILL.md) and
[centroid-plc-programming](../../centroid-plc-programming/SKILL.md) for the macro side.

## Run a macro or a line directly (no Aux key)

CNC12 v5.08+ lets any button run G-code directly with `<run>`. Use **either** one `<line>`
**or** one `<macro>` -- never both in the same `<run>` (if mixed, only the macro runs).

```xml
<!-- one line of G-code -->
<vcp_button>
	<run>
		<line>G0 X0 Y0</line>
	</run>
</vcp_button>

<!-- a macro file -->
<vcp_button>
	<run>
		<macro>C:\cncm\ncfiles\myMacro.cnc</macro>
	</run>
</vcp_button>
```

For more than one line, put the lines in a macro file and use `<macro>`. These buttons only work
when pressed from the main CNC12 menu.

## Launch an external application

```xml
<vcp_button>
	<app>C:\cncm\PlasmaProfileManager.exe</app>
</vcp_button>
```

## Read or drive a PLC bit

- **Read (LED):** `<plc_output>` / `<plc_input>` / `<plc_memory>` with a `<number>` reflect a
  PLC bit's state as an LED or image swap ([visual-states.md](visual-states.md)). From a macro,
  the same PLC `OUT`/`MEM` bit `n` is read as `#(60000 + n)`.
- **Drive (write):** a button does not set a PLC bit by itself -- it runs a function/macro that
  does. In the macro, set a bit with `M94 /bit` and reset it with `M95 /bit`.

Keep this file to the button-to-function wiring; the PLC/macro logic itself lives in
[centroid-plc-programming](../../centroid-plc-programming/SKILL.md) and, for this machine,
[acroloc-s10](../../acroloc-s10/SKILL.md).

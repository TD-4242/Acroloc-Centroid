# CNC12 Tool Setup: Offset Library, Tool Library, Tool Life Management, and Laser Setup

Configure tool height and diameter offsets, assign tool descriptions and default parameters, manage
tool life tracking, and set up PWM laser output.
Source: operator manual Ch 5 (Tool Setup).

## Ch 5 Overview (p.59)

Access via **F1 – Setup** → **F2 – Tool** from the main screen (see `interface.md` §F1–Setup
for the Setup menu map). The Tool Setup menu has three entries:

| Softkey | Label | Purpose |
|---|---|---|
| **F1** | Offset Library | Edit Height Offset (H) and Diameter (D) values |
| **F2** | Tool Library | Edit tool descriptions and default parameters |
| **F3** | Tool Life | Edit Tool Life Management settings |

---

## 5.1 Offset Library (p.59–63)

(from Main Screen: **F1 – Setup** → **F2 – Tool** → **F1 – Offset Lib**)

The Offset Library file contains the values for Height Offset and Diameter Numbers (p.59). For
example, if entry H01 has a value of −.25, a height offset of −.25 is applied when height offset
01 is referenced. If entry D01 shows a value of 1.5, the diameter offset 01 has a diameter of 1.5
associated with it.

The screen shows the **Tool Geometry Offset Library** with two columns: Height Offset and Diameter
(screenshot p.59). H01 and D01, H02 and D02, etc. are displayed together on the same line for
convenience only. The Height and Diameter Offset Numbers can be used independently; associations
are made only in the Tool Library (§5.2).

You can inspect and change any of the 200 Height Offset (H) or 200 Diameter (D) values. In most
cases, the automatic tool length measurement features are used to set H-values. D-values are
entered manually based on the known or measured diameters of your tools (p.60).

### Offset Library Softkeys (p.59)

| Softkey | Label | Description |
|---|---|---|
| **F1** | Z Ref | Select the Z-reference setting function. |
| **F2** | Manual Measure | Manually measure the current tool's height offset. |
| **F3** | Auto Measure | Automatically measure tool lengths (requires TT1 option). |
| **F5** | +.001 | Increase highlighted offset value by 0.001" (0.02 mm metric). |
| **F6** | −.001 | Decrease highlighted offset value by 0.001" (0.02 mm metric). |
| **F7** | ATC | Change tools using the Automatic Tool Changer (if installed). |
| **F10** | Save | Save changes and exit. Press **ESC** to exit without saving. |

> **Note:** F3 – Auto Measure and the optional F4 – Batch key require the Automatic Tool
> Measurement (TT1) option. F7 – ATC requires an Automatic Tool Changer.

Navigate to height offset entries using **Arrow**, **Page Up**, **Page Down**, **HOME**, and
**END** keys. To manually edit a Height Offset value, type the desired value and press **ENTER**.
When the edit is complete, press **F10 – Save** to save the Offset Library and exit (p.60).

### Height Offset (p.60)

This is the distance that the control adjusts Z-axis positions when tool length compensation
(G43 or G44) is used with a particular H-value. For example, if H001 is −1.0 and the job
contains G43 H1, the CNC software shifts all Z-axis positions down 1.0 to compensate for the
shorter tool (p.60).

> For G43/G44 tool-length compensation G-code syntax, see the **`centroid-cnc12-gmcodes`** skill.

Height Offset values are measured using the **Z-reference position**. The Z-reference position is
the Z-axis position when the tip of the reference tool is touching the work surface. The reference
tool should always be the longest tool (p.60).

The Height Offset value for end mills and drills is the difference between the Z-axis position
when the tip of the tool is touching the work surface, and the Z-reference position. The Height
Offset value for ball nose and bull nose cutters is the difference between the Z-axis position
when the center of the tool is at the work surface, and the Z-reference position. Because it is
not possible to position the tool in this way, instead move the tip of the tool to the work
surface, and then manually edit the value to subtract the tool nose radius (p.60).

You can make small adjustments to Height Offsets and Diameters using **F5 – +.001** and
**F6 – −.001**. Use the **Arrow** keys to highlight the value to adjust. If cut parts are
undersized, use **F5 – +.001** to cut less material. If cut parts are oversized, use **F6 – −.001**
to cut more material (p.61).

#### Manual Height Offset Measurement Procedure

**Establishing the Z-reference position (p.60):**

1. Press **F1 – Z-ref** to select the Z-reference setting function.
2. Insert the longest tool into the tool holder (Jog or **TOOL CHECK** keys can assist).
3. Jog the tip of the tool to the top of the work surface.
4. Press **F10 – Save** to save this Z-position as the Reference Position.

**Measuring each tool height (p.60):**

1. Insert the desired tool into the tool holder.
2. Jog the tip of the tool to the top of the work surface.
3. If the tool is a drill or end mill, press **F2 – Manual Measure** to measure the height.
4. If the tool is a bull or ball nose cutter, press **F2 – Manual Measure**, then subtract the
   tool nose radius from the value.
5. After a tool height is measured, the next Height Offset entry is automatically selected.
6. When complete, press **F10 – Save** to save the Offset Library and exit.

**Height offset examples assuming Z-reference = −1.5 (p.61):**

| Tool position | Nose radius | Tool height |
|---|---|---|
| −1.75 | — | −0.25 |
| −1.75 | 0.25 | −0.50 |
| −2.25 | — | −0.75 |
| −2.75 | 0.125 | −1.375 |

### Diameter (p.61)

This field tells the control the distance to adjust when cutter diameter compensation (G41 or
G42) is used with a particular D-value. For example, if D001 is 0.5 and the job contains G41 D1,
the CNC software adjusts all X-Y positions 0.25 (half the tool diameter) to the left of the
programmed tool path (p.61).

To edit Diameter entries, move to the desired diameter offset number with **Arrow**, **Page Up**,
**Page Down**, **HOME**, and **END** keys. Type the desired value and press **ENTER** (p.61).

> For G41/G42 cutter diameter compensation G-code syntax, see the **`centroid-cnc12-gmcodes`** skill.

---

### 5.1.1 Automatic Tool Measurement (p.61–63)

Z-minus single-surface probing using the TT-1 tool touch-off post is available in the Tool
Offset Library (p.61). See diagram of TT-1 Tool Touch-Off Block on p.61.

> **WARNING:** Incorrect setup may cause damage to the machine, tool, and/or cause injury to
> the Operator (p.61).

**First Time Setup (p.61):** Make sure that the proper parameters are set as per Ch 9 and Ch 15
(see Parameters 18, 244, 257, 281, 282, 283, and 367), and that the detector is plugged in and
at the correct location on the table. When first testing the TT-1, hold the TT-1 in hand and
manually touch the unit to the tool to confirm the correct electrical connection and parameter
setup. See **`centroid-cnc12-config`** for parameter details.

> **NOTICE:** Before manually jogging any probe to a position, make sure that the machine feed
> rate is turned down (less than ten in/min) or damage to the probe may result (p.62).

#### Setting the Z-reference (p.62)

Using the longest tool for the job or the designated reference tool, press **F1 – Z-ref**, then
**F3**, and finally the **CYCLE START** button. The Z-axis will move down until the tool
touch-off is detected. The Z-reference will be set at this position. Parameter 3 bit 1 is used
to set Z-reference to the Z-home position (see Ch 15 / **`centroid-cnc12-config`**).

#### Setting the Tool Height Offsets (p.62)

Pressing **F3 – Auto Measure** then **CYCLE START** causes the Z-axis to move down until the
tool touch-off is detected. The resulting tool length is entered into the table (same as
**F2 – Manual**). The Z-axis then returns to its home position (p.62).

If Parameter 17 has been set to the number of a valid return point (1 or 2), **F3 – Auto Measure**
will move X- and Y-axes to that return point before moving Z downward:
- Return point 1 = G28 position from the WCS Configuration screen (Ch 4)
- Return point 2 = G30 position from the WCS Configuration screen

If Parameter 17 is zero, the X- and Y-axes will not move before Z moves downward; jog the
machine directly over the detector before pressing **F3 – Auto Measure**.

> **Note:** SHIFT+F3 can be used to override any return point movement when Parameter 17 is set
> to use it. This is helpful for measuring tools where the height measurement is not taken from
> the center point of the tool (p.62).

See Parameters 18, 244, 257, 281, 282, 283, and 367 in Ch 15 for full setup information.

#### Batch Tool Height Offset Measurement (p.62)

If both the Automatic Tool Measurement (TT1) option and an Automatic Tool Changer are installed,
press **F4 – Batch** to measure multiple tools in one process. After pressing **F4 – Batch**, a
dialogue box prompts: `Enter the list of tools to measure. Example: 1-4, 6, 15`. Press
**CYCLE START** to perform the batch measurement. This process is similar to the single tool
height offset measurement via **F3 – Auto Measure** but handles multiple tools in one shot (p.62).

---

### 5.1.2 Setting Up Tool Height Offsets (p.62–63)

#### Using a Probe as the Reference Tool (p.63)

Before setting the Z-reference, make sure the probe Tool Number is entered into Parameter 12 on
the Machine Parameters screen. Make sure Parameter 17 contains a 0. Steps:

1. Load the probe into the machine.
2. Jog the probe over the desired reference surface and press **F1 – Z-ref**.
3. Press **F3** and then **CYCLE START**. The probe finds the Z-reference.

At this point the Z-reference is entered into the Offset Library and is the reference height for
all other tools. Remove the probe and measure any other tool offsets manually as described earlier
in this chapter (p.63).

#### Measuring Each Tool Offset Using a Fixed Detector (p.63)

Before measuring any tool height, enter the probe or reference tool measuring location. Do this by
entering a reference point number (1 or 2) into Parameter 17 and entering the detector position as
the corresponding Reference Return Point on the WCS Configuration screen (Ch 4). Also ensure
Parameter 44 is set correctly — this is the input number for the TT1 (p.63).

Procedure:

1. Load a reference tool (preferably the longest tool) and highlight its corresponding Height
   Offset Number using the **UP** or **DOWN** arrow keys.
2. Press **F1 – Z Ref**, **F3 – Auto Measure**, then **CYCLE START** to set the Z-reference.
   X- and Y-axes traverse to the preset location, then Z moves downward until the tool is
   detected and the Z-reference is set.
3. Load the next tool.
4. Highlight the desired Height Offset Number using the **UP ARROW** and **DOWN ARROW** keys.
5. Press **F3 – Auto Measure** then **CYCLE START**. X- and Y-axes traverse to the preset
   location, then Z moves downward until the tool is detected. A negative offset means the tool
   is shorter than the reference tool.

Once all tool offsets have been measured, press **F10 – Save** to save them. Press **ESC** to
cancel any changes (p.63).

---

## 5.2 Tool Library (p.63–65)

(from Main Screen: **F1 – Setup** → **F2 – Tool** → **F2 – Tool Lib**)

The definitions in the Tool Library associate tool (T) numbers with height offset (H) values,
diameter (D) values, default coolant types, spindle directions, spindle speeds, and text
descriptions of the tools (p.64). This information is used by the Intercon programming package
(Ch 10) to provide defaults whenever a tool change is selected. For enhanced ATC features, the
(T) numbers are also associated with bin numbers. The screen shows the **Tool Library** with
columns: Tool, Bin, Ht., Dia., Coolant, Spindle, Speed, Description (screenshot p.64).

> See **`centroid-cnc12-config`** for Parameter 160 (enhanced ATC features).

You can inspect and change any of the 200 tool definitions. To edit a Tool Library definition,
move to the desired tool number using the **Arrow**, **Page Up**, **Page Down**, **HOME**, and
**END** keys. To change Height Offset numbers, Diameter numbers, default spindle speed values,
and the tool description, type a new value into the field and press **ENTER**. To change the
default spindle direction and coolant, press the **SPACE** bar to cycle through the possible
values. When changes are complete, press **F10 – Save** to save the Tool Library and exit (p.64).

### Tool Library Field Definitions

#### Bin (p.64)

This field specifies the bin location, or ATC position, that the tool is occupying. Valid values
are −1 (shown as dashes "—") through the maximum number of tools specified by machine Parameter
161 (see **`centroid-cnc12-config`**). A value of 0 indicates that the tool is currently in the
spindle. The **F1–F2** keys work when the cursor is in the Bin column (p.64).

| Softkey | Label | Description |
|---|---|---|
| **F1** | Clear Bin | Places dashes "—" into the bin field (same as entering −1). |
| **F2** | ClearAll | Places dashes into every bin field. |

> **Note:** If enhanced ATC features are not on, the cursor cannot be moved into the Bin column
> and the message "Bin fields are locked" will appear where the tool in spindle display is
> located. **F1 – Clear Bin** and **F2 – ClearAll** only appear if enhanced ATC features are on
> (p.64).

> **Note:** For enhanced ATC applications, bin numbers will be updated when tool changes are
> completed. For random or arm-type tool changers, tools in the spindle are placed into the same
> bin that the next tool is picked up from, and not necessarily from the same bin it was
> originally taken from (p.64).

#### Height (p.65)

This field specifies a default Height Offset (H) number to use with each tool. Possible values
are 1 to 200. Intercon uses this information to provide a default H-value at each tool change.
The CNC software also uses this information to correct for the length of the tool that is used to
establish the Z-axis position of the Part Setup (see Ch 5 §5.1 and Part Setup Ch 4 / `part-setup.md`
§4.1.2) (p.65).

#### Diameter (p.65)

This field specifies a default Diameter (D) number to use with each tool. Possible values are 1
to 200. Intercon uses this information to provide a default D value at each tool change. To change
the value, type a new number and press **ENTER** (p.65).

#### Coolant (p.65)

This field specifies a default coolant type to use with each tool.

| Value | M-code inserted by Intercon |
|---|---|
| FLOOD | M7 |
| MIST | M8 |
| OFF | — |

To change this value, press the **SPACE** bar until the desired value is shown (p.65).

> For M7/M8 M-code definitions, see the **`centroid-cnc12-gmcodes`** skill.

#### Spindle (p.65)

This field specifies a default spindle direction to use with each tool.

| Value | M-code inserted by Intercon |
|---|---|
| CW | M3 |
| CCW | M4 |
| OFF | — |

To change this value, press the **SPACE** bar until the desired value is shown (p.65).

> For M3/M4 M-code definitions, see the **`centroid-cnc12-gmcodes`** skill.

#### Speed (p.65)

This field specifies a default spindle speed to use with each tool. Possible values are 0 to
500000. Intercon uses this information to automatically insert an S-code after a tool change. To
change this value, type a new number and press **ENTER** (p.65).

#### Description (p.65)

This field contains a text description of the tool. The description appears in a prompt message
on the screen when the CNC software reaches a tool change (M6) (p.65).

### F5 – Export Lib (p.65)

The tool library can be exported in txt (space-separated and aligned columns) or csv
(comma-separated columns) formats by pressing **F5**. Choose txt or csv to export the desired
format (p.65).

> **Note:** The §5.2 screenshot on p.64 shows this function at F4; the body text on p.65 states
> F5. F5 is used here per the text.

---

## 5.3 Tool Life Management Menu (p.65–69)

(from Main Screen: **F1 – Setup** → **F2 – Tool** → **F3 – Tool Life**)

> **Note:** The §5.3 section heading on p.65 prints the path with "F1 Tool Life"; this appears to
> be a typo. The Ch 5 intro (p.59) clearly lists F3 as Tool Life and F1 as Offset Library.

The Tool Life Management feature allows you to set up each tool's pre-determined life, and to
have its usage tracked and monitored for end-of-life condition. By default, Tool Life Management
is turned off, but can be enabled for each tool individually (p.65).

The Tool Life Management screen (screenshot p.66) shows columns: Tool#, Type, Total Life, Used,
Remaining, Units, Mode, Description.

### Tool Life Management Softkeys (p.66)

| Softkey | Label | Description |
|---|---|---|
| **F1** | Show/Hide Unmanaged | Toggles including/excluding tools whose Total Life is set to 0 (Off). |
| **F2** | Sort Recent | Sorts the list by tools whose Total Life and/or Used field were most recently modified. |
| **F3** | Sort Tool # | Sorts the list by Tool Number. |
| **F4** | Sort Remaining | Sorts the list by Life Remaining. |
| **F10** | Save | Saves changes. |

### Automatic Management Table (p.66)

A tool is set up for automatic management by setting its Mode to Auto and Total Life to a
non-zero value. The following table shows the effects of monitored tool activity (p.66):

| Type | Units | Tool Activity Monitored | Effect on "Used" field |
|---|---|---|---|
| Drill | Cycles | Downward Z-plunge at feed rate at a unique XY location | "Used" field incremented by one cycle |
| Drill | Inch/mm | Downward Z-plunge at feed rate at a unique XY location | Total downward Z-distance (minus overlaps) added to "Used" field |
| EM (End Mill) | Cycles | Tool Change | "Used" field incremented by 1 cycle |
| EM (End Mill) | Inch/mm | Sideways XY feed rate moves (non-rapid) | XY distance accumulated in the "Used" field |

### Tool Life Management Field Definitions (p.67)

#### Type

This is the type of tool — either Drill or EM (End Mill). When Mode is set to Auto, this field
determines the type of tool activity that will be automatically tracked. Note that if the tool is
a Bore or Tap, select Drill (p.67).

#### Total Life

This field specifies the total amount of tool life. A value greater than 0 enables Tool Life
management for the tool. A value of 0 (Off) excludes the tool from Tool Life management — this
is called an "Unmanaged" tool. Unmanaged tools can be shown or hidden by pressing **F1**. The
units are specified in the Units field (p.67).

#### Used

This field is the amount of consumed tool life. When a new tool is first set up, initialize this
field to 0 (zero usage). If Mode is Auto, this field will automatically be modified during a job
run to reflect accumulated tool usage. The units are specified in the Units field (p.67).

#### Remaining (non-edit)

This is the display of the remaining amount of tool life. This field cannot be edited (p.67).

#### Units

This specifies the units (either Cycles or distance) used and displayed for the Total Life, Used,
and Remaining fields. Distance is specified in mm or Inches (as set in the Control Configuration
menu — see Ch 15 / **`centroid-cnc12-config`**) (p.67).

#### Mode

This specifies the update mode of the Used field — either Auto or Manual.

- **Auto:** Tool activity is monitored during a job run and automatically accumulated in the Used
  field (see the Automatic Management table above).
- **Manual:** No automatic updates occur. Updates to the Used field are dependent upon user
  variable modifications programmed in the G-code program being run (see §5.3.2) (p.67).

#### Description

This field contains a text description of the tool. The description appears in a prompt message
on the screen when the CNC software reaches a tool change (M6) during a job run (p.67).

---

### 5.3.1 Effect on Job Run and Backplot (p.67–69)

#### At Start of Job (p.67–68)

Tool life expiration is checked at the beginning of a job run. If any managed tools are expired
at the beginning of a job, the following dialog appears with three choices (p.67–68):

```
Tool life expired:
T1

F1 = Go to the Tool Life Management menu
F2 = Continue to run job   F3 = Cancel job
```

> **Note:** When a job is first started, the CNC software does not yet know which tools will be
> used until the job is successfully completed. Therefore, the tools listed will be all expired
> tools, even if they are not going to be used in the job (p.68).

#### At Job Restart (p.68)

Tool life expirations are also checked upon job restart (i.e., upon encountering M2 or M102).
If any tool(s) expired during the previous job run (previous to the M2 or M102), the dialog
displayed is similar to the above, except that the expired tools listed will only be the ones
that were used in the job (p.68).

> For M2/M102 M-code definitions, see the **`centroid-cnc12-gmcodes`** skill.

#### At End of Job (p.68)

When tool life expires during a job, such an event will not cancel the job. Instead, upon
successful completion of the job, the following dialog appears (p.68):

```
Tool life expired during job:
T1

Go to the Tool Life Management menu?
F1 = Yes   F2 = No
```

This end-of-job dialogue shows only the expired tools that were used in the job (p.68).

#### Using Backplot Graphics to Predict Tool Expirations (p.68–69)

You can use Backplot Graphics to predict ahead of time whether any tools will expire during a
job. Press **F8 – Graph** at the Main Screen or in the Load menu. If the job being graphed would
result in an expired tool, the following message appears (p.68–69):

```
Tool life will expire on this job:
T1
```

---

### 5.3.2 Using G-code User Variables (p.69)

If a tool's Mode field is set to Manual, there will be no updates to the Used field during a job
run unless the job's G-code is programmed to modify it (p.69).

The following G-code user variable accesses a tool's Used Life field (p.69):

```
#[19000+[#4120-1]*5+2]
```

**Example:** Assuming tool T23's Mode is Manual and Units are Cycles, the following G-code
increments T23's Used Life field by one after completing `examplecycle.cnc`:

```
M6 T23                             ; Change tool to T23
M98 "examplecycle.cnc" L1         ; Run the cycle 1 time
IF #4201 || #4202 THEN GOTO 100   ; Skip to N100 if in backplot or search mode
IF #4120 < 1 || #4120 > 200 THEN GOTO 100  ; Skip to N100 if T number not valid
#[19000+[#4120-1]*5+2] = #[19000+[#4120-1]*5+2] + 1  ; Increment Used Life by 1 cycle
N100                               ; Destination of gotos
```

> See Ch 11 for more information about the use of User or System Variables (p.69).

---

## 5.4 Laser Setup (p.69–76)

### 5.4.1 PWM Output for Spindles and Lasers (p.69)

Key facts about the PWM output:

- a. 5-volt PWM output signal is on DB25 pin #14.
- b. DB25 pin #14 is Output 2.
- c. Output 2 is also connected to Relay 2 via the ribbon cable.
- d. If PWM output is used, Relay 2 must be disabled. See schematic S15049 to cut the ribbon
  cable lead to Relay 2.
- e. PWM is based on the 0–100 OR 0–1000 S-command. The user selects the range of 0–100 or
  0–1000 in the Acorn Wizard.
- f. M37 turns ON Laser Output; M38 turns OFF Laser Output:
  - **M37** activates Laser Enable, Laser Reset, and PWM Select. After 0.5s it turns off
    LaserReset. At this point the laser controller looks at the PWM signal from OUTPUT 2.
  - **M38** waits 30s to allow the JTECH laser controller to cool, then performs M95/37/38 to
    turn off both Laser Enable and PWMSelect.
- g. The PWM Velocity Modulation feature adjusts the PWM output based on machine tool velocity
  so that overburning is avoided on corners and turn-arounds. G37 is used to turn ON and OFF
  PWM Velocity Modulation: G37 ON = PWM VM ON; G37 OFF = PWM VM OFF.
- h. Simple PWM controls are located in the Acorn Wizard. In addition to "manual PWM controls",
  preset buttons for common Jtech configurations are present and have matching schematics
  (S15049, S15056, S15057).

> For M37, M38, G37 M-code and G-code definitions, see the **`centroid-cnc12-gmcodes`** skill.

#### PWM Setup Screen Fields (p.70)

Access the PWM Setup screen from the Acorn Wizard under **Spindle → PWM Setup** (screenshot p.70).

| Field | Description |
|---|---|
| **PWM Enable** | Enable or disable PWM output (Yes/No). |
| **Base Frequency (Hz)** | PWM carrier frequency. Min value = 1, max value = 24,000. |
| **Laser PWM S command range** | Selects whether S-command range is 0–100 or 0–1000. |
| **PWM minimum S command power level to start Laser** | Minimum S-command value that activates the laser. |
| **Inverse Output** | Inverts the PWM output signal (Yes/No). |

**Common J Tech Laser Configuration Presets (p.70):**

| Preset | Description |
|---|---|
| Jtech Laser (Dedicated Laser Machine, No spindle motor) | Laser-only machine with no spindle. |
| Jtech Laser with PWM BLDC spindle | Machine with both laser and PWM BLDC spindle motor. |
| Jtech Laser with analog output AC spindle motor controlled by VFD | Machine with laser and VFD-controlled AC spindle. |

---

### 5.4.2 PWM-related I/O in the Wizard (p.70)

Configure the following output functions in the Wizard under **Primary System → Output Definitions**
(screenshot p.71):

| I/O Function | Description |
|---|---|
| **PWM Output** | The PWM signal itself. Can only be used on Output 2 (DB25 pin #14). Related CNC code is the S-command. |
| **LaserEnable** | Typically used in a safety interlock circuit (see Jtech schematic S15049). M37 enables safety interlock and resets laser; M38 disables safety interlock after a delay to allow the component to cool down. |
| **LaserReset** | Momentary output used to send a reset signal to the laser controller. See Jtech schematic S15049 as an example. |
| **PWMSelect** | Output used to move the PWM signal from Spindle to Laser. When deactivated, PWM signal goes to the Spindle. When activated, PWM signal goes to the Laser. See schematic S15057 (BLDC Spindle + Jtech Laser) for an example. |

**Wiring schematics referenced in Ch 5 (p.71–74):**

| Schematic | Title |
|---|---|
| S15049 (p.72) | J-TECH PHOTONICS LASER |
| S15056 (p.72) | J-TECH PHOTONICS LASER, GENERIC VFD ENABLE-DIRECTION |
| S15057 (p.73) | J-TECH PHOTONICS LASER, BLDC SPINDLE CONTROL (NOVUSUN NVBL+) |
| S15061 (p.73) | OBT LASER |
| S15062 (p.74) | NEJE LASER |
| S15063 (p.74) | COMCROW D-B500F LASER |

> **Note:** Schematic diagrams are reproduced in the manual at p.71–74. Cite the document page
> number when referencing a specific wiring diagram.

---

### 5.4.3 ZigZagSyncTest Instruction (p.75)

**Requirements:** Acorn CNC12 v4.6+ Mill or Router.

These test programs are included with the installation:

```
ZigZagLaserSyncTest-X_Axis.cnc
ZigZagLaserSyncTest-Y_Axis.cnc
```

### 5.4.4 Purpose (p.75–76)

These two programs test for and adjust backlash in laser table axes. The program creates four
lines in either the X- or Y-direction by moving back and forth in that axis while firing the
laser in short 0.006 inch pulses at specific points in each direction (p.75).

**Interpreting results (p.75–76):**

- **Good alignment:** Four separate vertical lines that are straight and aligned (see photo p.75).
- **Backlash present:** Lines appear as clusters of "dots" offset when direction changes (see
  photo p.76). Each "dot" is 0.006 inches long; use this as a reference to estimate the backlash
  compensation adjustment needed.

**Procedure to correct backlash:**

1. Run the ZigZagSyncTest program and observe the result.
2. Use the Acorn Wizard to adjust the backlash compensation for the affected axis.
3. Run the program again to determine if more or less compensation is needed (p.76).

> For backlash compensation parameter details, see the **`centroid-cnc12-config`** skill (Ch 15).

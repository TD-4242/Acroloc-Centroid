# CNC12 Part Setup: Part Zeros, Work Coordinate Systems, and CSR

Set part zeros, configure work coordinate systems (WCS), rotate the coordinate system (CSR), and
enable transformed WCS (TWCS) for Articulated Head machines.
Source: operator manual Ch 4 (Part Setup).

## 4.1 Operation Description

The Part Setup menu is used to set the part position or the coordinate system origin for the part
(p.48). Access via **F1 – Setup** → **F1 – Part** from the main screen (see `interface.md`
§F1–Setup for the Setup menu map). Setting the part position establishes a coordinate system with
an origin at the part zero.

The **F1 – Next Axis** option selects the axis to be defined next. This field toggles between
X-, Y-, Z-, 4th-, and 5th-axes. For each axis, a graphical description of the parameters to be
entered and the corresponding fields is shown (p.49).

### Part Setup Screen Softkeys (p.48)

| Softkey | Label | Description |
|---|---|---|
| **F1** | Next Axis | Toggles to the next axis (X → Y → Z → 4th → 5th). If changes were made to the current axis but not yet accepted, they will be discarded. |
| **F4** | Auto | Uses the probe to automatically measure and set part position. Make sure probe height and diameter offsets are set for the assigned probe tool number, and that Parameter 12 is set to that tool number. See Ch 9. |
| **F5** | Probe | Opens the probing operations menu. See Ch 9 for details. |
| **F6** | Prev WCS | Selects the previous work coordinate. The position being set will only affect the currently-selected work coordinate. |
| **F7** | Next WCS | Selects the next work coordinate. The position being set will only affect the currently-selected work coordinate. |
| **F8** | CSR | Opens the CSR menu for automatic coordinate system rotation detection. This key only appears when the Coordinate System Rotation software option is unlocked. |
| **F9** | WCS Table | Opens the Work Coordinate System (WCS) Configuration screen. See §4.3. |
| **F10** | Set | Accepts the position for the current axis, correcting for edge finder diameter based on the approach direction (if appropriate). Does not automatically advance to the next axis. |

> **Note:** F4 – Auto and F5 – Probe invoke probing workflows. For the full probing reference, see
> the **`centroid-cnc12-intercon-probing`** skill and Ch 9.

The currently-selected coordinate system is displayed below the axis picture on the Part Setup
screen and above the DRO at all times (p.51).

### 4.1.1 Setting Up X- or Y-axis (p.49)

**Set Part Position procedure:**

1. Select Axis with **F1**
2. Jog to Touch-off on Part
3. Edit the Value if Necessary
4. Press **F10** to Set Position

Fields for X/Y axes:

| Field | Description |
|---|---|
| **Part Position** | Enter the value of your part zero position or the offset. |
| **Edge Finder Diameter** | Enter the diameter of the tool or edge finder being used to determine the part zero. The value entered is stored. |
| **Approach From** | Toggle the direction that the edge finder or probe will be approaching the part from. |

> **Note:** Use the arrow keys to toggle between Part Position, Edge Finder Diameter, and
> Approach From options (p.50).

### 4.1.2 Setting Up the Z-axis (p.50)

**Set Part Position procedure:**

1. Select Axis with **F1**
2. Jog to Touch Off on Part
3. Edit the Value if Necessary
4. Press **F10** to Set Position

Fields for Z-axis:

| Field | Description |
|---|---|
| **Part Position** | Enter the value of your part zero position or the offset. |
| **Tool Number** | Enter the tool number from the Tool Library corresponding to the tool in use. When set to a value other than zero, the controller uses the Height Offset for that tool from the Tool Library to calculate the actual position. |

**Z-axis Tool Number examples (p.50):**

- **Example 1 (reference tool):** Set Tool Number to 0: setting the Tool Number to zero tells the
  controller that you are using the reference tool.
- **Example 2 (non-reference tool, not a ball nose cutter):** Set Tool Number to a Tool Number
  that is assigned in the tool library (make sure its height offset is set).
- **Example 3 (ball nose cutter, other than the reference tool):** Set Part Position to the
  position of the surface plus the nose radius of the ball nose cutter. Set Tool Number to the
  number that this tool is assigned in the tool library.

> The Tool and Offset libraries must be up-to-date before setting the Z-axis Part Zero (p.50).

### 4.1.3 Setting Up the 4th- or 5th-axis (p.51)

**Set Part Position procedure:** same four-step sequence as §4.1.1.

Field for rotary axes:

| Field | Description |
|---|---|
| **Position** | Enter the value of your part zero position or the offset. |

### 4.1.4 Using Multiple Work Coordinate Systems (p.51)

If using multiple work coordinates, set the part position separately for each work coordinate:

1. Set the position for each axis in the first coordinate system.
2. Move to the next fixture.
3. Press **F6 – Prev WCS** or **F7 – Next WCS** to select the desired work coordinate.
4. Set positions for the new coordinate system.

The currently-selected coordinate system is displayed below the axis picture on the Part Setup
screen and above the DRO at all times. For a complete description of setting up each work
coordinate, see the Work Coordinate System Configuration section (§4.3).

> **NOTICE:** This procedure does NOT apply to tilt table setup (p.51).

---

## 4.2 Part Setup Examples (p.51–53)

### Example 1: Setting the X-axis Part Zero with No Offset (p.51–52)

Scenario: set the left edge of the part as the X-axis origin, using a 0.25" diameter edge finder
approaching from the left (−X) side.

Steps:
1. Move the Edge Finder to the left edge of the part.
2. Press **F1 – Next Axis** until the Axis label displays 'X'.
3. Move the cursor to the Edge Finder Diameter field.
4. Type `.25` and press **ENTER**.
5. Press **SPACE** until `Left (-)` is displayed.
6. Press **F10 – Set** to accept the values.

Resulting field values:

| Axis | Part Position | Edge Finder Diameter | Approach From |
|---|---|---|---|
| X | 0 | 0.25 | Left (−) |

Since no offset is being applied, Part Position is zero. Once **F10 – Set** is pressed, the X-axis
DRO will read −0.125. The center of the Edge Finder is sitting to the left (minus) of the part by
0.125 inches (half the Edge Finder Diameter).

Formula: `Position (Approach from) Edge Finder Diameter / 2`

Where (Approach from) is the sign of the approach direction. If the approach direction is minus,
then the value is: `Position − Edge Finder Diameter/2 = 0.0 − .25/2 = −0.125` (p.52).

### Example 2: X-axis Origin Offset Into the Part by One Inch (p.52–53)

Scenario: set the X-axis origin 1 inch inside the part from the left edge, using a 0.25" diameter
edge finder approaching from the left (−X) side.

Steps:
1. Move the Edge Finder to the left edge of the part.
2. Press **F1 – Next Axis** until the axis field displays 'X'.
3. Move the cursor to the Part Position field.
4. Type `-1` and press **ENTER**.
5. Type `0.25` and press **ENTER**.
6. Press **SPACE** until `Left (-)` is displayed.
7. Press **F10 – Set** to accept the value.

Resulting field values:

| Axis | Part Position | Edge Finder Diameter | Approach From |
|---|---|---|---|
| X | −1 | 0.25 | Left (−) |

The position value is relative to the current position of the Edge Finder. Part Position equals
−1.0 since the Edge Finder is positioned one inch to the left (minus direction) of where you want
the X-axis origin. Once **F10 – Set** is pressed, the X-axis DRO will read −1.125. The X-axis
origin is now one inch into the part.

Formula: `Position − Edge Finder Diameter/2 = −1.0 − .25/2 = −1.125` (p.53).

---

## 4.3 Work Coordinate Systems (WCS) Configuration (p.53–56)

Press **F9 – WCS Table** from the Part Setup screen to display the Work Coordinate System (WCS)
Configuration screen (p.53). This screen provides access to reference return points, coordinate
system origins, and work envelope. Make sure the Home position has been set properly; otherwise,
the positions of each coordinate system will not be in the appropriate position.

When entering the Work Coordinate System Configuration screen, the DRO display will automatically
switch to machine coordinates as an aid to entering numbers. All values on this screen are
represented in machine coordinates (p.53).

### WCS Table: F1 – Reference Return Points (p.53–54)

Press **F1 – Reference Return Points** to access the menu that sets the reference return points for
the machine. These points are used with the G28 and G30 codes (see Ch 12 and
`centroid-cnc12-gmcodes`). They are specified in machine coordinates. The Z-coordinate of the
first reference point is also used as a Z-home position by the M2, M6, and M25 codes
(see Ch 13) (p.54).

Reference return point columns:

| Column | G-code |
|---|---|
| Return #1 | G28 |
| Return #2 | G30 |
| Return #3 | G30 P3 |
| Return #4 | G30 P4 |

**F2 – Teach:** Copies current axis machine coordinate values to the table (p.54).

### WCS Table: F2 – Origin (p.54–55)

Press **F2 – Origin** to access the menu for specifying the locations (in machine coordinates) of
the origins for all 18 Work Coordinate Systems (p.54). All coordinate systems are relative to the
Home position set during control power-up.

If the Coordinate System Rotation software option is unlocked, the CSR angle for each coordinate
system can also be set. For Articulated Head machines with the TWCS feature enabled (via
Parameter 166), the TWCS=Yes/No setting differentiating which WCSs are transformed is also shown.

**Available Work Coordinate Systems (p.55):**

Regular WCS (standard):

| WCS | G-code |
|---|---|
| WCS #1 | G54 |
| WCS #2 | G55 |
| WCS #3 | G56 |
| WCS #4 | G57 |
| WCS #5 | G58 |
| WCS #6 | G59 |

Extended WCS (extra-cost option), WCS #7–#18:

| WCS | G-code | WCS | G-code |
|---|---|---|---|
| WCS #7 | G54 P1 | WCS #13 | G54 P7 |
| WCS #8 | G54 P2 | WCS #14 | G54 P8 |
| WCS #9 | G54 P3 | WCS #15 | G54 P9 |
| WCS #10 | G54 P4 | WCS #16 | G54 P10 |
| WCS #11 | G54 P5 | WCS #17 | G54 P11 |
| WCS #12 | G54 P6 | WCS #18 | G54 P12 |

The DRO always displays the tool position from the WCS currently in use. The currently-active WCS
is shown in the upper-left corner of the screen above the DRO (p.55).

**To change the WCS in use (p.55):**
- From the main screen, press **F1 – Setup**, **F1 – Part**.
- Press **F6 – Prev WCS** or **F7 – Next WCS**; the WCS number in the upper-left corner changes.

These different part zero positions are typically used to reduce setup and/or programming time.
Regular WCS #1–6 are standard; extended WCS #7–18 are an extra-cost option.

> For G-code syntax and the definition of work coordinate codes (G54–G59, G54 Pn), see the
> **`centroid-cnc12-gmcodes`** skill (Ch 12).

**WCS Origin sub-screen softkeys (p.55):**

| Softkey | Label | Description |
|---|---|---|
| **F1** | Next Table | Cycles through viewing the other WCS (six per page). |
| **F2** | Lock/Unlock Table | Locks or unlocks WCS tables from editing (see Parameter 45). |
| **F3** | +.001 | Increases existing cell values by 0.001 inches (0.01 mm for metric installations). |
| **F4** | −.001 | Decreases existing cell values by 0.001 inches (0.01 mm for metric installations). |
| **F5** | Abs/Inc | Cycles between Absolute and Incremental modes for altering existing cell values. |
| **F6** | Copy | Copies cell/column contents. |
| **F7** | Paste | Pastes cell/column contents. |
| **F8** | Clear Cell or Column | Clears cell/column contents. |
| **F10** | Save | Saves the current WCS table configuration. |

### WCS Table: F3 – Work Envelope (p.56)

Use **F3 – Work Envel** to specify the '+' and '−' work envelope locations (in machine
coordinates) used with the G22 G-code. The X, Y, Z and I, J, K parameters specified in the G22
G-code are stored here, so subsequent G22 codes do not need to specify the limits unless they
change (p.56).

> **Note:** The work envelope will only work in programmed moves. You will still be able to jog
> outside the work envelope (p.56).

> For G22 G-code syntax and behavior, see the **`centroid-cnc12-gmcodes`** skill.

---

## 4.4 Coordinate System Rotation (CSR) (p.56–57)

Coordinate System Rotation saves setup time. Rather than physically indicating the edge of
material to square it with the machine axes, CSR automatically rotates the coordinate system to
the angle of the part or fixture that was probed (p.56).

Press **F8 – CSR** from the Part Setup screen (only appears when the CSR software option is
unlocked) to enter the CSR menu.

**Procedure:** Clamp the part, then probe two points along either the X- or Y-axis of the material
using the process described on screen (p.56).

### CSR Screen Softkeys (p.57)

| Softkey | Label | Description |
|---|---|---|
| **F1** | Orient | Selects the orientation for the CSR measurement: front (pictured), back, left, or right sides. |
| **F2** | Manual | Determines the CSR angle without probing. The user jogs an edge finder to two positions along one wall; these positions are used to compute the CSR angle. |
| **F3** | Zero Cur | Sets the CSR angle for the current WCS to zero. |
| **F4** | Zero All | Sets all CSR angles to zero. |
| **F5** | Probe | Opens the probing operations menu. See Ch 9 and `centroid-cnc12-intercon-probing` for details. |
| **F6** | Prev WCS | Cycles through the available WCS systems (backward). |
| **F7** | Next WCS | Cycles through the available WCS systems (forward). |
| **F8** | MDI | Opens the MDI menu to run a single line command (e.g., `G1 X2 Y3 F20`). |
| **F9** | WCS Table | Shortcut to the Work Coordinate System Configuration screen (§4.3). |
| **F10** | Accept | Accepts the CSR measurement result. |

### CSR Measurement Fields (p.57)

| Field | Description |
|---|---|
| **Distance** | The distance the X-axis (front or back orientation) or Y-axis (right or left orientation) will move to probe the second point. If the distance is negative, the axis will move in the negative direction. |
| **Clearance Amount** | The distance the Z-axis will be moved upward when moving between the first and second probe points. The clearance move is only made when using the "Auto" option of Movement Between Points. |
| **Movement Between Points** | Toggleable between Jog and Auto modes. In Auto mode, the clearing moves and movement to the second point are made automatically. In Jog mode, a prompt is displayed in the center of the screen after the first point is probed. |

**Manual CSR procedure (on-screen instructions, p.57):**
1. Jog probe to FIRST position along wall.
2. Press **F10** to accept FIRST position.
3. Jog probe to SECOND position along wall.
4. Press **F10** to accept SECOND position.

The instructions on how to perform a CSR measurement are numbered on the screen (p.57).

---

## 4.5 Transformed WCS (TWCS=Yes) (p.58)

This section only applies to Articulated Head machines with the TWCS feature enabled via
Parameter 166 (see Ch 15 and `centroid-cnc12-config` for Parameter 166 details). On such a
machine, when a WCS has a setting of TWCS=Yes, this is called a transformed WCS (abbreviated
TWCS) (p.58).

When a TWCS is selected:
- The DRO shows axis positions based on the TWCS's frame of reference: positions are transformed
  based on the position of the B-axis (5th-axis).
- The WCS label in the upper-left corner of the screen displays "TWCS" to indicate that the
  currently-selected WCS is transformed.
- When Probing Cycles are run with a TWCS selected, the results shown are based on the TWCS
  frame of reference.

**Move types automatically transformed** when running a CNC program with a TWCS selected (p.58):
- G0, G1, G2, and G3
- Protected move probing functions M115, M116, M125, and M126
- Canned Cycles G73, G74, G76, G81, G82, G83, G84, G85, and G89
- M25
- Moves that involve CSR and Cutter Compensation

**Move types NOT transformed (p.58):**
- Homing moves M91/M92
- Move to switch M105/M106
- Move axis by counts M128

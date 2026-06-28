# M-series Operator Panel Controls, VCP, and Keyboard Interface

Hardware panel controls (§2.1–2.24), Virtual Control Panel (§2.25), keyboard jog panel
(§2.26), and keyboard shortcut keys (§2.28).
Source: operator manual Ch 2.

> **Note:** The behavior of the control system in response to the functions listed in this
> chapter is dependent upon optional software settings, the PLC program, machine parameters,
> and hardware wiring of the system. It is possible that the functioning explained here does
> not apply to a particular control system, or that it may differ in some aspects (p.22).

## Panel Overview

The M-series Operator Panel is a sealed membrane keyboard that enables you to control
various machine operations and functions. The panel contains momentary membrane switches.
The M-series jog panel can be customized as to the location of various keys. The panel
layout shown in the operator manual (p.18) is representative of a default configuration
found on most M-series controls.

The panel is divided into three main areas:
- **Spindle Control** — speed, direction, start/stop, auto/manual mode
- **Axis Motion Controls** — jog mode selection, increment selection, MPG, axis jog buttons
- **Auxiliary Controls** — AUX function keys, coolant
- **Bottom section** — Emergency Stop (large button), Feed Rate Override (knob)

## 2.1 Axis Jog Buttons

**X+  X−  Y+  Y−  Z+  4th+  4th−**

The yellow X, Y, Z, and 4th keys are momentary switches for jogging each of the four axes.
There are two buttons for each axis (+/−). Only one axis can be jogged at a time (p.19).

> **Note:** The jog buttons will not operate if the M-series CNC software is not running or
> if a job (a CNC program) is running.

## 2.2 Slow/Fast

The **Slow/Fast** key is located in the center of the Axis Motion Controls section and is
labeled with a turtle and rabbit icon. The turtle represents slow jogging mode. When SLOW
jog is selected (LED on) and a jog button is pressed, the axis moves at the slow jog rate.
If FAST jog is selected, the axis moves at the fast jog rate (p.19).

> See Chapter 15 (and `centroid-cnc12-config`) for information on setting the fast and slow
> jog rates for each axis.

## 2.3 Inc/Cont

**INC/CONT** selects between incremental and continuous jogging. Pressing the key toggles
between the two modes. The LED is lit when INC is selected. If CONT jog is selected and an
axis jog button is pressed, the axis moves continuously until the button is released (p.19).

## 2.4 x1, x10, x100

Press any one of these keys to set the jog increment amount. The selected amount is the
distance the control moves along an axis for each incremental jog press (p.19):

| Key | Increment |
|---|---|
| x1 | 0.0001" |
| x10 | 0.0010" |
| x100 | 0.0100" |

Only one jog increment can be selected at a time; the current selection is indicated by the
lit LED. The jog increment applies to all axes; separate per-axis increments cannot be set.
The jog increment also sets the distance the control moves per click of the MPG handwheel.

## 2.5 MPG

The MPG is housed in a separate hand-held unit. Press the **MPG** key to set the control
jog to respond to the MPG hand wheel (if equipped). When selected, the LED is on. Select
the Jog Increment and desired axis, and slowly turn the wheel. When the LED is not lit, the
MPG is disabled and the jog panel is on (p.19).

## 2.6 Single Block

The **SINGLE BLOCK** key selects between auto and single block mode (p.19).

| LED State | Mode | Behavior |
|---|---|---|
| On | Single Block | Program executes one block at a time; press **CYCLE START** after each block |
| Off (default) | Auto | Loaded program runs continuously after **CYCLE START** is pressed |

While in single block mode you can select auto mode at any time. While in auto mode with
a program running, you cannot select single block mode.

## 2.7 Cycle Start

When the **CYCLE START** button is pressed, the M-series Control immediately begins
processing the current program and prompts you to press **CYCLE START** again to begin
execution. After an M0, M1, M2, or M6 is encountered in the program, the message "Press
CYCLE START to continue" is displayed and the control waits until **CYCLE START** is
pressed before continuing (p.20).

> **WARNING:** Pressing **CYCLE START** will cause the M-series Control to start moving the
> axes immediately without further warning. Be certain that you are ready to start the
> program when you press this button. Pressing the **FEED HOLD**, **E-STOP**, or
> **CYCLE CANCEL** buttons will stop any movement if **CYCLE START** is pressed accidentally.

## 2.8 Feed Rate Override

This knob controls the percentage of the programmed Feed Rate used during feed rate cutting
moves (lines, arcs, canned cycles, etc.). This percentage can be from 0% to 200% (p.20).

> **CAUTION:** The Feed Rate Override knob will not work during tapping cycles (G74 and
> G84). See `centroid-cnc12-gmcodes` for tapping cycle details.

## 2.9 Feed Hold

**Feed Hold** decelerates the motion of the current movement to a stop, pausing the job
that is currently running. Pressing **CYCLE START** continues the movement from the stopped
location (p.20).

> **CAUTION:** **Feed Hold** is temporarily disabled during tapping cycles (G74 and G84),
> and automatic tool changes (M6).

## 2.10 Tool Check

Press **TOOL CHECK** while no program is running to move the Z-axis to its home
position/G28 position. Press **TOOL CHECK** while a program is running to abort the
currently-running program. The control will stop normal program movement, pull Z to its
home position, clear all M-functions, and automatically display the Resume Job Screen. From
the Resume Job Screen you can change tool settings (height offsets, diameter offsets, etc.)
and resume the job with the new tool settings (p.20).

## 2.11 Cycle Cancel

Press **CYCLE CANCEL** to abort the currently-running program. The control stops movement
immediately, clears all M-functions, and returns to the Main Screen (p.20).

> **Note:** It is recommended to press **FEED HOLD** first before **CYCLE CANCEL**. If
> **CYCLE CANCEL** is pressed, program execution stops; to restart the program you must
> rerun the entire program or use the search function (see Ch 3 or Ch 6).

## 2.12 Emergency Stop

**EMERGENCY STOP** releases the power to all of the axes and cancels the current job
immediately upon being pressed. **EMERGENCY STOP** also resets certain faults if the fault
condition has been fixed or cleared (p.21).

> **WARNING:** On some machines, vertical axes (such as Z and/or W) may start to move due
> to gravity pulling them down when motor power is cut due to **EMERGENCY STOP** being
> pressed.

## 2.13 Spindle CW/CCW

The **SPINDLE CLOCKWISE/COUNTERCLOCKWISE** keys determine the direction that the spindle
will turn if it is started manually. If the spindle is started automatically, the direction
keys are ignored and the spindle runs according to the program. The default direction is CW
(p.21).

## 2.14 Spindle Speed +

| Mode | Effect |
|---|---|
| Auto Spindle mode | Increases spindle speed by 10% of the commanded speed (limited by the maximum speed or 200% of commanded speed, whichever is less) |
| Manual Spindle mode | Increases spindle speed by 5% of the maximum spindle speed (up to the maximum speed) |

This key's LED turns on if the spindle speed is set above the 100% point (p.21).

## 2.15 Spindle Speed 100%

Pressing this key sets the spindle speed at the 100% point (p.21):

| Mode | 100% Definition |
|---|---|
| Auto Spindle mode | The commanded speed |
| Manual Spindle mode | 1/2 the maximum spindle speed |

This key's LED turns on when the spindle is at the 100% point.

## 2.16 Spindle Speed −

| Mode | Effect |
|---|---|
| Auto Spindle mode | Decreases spindle speed by 10% of the commanded speed (limited to 10% of the commanded speed) |
| Manual Spindle mode | Decreases spindle speed by 5% of the maximum spindle speed (down to 5% of the maximum spindle speed) |

The LED turns on if the spindle speed is set below the 100% point (p.21).

## 2.17 Spindle Auto/Man

This key selects whether the spindle operates under program control (automatic) or operator
control (manual). Pressing the **SPINDLE (AUTO/MAN)** key toggles between Automatic and
Manual modes. The default is AUTO mode (p.21).

| LED State | Mode | Meaning |
|---|---|---|
| On | Automatic | The spindle is under automatic control |
| Off (default) | Manual | The spindle is under manual control |

## 2.18 Spin Start

Press the **SPIN START** key when manual spindle mode is selected to cause the spindle to
start rotating. Press the **SPIN START** key when automatic mode is selected to restart the
spindle if it has been paused with the **SPIN STOP** key (p.22).

## 2.19 Spin Stop

Press the **SPIN STOP** key when manual spindle mode is selected to stop the spindle. Press
the **SPIN STOP** key when automatic spindle mode is selected to pause spindle rotation. The
spindle can be restarted with the **SPIN START** key (p.22).

> **NOTICE:** The **SPIN STOP** key should only be pressed during **FEED HOLD** or when a
> program is NOT running.

## 2.20 Coolant Auto/Manual

This key toggles between automatic and manual control of coolant (p.22):

| Mode | Behavior |
|---|---|
| Automatic | M7 (Mist) and M8 (Flood) can be used in G-code programs to select the coolant type |
| Manual | Flood coolant and mist coolant are controlled by separate keys (§2.21, §2.22) |

> **Note:** When switching from automatic to manual mode, both flood and mist coolants are
> turned off automatically.

## 2.21 Coolant Flood

In manual coolant control mode, flood coolant can be toggled off and on by pressing this
key. The LED is on when flood control is selected in either automatic or manual mode (p.22).

## 2.22 Coolant Mist

In manual coolant control mode, mist coolant can be toggled off and on by pressing this
key. The LED is on when mist control is selected in either automatic or manual mode (p.22).

## 2.23 Auxiliary Function Keys (AUX1–AUX12)

The M-series jog panel has 12 Auxiliary Keys (9 labeled on the default panel), some of
which may be defined by customized systems (p.22). A custom PLC program is required to act
upon jog panel Auxiliary Key signals.

## 2.24 Notes About Operator Panels

The behavior of the control system in response to the functions listed above for the
M-series jog panel is dependent upon optional software settings, the PLC program, machine
parameters, and hardware wiring of the system. It is possible that the functioning
explained in this chapter does not apply to a particular control system, or that it may
differ in some aspects (p.22).

---

## 2.25 VCP Introduction

The Virtual Control Panel (VCP) allows the user to use a mouse and/or a touch screen
monitor to activate the CNC Control Operator Interface Panel. The VCP has been designed
from the ground up to allow users, re-builders, and OEMs a simple way to change the look,
feel, and function of the VCP (p.23).

CNC12 automatically installs the default Centroid VCP skin. Users can use the default VCP
"as-is", or modify it by reading the VCP Manual (linked from the CNC12 help system).

The following table describes the function of each VCP button (p.23–27):

| Function | Description |
|---|---|
| 4th+ Jog | Jogs the 4th-axis positively |
| 4th− Jog | Jogs the 4th-axis negatively |
| Toggle Auto Coolant | Toggles coolant mode between auto and manual |
| Toggle Spindle Auto/Manual | Toggles between automatic and manual spindle operation mode |
| Cycle Start | Same as Cycle Start |
| Cycle Cancel | Same as Cycle Cancel |
| Spindle Override Percentage | Displays the percentage of the default spindle speed that the spindle is currently operating at |
| Spindle Override +1% | Increase the spindle override by 1% while held |
| Spindle Override −1% | Decrease the spindle override by 1% while held |
| Feed Hold | Temporarily pauses the feed rate |
| Single Block | Selects Single Block Mode |
| Tool Check | Performs a tool check |
| VCP Options | Allows the user to edit VCP Settings |
| Push to Free | Used to unpin the VCP window, allowing the user to move it around their screen |
| Push to Pin | Used to pin the VCP, preventing it from being moved from its pinned location |
| Emergency Stop | Same as Emergency Stop |
| Increase/Decrease Feed Rate Override | Increase/Decrease feed rate override by 1% while held |
| Incremental/Continuous Jog Selection | Toggles incremental or continuous jog mode |
| Toggle Work Light | Toggles the work light between ON and OFF positions |
| Limit Switch Defeat | Overrides the limit switches when active |
| Selects CW Spin | Selects CW Spin direction in manual mode |
| Selects CCW Spin | Selects CCW Spin direction in manual mode |
| Toggle Mist Coolant | Toggles Mist coolant if in manual mode |
| Toggle Flood Coolant | Toggles Flood coolant if in manual mode |
| Vac On | Toggles the vacuum between on and off positions |
| M Functions (M55, M56, M57, M58) | Used to toggle M-functions |
| Toggle MPG | Toggles between the MPG and jog panel |
| Park | Parks the machine in its current position |
| Rapid Override | Toggles rapid jog movement override |
| Reset Home | Resets the home values that are currently set |
| Set All 0 | Sets all axes to zero values |
| Set Axis 0 | Sets the currently-selected axis to a value of zero |
| Slow/Fast | Toggles between slow and fast jogging modes |
| Spindle Brake | Toggles the spindle brake |
| Spindle Speed (SPIN HIGH / SPIN MED / SPIN LOW) | Allows the user to select the spindle speed (high, medium, and low) |
| Spin Start | Starts spindle in selected direction if in manual mode |
| Spin Stop | Stops spindle regardless of auto or manual mode |
| Decrease/Increase Jog Increment | Decreases/increases current jog increment to the next available increment |
| X+ Jog | Jogs the X-axis positively |
| X− Jog | Jogs the X-axis negatively |
| Y+ Jog | Jogs the Y-axis positively |
| Y− Jog | Jogs the Y-axis negatively |
| Z+ Jog | Jogs the Z-axis positively |
| Z− Jog | Jogs the Z-axis negatively |

---

## 2.26 Keyboard Jog Panel

The PC keyboard may be used as a jog panel. Press **ALT-J** to display and enable the
keyboard jog panel (p.28).

- Some controls — coolant on/off, spindle on/off, feed rate, and spindle override — work
  without the jog panel displayed on screen.
- For full functionality (including jogging), the jog panel must be displayed on screen.
  To enable keyboard jogging, **Parameter 170** must be set to "1".
- The status window in the upper-right corner of the screen displays the jogging mode
  (continuous/incremental), incremental step size, and jog speed (fast/slow).
- In **continuous mode**: jog keys start movement when pressed and stop movement when
  released.
- In **incremental mode**: the axis moves the indicated incremental step amount.
- The jog keys are located in the cursor key block to the right of the main keyboard and to
  the left of the numeric keypad. If a jog key controls an axis, it is overlaid with the
  axis symbol ("X", "Y", etc.). The jog keys are the **Arrow**, **Page Up**, and
  **Page Down** keys.

| Key(s) | Function | Description | Availability |
|---|---|---|---|
| **ALT+J** | Start/Exit Keyboard Jogging | Invokes or exits the keyboard jogging panel | Always, with few exceptions |
| **ALT+S** | Cycle Start | Same as Cycle Start | Always, with few exceptions |
| **ESC** | Cycle Cancel | Same as Cycle Cancel | During a job; Otherwise, Esc is used to exit menus |
| **CTRL+F1** | Aux 1 | Executes functions defined to Aux 1 Key. A custom PLC program is required to act upon jog panel signals | Always, with few exceptions |
| **CTRL+F2** | Aux 2 | Executes functions defined to Aux 2 Key. A custom PLC program is required to act upon jog panel signals | Always, with few exceptions |
| **CTRL+F3** | Aux 3 | Executes functions defined to Aux 3 Key. A custom PLC program is required to act upon jog panel signals | Always, with few exceptions |
| **CTRL+F4** | Aux 4 | Executes functions defined to Aux 4 Key. A custom PLC program is required to act upon jog panel signals | Always, with few exceptions |
| **CTRL+F5** | Aux 5 | Executes functions defined to Aux 5 Key. A custom PLC program is required to act upon jog panel signals | Always, with few exceptions |
| **CTRL+F6** | Aux 6 | Executes functions defined to Aux 6 Key. A custom PLC program is required to act upon jog panel signals | Always, with few exceptions |
| **CTRL+F7** | Aux 7 | Executes functions defined to Aux 7 Key. A custom PLC program is required to act upon jog panel signals | Always, with few exceptions |
| **CTRL+F8** | Aux 8 | Executes functions defined to Aux 8 Key. A custom PLC program is required to act upon jog panel signals | Always, with few exceptions |
| **CTRL+F9** | Aux 9 | Executes functions defined to Aux 9 Key. A custom PLC program is required to act upon jog panel signals | Always, with few exceptions |
| **CTRL+F10** | Aux 10 | Executes functions defined to Aux 10 Key. A custom PLC program is required to act upon jog panel signals | Always, with few exceptions |
| **CTRL+F11** | Aux 11 | Executes functions defined to Aux 11 Key. A custom PLC program is required to act upon jog panel signals | Always, with few exceptions |
| **CTRL+F12** | Aux 12 | Executes functions defined to Aux 12 Key. A custom PLC program is required to act upon jog panel signals | Always, with few exceptions |
| **CTRL+M** | Toggle Auto Coolant | Toggles coolant mode between auto and manual | Always, with few exceptions |
| **CTRL+N** | Turns Flood Coolant | Toggles Flood coolant if in manual mode | Always, with few exceptions |
| **CTRL+K** | Toggle Mist Coolant | Toggles Mist coolant if in manual mode | Always, with few exceptions |
| **CTRL+** | Increase Feedrate Override | Increase feed rate override by 1% while held | Jog panel, job run, graphing, and some other times |
| **CTRL−** | Decrease Feedrate Override | Decrease feed rate override by 1% while held | Jog panel, job run, graphing, and some other times |
| **CTRL+C** | Selects CW Spin | Selects CW Spin direction in manual mode | Always, with few exceptions |
| **CTRL+W** | Selects CCW Spin | Selects CCW Spin direction in manual mode | Always, with few exceptions |
| **CTRL+A** | Toggle Spindle Auto/Manual | Toggles between automatic and manual spindle operation mode | Always, with few exceptions |
| **CTRL+S** | Spindle Start | Starts spindle in selected direction if in manual mode | Always, with few exceptions |
| **CTRL+Q** | Spindle Cancel | Stops spindle regardless of auto or manual mode | Always, with few exceptions |
| **CTRL+>** | Spindle Override +1% | Increase the spindle override by 1% while held | Always, with few exceptions |
| **CTRL+<** | Spindle Override −1% | Decrease the spindle override by 1% while held | Always, with few exceptions |
| **CTRL+T** | Tool Check | Performs a tool check | Always, with few exceptions |
| **CTRL+I** | Incremental/Continuous Jog Selection | Toggles incremental or continuous jog mode | Available most times that jogging is available |
| **CTRL+B** | Selects Single Block Mode | Selects Single Block Mode | Always, with few exceptions |
| **DELETE / INSERT** | Decrease/Increase Jog Increment | Decreases/increases current jog increment to the next available increment | Always, with few exceptions |
| **CTRL+Right Arrow** | X +Jog | Jogs the X-axis positively | With on-screen jog panel displayed |
| **CTRL+Left Arrow** | X −Jog | Jogs the X-axis negatively | With on-screen jog panel displayed |
| **CTRL+Up Arrow** | Y +Jog | Jogs the Y-axis positively | With on-screen jog panel displayed |
| **CTRL+Down Arrow** | Y −Jog | Jogs the Y-axis negatively | With on-screen jog panel displayed |
| **CTRL+Page Up** | Z +Jog | Jogs the Z-axis positively | With on-screen jog panel displayed |
| **CTRL+Page Down** | Z −Jog | Jogs the Z-axis negatively | With on-screen jog panel displayed |
| **CTRL+Home** | 4th +Jog | Jogs the 4th-axis positively | With on-screen jog panel displayed |
| **CTRL+End** | 4th −Jog | Jogs the 4th-axis negatively | With on-screen jog panel displayed |
| **SPACEBAR** | Feedhold | Enables Feedhold; press Cycle Start to resume | Always, with few exceptions |

> **Note:** To avoid unexpected movement, keyboard jogging disables and re-enables itself
> when leaving and entering the main menu. Keyboard jogging can still be enabled in any
> menu by pressing **ALT+J** (even after being disabled by CNC12). For instance, if keyboard
> jogging is active and the user navigates to the CNC12 parameters menu, keyboard jogging
> is suppressed while in that menu and reactivated when back in the main menu of CNC12.

---

## 2.27 MDI and the Keyboard Jog Panel

Many of the keys used by the keyboard jog panel are also possible commands to use in MDI.
To use the keyboard jog panel functions in MDI, press **ALT+J**. You may jog, use the
handwheels, or any other jog panel function. Press **ALT+J** or **Esc** to return to MDI
(p.33).

---

## 2.28 Keyboard Shortcut Keys

A computer-style keyboard is supplied with most systems and can be used as a jog panel. The
keyboard jog panel has many "hot keys" — keys that can be used at almost any time, with few
exceptions. Some menus may prohibit their use (p.33).

| Keystroke | Function | Description |
|---|---|---|
| **ALT+D** | WCS/Machine Coordinates | Switches the DRO display between the current WCS position and current machine position (p.33) |
| **ALT+E** | Generate Screenshot | If Parameter 389 is greater than 0, generates a screenshot saved as `screenshot-nnn.png` (nnn starts at 000, increments each screenshot, resets on CNC restart) (p.33) |
| **ALT+I** | Live PLC I/O | Brings up the CNC12 PLC Diagnostic Screen to view real-time status of all inputs and outputs (p.33–34) |
| **ALT+J** | Keyboard Jog Panel | Brings up the keyboard jog panel; a new window shows a VCP-like legend overlaid with keyboard key labels (p.34) |
| **ALT+K** | ATC Bin | Displays the current ATC bin (p.35) |
| **ALT+L** | ATC Putback Location | Displays the current ATC putback location (p.36) |
| **ALT+M** | Run MDI | Runs MDI (p.36) |
| **ALT+P** | Live PID Display | Displays the live PID screen showing current axis positioning information (p.36) |
| **ALT+S** | Cycle Start | Alternative to the CYCLE START button (p.36) |
| **ALT+T** | Temperature Display | Displays current temperatures for each axis in the message window (p.36) |
| **ALT+V** | Display CNC Software Version Info | Displays CNC12 software version information (same as pressing **F1** from the main menu) (p.36) |
| **ALT+1** … **ALT+0** | Select WCS | Cycles through the first ten Work Coordinate Systems (p.36) |
| **ALT+−** | Select Previous WCS | Selects the previous WCS (p.36) |
| **ALT+=** | Select Next WCS | Selects the next WCS (p.37) |
| **ALT+F10** | Exit CNC12 | Exits CNC12 (in the utility menu only) (p.37) |
| **CTRL+D** | Swap DRO and Distance-to-Go DRO | Swaps the positions of the DRO and the Distance-to-Go DRO (p.37) |
| **CTRL+E** | Launch PLC Detective | Launches the PLC Detective application (p.37) |
| **CTRL+H** | Enable G-code Display | If a job is running and the G-code display is hidden, shows the G-code display (p.37) |
| **CTRL+I** | Save PLC state to file | When in the Live PLC I/O display screen (via **ALT+I**), prints the current PLC I/O state to a file titled `plcstate.txt` (p.37) |
| **CTRL+Q** | Probing Cycles History | Displays the probing cycles history window (see `centroid-cnc12-intercon-probing`); press **CTRL+Q** again or click outside to close (p.37) |
| **SHIFT+F1** | Switch to Old-style Graphics Backplot | When in the accelerated backplot, switches to the old-style graphics backplot that does not use OpenGL (p.38) |
| **SHIFT+F2** | Erase Log File | From Utility → Logs → Errors (or Stats) screen, erases the log file after a confirmation dialog (p.38) |
| **CTRL+ALT+X** | Go to Shutdown Screen | From the main menu, takes you to the CNC12 shutdown screen (p.38) |
| **CTRL+C** | Copy | From any field that contains a number, and from the WCS Table columns, copies the selected value to the clipboard (p.38) |
| **CTRL+X** | Cut | From any field that contains a number, and from the WCS Table columns, cuts the selected value to the clipboard; the previous value is set to 0 (p.38) |
| **CTRL+V** | Paste | From any field that contains a number, and from the WCS Table columns, pastes the selected value from the clipboard (p.39) (manual body text erroneously says CTRL+P; the section heading CTRL+V is used here) |

### ALT+I – Live PLC I/O: Advanced View

To access a more advanced view of the Live PLC I/O (p.34):

1. Enter the utilities menu (**F7**).
2. Enter the CNC12 Wizard menu (**F10**).
3. Select "CNC Control" under the "Preferences" header.
4. Toggle the option "Enable Simple PLC Diagnostic as default."

With the Enhanced PLC Diagnostics screen enabled:
- Use the **Arrow**, **F11**, and **F12** keys to navigate the Live PLC I/O screen.
- **CTRL+ALT+I** — toggle the value of Inputs 1 through 80.
- **CTRL+ALT+F** — toggle outputs.

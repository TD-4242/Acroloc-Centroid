# CNC12 Screen Layout and Main-Screen Menu Map

Screen windows, keystroke conventions, startup homing procedure, and the F1–F10 main-screen menu map.
Source: operator manual Ch 1 (Introduction), Ch 3 (CNC Software Main Screen).

## 1.1 DRO Display

The DRO (Digital Read Out) display shows the current position of the tool in real time (p.10). It is
configurable for number of axes and desired display units of measure — see Ch 15 and
`centroid-cnc12-config` for parameter details. The bars beneath each axis label are **load meters**,
representing the amount of power being supplied to the drive for that axis. Load-meter display is
controlled by Parameter 143.

## 1.2 Distance-to-Go DRO

Located below the main DRO, this sub-display shows the remaining distance to complete the current
move (p.10). It is controlled by Parameter 143 and can be turned on by using **Ctrl+D** (see "Hot Keys" in
the operator manual for a complete list of keyboard shortcuts).

## 1.3 Status Window

The top line of the status window shows the name of the currently-loaded job file (p.11). Below the
job name are the following indicators:

| Indicator | Description |
|---|---|
| Tool Number | Currently-active tool |
| Program Number | Active subprogram number |
| Feed Rate Override | Current override percentage set on the Jog Panel; label turns RED if the rapid override is turned off |
| Spindle Speed | Current spindle speed (requires variable-frequency spindle drive/inverter) |
| Feed Hold | Current on/off status of FEED HOLD |

When **CYCLE START** is pressed and a job is running, additional indicators appear:

| Indicator | Description |
|---|---|
| Part Cnt | Number of times the currently-loaded job has been run; increments only on successful completion |
| Part # | How many parts have been run; up/down arrow indicates count direction |
| Part Time | Elapsed time since CYCLE START was pressed; continues counting through optional stops, tool changes, and FEED HOLD |

See Ch 2 for descriptions of the Feed Hold Button, Feed Rate Override Knob, and Spindle controls.
See G65 (Ch 12) or M98 (Ch 13) for Program Number details.

## 1.4 Message Window

The message window is divided into a **message section** (upper lines) and a **prompt section** (lowest
line) (p.11). Behavior:

- Newest messages always appear at the bottom of the message section; older messages scroll upward.
- When old messages scroll out of view, a scroll bar appears on the right side; use the **UP ARROW**
  and **DOWN ARROW** keys to view older messages.
- The prompt line displays control prompts (e.g., "Press CYCLE START to start job" appears on
  power-up).

For a description of CNC software error and status messages, see Ch 16 and `centroid-cnc12-config`.

## 1.5 Options Window

Displays the currently available softkey (function key) choices for the active screen (p.11). Options
are selected by pressing the function key shown in the box. For example, on the main screen pressing
**F5 – CAM** selects the CAM option.

## 1.6 User Window

Context-sensitive display area; its content depends on what the operator is currently doing (p.11).
When no action is being taken, the window is empty. When **CYCLE START** is pressed and a job
processes correctly, up to 11 lines of G-codes are displayed for the operator to observe during the
run. Part zeros, tool library setup, and Digitizing/Probing information are also entered by the user
in this window.

## 1.7 Conventions

Keystroke and softkey notation used throughout the operator manual (p.11–12):

| Convention | Meaning |
|---|---|
| **A** | Bold, capitalized letter = a keyboard key (e.g., the A key) |
| **ENTER** | Bold, capitalized word = a named key |
| **ESC** | The Escape key |
| **ALT-D** | Hold **ALT** and then press **D** |
| **F10 – Save** | All data entry screens use **F10 – Save** to save changes |
| **ESC** | Any menu can be exited by pressing **ESC**; returns to previous menu and usually discards changes |

Coordinate system conventions (p.12):

- All program examples use the standard right-hand Cartesian coordinate system (see axis diagram p.12).
  Facing the mill: X-axis is positive to your right, Y-axis is positive toward the mill, Z-axis is
  positive upward (perpendicular to the XY plane).
- Direction of motion is defined by **CUTTER** motion, not TABLE motion.
- **CW** = clockwise; **CCW** = counter-clockwise.

## 1.8 Machine Home

When the M-series control is first started, the Main screen displays a "Machine Home Position Not Set"
warning (p.14). Machine home must be set before running any jobs.

**If the machine has home/limit switches, reference marks, or safe hard stops:**

The control can automatically home itself. If the machine has reference marks, jog each axis until the
reference marks are aligned, then press **CYCLE START** to begin the automatic homing sequence. The
control executes the G-codes in `cncm.hom` located in `c:\cncm`. By default this file homes Z in the
plus direction, then X in the minus direction, and Y in the plus direction.

**If the machine does not have home/limit switches or safe hard stops:**

The following warning appears (p.15):

```
--- Warning: Machine Home Position Not Set ---

1) Jog all axes to Machine Home Position
2) Press CYCLE START to set the home position
```

In this case, move the machine to its home position manually using the jog keys or handwheels, then
press **CYCLE START** to set the machine home.

## 1.9 Mill M- and G-codes

Section 1.9 of the operator manual provides a summary index of available M- and G-codes (p.15–16).
It notes: "This is a summary list of M- and G-codes. See Chapters 12–13 for more information."

> For the complete M- and G-code language reference — syntax, parameters, modal groups, and usage
> examples — see the **`centroid-cnc12-gmcodes`** skill. The operator manual's full reference is in
> Chapters 12 (G-codes) and 13 (M-codes).

## 1.10 How to Unlock Software Features or Unlock Your Control

The following steps are necessary to unlock software features (p.16):

1. Go to the Main screen of the Control software.
2. Press the **F7 – Utility** key and then the **F8 – Import License** key.
3. Select your license file from the file browser that appears.
4. Repeat Steps 1–3 for each new unlock.

## 1.11 Centroid API

CNC12 provides a C# programming language API that allows users to create custom interface programs
communicating with CNC12 to perform tasks such as moving the machine and setting parameters (p.17).

- Documentation is in the `CentroidAPIDocumentation` folder in the root of the CNC12 installation
  directory.
- Community API discussion: https://centroidcncforum.com/viewforum.php?f=72

## 1.12 CNC12 with Multiple Displays

When using CNC12 with multiple displays, the software defaults to the display located farthest to the
right (p.17). To override this:

1. Right-click on the CNC12 shortcut on the Windows Desktop and click **Properties**.
2. Under the **Target** field, add the text `–displayX` where `X` is the identification number of
   the desired display.

An error message may appear upon starting the program, but the desired display will be used.

---

## F1–F10 Main-Screen Menu Map

The main screen Options Window shows ten softkey menus accessed from the main screen (p.40).

| F-key | Menu name | One-line purpose | Note |
|---|---|---|---|
| **F1** | Setup | Set part zeroes, set/change tool offsets, and change control configuration | See §F1 Setup below |
| **F2** | Load Job | Load a job file from disk | See §F2 Load Job below |
| **F3** | MDI | Run a single-line M- or G-code command immediately | See §F3 MDI below; see `centroid-cnc12-gmcodes` for code reference |
| **F4** | Run | Search and run a job; resume a canceled job; change how a job runs | See §F4 Run below |
| **F5** | CAM | Open Intercon conversational part programmer | See §F5 CAM below; see `centroid-cnc12-intercon-probing` for Intercon detail |
| **F6** | Edit | Open the currently-loaded job in a G-code text editor | See §F6 Edit below |
| **F7** | Utility | Backup/restore configuration, view software options, import/export files | See §F7 Utility below; see `centroid-cnc12-config` for configuration detail |
| **F8** | Graph | Graph the toolpath of the currently-loaded part program | See §F8 Graph below |
| **F9** | Digitize | Touch-probe digitizing (option; only displayed if purchased) | See `centroid-cnc12-intercon-probing` for full digitizing reference |
| **F10** | Shut Down | Park machine, power off control, or exit CNC software | See §F10 Shutdown below |

### F1 – Setup

Pressing **F1** from the main screen enters the Setup menu, which shows the CNC12 version and system
ID in the user window (p.41). Sub-menus:

| Sub-key | Menu | Description |
|---|---|---|
| **F1** | Part | Part Setup menus — part zeroes, work coordinate systems (see Ch 4) |
| **F2** | Tool | Tool Setup menus — tool offsets, tool library (see Ch 5) |
| **F3** | Config | Configuration menu — machine parameters and settings (see Ch 15; `centroid-cnc12-config`) |
| **F4** | Feed | Feed menu — feed rate and related settings (see Ch 6) |
| **F8** | Smoothing Setup | Simplified access to Smoothing module parameters |

Press **ESC** (or **X**) to return to the main screen.

### F2 – Load Job

Opens a Windows-style file browser to select and load a job (part program) file (p.41). The loaded
job name appears in the Status Window. Press **ESC** to cancel without loading.

### F3 – MDI

MDI (Manual Data Input) mode allows direct entry of M- and G-code commands one line at a time (p.42).

- Type a command at the `Block?` prompt, then press **CYCLE START** to execute.
- After execution, the control prompts for another line.
- When finished, press **ESC**.
- Navigate previous commands with **UP ARROW** / **DOWN ARROW**; edit with **LEFT** / **RIGHT** arrow keys.

Example commands:
```
Block? G92X0Y0   ; Set the current XY position to 0,0
Block? M92 /Z    ; Move the Z to the positive limit.
Block? M26 /Z    ; Set the current Z position as Z home.
```

> For the complete G- and M-code language reference see the **`centroid-cnc12-gmcodes`** skill.

### F4 – Run

The Run menu is used to start, search, resume, and control job execution (p.42). Run menu options:

| Field/Toggle | Default | Description |
|---|---|---|
| Single Block Mode | Off | Program executes one block at a time when On |
| Optional Stops | Off | Honors M01 optional stop codes when On |
| Block Skips | Off | Skips blocks prefixed with `/` when On |
| Job Repeat | Off | Repeats the current program when a job finishes when On |
| Run-Time Graphics | On | Displays toolpath graphics during run |
| Part Count | 0 | Displays how many times the job has run |

Run sub-menu softkeys:

| Sub-key | Label | Description |
|---|---|---|
| **F2** | Search | Resume a job by searching for a line, tool, or block number |
| **F3** | Repeat On | Toggles Job Repeat |
| **F4** | /Skips On | Toggles block skip |
| **F5** | Block | Toggles Single Block mode |
| **F6** | Stops | Toggles optional stops (M01) |
| **F8** | Graph | Graphs toolpath of currently-loaded program |
| **F9** | Rapid Off | Toggles the rapid override function |
| **F10** | RTG On/Off | Toggles Run Time Graphics |

For further information see Ch 6.

### F5 – CAM

Opens Intercon, Centroid's conversational part-programming system (p.43). Intercon supports
rectangular, circular, and irregular pockets; pockets with islands; bolt hole circles; frames;
thread milling; and other canned cycles. When programming is complete, exit Intercon to return to
the Main Screen — the posted Intercon program is automatically loaded and ready to run.

> **Note:** The F5 CAM screen can be customized with additional F Keys.

For full Intercon reference and canned-cycle details, see the **`centroid-cnc12-intercon-probing`**
skill and Ch 10.

### F6 – Edit

Loads the current job into a G-code text editor for viewing or editing (p.43).

> **WARNING** Editing a file (modifying and saving) **while the machine is moving** can cause
> personal injury or machine damage.

> **WARNING** Do not edit configuration data located in the `C:\cncm` directory. Doing so can
> cause personal injury or machine damage.

When editing is complete, save the file and exit the text editor before running the job. It is best
practice not to edit any files while the machine is moving. Note that `C:\cncm` contains
configuration files and binary data — do not edit these files as doing so can cause loss of data
and serious malfunctions.

### F7 – Utility

The Utility menu provides access to software options, diagnostics, backup/restore, and file
management (p.44). Sub-menu softkeys:

| Sub-key | Label | Description |
|---|---|---|
| **F2** | Restore Report | Update the control's configuration with a `report.zip` file |
| **F5** | Color Picker | Change from the default Centroid Classic Color Scheme |
| **F6** | User Maint | Perform user maintenance |
| **F7** | Create Report | Generate a backup of system configuration files called `report.zip` |
| **F8** | Options | Show software plugins and software level information |
| **F9** | Logs | Show messages and errors logged by the control |

The license-import option (Import License) is reached from this Utility menu via **F8** — see §1.10
for the unlock procedure.

For further information see Ch 7. For configuration parameters and error codes, see
`centroid-cnc12-config`.

### F8 – Graph

Graphs the toolpath of the currently-loaded part program (p.44). Graph can also be accessed from
the Load Job Screen and various Run Job menus. Pressing **CYCLE START** while in the Graph screen
animates the toolpath as it draws.

**Accelerated Graphics Backplot** (default, p.44–45):

| Sub-key | Label | Description |
|---|---|---|
| **F1** | Pan/Rotate | Toggles arrow keys between pan (scroll) and rotation modes; axis indicator marks center of rotation |
| **F2** | View | Changes planar view (TOP / RIGHT / FRONT) |
| **F3** | Set Range | Select which G-code lines to display |
| **F4** | Dimension Menu | Sub-menu: F1 Prev Line, F2 Next Line, F3 Go To Line, F4 Measure |
| **F5** | Redraw | Redraws part slowly; feed rate override knob (or **+**/**−** keys) controls draw speed; press **F5** again to cancel |
| **F6** | Options & Help | Sub-menu: F2 Reset to Defaults, F3 Help, F10 Save |
| **F7** | Zoom In | Zoom into part relative to screen center |
| **F8** | Zoom Out | Zoom away from part relative to screen center |
| **F9** | Zoom All | Fit entire part inside screen |
| **F10** | Show Tools | Toggle tools highlight menu |
| **Spacebar** | Measure | Measure between two snapped points (2D or 3D depending on view) |

Mouse/touch screen: left-button drag pans, right-button drag rotates, scroll wheel (or both
buttons) zooms. Double-clicking a feed-rate move centers the camera on that move and shows its
length. For touch screens, **F1** switches between Pan and Rotate modes.

**Legacy Graphics Backplot** (enabled by setting Parameter 260 to −1, or temporarily with
**Shift+F1** while in the F8 Graph menu; press **ESC** then **F8** to return to Accelerated, p.46):

| Sub-key | Label | Description |
|---|---|---|
| **F1** | 2D/3D | Toggle isometric 3D view |
| **F2** | View/Rotate | Change planar view; in 3D, rotate with arrow keys |
| **F3** | Range | Set line/block number range to graph |
| **F4** | Time | Estimate part machining time (accounts for accelerations; neglects tool change times) |
| **F5** | Redraw | Redraw part at any time |
| **F6** | Pan | Move part on screen; press **F6** again after selecting location to continue |
| **F7** | Zoom In | Zoom in |
| **F8** | Zoom Out | Zoom out |
| **F9** | Zoom All | View entire part |

Legacy color scheme: canned drilling cycles = gray; rapid traverse = red; feed rate moves =
yellow; cutter-compensated moves = gray.

> **Note:** Use the FEED RATE OVERRIDE knob to control graphing speed. Turn counter-clockwise to
> pause; clockwise to resume. On the offline demo software, use **Ctrl+** or **Ctrl−**.

### F9 – Digitize

Displayed only if the Digitize option has been purchased (p.47). Opens the Digitize screen for
setting up and running touch-probe digitizing (reverse-engineering parts).

> For full digitizing and probing reference, see the **`centroid-cnc12-intercon-probing`** skill
> and Ch 8.

### F10 – Shutdown

Enters the Shutdown menu to safely power off or exit the control (p.47).

> **WARNING** Shutting down the machine without using this menu may damage your control.

Sub-menu softkeys:

| Sub-key | Label | Description |
|---|---|---|
| **F1** | Park | Park machine at end of day for quicker homing at next startup; homes each axis at the maximum rate to 1/4 of a motor revolution from its home position; press **CYCLE START** to begin movement |
| **F2** | Poweroff | Properly shut down the control (turns off control only — machine itself must be turned off manually) |
| **F6** | System Prompt | Opens a Windows command line interface; type `exit` to close |
| **F9** | Exit CNC12 | Exits the CNC control software without powering off |

> **Note (F2 Poweroff):** This will only turn off the control. The machine itself will still need
> to be manually turned off.

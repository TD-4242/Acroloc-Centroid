# CNC12 Running Jobs: Job Run Screen, Run Menu, Cancel/Resume, Power Feed, Utility Menu

Start, monitor, cancel, and resume CNC job programs; use Power Feed for manual axis moves; access
Utility Menu functions.
Source: operator manual Ch 6 (Running a Job), Ch 7 (The Utility Menu).

---

## Ch 6 Overview (p.77)

To start the currently-loaded job, go to the Main Screen and press the **CYCLE START** button on
the jog panel. If the control is not equipped with a jog panel, press **ALT+S** on the keyboard.

See `interface.md` §F4–Run and §F7–Utility for the top-level softkey paths established in the
main-screen menu map.

---

## 6.1 Active Job Run Screen with G-code Display (p.77)

If the Run-time Graphics option is set to Off, the following screen is displayed while a job is
running (screenshot p.77). The screen shows current position (X/Y/Z), Distance to Go, Machine
Coord, Job Name, Tool, Feedrate, Spindle, Program number, Part Count, Part Number, and elapsed
Time. The G-code display panel shows the lines near the currently-executing block, with the
active line highlighted.

On this screen, the following F-keys are available (p.77):

| Softkey | Label | Description |
|---|---|---|
| **F3** | Repeat On | Toggle the repeat feature for part counting. See §6.5 F3 for details. |
| **F4** | /Skips On | Enable/Disable block skips. See §6.5 F4 for details. |
| **F5** | Auto | Single Block mode only. Turns on Auto mode and disables Single Block mode. Once Auto mode is on, Single Block cannot be re-enabled unless you stop the job. See §6.5 F5 for details. |
| **F6** | Stops off | Appears only if Optional Stops is on. Turns off Optional Stops. Cannot be re-enabled unless the job is stopped. See §6.5 F6 for details. |
| **F8** | Graph | Switch to the Run-time Graphics screen. Only appears if the job was started with the run-time graphics option turned on. |
| **F9** | Rapid Off | Turn rapid override on/off. |

> For information on other keys available while a job is running, see Chapter 2 (operator panel /
> `operator-panel.md`).

---

## 6.2 Run-time Graphics Screen (p.78)

When a job is running with Run-time Graphics set to On, a screen similar to the following is
displayed (screenshot p.78). It shows axis positions, Distance to Go, Spindle RPM, Feedrate, Job
Name, and the current block's action (e.g., "Tool change: T2 Drill") along with a live graphical
tool-path display.

The following keys are available while the job is running in Run-time Graphics (p.78):

| Softkey | Label | Description |
|---|---|---|
| **F7** | Clear | Clears the trail up to the tool's current position in the program. |
| **F8** | G-Code | Switch to the Job Run Screen with G-code display (§6.1). |
| **F9** | Trail On | Turn on/off the tool trail display. |

---

## 6.3 Canceling a Job in Progress (p.78)

There are three conventional ways to cancel a currently-running job (CNC program). When a job is
canceled using any of the following methods, the job's progress will be recorded. This allows the
user to restart the job using the Resume Job option or the Search and Run option (p.78).

**CYCLE CANCEL:** Pressing this key while a job is running causes the control to abort the job
currently being run. The control will stop movement immediately, clear all M-functions, and
return to the main screen. Hitting the escape key on the keyboard is equivalent to hitting
CYCLE CANCEL.

**TOOL CHECK:** Pressing this key while a job is running causes the control to stop the normal
program movement. In addition, the Z-axis will be pulled to its home position and all M-functions
will be cleared. The control will automatically go to the resume job screen.

**EMERGENCY STOP (E-Stop):** Pressing the EMERGENCY STOP button while a job is running causes the
control to abort the job currently being run. The control will stop movement immediately, clear
all M-functions, and return to the main screen. Also, the power to all axes will be released.

---

## 6.4 Resuming a Canceled Job (p.79)

If a job is canceled using one of the methods described in §6.3, it can be resumed in one of
three ways (p.79):

**CYCLE START:** Pressing the CYCLE START button will restart the job at the **BEGINNING** of the
part program.

> **Note:** Before performing F1 – Resume Job or F2 – Search, the tool may need to be positioned
> in X and Z for cycles that start down inside an ID or behind a shoulder (p.79).

**F1 – Resume Job** (located in **F4 – Run menu**): Restart the canceled job at or near the point
of interruption. See §6.5 for full details.

**F2 – Search** (located in **F4 – Run menu**): Restart at a specified point in the part program.
See §6.5 for full details.

### Resume Job procedure (p.79)

1. Press **F4 – Run** from the Main Screen to go to the Run screen.
2. Press **F1 – Resume Job** to go to the resume job screen.
   *(If the job was canceled by pressing TOOL CHECK, the control will go to the resume job
   screen automatically — skip steps 1–2.)*
3. On the resume job screen you may optionally:
   - Modify tool offsets.
   - Modify the tool library.
   - Turn block mode on or off.
   - Turn optional stops on or off.
   - Graph the partially-completed job (press **F8 – Graph**).
4. Press **CYCLE START** to start the partially-completed job from the point of interruption.

### Resume Job availability (p.79–80)

The resume job option is not always available. The following situations cause it to be
unavailable:

- Loading a new job.
- Running a job to completion.
- Parse errors in the job.
- Editing or reposting the job file.
- Loss of power while a job is running.

---

## 6.5 Run Menu (p.79–81)

Press **F4 – Run** from the Main Screen to access the Run menu (screenshot p.79). From this menu,
the operator can restart a canceled job or change the way a job will be run.

### Run Menu Softkeys (p.79–81)

| Softkey | Label | Description |
|---|---|---|
| **F1** | Resume Job | Access the resume job screen. See §6.4. |
| **F2** | Search | Access the "Search and Run" menu. |
| **F3** | Repeat On/Off | Toggle the repeat feature for part counting. |
| **F4** | /Skips On/Off | Toggle the block skip feature. |
| **F5** | Block | Turn single block mode on and off. |
| **F6** | Stops | Turn optional stops on and off. |
| **F8** | Graph | Graph the part. |
| **F9** | Rapid On/Off | Toggle Rapid Override. |
| **F10** | RTG On/Off | Toggle the Run-time Graphics option. |

The Run menu user window shows the current state of: Single Block Mode, Optional Stops, Block
Skips, Job Repeat, Part Count, and Run-Time Graphics (p.79).

### F1 – Resume Job (p.79)

Access the resume job screen by pressing **F4 – Run** on the main screen to go to the run screen,
then pressing **F1 – Resume Job** in the run screen. If the job was canceled by pressing TOOL
CHECK, the control will go to the resume job screen automatically. From this screen, the user can
modify tool offsets, modify the tool library, turn block mode on and off, turn optional stops on
or off, graph the partially-completed job, or start the partially-completed job.

### F2 – Search (p.80)

Invoking this option brings you to the "Search and Run" menu. This menu allows you to specify
the program line, block number, or tool number at which execution of a program is to begin.
Program lines are numbered from the top of the file down, with the first line numbered 1.

- To enter a block number: place an "N" in front of the number.
- To enter a tool number: place a "T" in front of the number.
- Press **CYCLE START** to start the program at the point you specified.

An extra option unique to the "Search and Run" screen is **F1 – Tool Change** ("Do Last Tool
Change" function). This key toggles the tool change option:

- **YES** — the control performs a tool change so that the tool specified for the line or block
  has the tool indicated in the program.
- **NO** — use the currently-loaded tool, regardless of what tool is specified for the line or
  block being searched.

CNC12 will remember previous searches. They are accessible by pressing the **UP** and **DOWN**
arrow keys in the Search text box.

> **Note:** You cannot search within a subroutine (p.80).

### F3 – Repeat On/Off (p.80)

This key toggles the repeat feature for part counting. When part counting is in effect and Repeat
is on, the job will be automatically run again until the specified number of parts has been run.
The On or Off label indicates the state to which the repeat feature will toggle when pressed; it
does not indicate the current state. The current state is indicated in the user window (p.80).

**Part Count prompt (p.80):** Used to set the Part count.

- Positive values set the part counter to count up. For example, if ten is entered in the Part
  Count prompt, the Part Cnt in the status window changes to ten and the Part # changes to zero
  with an upward arrow indicator. When a job is run and completes, the Part # increments to one.
  If repeat is on, the job automatically starts again and keeps running until Part # reaches the
  Part Cnt.
- Negative values configure the part count to count down. For example, if −10 is entered, the
  Part Cnt changes to ten and the Part # changes to ten with a downward arrow indicator. When a
  job finishes, the Part # decrements to nine. If repeat is on, the job starts again and keeps
  running until the Part # reaches zero.

### F4 – Skips On/Off (p.80)

This function toggles the block skip feature. When block skipping is on, G-code lines that start
with a forward slash character '/' are skipped (not processed). Note that because of the way a
job is processed (in a pre-processed buffered fashion), the effect of this key may be delayed if
pressed while a job is running. The On or Off label indicates the state to which the /Skips
feature will toggle when pressed; it does not indicate the current state. The current state is
indicated in the user window (p.80).

### F5 – Block Mode (p.80)

Turns single block mode on and off. This is similar to pressing the **AUTO/BLOCK** key. If Single
Block mode is on, the CNC software will stop after each block in the part program and wait for
the **CYCLE START** button. Note that Auto mode is the default mode. If this key is used to turn
on Single Block mode and then run a job, Auto mode will be re-instated when the job ends. The
current state of this setting is indicated in the user window (p.80).

### F6 – Optional Stops (p.80–81)

Turns optional stops on and off. If optional stops are on, any M1 codes that appear in the
program will cause a wait for the **CYCLE START** button (just like M0). If optional stops are
off, M1 codes will be ignored. Note that the default mode for Optional Stops is off. If this key
is used to turn on Single Block mode and then run a job, Optional Stops will be set to off when
the job ends. The current state of this setting is indicated in the user window (p.81).

> For M0/M1 M-code definitions, see the **`centroid-cnc12-gmcodes`** skill.

### F8 – Graph (p.81)

Graphs the part. For more information, see the "F8 – Graph" section in Chapter 3. If this feature
is invoked from the Run and Search screen or the Resume Job screen, the graphics will show exactly
where the searched line or block begins. Dotted lines indicate the portion of the part that will
be skipped. Solid lines indicate the portion of the part that will be machined (p.81).

### F9 – Rapid On/Off (p.81)

This function key toggles Rapid Override. The On or Off label indicates the state to which the
Rapid Override feature will toggle when pressed. In the Rapid Override On state, the speed of
rapid moves (G0) can be adjusted by the Feed Rate Override knob. In the Rapid Override Off state,
the speed of rapid moves will be at full speed (max rate) (p.81).

> For G0 rapid move syntax, see the **`centroid-cnc12-gmcodes`** skill.

### F10 – RTG On/Off (p.81)

This function key toggles the Run-time Graphics option. If the option is turned on, Run-time
Graphics automatically starts when the **CYCLE START** button is pressed. This option must be
turned on for Run-time Graphics to be used. If the option is turned off, Run-time Graphics cannot
be started while a job is running (p.81).

### Parameter 400 and CYCLE START on the Run Menu (p.81)

Machine Parameter 400 determines whether or not the CYCLE START button is enabled on the Run
Menu. If Parameter 400 is set to zero, the CYCLE START button is disabled in the Run Menu. For
any other value of Parameter 400, the CYCLE START button is enabled. Note that this does not
apply to the Resume and Search sub-menus, where the CYCLE START button is always enabled (p.81).

> For Parameter 400 details, see the **`centroid-cnc12-config`** skill.

---

## 6.6 Power Feed (p.81)

Press **F4 – Feed** from the Setup menu (**F1 – Setup** → **F4 – Feed**) to access the Power Feed
screen. This screen is used to command axis movement. All of the operations available on the Power
Feed screen may also be performed in MDI with the appropriate M- and G-codes (p.81).

### Power Feed Softkeys (p.81)

| Softkey | Label | Description |
|---|---|---|
| **F1** | ABS | Move an axis to an absolute position at a specified feed rate. |
| **F2** | INC | Move an axis an incremental distance at a specified feed rate. |
| **F3** | Free XY | Release power to the X and Y motors, allowing manual use of the machine for these two axes. |
| **F4** | Power XY | Apply power to the X and Y motors, allowing use of the machine with the jog panel for these two axes. |

---

## 6.7 Communications Stress Test (p.81–82)

Included in the example files is a communications stress test that can be run by the user. This
file can help report communication errors, such as the number of packets resent, generic
communication errors, packets out of order, number of NAcks packets sent, and number of NAcks
packets received (p.81).

### Running the Communications Stress Test (p.81–82)

1. Press **F2 – Load**.
2. If not already in the `ncfiles` directory of the `cncm` folder, navigate to `cncm\ncfiles`.
3. Select the `com_stress_test.cnc` file.
4. Press the **CYCLE START** button.
5. The test will run and the following message will appear (screenshot p.82):
   `Communications Stress Test will start after this message disappears, Please Wait for results`
6. Please allow the system time to process. Once complete, a message similar to the following
   will appear with your results (screenshot p.82):

```
Communications Stress Test PASSED
max. errors acceptable = 5
Results:
Packets Resent: 0
Generic Communication Errors: 0
Packets Out of Order: 0
NAcks Packets Sent: 0
NAcks Packets Recieved: 0
```

---

## Utility Menu (F7) (p.83–85)

To get to the Utility Menu, press the **F7 – Utility** key at the CNC Software Main Screen
(screenshot p.83). The model will vary depending on your M-series Control model.

### Utility Menu Softkeys (p.83–85)

| Softkey | Label | Description |
|---|---|---|
| **F2** | Restore Report | Restore a system configuration from a previously-saved `report.zip` file (created by F7 – Create Report). |
| **F5** | Color Picker | Change display colors from the default Centroid Classic color scheme. |
| **F6** | User Maint | Access file options, the manual, or machine notes. |
| **F7** | Create Report | Generate a backup of system configuration files (`report.zip`) for servicing. See **`centroid-cnc12-config`**. |
| **F8** | Import License | Select a license file for use with CNC12. See **`centroid-cnc12-config`**. |
| **F9** | Logs | View error/message logs and counts logged by the control. See **`centroid-cnc12-config`**. |
| **F10** | Acorn Wizard | User-friendly configuration tool for axis motors, I/O, spindle control, and homing. See **`centroid-cnc12-config`**. |

### F2 – Restore Report (p.83)

Used primarily for restoring a system configuration from a previously-saved `report.zip` file.
See F7 – Create Report.

### F5 – Color Picker (p.83–84)

This menu allows you to change colors from the default Centroid Classic color scheme. Preset
themes available include Centroid Classic, Dark Theme, and Grey Theme (screenshot p.84).

Edits can be made to individual colors either by clicking the colored square or typing the hex
color code manually. Clicking on the colored square next to an item brings up the Pick Swatch
Type screen (screenshot p.84).

On the Pick Swatch Type screen, you can use the color wheel to select and preview the color. You
can also manually input values via the RGB or Hex Color Code options. When finished, select
**Accept**. When finished modifying all colors, select **Save** to create a new Color Profile.
Select **Done** to return to the previous screen.

If changes are saved to the Centroid Classic theme and a return to the original is desired, select
**File** then **New**. The new profile will start with Centroid Classic settings (p.84).

### F6 – User Maint (p.84)

| Softkey | Label | Description |
|---|---|---|
| **F1** | File Ops | Access files in a DOS format. |
| **F2** | Manual | Opens a PDF of the CNC12 Operator's manual. |
| **F3** | Machine Notes | Opens a text file in the `cncm` folder — a convenient way to store notes about the machine, control customizations, and other notes. |

### F7 – Create Report (p.84) — defer to centroid-cnc12-config

Generates a backup of system configuration files called `report.zip` and copies it to the
specified location. Your dealer may use this file for servicing and troubleshooting purposes.
To restore the configuration files from the report, press **F2 – Restore Report** from the
Utility menu. Full details: see **`centroid-cnc12-config`**.

### F8 – Import License (p.85) — defer to centroid-cnc12-config

Use this option to select a license file for use with CNC12. Full details: see
**`centroid-cnc12-config`**.

### F9 – Logs (p.85) — defer to centroid-cnc12-config

Shows the messages and errors logged by the control. Sub-keys: F1 – Errors (error/message log),
F2 – Stats (error counts), F3 – Export (export log). Full details: see
**`centroid-cnc12-config`**.

### F10 – Acorn Wizard (p.85) — defer to centroid-cnc12-config

Currently only available with Acorn, AcornSix, and Hickory. A user-friendly configuration tool
designed to simplify the setup process for your CNC machine (mill, lathe, router, or plasma
cutter). It acts as a guided interface to configure essential settings like axis motors,
inputs/outputs, spindle control, and homing routines (screenshot p.85). Full details: see
**`centroid-cnc12-config`**.

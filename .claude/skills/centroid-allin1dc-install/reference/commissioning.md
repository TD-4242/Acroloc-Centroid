# Commissioning & Tuning Reference

Final software configuration in CNC12 after cabinet wiring: encoder confirmation, motor &
spindle setup, DRO calibration, homing, feedrate/acceleration tuning, backlash, travel
limits, deadstart, and the system test.
Source: install manual Ch6. Assumes the board-level/bench test (Ch4) is complete and all
faults are cleared (check via **F3 MDI** — a clean MDI screen means no faults). The CNC12
menu path `F1 Setup → F3 Config` uses password **137** throughout.

## 6.2 Confirm encoder communication

> **DANGER: mechanically disconnect the servo motors from the machine** so they move freely.

F1 Setup → F3 Config (137) → **F4 PID**. Manually rotate each motor and watch the **Abs Pos**
field for that axis: feedback should be smooth, the right axis DRO should update, and Abs Pos
should **count up when spinning the shaft counter-clockwise**. Repeat per axis.

## 6.3 Motor software setup

1. **Torque mode:** the ALLIN1DC runs **only in torque mode**. F1 Setup → F3 Config (137) →
   F3 Parms → F8 Next Table to **Parameter 256** → set **P256 = 0**.
2. **PID settings:** F1 Setup → F3 Config (137) → F4 PID → F1 PID Config. Enter **Kp, Ki,
   Kd, Limit** per Appendix C (see `parameters.md`). Kg, Kv1, Ka, Accel are filled by
   autotune later. F10 Save & Exit.
3. **Do not leave stall detection disabled** for the rest of commissioning (re-enable it).
4. Release E-stop to clear errors and **provide VM power to the servo motors**.
5. Feedrate to ~**10%**.
6. **Jog each motor while disconnected from the machine** (arrow keys or MDI); confirm
   correct motion; disable increment mode (the **Incr Cont** button must not be lit).
   - *A little "rumbling" when a motor stops is normal (holding position).*
   - **Run-away / "SV_ Stall Error":** the control doesn't see proper encoder signals (bad
     encoder config **or reversed motor power leads** — control commands one way, encoder
     reports the other). Oscillation/singing → PID problem; manual-tune via **TB260**.
     `M93` (MDI) stops motors holding position.
7. Power down; manually center all axes for clearance; mechanically connect the motors.
8. **Manual tuning (optional, usually unnecessary):** reduce error / fix singing via **TB260**;
   3rd-party servo settings in **TB288**.
9. **Correct servo direction (TB137):** direction is defined by **tool motion relative to
   the part**. On a knee mill, table-moving axes (X/Y) move **opposite** the tool motion;
   tool-moving axes (the quill) move **the same**. Use MDI to move each axis — the DRO should
   count **more positive** moving in the **positive** direction. To flip an axis: F1 Setup →
   F3 Config (137) → F2 Mach → F2 Motor → toggle **Dir Rev** with the spacebar.
   - **Re-verify home is set to Jog** (limit switches not yet trusted — homing to limits now
     could crash the machine). Home with Start / `alt+s`, then slow-jog each axis.

## 6.4 Spindle setup

F1 Setup → F3 Config (137) → **F1 Contrl** (Control Configuration screen).

- **Max spindle (high range):** high-range max RPM for a VFD spindle (0–500000). All
  programmed spindle speeds are output to the PLC as a **percentage** of this max.
- **Min spindle (high range):** if > 0, the spindle outputs the minimum-voltage equivalent
  until commanded speed exceeds it (0–500000).
- **Enable spindle fault inputs:** if used, `alt+I` real-time I/O → `ctrl+alt+i` to remove
  any bar over the spindle-fault input.
- **Spindle encoder parameters** (if a spindle encoder is fitted): **P34** = spindle encoder
  counts/rev (line × 4), **P35** = spindle encoder axis number (**6**), **P78** = spindle
  speed display & operations (**1**). If it counts backward, **negate P34** (e.g. 4000 →
  −4000).
- **Dual-/multi-range spindle gear ratios — P65–P67:** ratios of each lower range relative
  to high range (high range is the default). E.g. low range turns 1/10 of high → **P65 = 0.1**.
  P65 = low-range ratio (negative if a **back gear** is used), P66 = medium-low ratio,
  P67 = medium-high ratio. The PLC signals the active range to CNC12 via **INP63/INP64**:

  | | High | Medium-High | Medium-Low | Low |
  |---|---|---|---|---|
  | INP63 | 0 | 1 | 1 | 0 |
  | INP64 | 0 | 0 | 1 | 1 |

## 6.5 Coarse DRO adjustment (machine revs/inch or mm/rev) — TB36 Method 1

The DRO is computed from motor movement × motor revs per inch/mm (the ballscrew). Get close
first, fine-tune in §6.9.

1. Jog the spindle to the table center.
2. **Zero:** F1 Setup → F1 Part → F10 Set Zero.
3. Set up a tape measure with 0" under the spindle center.
4. **Command a move** (≥1 ft for accuracy) via F3 MDI, e.g. `X 12`. *(Feed down, ready to
   E-stop — limits aren't configured.)*
5. **Calculate & enter** in F1 Setup → F3 Config (137) → F2 Mach → F2 Motor:
   - **Imperial:** `new revs/in = current revs/in × (commanded / actual)`. E.g. commanded
     7.5", actual 6", current 5.000 → 5 × (7.5/6) = **6.25**.
   - **Metric:** `new mm/rev = current mm/rev × (actual / commanded)`. E.g. actual 150 mm,
     commanded 175 mm, current 5.08 → 5.08 × (150/175) = **4.35428**.
6. Repeat until the DRO matches the tape; repeat per axis.

## 6.6 Homing the machine — TB22

1. **Homing file** (`cncm.hom` for mills, `cnct.hom` for lathes), in the CNC12 directory.
   Default works for most machines; edit only for unusual axis counts/configs. Create it if
   missing. **Centroid recommends Z-positive always homes first** to prevent crashes.
2. **Configure limit switches** (TB127): motor direction (§6.3) must be correct first; center
   the spindle. F1 Setup → F3 Config (137) → F2 Mach → F2 Motor. Physically trip the **minus**
   limit of an axis and try to jog — it should move **plus only**; if not, flip the limit in
   software (Fig 6.5.4). Repeat for each home switch. *(If you disabled limits earlier with
   `ctrl+alt+i` on inputs 1–6, re-enable them: `alt+I` → `ctrl+alt+i` to remove the bar.)*
3. **Home type:** F1 Setup → F3 Config (137) → F1 Contrl → **Machine home at power up =
   Limit Switch** → Save.
4. Restart, then **home** with Start / `alt+s` (feed low, ready to E-stop). *"Warning:
   Machine not homed" = a switch tripped in the wrong order; check switch order.*

## 6.7 Tuning maximum feedrate

F1 Setup → F3 Config (137) → F2 Mach → **F1 Jog** (Jog Parameters / Max Rate field).
Estimate: **`(max motor rpm / motor revs per inch) × 0.85 = max feedrate`**. The estimate may
be too high (supply-voltage/load variation) — use MDI to ramp feed commands up to the real
limit. **Decrease** if: the DRO load bar graph goes red, position errors appear, or motors
overheat. *(Autotune exists at F4 PID → F5 Tune but is not recommended — it pushes to the
servos' max, often beyond what the machine can mechanically handle; manual tuning is preferred.)*

## 6.8 Manually tune acceleration

Acceleration = time to reach max velocity. **0.1 s is very fast; 1.0 is very slow; CNC12
defaults to 0.5.** Subjective — limited by mechanical stress and available current.

- Center the axes; **turn the real-time I/O display OFF** (`alt+I` toggles it); feed override
  to max (~120%).
- **Test program:** F1 Setup → F3 Config (137) → F4 PID → F1 PID Config → F1 Edit Program
  (edits `PID_Collection_Moves.txt`). Set the feedrate to the §6.7 max (e.g. `F500`). A good
  test: wait 0.1–1 s → accelerate to max → run at max 0.5–1 s → decel to stop → wait → repeat
  the opposite direction (ends with `M102` to loop). Sample:
  ```
  G20            ; Inch mode
  G90            ; Absolute
  F500           ; max feedrate
  G4 P0.5
  G1 X0.0
  G4 P0.5
  G1 X3          ; short move reaching max speed for 0.5–1 s
  G4 P0.5
  M102           ; loop forever
  ```
- **F2 Run Program**; **F7 Zoom All** for a clearer graph. Watch **VAbs** (velocity — should
  be a clean trapezoid) and **ErrAbs** (position error in encoder counts; **~15 counts is
  typical/acceptable**, zero is impossible). If accel is too fast you'll see excess ErrAbs,
  shock/vibration, bumpy motion, thunks/rapping, or position errors → stop, **increase the
  Accel value** (slower) until clean. If clean → **decrease Accel** (faster) and repeat.
  Edit `PID_Collection_Moves.txt` and repeat per axis. *(If it says "Finished Running
  Program" or nothing moves, there's a status-window error.)*

## 6.9 Fine DRO adjustment — TB36 Method 2

Calculate motor revs/inch (imperial) or mm/rev (metric) precisely with a **dial indicator**
and an **L-shaped test fixture** (6–12", longer = better; exact long-leg length known, e.g.
a 12.000" gauge block). *(A Centroid probe makes this easier; not covered here.)*

1. Mount the fixture parallel to the axis; jog (incremental near the end) **toward** the block
   only until the dial reads ≈0 *(backing up introduces backlash — restart if so)*.
2. **Zero:** F1 Setup → F1 Part → F10 Set Zero.
3. Raise the spindle (Z) clear; jog to the **base of the L**, dial ≈0 again.
4. **Calculate & enter** revs/in or mm/rev in F2 Mach → F2 Motor, same formulas as §6.5.
   Repeat until the DRO equals the gauge block; repeat per axis.

## 6.10 Backlash compensation — TB37

> Reduce **mechanical** lash to **< 0.001"** first — electronic comp helps point-to-point but
> overall accuracy is set by the mechanical lash.

1. Dial indicator on the spindle; **zero previous lash** values in F2 Mach → F2 Motor.
2. Mount a test fixture/gauge block; jog **toward** it only, dial ≈0; F1 Setup → F1 Part →
   F10 Set Zero.
3. F3 MDI: back away `G1 X-0.025 F0.5` then return `G1 X0 F0.5` (**very slow feed** — inertia
   skews fast feeds).
4. If the dial reads **< 0.001"**, enter that into **Lash Compensation** (F2 Mach → F2 Motor).
   If **> 0.001"**, fix the mechanical lash first.

## 6.11 Software travel limits — TB289

Without travel limits the axis runs at full speed until a limit trips and can crash the hard
stop. Software limits decelerate before the switch and reject G-code past the limit.

1. **Prereqs:** DRO calibrated (§6.5/6.9), limit switches working, max feedrate & accel set;
   restart and home.
2. **Show machine coordinates:** `alt+D` until the DRO corner reads **machine**.
3. Slow-jog away from home toward the far limit until it trips ("407 ## limit (#5000x)
   tripped").
4. Incremental-jog back until the limit clears ("340 ## limit (#500x) cleared").
5. F3 MDI: move **0.1" (2.5 mm)** further from the switch — this DRO position is the limit.
6. F1 Setup → F3 Config (137) → F2 Mach → F1 Jog → enter the value in **Travel (−)** or
   **Travel (+)**. *(Both limits = 0 disables travel limits; setting **one** non-zero enables
   **both**, so leave the home side at 0.)* Repeat per axis.
7. **Test:** jog toward a limit — it should stop at the software limit before the switch
   trips; a G-code past it throws "907 # axis travel exceeded, 325 Limit: job canceled".

## 6.12 Deadstart

In the Jog Parameters menu; governs axis direction reversal. Usually left at default on
mills. Very light, low-friction/low-inertia wood routing tables can benefit from a deadstart
change with other hand-tuning — call Centroid for that case.

## 6.13 Performing a system test — TB327

Some CNC12 versions show "Machine Setup Not Completed. Machine Is Not Ready To Run. Contact
Your Dealer" until a **System Test** is run to clear it. Procedure is in **TB327**; if it
doesn't apply to your system, contact technical support.

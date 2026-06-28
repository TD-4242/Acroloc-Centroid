# Software Install & Bench Test Reference

Windows prep, CNC12 install, software configuration, and the bench-test procedure.
Source: install manual Ch3, Ch4, and Appendix A. CNC12 screens are images in the manual
(cited by page). Menu keystrokes and parameter values are transcribed verbatim.

## Windows preinstallation (3.1, Appendix A)

- Consoles/PCs bought from Centroid ship preconfigured. Self-built PCs must meet the specs
  in **Tech Bulletin #273** (minimum hardware/benchmark). Configure a Windows 10/11 PC for
  CNC use per **TB309**. Run the **Centroid PC Tuner** to do most of the work.
- **Supported:** Windows 10 and 11 only. **Not supported:** Windows 8.1/7/older, macOS, Linux.
- **Before installing CNC12, UNINSTALL (not just disable) all anti-virus, anti-malware,
  and 3rd-party firewall software, then reboot.** Nearly 100% of CNC12↔ALLIN1DC comm
  problems are caused by AV/firewall software. The built-in Windows firewall is fine if
  you allow access as the manual specifies. If corporate policy requires AV/3rd-party
  firewall, keep the CNC12 PC **off the network**.

## CNC12 installation (3.2)

Bench config fully powered (per §2.4) and **ALLIN1DC powered on and connected to the PC by
Ethernet before running the installer.**

1. Download the latest **CNC12** from Centroid; extract the `centroid_cnc12_v…_installer`
   folder to the desktop and run the application.
2. Allow it past User Account Control / Windows Defender SmartScreen ("More info" →
   "Run anyway"); accept the license.
3. **Installer options:** Install Desktop Shortcuts (recommended); optionally Start CNC12
   at Startup; optionally Copy Manuals to Desktop.
4. **Control board model:** select **Oak/Allin1DC/MPU11** (not AcornSix/Acorn/Hickory).
5. **Component:** **CNC12 Mill** (or CNC12 Lathe). The manual assumes a mill.
6. **Units:** Imperial or Metric (changeable later).
7. **Network Adapter Setup** (ALLIN1DC must be powered + connected):
   - If an adapter is already set up for CNC use → "Yes" to keep using that Ethernet port.
   - Otherwise pick the **Ethernet** option (auto-configures the PC to **10.168.41.1** for
     CNC use) → "Yes" to change the IP. **DO NOT pick Wi-Fi.**
   - If no Ethernet option appears (Fig 3.2.10) → **STOP, Cancel**, confirm the board is
     powered and Ethernet-connected, re-check Windows config (§3.1 / TB270), retry.
   - With two Ethernet ports, install with the LAN/internet port disconnected so CNC12
     binds the correct port. One Ethernet + one Wi-Fi is acceptable.
8. **PLC program:** when prompted, "Yes" opens the PLC installer. Expand **Mill →
   ALLIN1DC → _Centroid_Standard**, then **Install**. (Lathe path: `_Lathe → _ALLIN1DC →
   _Centroid_Standard`.) PLC program quick reference: **Tech Bulletin #312**.
9. **Finish**, then **power off the PC and ALLIN1DC and restart everything.** Confirm CNC12
   starts.

**Comm troubleshooting:** "Timeout: MPU11 not responding" usually means the wrong Ethernet
port is configured. Control Panel → Network and Sharing Center → the ALLIN1DC's Ethernet →
Properties → Internet Protocol Version 4 (TCP/IPv4) → Properties → **Use the following IP
address: 10.168.41.1, Subnet mask 255.255.255.0** → OK, restart CNC12. See Appendix C.

### Importing a license

CNC12 runs free, but Pro/Ultimate features are locked without a license. From the main
screen: **F7 Utility → F8 Option → F2 Import License** → select the Centroid `.dat`
hardware-key file → "License successfully imported"; Software Level should match the
license and CNC Hardware Key should read **Yes**. Other messages → **TB325**.

## Bench test — disabling fault logic for testing (4.1)

CNC12 + the `Centroid_ALLIN1DC_Mill_standard.src` PLC monitor Limit Switches (inputs 1–8),
Lube Fault (input 9), Spindle Fault (input 10), E-Stop (input 11), and Axis Drive Faults
(inputs 17–20); any open input faults. To bench test, temporarily disable these.

1. **Machine home type:** F1 Setup → F3 Config (password **137**) → F1 Contrl → set
   **Machine home at powerup** to **Jog** → F10 Save. *(If changes won't save: close CNC12,
   right-click shortcut → Properties → Compatibility → "Run this program as an
   administrator".)*
2. **Disable jog-panel comm faults** (skip if you have a jog panel/pendant connected):
   F1 Setup → F3 Config → F1 Contrl → **Jog panel required = No** → F10 Save. Then power
   everything off, wait 30 s, power back up.
3. **Disable PLC faults** for limits/lube/spindle/E-stop/axis: at the main screen `alt+I`
   for the real-time I/O display, select each input, press `ctrl+alt+i` to invert it
   (LED red→green, a line drawn over it) until **inputs 1–11 are green** (leave any already
   green). `alt+I` again to exit.
4. **Label axes:** F1 Setup → F3 Config (137) → F2 Mach → F2 Motor → under **Label** set
   the axis count/labels (mill: 1=X, 2=Y, 3=Z; unused axes = **N**). Spindle axis is set
   in §6.4.
5. **Drive Bus assignment:** F1 Setup → F3 Config (137) → F3 Parms → F8 Next Table to
   **P300–P307**. Three-axis mill: **P300=1, P301=2, P302=3** (axis→drive-bus channel).
   **Unused axes must be set to 0 or errors occur.**
6. **Encoder assignment:** **P308=1, P309=2, P310=3** (MPU11 encoder channels P308–P315).
   Unused encoder axes can be left as-is.
7. **Encoder counts/rev:** F1 Setup → F3 Config (137) → F2 Mach → F2 Motor → set **Encoder
   counts/rev** per axis. Quadrature line count × 4 = counts/rev (2000-line = **8000**;
   5000-line = 20,000; 10,000-line "high-res" = 40,000).
8. **Disable stall detection:** F1 Setup → F3 Config (137) → F4 PID → `ctrl+v` →
   "Stall detection disabled" appears. **Must be redone every time the ALLIN1DC restarts.**
9. **Clear software-ready / stop faults:** restarting CNC12 without power-cycling hardware
   raises a "9039 Software Ready Fault"/"Software Exited" **stop fault** — clear by cycling
   E-Stop: `alt+I` → select **INP11 EStopOK_I** → `ctrl+alt+i` to toggle red→green. (Status
   shows 406 Emergency Stop Detected when red, 335 Emergency Stop Released when green.)
10. **Confirm faults cleared:** F3 MDI from the main menu — a clean MDI screen (Fig 4.1.15)
    means all faults cleared. All faults are stop faults; remove the cause then cycle E-Stop.
    Error log: F7 Utility → F9 Logs → F1 Errors.
11. **Virtual Control Panel (VCP):** if no physical jog panel — F1 Setup → F3 Config (137) →
    F1 Contrl → Jog Panel Type → spacebar to **Virtual** → F10 Save.
12. **Wireless MPG** (needs ≥ Pro license): import license, then F1 Setup → F3 Config (137) →
    F3 Parms → **#218 = 15** (4-axis mill/router), **=7** (3-axis), **=3** (lathe);
    **#348 = 15** (MPG on); **#350 = 100** (100 steps/rev). Restart CNC12.

## Bench test execution (4.2)

Requires a DVM. Uses `spindlebenchtest.cnc` (download from
`http://centroidcnc.com/usersupport/support_files/benchtest/spindlebenchtest.cnc`; place in
the CNC12 root `c:\cncm\ncfiles` directory; F5 Refresh in the Load menu).

### Spindle analog-output test

ALLIN1DC provides a **0 to +10 VDC** analog output for VFD spindle-speed control. Default
max spindle speed in Control Configuration is **3000 rpm**, so 0–10 V maps to 0–3000 rpm
(S1500 → +5 VDC, S1000 → +3.33 VDC).

1. DVM to VDC; connect the seven-pin terminal block to **H9**; insert DVM leads into H9
   (Fig 4.2.4), screws tight.
2. Load `spindlebenchtest.cnc`, **Cycle Start (alt+s)**. Enter each requested voltage
   reading (between Spindle Analog and Spindle Analog Com) and Cycle Start to continue; the
   program errors if a reading is off. "Job finished" = pass.
3. **Spindle bench-test troubleshooting:** if voltages are wrong, check the **DAC dip
   switches**. For 0–10 V operation set **1=Up, 2=Down, 3=Up, 4=Down, 5=Up** (see p.7 of
   the ALLIN1DC Technical Component manual at the end of the install manual).

### Encoder test

1. F1 Setup → F3 Config (137) → F4 PID.
2. Manually spin the motor shaft **counter-clockwise**; confirm **Abs Pos counts up** in the
   PID menu. Repeat per axis.
3. Rotate the motor one full revolution and record the count; F1 Setup → F3 Config (137) →
   F2 Mach → F2 Motor — the recorded count should ≈ the entered **Encoder counts/rev**.

# Tool-to-Bin Mapping (tools numbered > 12) - Design

Date: 2026-07-22
Status: revised after on-machine Phase A (approach changed - see Revision note)

## Revision note (what the machine taught us)

The first version of this spec assumed CNC12 had a generic "enhanced ATC" mode
that merely changed `SV_TOOL_NUMBER` into a bin while leaving the custom changer
flow intact, with a *conditional* PLC position report. On-machine testing
corrected that:

- **Machine parameter 160 is the ATC-TYPE selector**, confirmed by comparing every
  example config in `docs/official`: `0` = no built-in ATC (works today),
  `1` = non-random (tool number IS the pocket - no help for tools > 12),
  `2` = random (the tool-library **bin** column, what we want).
- The tool-library bin column **only exists at P160 != 0**. There is no way to get
  bin assignment while staying at P160 = 0. So random mode is required.
- At P160 = 2, `M6` did nothing (no motion, no error). Root cause: **CNC12 random
  ATC will not move the carousel until the PLC reports `SV_PLC_CAROUSEL_POSITION`**
  ("the carousel must not turn unless software is running"). Our PLC never reports
  it, so CNC12 sat silent. This is not an incompatibility - it is a required
  handshake we had not built.
- Reverting to P160 = 0 restored the custom tool change and removed bin assignment
  (owner confirmed), proving the two are mutually exclusive as-was.

The position report is therefore **required, not conditional**, and the target
mode is specifically **P160 = 2 (random)**.

## Goal

Assign a tool to a physical carousel bin in CNC12's tool library (e.g. tool 31
-> bin 2), and have `M6T31` spin the carousel to bin 2 and snap the tool in as
it does today. Tools 1-12 keep working (assigned bins 1-12).

## Background

### How the change works today (P160 = 0)

The tool swap is **Z-driven and mechanical**. `mfunc6.mac` stops the spindle,
parks Z at tool-change zero (`G53 Z0`), and fires `M94 /8` (`M6_SV`); the PLC's
`ATCStage` (STG16) unlocks and spins the carousel, decodes the 5 position
switches into `CarouselToolID_W`, and stops/relocks when
`CarouselToolID_W == ChangeToTool_W`. `ChangeToTool_W` is latched from
`SV_TOOL_NUMBER` in exactly one rung (`Centroid-Acroloc-ALLIN1DC.src:2931`).

**Put-back is automatic and mechanical** (owner): the outgoing tool is released
into the bin currently under the spindle when Z reaches zero with
`ATC_Z_Zero_Release_I` (INP27) true. Because the carousel is always parked at the
current tool's bin (where `ATCStage` last stopped), the deposit lands the tool in
its own home bin with no software move. This is why **no put-back choreography is
needed** - unlike the umbrella example's two-move `AtPutbackLocation` dance.

### What random ATC needs (from the working umbrella example)

The umbrella ATC (`docs/official/_ALLIN1DC/_atc/_umbrella/cncm/`) is a working
random changer. The relevant, transferable parts:

- **Same M6 trigger.** `M6 IS SV_M94_M95_8` (umbrella src:958) - identical to our
  `M6_SV IS SV_M94_M95_8`. CNC12 does not use a special tool-change variable in
  random mode; the macro's `M94 /8` is the request in both.
- **Boot seed** (umbrella src:1198-1200): `CarouselPosition_W =
  SV_ATC_CAROUSEL_POSITION` (CNC12's persisted last-known bin),
  `PutBackPosition_W = SV_ATC_TOOL_IN_SPINDLE`.
- **Report position every scan** (umbrella src:2530): `SV_PLC_CAROUSEL_POSITION =
  CarouselPosition_W`. **This is the missing piece.**
- **Bin request** (umbrella src:2543): `RequestedBinPosition_W = SV_TOOL_NUMBER` -
  in random mode `SV_TOOL_NUMBER` is the **bin**. Our `ChangeToTool_W =
  SV_TOOL_NUMBER` already does exactly this.
- Max bin from `SV_MACHINE_PARAMETER_161`; ATC timers P961/P965 exist if tuning
  is needed.

The umbrella tracks position by dead-reckoning a single counter pulse. **We do
better:** our 5 switches decode the **absolute** bin ID every time a bin passes,
so our current bin is always known directly (the last matched
`CarouselToolID_W`), no dead-reckoning.

## Approach

Run **P160 = 2 (random)** so the tool-library bin column exists and CNC12 loads
`SV_TOOL_NUMBER` with the bin, then **add the position-report handshake** so
CNC12 permits the change. Our existing `ATCStage` search is the carousel
indexer; we wrap it in the handshake rather than rewrite it.

Concretely, the delta from today's working flow:

1. **Config:** `P160 = 2`, `P161 = 12` (max bin); assign bins in the tool library
   (tools 1-12 -> bins 1-12, tool 31 -> bin 2, etc.).
2. **PLC (required):** a new `CurrentBin_W`, seeded at boot from
   `SV_ATC_CAROUSEL_POSITION` and updated to the settled bin after each change
   (from `CarouselToolID_W`), reported every scan as
   `SV_PLC_CAROUSEL_POSITION`. All outside `ATCStage`, tagged `; Acroloc`.
3. **`ATCStage`:** unchanged - `ChangeToTool_W = SV_TOOL_NUMBER` already receives
   the bin.
4. **`mfunc6.mac`:** unchanged unless the probe (Phase 0) shows CNC12 needs
   additional completion signaling in random mode; the `M94 /8` request and
   `M100 /93016` -> `M95 /8` completion are already the right primitives.

## Phase 0 - On-machine probe (validation, do first)

Confirms exactly what this CNC12 version waits on before we finalize the PLC/
macro edits. At **P160 = 2**, with the PLC diagnostic screen open (**ALT+I**),
run `M6T5` and record:

- Does Z move (does `mfunc6` start)? Does `W72` (`ChangeToTool_W`) change?
- Any text on the status/message line (even quiet)?
- Is there an **ATC setup / carousel-position "reset"** screen (to declare the
  current bin / tool in spindle)? What do parameters **160 / 161** say on-screen?

Expected: with no `SV_PLC_CAROUSEL_POSITION` report, nothing moves - matching the
observed silent M6. This confirms Phase 1 is the fix. If instead CNC12 also
demands completion signals beyond the existing `M95 /8`, Phase 2 covers it.

## Phase 1 - PLC position-report handshake (required)

All additions outside `ATCStage`; tagged `; Acroloc`.

- **Definition:** `CurrentBin_W IS W78` (W78 free, adjacent to the ATC words
  W71/W72).
- **Boot seed** in `InitialStage` (STG2): `CurrentBin_W = SV_ATC_CAROUSEL_POSITION`
  so a cold start adopts CNC12's persisted position.
- **Latch + report** in `MainStage`, right after the ATC kickoff rung (src:2931):

  ```
  ; Acroloc -- random ATC: report carousel bin to CNC12 (outside ATCStage)
  IF !ATCStage && CarouselToolID_W > 0 THEN CurrentBin_W = CarouselToolID_W
  IF True_M THEN SV_PLC_CAROUSEL_POSITION = CurrentBin_W
  ```

  The latch only updates between changes (never mid-spin), so CNC12 always sees a
  settled bin. `CarouselToolID_W` holds the matched bin from end-of-change until
  the next kickoff zeroes it.
- `./compile.sh` after the edit; report the token/warning delta.

## Phase 2 - mfunc6 completion signaling (conditional on Phase 0)

Only if the probe shows CNC12 will not mark the change complete on the existing
`M95 /8` in random mode. If needed, mirror the umbrella macro's completion
signaling (e.g. its `M94 /41` "report tool info") - the minimum set the probe
identifies, preserving the graph/search guard and `N1000` label. If the probe
shows the existing handshake suffices, `mfunc6.mac` is unchanged.

## Non-goals

- **No put-back move logic.** Put-back is mechanical (Z-zero + `ATC_Z_Zero_Release_I`);
  the umbrella's `AtPutbackLocation` two-move dance does not apply.
- No change to `ATCStage`'s switch decode, peak/`InToolSelect_M` gating,
  match/exit rung, or the 20 s `ATCSpin_T` watchdog.
- No dead-reckoning position tracking; we use the absolute switch decode.
- No P160 = 0 param-table fallback (it cannot surface the tool-library bin
  column, which is the whole point).

## Deliverables

1. This design doc.
2. On-machine: P160 = 2, P161 = 12, tool-library bin table, Phase 0 probe result
   recorded.
3. PLC: `CurrentBin_W` (W78) + boot seed + `SV_PLC_CAROUSEL_POSITION` report,
   tagged `; Acroloc`, verified with `./compile.sh`.
4. `mfunc6.mac` completion signaling only if Phase 0 requires it.
5. Doc updates: `docs/plc-spec/atc.md` (+ pinned commit hash) and the
   `acroloc-s10` ATC references - random-ATC mode, P160 = 2, the position
   handshake, and `SV_TOOL_NUMBER`-as-bin.

## Testing / rollout

- Phase 0 probe first (records what CNC12 waits on).
- After Phase 1: `./compile.sh` clean (delta reported); load the `.plc`; at
  P160 = 2 run `M6T31` (tool 31 -> bin 2) and confirm the carousel indexes to bin
  2 and `SV_PLC_CAROUSEL_POSITION` tracks. Regression: `M6T5` (bin 5) still
  changes normally.
- Cold-start check: power-cycle, confirm the seeded position matches the physical
  carousel (use the ATC reset screen if one exists) before the first change.

# VARA Cartridge Interface — CONTRACT SPEC v0.2

**Date:** 2026-06-03 · **Status:** contract frozen for Phase 2/3; dovetail *profile* is a
Phase-2 study variable (clearly tagged below). **This document is the single source of
truth.** Every core and cartridge part references it. Change a value here → propagate
everywhere downstream (architecture, CAD, electronics). Bump the version on any change.

> Two kinds of numbers live here. **[CONTRACT]** = frozen; any cartridge ever built must
> conform, and the core mates to it. **[STUDY]** = the dovetail cross-section geometry being
> optimized in Phase 2; the current best always lives in `cad/connector/`. The contract is
> stable even while the profile evolves — that separation is deliberate.

---

## 1. Coordinate datum & reference frame [CONTRACT]

A single right-handed frame governs both halves. The **female** rail is in the **core**;
the **male** rail is on the **cartridge**.

```
            +Z  (out of core mating face; OPTICAL AXIS ∥ +Z; cartridge sits above)
             │           camera (in core) looks out +Z through cartridge barrel
             │
             │     ┌───────────── cartridge envelope ──────────────┐
             │     │   ◎ optical axis @ (Xopt,0)   ⦿ LED ring      │
             O─────┼────●●●●●● pad array @ (Xpad, Y)────────────────┼──▶ +X
          (datum   │                                                │   (removal dir;
           origin) └────────────────────────────────────────────────┘   insertion = −X)
             │      ◀── slides −X to seat against stop at X=0 ──
            +Y (lateral, into page complete RH frame)
```

- **Origin O** = center of the **positive-stop face**, on the rail axis, at the mating
  base plane. All features are dimensioned from O.
- **+X** = cartridge **removal** direction. Insertion travels **−X** until the male rail's
  seat face contacts the stop at **X = 0** (hard positive stop — cartridge cannot
  over-insert).
- **+Z** = normal to the core mating base plane, pointing toward the cartridge. The core
  camera looks out **+Z**; the cartridge lens barrel is coaxial above it.
- **+Y** = lateral, completing the right-hand frame.

---

## 2. Envelope [CONTRACT]

| Item | Value | Note |
|---|---|---|
| Max cartridge bounding box (W×L×H = Y×X×Z) | **36 × 32 × 26 mm** | hard ceiling; hero cartridge sits inside this |
| Mating base plane | Z = 0 | shared face between core and cartridge |
| Insertion direction | −X | seats against stop at X=0 |
| Rail nominal length (along X) | **24 mm** [STUDY] | bearing length; affects angular stiffness |

---

## 3. Pad array & optical axis (the alignment-critical features) [CONTRACT]

Pogo pins live in the **core** (protrude +Z); flat gold pads on the **cartridge** (on the
Z=0 plane, facing −Z toward the core).

| Feature | Location (from O) | Spec |
|---|---|---|
| Pad array center | X = **+6.0 mm**, Y = 0, Z = 0 | engages only near full seat |
| Pad pitch / count | **2.54 mm × 6** | pins along Y; outer pads at Y = ±6.35 mm |
| Pad size | **Ø2.0 mm gold** | ≥ pogo crown + 2×(0.3 mm budget) + margin |
| Pogo working compression | **0.5 mm** | sets the alignment budget below |
| **Optical axis** | X = **+15.0 mm**, Y = 0, along +Z | core camera ↔ cartridge barrel, coaxial |
| Optical clear bore (keep-out) | **Ø14 mm** about the optical axis, full Z | no structure intrudes (lens clear aperture ~Ø12 + margin) |
| Pad keep-out | pad rect + 1.0 mm margin, +Z to pogo housing | no ribs/walls in the contact volume |

### 3.1 Alignment budget [CONTRACT] — the number the dovetail must hold
The pogo compression (0.5 mm) and pad oversize give an absorbable misalignment of
**±0.3 mm** at the **pad plane** *and* at the **optical axis**, in Y and X.

This budget is **lateral + angular combined**. Angular slop is the dominant risk because
the optical axis (X=+15) is **9 mm forward of the pad centroid (X=+6)**, so rail tilt is
amplified by lever arm:

```
   error_at_optical_axis ≈ lateral_play + θ · (distance from rail-bearing centroid)
   require: error_at_optical_axis ≤ 0.3 mm  AND  error_at_pads ≤ 0.3 mm
```

→ **Phase-2 acceptance:** the chosen `flank_clearance` + rail bearing length must keep
both the pad-plane and optical-axis error ≤ 0.3 mm under worst-case clearance + a stated
print-tolerance allowance. This is the dovetail study's primary quantitative gate.

---

## 4. Electrical pinout — FINAL [CONTRACT]

Pin order along Y, from −Y outer pad (pin 1) to +Y outer pad (pin 6):

| Pin | Net | Direction / level | Notes |
|----:|-----|-------------------|-------|
| 1 | **V+ (3V3, switched)** | core→cart | Core-side **load switch + current limit, ≤150 mA budget**. Enabled by firmware *after* CD# asserts. Single logic+LED rail keeps the interface to 6 pins. |
| 2 | **GND** | — | Reference. (Provision: a longer GND pogo could make-first for hot-plug safety; design-time option, not testable without hardware.) |
| 3 | **I²C SDA** | bi | Pull-up **on core**. EEPROM + any future cartridge I²C sensor. |
| 4 | **I²C SCL** | core→cart | Pull-up **on core**. 100/400 kHz. |
| 5 | **CD# (cartridge-detect)** | cart→core | Cartridge **ties to GND**; core pulls up. Falling edge = seated → core enables V+ → reads EEPROM. Replaces the seed's resistor/1-Wire ID (Zero 2 W has no ADC, so a resistor divider would need an extra ADC chip — rejected). |
| 6 | **INT** | cart→core | Active-low, core pull-up. Cartridge interrupt (e.g. shutter button, sensor data-ready). |

### 4.1 Cartridge ID — EEPROM scheme [CONTRACT]
- I²C EEPROM (24AA02-class), fixed address **0x50**.
- Layout (starting): `magic(2) | cartridge_type(1) | hw_rev(1) | serial(4) | name[16] |
  calibration/params(rest)`. The core auto-detects which cartridge is mounted and adapts
  the UI/pipeline.
- Cheapest possible cartridge still carries this EEPROM (~$0.10) — cleaner and more
  capable than a resistor code, and it reuses pins 3/4 (no extra pin).

### 4.2 Mate/power sequence (firmware, not mechanical staggering)
Pads are coplanar and pogos equal-length → all contacts close together at full seat.
Sequencing is handled in firmware: detect **CD# low** → enable **V+ load switch** →
settle → read **EEPROM @0x50** → configure pipeline → arm **INT**. This avoids needing
mechanically staggered pin lengths (which we can't validate without hardware).

---

## 5. Dovetail profile — Phase-2 STUDY SEED [STUDY]

These define the *cross-section* being optimized. **Not** part of the frozen contract —
the current best geometry always lives in `cad/connector/` and feeds Part IV's study.
**Resolved in Phase 2 — see [`dovetail-study.md`](dovetail-study.md) for the 6-generation
derivation.** Configuration: **dual rails at Y = ±13 mm** flanking the central pad/optical
channel (a single central rail would collide with the pads + optical bore).

| Param | Seed | **Resolved (Gen 6)** | Meaning |
|---|---|---|---|
| `dovetail_angle` | 55° | **55°** | Flank angle from base plane (Z=0). 90° = vertical; <90° = undercut. 55° ⇒ 35°-from-vertical flanks — self-supporting when printed rail-axis-vertical (see §6). |
| `flank_clearance` | 0.20 mm | **0.13 mm** | per-side gap. Tightened to hold the ±0.3 mm budget with margin (E_align = 0.28 mm). |
| `detent_depth` | 0.6 mm | **0.50 mm** | snap engagement; balances retention (~10.6 N) vs. finger strain. |
| `rail_length` | 24 mm | **26 mm** | bearing length; keeps pads (X=6) & optical (X=15) well inside the span. |
| `wall_thk` | 2.4 mm | **2.4 mm** | female wall (≈6 perimeters @0.4 mm nozzle). |
| `lead_in_chamfer` | 1.0 mm | **1.2 mm** | +X mouth lead-in. |
| detent | X ≈ +2.5 mm | **cantilever finger 13×1.1 mm, one per rail** | Gen 1's wall-flex detent over-strained ~5×; replaced by dedicated snap fingers. |
| (print req) | — | **rail-axis-vertical; per-part tol ≤ ±0.075 mm** | required to meet alignment + keep flanks support-free. |

**Resolved performance (analytical, validated-by-design — NOT tested):** alignment
**0.28 mm ≤ 0.30**; detent **SF_yield 5.1 / SF_interlayer 2.56**; insertion **~2.9 N**,
retention **~10.6 N**; all geometry gates 6/6, watertight.

**Objectives in tension (per plan §4.2):** stiffness↔printability ·
retention force↔insertion ease · tight fit (alignment)↔wear life · wall thickness↔size.

---

## 6. Material & print intent [CONTRACT-level intent; details Phase 3]

- **Material:** PA12-CF, FDM. No printer in the loop → all fits are
  **"validated-by-design, print-ready," never tested.**
- **The core printability↔strength tension (to resolve in Phase 2):**
  - *Rail axis vertical (X ∥ Z-build):* sliding flank faces become near-vertical walls →
    clean surfaces, **no support on functional faces**. But layer lines run ⟂ to insertion
    and the **detent cantilever loads across layers** (weak interlayer adhesion in CF).
  - *Flat on bed (X horizontal):* strong, isotropic-ish detent; but the undercut flanks
    (35° overhang at 55°) become **overhangs needing support → wrecks the sliding faces.**
  - Phase 2 resolves this with geometry (e.g. raising `dovetail_angle` toward printable
    overhang limits) + orientation, logged as generations.

---

## 7. Keep-out summary (for body integration, Phase 3)

| Zone | Keep-out |
|---|---|
| Optical bore | Ø14 mm cylinder about (X=+15, Y=0), full Z, both halves |
| Pad/pogo volume | pad rect +1 mm margin, +Z to pogo housing height |
| Detent travel | clear path for the male rail X = 0 → +24 mm during insertion |
| LED ring | annulus around optical bore, within cartridge envelope; powered from V+ (≤150 mA) |

---

## Change log
- **v0.2** (2026-06-03): Phase 2 resolved the [STUDY] dovetail profile (§5) — dual rails,
  cantilever snap fingers, c=0.13, rail_length=26, etc. **[CONTRACT] sections unchanged.**
  See `dovetail-study.md`.
- **v0.1** (2026-06-03): initial contract. Camera in core; optics-only hero cartridge;
  6-pin pogo (V+/GND/SDA/SCL/CD#/INT); EEPROM ID @0x50; ±0.3 mm alignment budget serving
  pads *and* optical axis; dovetail profile seeded for Phase 2.

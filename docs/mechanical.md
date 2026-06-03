# VARA — Mechanical Design & Design-for-AM (Phase 3)

**Date:** 2026-06-03 · Parts: **core body** + **hero vision cartridge**, both consuming the
**resolved Gen-6 connector geometry** (`connector-spec.md` v0.2) via `dovetail_lib`
primitives — the `[STUDY]` geometry was **not re-opened**. Source:
`cad/core/core_body.py`, `cad/cartridge/vision_cartridge.py`, `cad/vara_assembly.py`.

> **Honesty banner:** No printer is in the loop — every fit/orientation is
> **"validated-by-design, print-ready," never tested.** Material is **PA12-CF** (FDM).
> Internal packaging (Pi, battery, PMIC) is dimensionally representative, not a routed
> layout. The core is modeled as a **sealed unibody** for a clean watertight single-STL
> deliverable; the production part splits on a rear parting line (see §6).

---

## 1. What was built (and the gate results)

| Part | bbox (mm) | mass (PA12-CF) | solids | watertight | gates |
|---|---|---|---|---|---|
| Core body | 44 × 64 × 20 | 21.9 g | 1 | **yes** | **5/5** |
| Vision cartridge | 26 × 35.6 × 19 | 5.9 g | 1 | **yes** | **5/5** |
| Assembly (semi-exploded) | 44 × 64 × 43 | — | 2 | yes | **0 interferences** |

**Geometry gates run (forge `REQUIREMENTS`, on the real solids):**
- Core: valid+watertight · optical bore Ø13 clear path · pad strip flat (nothing past the
  mating plane) · rail socket actually formed · **protected finger-root fillet ≥ 0.5 mm**.
- Cartridge: valid · barrel bore (optical path) clear end-to-end · pad strip exposed below
  the mating plane · within 32×36×26 envelope · rails+barrel **fused to one solid**.

**Device proportions — honest consequence of the connector.** The rail span (35.6 mm in Y)
plus the 1.69″ display set the core at 44 W × 64 H × 20 T mm: a chunky, grippable instrument,
not a thin phone. That thickness/height is *driven by the frozen connector geometry* and the
need to seat the camera coaxially behind the cartridge — stated plainly rather than fought.

---

## 2. Core body — feature inventory
Display: 1.69″ 240×280 bezel recess (module 30.4×36.6, +0.4 clearance) with a through window
to the **28.0 × 32.6 mm active area** (viewfinder + caption split is software on one panel).
Back: integrated **female rail socket** (Gen-6, with the snap-finger slots + detents) and the
**Ø14 optical bore** coaxial with the cartridge barrel, behind it a camera mount pocket.
Sides/edges: **USB-C** cutout (bottom), **jog-encoder** aperture (right edge), **I²S mic**
port (bottom), **speaker grille** (3×3, front lower). Internal: sealed electronics cavity +
**4× M2.5 heat-set bosses** on the Pi Zero 2 W hole pattern (58 × 23 mm).

## 3. Vision cartridge — feature inventory
**Male rails** (Gen-6, consumed as-is, with seating dimples) → backing plate (3 mm) →
**macro-lens barrel** coaxial on the optical axis (Ø12 outer, **Ø8 bore = optical path**,
12 mm tall). **LED-ring recess** (Ø16/Ø12.5, 2 mm) around the barrel base facing the subject.
**EEPROM-ID pocket** (5×4×1.6 mm) on the underside near the pad strip. **6 flat pogo-pad
seats** (Ø2.0, 2.54 mm pitch, 0.3 mm recess) on the underside at X=6. Optical coaxiality of
the barrel is governed by the connector's **±0.28 mm** alignment budget.

---

## 4. Design-for-AM — per part

### Print orientation (the real tension, resolved per part)
There is **no single orientation optimal for every face**; each part is oriented for *its*
most critical faces, and the connector's alignment margin (0.28 < 0.30 mm) + the finger-root
fillet absorb the residual.

- **Core body → front-face-down.** Screen face flat on the bed (best cosmetic face); the
  back socket + bosses build upward. Two payoffs: (1) the female groove flanks sit at ~35°
  from vertical — **within the FDM ~45° self-support limit, no support in the sliding zone**;
  (2) layers stack along the device thickness (conn-Z), so the **snap finger flexes
  *in-plane*** → the **in-plane SF_yield ≈ 5.1 applies, not the interlayer case** (better than
  the Phase-2 worst-case assumption). Bosses' heat-set bores open upward (toward the print
  top), clean to ream.
- **Vision cartridge → rail-axis (X) vertical** (stand on the +X mouth end), per the Phase-2
  connector resolution. Rail flanks become near-vertical walls → **support-free sliding
  faces** (the alignment-critical surfaces win). Trade-offs, stated: the **barrel bore prints
  horizontally** (top crown slightly rough → **ream the Ø8 bore**, standard for an optical
  barrel); the **pad face prints vertical** → the flat gold pads are an adhered contact strip
  that seats into the 0.3 mm recess, so layer texture under them is non-critical.
  *(Rejected alternative: rail-floor-down — leaves a 26 mm unsupported plate-underside bridge
  across the central pad/optical channel, which would need support exactly on functional
  faces. Rejected.)*

### Wall thickness, clearances, supports, fasteners

| Item | Core | Cartridge |
|---|---|---|
| Wall thickness | 2.4 mm side / **3.0 mm front (screen)** (≈6–7 perimeters @0.4 mm) | 3.0 mm plate / **2.0 mm barrel** |
| Connector walls | female `wall_thk` 2.4, finger 1.1 (from study, unchanged) | rails per study |
| Support on functional faces | **none** (front-down → flanks self-support; finger in-plane) | **none on flanks** (rail-vertical); bore reamed |
| Fasteners / heat-set | **4× M2.5 heat-set** (Pi mount); melt bore Ø3.4 (Ø2.2 pilot shown) + rear-cover corner inserts (production) | **none** — snap-fit retention; LED ring / EEPROM / lens retained by pockets + adhesive |

### Tolerance call-outs
| Feature | Nominal | Tolerance / clearance |
|---|---|---|
| Dovetail flank fit | `flank_clearance` 0.13 mm | **per-part print tol ≤ ±0.075 mm** (calibrated printer) — required to hold ±0.30 mm budget (study §4) |
| Display module pocket | 30.4 × 36.6 mm | +0.4 mm |
| Optical bore | Ø14 (lens Ø12) | +0.0/−0.0 keep-out; lens clear aperture ≤ Ø12 |
| Pad pattern | 2.54 mm pitch, Ø2.0 | recess 0.3 mm; pads = adhered contact strip |
| USB-C cutout | 9.2 × 3.6 mm | +0.4 mm over connector body |
| Heat-set boss bore | Ø3.4 (M2.5) | per insert datasheet |

---

## 5. Keep-outs — validated by gate (not by eye)
- **Optical bore:** a Ø13 test cylinder through the core back is empty (< 5 mm³); the
  cartridge barrel **bore** is open end-to-end — the optical path is clear and coaxial. ✔
- **Pad strip:** nothing on either part protrudes past the mating plane into the X=6 pad
  footprint → pads stay flat for pogo contact. ✔
- **Central channel:** rails are outboard at Y=±13 (inner edge ≥ 7.0 mm by the connector
  gate), so pads (Y±6.35) and the Ø14 bore stay clear. ✔
- **Envelope:** cartridge 26×35.6×19 ≤ 32×36×26. ✔ (Y=35.6 is tight against the 36 mm limit
  — flagged; any future wider rail would breach it.)

## 6. Production note (why the core is a sealed unibody here)
A printed enclosure is two shells. The single watertight STL seals the electronics cavity
for a clean manifold deliverable; the **production core splits on a rear parting line** into
the front housing (shown) + a back cover, joined at the **4× M2.5 heat-set bosses** (on the
real Pi hole pattern). The cavity dimensions and boss pattern are the real internal layout;
only the closing face is sealed in this STL. The cartridge needs no such split (snap-fit).

## 7. Protected feature — finger-root fillet
The detent **finger-root fillet (0.6 mm)** is a **functional** feature: the straight-beam
stress model (study §2) understates the real stress concentration at the finger root, so the
fillet is what keeps the actual peak stress in check. It is gated (`finger_root_fillet ≥ 0.5`)
and **must not be reduced for packaging convenience**, per the Phase-3 brief.

## 8. Outputs & honest limitations
**Outputs:** `cad/core/core_body_v1.{stl,step}`, `cad/cartridge/vision_cartridge_v1.{stl,step}`,
`cad/vara_assembly_v1.glb`, per-part diagnostics in `cad/*/out/`.
**Limitations:** (1) internal packaging is representative, not routed — Pi/battery/PMIC fit is
asserted by envelope, not by a populated layout; (2) the sealed-unibody core defers the real
parting-line/cover detailing; (3) no fit, insertion, or drop behaviour is measured —
validated-by-design only.

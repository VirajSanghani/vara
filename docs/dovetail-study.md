# VARA Dovetail Connector — Optimization Study (Phase 2)

**Date:** 2026-06-03 · **Centerpiece per Build Plan Part IV.**
Parametric source: `cad/connector/dovetail_lib.py` · generations: `cad/connector/genparams.py`
· analytics: `cad/connector/analysis.py` · artifacts: `cad/connector/{out,glb}/`,
`connector_male_v1.stl`, `connector_female_v1.stl`, `connector_assembled_v1.glb`.

> ## ⚠️ Honesty banner — read first
> - **No FEM is available in this environment** (see `tool-capabilities.md`). The detent
>   stress numbers are **first-order analytical hand-calculations (cantilever beam theory),
>   NOT FEA.** They are order-of-magnitude design guidance.
> - **No printer is in the loop.** Every fit/tolerance is **"validated-by-design,
>   print-ready," never tested.**
> - Material constants are **estimates** from typical CF-PA12 ranges, not a measured
>   datasheet. Each is marked *(est.)*.
> - **Marginal and failing generations are kept in the table** and drive the next change.
>   Nothing is silently discarded.

---

## 1. The problem (why this is a real multi-objective optimization)

The shared cartridge connector must simultaneously: **locate** the cartridge so its pads
*and* the optical axis land inside the pogo/optical budget (**±0.30 mm**, set by 0.5 mm
pogo compression — `connector-spec.md` §3.1); **slide smooth then lock positive**;
**survive thousands of cycles** in PA12-CF (wear + creep); **carry power/data**; and **be
printable** despite layer anisotropy and undercut overhangs. These objectives genuinely
fight: `stiffness ↔ printability`, `retention force ↔ insertion ease`, `tight fit
(alignment) ↔ wear life`, `wall thickness ↔ size`.

**Configuration decision (made before Gen 1):** **dual rails at Y = ±rail_offset**, not one
central rail. A single centered dovetail would collide with the pad array (Y = ±6.35) and
the optical bore (Ø14 @ Y=0) — both live down the centerline. Two outboard rails leave the
center clear, and the wide Y-separation strongly resists roll/pitch. Geometry gate
`req_central_channel_clear` enforces rail inner edge ≥ 7.0 mm so the optical bore stays free.

---

## 2. The two models

### Model A — Alignment (analytical bound)
For a feature at axial position `X_f` **inside** the bearing span `[0, rail_length]`, the
worst-case lateral error is bounded by clearance + dimensional tolerance and is **not**
amplified by rail tilt: a straight rail held to ±c at both span ends keeps every interior
point within ±c (linear interpolation of two values each ≤ c stays ≤ c). Amplification only
happens for features *outside* the span — hence the design rule **keep pads (X=6) and
optical axis (X=15) inside `rail_length`.**

```
E_align = flank_clearance + 2·print_tol      (worst-case, two printed halves)   ≤ 0.30 mm
```
`print_tol` = assumed per-part FDM tolerance *(est.)*. RSS alternative
`flank_clearance + √2·print_tol` is also computed (less conservative); we gate on worst-case.

### Model B — Detent snap (straight cantilever, end load) — **analytical, NOT FEA**
Classic snap-fit beam relations (Bayer/BASF snap-fit design guide):
```
ε_max = 3·t·δ / (2·L²)            F = E·b·t³·δ / (4·L³)        (= 3EIδ/L³, I = b·t³/12)
F_ins = F·(μ+tanθ)/(1−μ·tanθ)     F_ret = F·(μ+tanβ)/(1−μ·tanβ)
```
`t`=beam thickness, `δ`=snap deflection, `L`=beam length, `b`=beam width (=detent_w).
**Gen 1 has no finger** → the female mouth-lip *wall* flexes (`L=engage_depth=4`,
`t=wall_thk=2.4`). **Gen 2+** use a dedicated cantilever finger. There are **two detents
(one per rail)** → reported `F_ins`/`F_ret` are ×2.
`SF_yield = ε_yield/ε_max` (target ≥ 2 for cycle life); `SF_interlayer = k·ε_yield/ε_max`
(if the beam bends *across* print layers — the FDM anisotropy case).

### Assumed constants — CF-PA12 on FDM *(estimates, not measured)*
| Symbol | Value | Basis |
|---|---|---|
| `E_flex` | **5000 MPa** *(est.)* | CF-PA12 spans ~3000–8000 MPa |
| `ε_yield` | **2.5%** *(est.)* | CF fill embrittles vs neat PA12 (~10%+) |
| `k_interlayer` | **0.50** *(est.)* | interlayer Z-strength ~40–60% of in-plane |
| `μ` | **0.25** *(est.)* | PA12-CF self-friction |
| `θ_insert / β_retain` | **30° / 60°** | lead ramp / retention ramp |

---

## 3. Two kinds of gate (don't conflate them)
- **Geometry gates (forge `REQUIREMENTS`, run on real built solids):** captive, clearance
  present, central channel clear, within cartridge envelope, min wall, both solids valid +
  watertight. **All six generations pass 6/6 and are watertight** — i.e. every generation is
  a *buildable, valid* part. Gen 1 is geometrically fine yet **functionally catastrophic**.
- **Functional gates (analytical, Models A/B):** the ±0.30 mm budget and the snap SFs.
  This is where the generations actually differ.

---

## 4. Generation table

Functional numbers from `analysis.py` (`cad/connector/out/analysis.txt`); geometry from
`forge build`. `c`=flank_clearance, `δ`=detent_depth, `E_w`=worst-case alignment error.

| Gen | What changed | Why (problem the previous gen exposed) | c / tol | E_w ≤0.30 | finger L×t | δ | ε_max | SF_y | SF_z | F_ins / F_ret (N) | Geom | **Verdict** |
|----:|---|---|---|---|---|---|---|---|---|---|---|---|
| **1** | baseline = spec seed | — (establish baseline) | 0.20/0.10 | **0.40 NO** | none (wall flexes) 4×2.4 | 0.60 | **13.5%** | 0.09 | 0.05 | **1253 / 4531** | 6/6 wt | **FAIL align+stress** |
| **2** | + dedicated cantilever finger | Gen1 detent over-strains the stiff lip wall by ~5× and needs 1253 N to insert (would shatter) | 0.20/0.10 | 0.40 NO | 12×1.2 | 0.60 | 0.75% | 3.33 | 1.67 | 5.8 / 21.0 | 6/6 wt | **FAIL align+interlayer** |
| **3** | tighten c 0.20→0.15; declare calibrated print-tol ±0.075 | Gen2 alignment still 0.40 > 0.30 | 0.15/0.075 | **0.30 (=budget)** | 12×1.2 | 0.60 | 0.75% | 3.33 | 1.67 | 5.8 / 21.0 | 6/6 wt | **FAIL interlayer** *(align marginal, zero margin)* |
| **4** | δ 0.60→0.45; lead-in 1.0→1.2 | Gen3 finger fails interlayer SF (1.67<2); tight c risks bind on insertion | 0.15/0.075 | 0.30 (=budget) | 12×1.2 | 0.45 | 0.56% | 4.44 | **2.22** | 4.4 / 15.7 | 6/6 wt | **PASS** *(but zero align margin)* |
| **5** | finger 12×1.2→13×1.0; c 0.15→0.12 | Gen4 has no alignment margin; want robust interlayer SF | 0.12/0.075 | **0.27** | 13×1.0 | 0.45 | 0.40% | 6.26 | 3.13 | 2.0 / **7.2** | 6/6 wt | **PASS** *(lock now light)* |
| **6** | finger t 1.0→1.1, δ 0.45→0.50, rail 24→26 | Gen5 retention dropped to ~7 N (soft lock); buy margin everywhere | 0.13/0.075 | **0.28** | 13×1.1 | 0.50 | 0.49% | 5.12 | 2.56 | 2.9 / **10.6** | 6/6 wt | **PASS ✓ resolved** |

### Reasoning, generation by generation
- **Gen 1 — baseline.** Build the seed verbatim. Geometrically valid, but the detent is
  formed by flexing the 2.4 mm-thick, 4 mm-tall female lip wall 0.6 mm: ε ≈ **13.5%**, ~5×
  the estimated yield strain, with an absurd ~1253 N insertion force. It would fracture
  before assembling. Alignment 0.40 mm also blows the budget. *Two problems exposed:
  detent stiffness, alignment.*
- **Gen 2 — give the detent its own spring.** Replace wall-flex with a dedicated cantilever
  snap finger (L=12, t=1.2). Strain drops to 0.75%, in-plane SF 3.3, insertion a sane 5.8 N.
  But **interlayer SF = 1.67 < 2** (if the finger bends across print layers) and alignment
  is still 0.40. *Exposed: print-orientation sensitivity of the thin finger; alignment.*
- **Gen 3 — attack alignment.** Tighten clearance to 0.15 and **declare a print-tolerance
  requirement** of ±0.075 mm/part (calibrated printer). E_align lands at **exactly 0.30 —
  on the budget, zero margin.** Kept as a marginal finding. Interlayer SF still 1.67.
  *Exposed: the fit is now tight (bind risk) and still no interlayer margin.*
- **Gen 4 — lower the detent, ease insertion.** Drop δ to 0.45 (cuts strain and force) and
  grow the lead-in chamfer to 1.2 mm. Interlayer SF clears 2.0 (**2.22**); first **PASS**.
  But alignment margin is still zero (0.30). *Exposed: no alignment headroom.*
- **Gen 5 — buy alignment margin + robust interlayer.** Make the finger longer & thinner
  (13×1.0) to push strain to 0.40% (interlayer SF 3.13) and tighten c to 0.12 → E_align
  **0.27, real margin**. Cost: retention force fell to **7.2 N** — a soft lock. *Exposed:
  the retention↔strain tradeoff went too far toward soft.*
- **Gen 6 — resolved compromise.** Trade a little strain margin back for lock feel: finger
  t 1.1, δ 0.50 → SF_y 5.1 / SF_z 2.56 (both comfortably ≥2) and **F_ret ≈ 10.6 N** (firm,
  positive) with **F_ins ≈ 2.9 N** (easy). Lengthen the rail to 26 mm so pads (6) and
  optical (15) sit well inside the bearing with roll headroom; c 0.13 keeps E_align at
  **0.28** with margin. **All functional and geometry gates pass.**

---

## 5. The printability ↔ strength tension — resolved

The undercut flanks (55° from base = 35° from vertical) and the thin snap finger pull
against each other across print orientation:

| Orientation | Flank faces | Snap finger bending | Sliding-face finish |
|---|---|---|---|
| **Rail axis vertical (X ∥ build-Z)** ✅ chosen | constant cross-section → **vertical walls, NO support on functional faces** | finger bends **across layers** → interlayer case applies → must hold SF_z ≥ 2 | layer lines run along slide axis (rings); acceptable, light |
| Flat on bed (X horizontal) ✗ | undercut flanks become 35°-from-vertical **overhangs needing support inside the groove → wrecks sliding faces** | finger bends in-plane (stronger) | better, but flanks ruined |

**Resolution:** print **rail-axis-vertical** to keep all sliding/flank faces support-free,
and *design the finger to survive the interlayer penalty* (that is exactly why Gen 4→6
target `SF_interlayer ≥ 2`, not just in-plane SF). The 35° overhang is *within* the ~45°
FDM self-support limit anyway, and in this orientation the flanks aren't overhangs at all —
so we did **not** need to raise `dovetail_angle` for printability (a lever we considered and
rejected — see dead ends).

---

## 6. Dead ends & rejected levers (the record is a deliverable)
- **Single central dovetail** — rejected before Gen 1: collides with pads + optical bore.
- **Raising `dovetail_angle` for printability** — considered as a way to reduce flank
  overhang; **unnecessary** once we commit to rail-axis-vertical printing (flanks become
  vertical walls regardless of angle). Left at 55° for capture/material balance.
- **Tightening clearance alone to hit alignment** — Gen 3 showed c=0.15 only reaches the
  budget *exactly* and increases bind risk; needed the print-tolerance requirement +
  lead-in/feel work (Gen 4–6), not just a smaller number.
- **Maximizing strain safety factor** — Gen 5 (SF_z 3.13) made the lock too soft (7.2 N).
  More margin is not free; Gen 6 deliberately spends some to get a firm 10.6 N lock.
- **Mechanically staggered pin lengths for hot-plug** — deferred to firmware sequencing
  (connector-spec §4.2); can't validate timing without hardware.

---

## 7. Resolved profile (Gen 6) — feeds back into `connector-spec.md` §5 [STUDY]

| Param | Resolved | | Param | Resolved |
|---|---|---|---|---|
| dovetail_angle | 55° | | detent_depth | 0.50 mm |
| flank_clearance | 0.13 mm | | finger_len × thk | 13 × 1.1 mm |
| rail_length | 26 mm | | lead_in_chamfer | 1.2 mm |
| wall_thk | 2.4 mm | | engage_depth | 4.0 mm |
| **Print requirement** | rail-axis-vertical; per-part tol ≤ ±0.075 mm | | rail_offset / mouth_w | 13 / 4 mm |

**Resolved performance (analytical, validated-by-design — NOT tested):**
alignment **E = 0.28 mm ≤ 0.30** with margin (pads & optical inside the 26 mm bearing);
detent **ε = 0.49%**, **SF_yield 5.1**, **SF_interlayer 2.56**; **insertion ≈ 2.9 N**
(easy), **retention ≈ 10.6 N** (firm positive lock); geometry **6/6 gates, watertight**.

---

## 8. Outputs
- **Resolved STLs:** `cad/connector/connector_male_v1.stl`, `connector_female_v1.stl`
- **Resolved assembled glTF:** `cad/connector/connector_assembled_v1.glb`
- **Evolution GLB set (Three.js clip, ~5 KB each):** `cad/connector/glb/gen1…gen6.glb`
- **Per-gen diagnostics + STL:** `cad/connector/out/gen1…gen6/`
- **Analytical record:** `cad/connector/out/analysis.txt`
- **Regenerate:** `forge build cad/connector/genN.py` · `python cad/connector/analysis.py`

## 9. Honest limitations
1. Stress is **beam theory, not FEA** — a real detent has stress concentrations at the
   finger root the straight-beam formula understates; treat SFs as guidance, hold ≥2.
2. Material constants are **estimates**; the true CF-PA12 modulus/strain from a chosen
   filament datasheet should replace them before any fab decision.
3. Alignment assumes ideal straight rails; real print warp/creep over thousands of cycles
   is **not** modeled — the design mitigates it by decoupling retention (finger) from the
   locating fit (flanks), so flank wear loosens *feel* before it loses *location*.
4. No fit, force, or cycle-life claim here has been **measured**.

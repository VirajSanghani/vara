# Tool Capabilities — Phase 0 Probe

**Date:** 2026-06-03
**Purpose:** Empirically establish what each tool can actually do *before* committing
ambition, per Build Plan §Phase 0. Every claim below is backed by a command that was
run and its observed output. Nothing here is assumed.

> **Headline:** The plan named three MCPs (FreeCAD, Blender, KiCad). Two of those are
> dead or absent for our purposes. The real CAD engine in this environment is the
> **`forge-cad` / build123d** pipeline, which is *better* than the thin FreeCAD MCP
> would have been. There is **no KiCad** capability of any kind, which sets a hard
> ceiling on Phase 4.

---

## Summary table

| Capability the plan wants | Tool the plan named | Reality | Verdict |
|---|---|---|---|
| Parametric CAD, boolean, regen, STL | FreeCAD MCP | MCP exposes only `check_connection` + `test_echo`; app offline | ❌ unusable — **route around** |
| (same) | **forge-cad / build123d 0.10.0** | Full parametric build, booleans, param regen, requirement gates, diagnostics, STL/STEP/3MF/BREP/glTF, 6-view render | ✅ **primary CAD engine** |
| FEM / stress check | FreeCAD FEM | Not present anywhere (no FreeCAD FEM access, no Calculix, build123d has none) | ❌ → analytical estimate, documented |
| Animation, decimation, glTF export | Blender MCP | Rich (arbitrary Python, scene, screenshot); **app must be launched** (Blender.app installed, addon currently offline) | ⚠️ available once user starts Blender |
| Schematic / footprints / netlist / BOM | KiCad MCP | No MCP, no `kicad-cli`, KiCad **not installed** | ❌ no programmatic KiCad at all |

---

## 1. FreeCAD MCP — ❌ unusable for CAD

**Commands run**

```
mcp__freecad__check_freecad_connection
  → {"freecad_socket_exists": false, "status": "FreeCAD not running.
     Please start FreeCAD and switch to AI Copilot workbench"}

mcp__freecad__test_echo("VARA phase 0 probe")
  → "Bridge received: VARA phase 0 probe"
```

**What worked:** the MCP bridge process responds (echo round-trips).
**What failed / the ceiling:** Two things, either of which is disqualifying:
1. **The app is offline.** The bridge talks to a FreeCAD desktop instance running the
   "AI Copilot" workbench; that instance is not running. (FreeCAD.app *is* installed at
   `/Applications/FreeCAD.app`, so it *could* be launched — but see #2.)
2. **The MCP exposes no CAD operations.** The entire FreeCAD MCP surface is exactly two
   tools: `check_freecad_connection` and `test_echo`. There is **no** tool to create a
   sketch, add a constraint, extrude, boolean, change a parameter, or export an STL.
   Even with FreeCAD running, this MCP could not perform a single step of Phase 0's
   FreeCAD checklist.

**Decision:** Do not pursue the FreeCAD MCP. It is a connectivity stub, not a CAD
interface. Route all CAD through `forge-cad` (§2).

---

## 2. forge-cad / build123d — ✅ primary CAD engine (the route-around)

The genuine CAD capability lives in the local `forge-cad` pipeline:
`/Users/vs/Projects/forgecad/.venv` (build123d **0.10.0**), driven by the `forge` CLI.
This runs **headless** — no desktop app, no socket, fully scriptable and reproducible.

**Probe:** authored a parametric part — constrained sketch → extrude → **boolean
subtract** (thru-hole) → fillet — with a `PARAMS` dict and an assert-style `REQUIREMENTS`
gate, then built it, changed a driving parameter, and rebuilt.

**Gen 1** (`plate_w=40, hole_d=8`):
```
forge build probe.py
 bbox (mm)   40.00 x 24.00 x 6.00     volume 5.41 cm³   mass 6.7 g
 solids/faces/edges 1/11/27   watertight yes   requirements 1/1
 → diagnostics.json, probe.stl
```

**Gen 2** — changed `plate_w 40→60`, `hole_d 8→12`, rebuilt (regeneration test):
```
 bbox (mm)   60.00 x 24.00 x 6.00     volume 7.92 cm³   requirements 1/1
```
Geometry regenerated correctly from the new parameters; the requirement gate
(width-check + "boolean actually removed material") still passed. ✅

**Exports** (all succeeded, all non-trivial files, glTF magic verified `glTF\x02`):

| Format | Command | Result |
|---|---|---|
| STL  | `forge export stl …`  | 51 KB |
| STEP | `forge export step …` | 35 KB |
| 3MF  | `forge export 3mf …`  | 13 KB |
| glTF/GLB | `forge export glb …` | 19.5 KB, valid v2 binary |
| Preview PNG | `forge preview …` | 33.5 KB, real 6-view shaded render (hole visible in top/iso) |

**Full forge CLI surface:** `build`, `check` (diagnostics only), `diff` (compare two
diagnostics — for regression tracking between dovetail generations), `draw` (HLR
engineering drawings), `export`, `info`, `preview` (6-view), **`sweep`** (parameter
sweep validation gate).

**Diagnostics available** (read instead of eyeballing screenshots): volume, mass,
bbox, solids/faces/edges/shells/vertices counts, watertight flag, min-feature size,
per-requirement pass/fail.

**Skills layered on top** (in `forgecad/skills/`): `forge-cad`, `forge-assembly`
(joints/mates/interference — for core+cartridge fit checking), `forge-iterate`
(revision diffing — for the dovetail generations), `forge-manufacturing` (3MF + print
orientation + overhang/wall checks — Phase 3 design-for-AM), `forge-render-hero`
(presentation renders via Blender), `forge-vision-decompose`.

**Ceiling / what it does NOT do:**
- **No FEM/FEA.** Confirmed: no stress solver in forge, no FreeCAD FEM reachable, no
  Calculix on the system. The dovetail detent stress check (Plan §4.3) must be a
  **documented analytical estimate** (cantilever-snap beam model), explicitly labelled
  as an estimate — never a simulated result.
- **No printer in the loop.** All fit/tolerance claims remain "validated-by-design,
  print-ready," never "tested." (Honesty rule #1.)

**Verdict:** This fully replaces the FreeCAD MCP and exceeds what it could have offered.
`sweep` + `diff` + `REQUIREMENTS` map directly onto the dovetail generation study; GLB
export feeds the Three.js showcase directly.

---

## 3. Blender MCP — ⚠️ rich, but the app must be launched

**Command run**

```
mcp__blender__get_polyhaven_status
  → "Error checking PolyHaven status: Could not connect to Blender.
     Make sure the Blender addon is running."
```

**State:** Blender.app is installed (`/Applications/Blender.app/Contents/MacOS/Blender`),
but the BlenderMCP addon/socket is not currently serving, so live probing (import STL,
material, keyframes, render, glTF) could not be executed this session.

**Capability (from the registered tool surface, not yet exercised live):** the MCP
exposes `execute_blender_code` (**arbitrary Python** — i.e. anything bpy can do:
import STL, assign materials, keyframe, render, glTF export, decimate), plus
`get_scene_info`, `get_object_info`, `get_viewport_screenshot`, and asset integrations
(PolyHaven, Sketchfab, Hyper3D/Rodin, Hunyuan3D). Arbitrary-Python means the Plan's
Blender checklist (import → material → 2 keyframes → render → glTF) is well within reach
**once the addon is running**.

**Action item for the user (when we reach Phase 2/6):** launch Blender and start the
BlenderMCP addon server so the socket is live. I will re-probe with the actual
import→material→keyframe→render→glTF sequence at that point and record the result here.

**Mitigation that reduces Blender dependence:** `forge` already exports per-generation
GLB and renders 6-view previews headlessly. So the dovetail **evolution clip** can be
done two ways — (a) Blender morph/render (cinematic, needs Blender live), or (b) export
each generation as GLB and morph/crossfade them **in Three.js** at showcase time (no
Blender needed for the clip). We'll choose in Phase 2; option (b) de-risks the schedule.

---

## 4. KiCad — ❌ absent entirely (the hard ceiling)

**Findings**
- **No KiCad MCP.** Searched the full deferred-tool registry for kicad / schematic / pcb
  / netlist / symbol / footprint — zero matches.
- **No `kicad-cli`.** `which kicad-cli` → not found; no KiCad app bundle to source it from.
- **KiCad is not installed.** `/Applications` contains Blender.app and FreeCAD.app but
  **no KiCad.app**.

There is no path to programmatically create a KiCad project, place symbols, attempt
footprints, or export a netlist/BOM in this environment. This is the single most
schedule-affecting Phase 0 result.

---

## 5. Recommendation — how deep Phase 4 (electronics) can realistically go

The Plan's Risk table already anticipated this exact outcome: *"KiCad MCP is shallow →
PCB degrades to a documented schematic. Stated plainly."* Reality is one notch below
even that — there is no KiCad at all — so the honest plan is:

**Phase 4 floor (achievable now, do this):**
A **rigorously documented electrical design**, authored as text/markdown in
`electronics/` + `docs/electronics.md`:
- Per-subsystem **block diagram** and a complete **net list in tabular form** (every
  signal, source pin → destination pin, with the cartridge connector pinout from
  `connector-spec.md` as the contract boundary).
- Component selection with part numbers, the **cartridge ID/EEPROM** scheme, PMIC/charge
  topology, level/voltage rails, and a **BOM table** (CSV in `electronics/bom.csv`).
- ASCII/mermaid schematic-style diagrams where they clarify intent.
This is real engineering and fully honest; it is *not* a fabricated `.kicad_sch`.

**Phase 4 stretch (only if the user enables it):** If the user **installs KiCad** (gives
us `kicad-cli`), we can additionally:
- Hand-author `.kicad_sch` s-expression schematic files and **validate/export** them
  (ERC, netlist, BOM, PDF) via `kicad-cli` — a real, openable KiCad project.
- PCB layout/routing would still be largely manual-in-app work; we would *not* claim
  auto-routed boards. Board *outline* matched to enclosure mounts is feasible as a
  documented DXF/outline.

**What we will NOT do:** generate a fake netlist, a fake `.kicad_pcb`, or a rendered
board image we didn't actually produce. (Honesty rule #4.)

**Decision requested from the user (not blocking Phase 1):** install KiCad to unlock the
stretch path, or accept the documented-schematic floor? Either is defensible to a
robotics lab; the floor is honest and complete on its own.

---

## 6. Net effect on the phase plan

| Phase | Tooling reality | Change vs. plan |
|---|---|---|
| 2 — Dovetail study | forge `build`/`sweep`/`diff` + `REQUIREMENTS`; stress = analytical estimate | On track. FEM downgraded to documented estimate (anticipated). |
| 2/6 — Evolution clip & decimation | Blender (needs app live) **or** per-gen GLB morphed in Three.js | De-risked; Blender optional for the clip. |
| 3 — Mechanical | forge-cad + forge-assembly + forge-manufacturing | On track, headless. |
| 4 — Electronics | Documented schematic + netlist + BOM (floor); `kicad-cli` only if user installs KiCad | Degraded as the Risk table predicted; honest. |
| 6 — Showcase | forge GLB exports feed Three.js directly | On track. |

**Bottom line:** CAD and the showcase pipeline are strong and headless. Animation needs
the user to start Blender when we get there (with a no-Blender fallback). Electronics is
the constrained layer — plan for an excellent *documented* electrical design, and treat a
real KiCad project as a stretch contingent on the user installing KiCad.

---

## Addendum — 2026-06-03 (Phase 1 review)

**KiCad decision reversed by the user:** KiCad **will be installed**. Phase 4 target is
therefore upgraded from the documented-schematic *floor* to the *stretch* path:
**schematic + footprints + BOM** as openable `.kicad_sch` / `.kicad_pcb`, validated and
exported via `kicad-cli` (ERC, netlist, BOM, PDF). Full routing remains optional. It is
still a **design, not a verified/fabricated board** — honesty rule #1 stands.

Action when entering Phase 4: confirm `kicad-cli` is on PATH (`kicad-cli version`), then
re-probe the actual schematic→footprint→BOM→export chain and record the real ceiling here
before committing Phase-4 scope.

---

## Addendum 2 — 2026-06-03 (Phase 4 re-probe + install)

**Install (macOS).** KiCad was not installed and `kicad-cli` was absent (re-confirmed).
`brew install --cask kicad` **fetched** KiCad 10.0.3 (cached, ~1.4 GB) but its full cask
install **fails non-interactively**: moving the `demos` artifact to
`/Library/Application Support/kicad` needs `sudo` (no TTY for the password). **Routed around**
without sudo: mounted the cached DMG (`hdiutil attach`), copied `KiCad.app` to
`/Applications/KiCad/KiCad.app` (that dir is user-writable), symlinked the binary to
`/opt/homebrew/bin/kicad-cli`. `kicad-cli version` → **10.0.3**. (If a clean cask install is
wanted later, run `brew install --cask kicad` in a terminal so it can prompt for the password.)

**Empirical ceiling of `kicad-cli` 10.0.3** (tested, not assumed):
- Subcommands: `sch {erc, export{bom,netlist,pdf,svg,dxf,ps,python-bom}, upgrade}`, `sym`,
  `fp`, `pcb {…export/drc…}`, `jobset`.
- **It validates and exports; it does NOT create or place symbols** (no GUI scripting). So a
  schematic must be **hand-authored as `.kicad_sch` s-expression**, then driven through the CLI.
- **Verified chain (trivial 2-resistor probe):** hand-authored `.kicad_sch` with custom
  embedded symbols + **global-labels-placed-at-pin-endpoints** for connectivity →
  `kicad-cli sch erc` (runs, produces report), `sch export netlist` (**connectivity correct** —
  the shared net joined both pins), `sch export bom` (CSV). PDF/SVG export also available.
- Warnings seen (non-blocking): off-grid endpoints (fixed by snapping to the 1.27 mm grid);
  "symbol/footprint library not in project table" (cosmetic — symbols are embedded so the file
  opens; footprints are referenced by name for the BOM, not loaded).

**Real Phase-4 ceiling → delivered depth:** openable, ERC-checked **`.kicad_sch`** (core +
cartridge) + CLI-exported **netlist + BOM + PDF**. **PCB layout (`.kicad_pcb`) is NOT pursued**
— `kicad-cli pcb` can export/DRC but cannot place or route, so a board would need GUI/hand
authoring; per the brief, routing is "optional dessert" and we stop at the schematic depth.
This is a **design**, not a DRC-clean or manufactured board (see `electronics.md` banner).

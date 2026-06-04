# VARA — Build Log

A decision record, phase by phase: the capability probes, the dead ends, and the honesty
calls. The point of this file is that the *process* is auditable — not just the result. Every
phase ended at a gate for review before the next began.

Honesty rules held throughout: never claim a fit is "tested" (only
"validated-by-design"); document dead ends, not just wins; never simulate tool output.

---

### Phase 0 — Capability probe (`docs/tool-capabilities.md`)
Probed the tools *before* committing ambition.
- **FreeCAD MCP**: dead — exposes only `check_connection` + `test_echo`, no CAD ops; app
  offline. Routed around it entirely.
- **Real CAD engine = `forge-cad` / build123d 0.10** (headless): parametric build, booleans,
  `REQUIREMENTS` gates, diagnostics, STL/STEP/3MF/glTF, `sweep`/`diff`. Verified live.
- **No FEM anywhere** → the dovetail stress check would have to be analytical, clearly labelled.
- **Blender MCP**: rich but needs the app running; the glTF showcase pipeline can avoid it.
- **KiCad**: absent (no MCP, no `kicad-cli`, not installed). Recorded as the hard ceiling for
  Phase 4 before designing anything.

### Phase 1 — Architecture & the frozen contract
- **Camera decision (RESOLVED):** camera lives in the **CORE**, not the cartridge. CSI is far
  too fast for a 6-pin pogo; putting it in the core keeps the interface low-speed and makes the
  vision cartridge "optics only." Bonus: the cartridge lens must be coaxial with the fixed
  camera, so the ±0.28 mm alignment budget governs the **optical axis**, not just the pads.
- **Reworked the seed pinout:** the proposed "ID resistor / 1-Wire" on pin 5 was dropped — the
  Pi Zero 2 W has no ADC, so a resistor divider needs an extra chip. Canonical ID became an
  **I²C EEPROM @0x50**; pin 5 became **CD# (cartridge-detect)**.
- **On-device VLM rejected** — and shown to be Pi-model-*independent*: no Pi runs a good
  identify-and-explain model, so it's a cloud call regardless, which *strengthens* the Zero 2 W
  choice. Documented the latency/Wi-Fi/key tradeoffs.
- Output: `architecture.md` + `connector-spec.md` (the single source of truth).

### Phase 2 — Dovetail optimization (the centerpiece, `docs/dovetail-study.md`)
Six problem-driven generations, each fixing what the last exposed (analytical, **not FEA**):
- **G1 baseline** — catastrophic: detent ε ≈ 13.5 %, ~1253 N to insert (would shatter), align
  0.40 mm. FAIL.
- **G2** dedicated cantilever finger → in-plane stress fine, but interlayer SF 1.67 < 2; align
  still 0.40. **G3** tighten clearance + declare a print-tolerance requirement → align lands
  *exactly* on 0.30 (kept as a marginal finding). **G4** lower detent → first PASS. **G5** buy
  alignment margin → lock went soft (7.2 N). **G6 resolved** — SF 5.1/2.56, 2.9 N insert,
  10.6 N retention, align 0.28 mm.
- **Dead ends recorded:** a single central rail (collides with pads/bore → dual rails); raising
  the dovetail angle for printability (unnecessary once printed rail-axis-vertical).
- **Honesty:** beam theory understates the real finger-root stress concentration → a protected
  root fillet, gated so a refactor can't quietly remove it.

### Phase 3 — Mechanical (`docs/mechanical.md`)
- Both parts **consume** the resolved connector via `dovetail_lib` primitives — the [STUDY]
  geometry is the single source, not re-derived.
- **Per-part print orientation** resolved a real tension: core front-down (snap finger loads
  *in-plane*, SF 5.1, beating the interlayer worst case); cartridge rail-axis-vertical
  (support-free flanks). Diagnostics caught two modelling defects (floating detent bumps,
  floating bosses — coincident faces don't weld).

### Phase 4 — Electronics (`docs/electronics.md`)
- **Re-probed first** (Phase-0 discipline): installed KiCad 10.0.3, but the full cask needs
  `sudo`; routed around by extracting the app + symlinking `kicad-cli`. Ceiling: `kicad-cli`
  validates/exports but **cannot place symbols** → schematics hand-authored as s-expression.
- **Floor + stretch both delivered:** netlist CSV + BOM, *and* openable `vara_core` /
  `vara_cartridge` `.kicad_sch` with CLI-exported netlist/BOM/PDF + ERC. Core 29 nets,
  cartridge 6 nets, **0 unconnected pins**; the 6-pin contract maps exactly on both sides.
- **PCB layout NOT pursued** — `kicad-cli` can't route. Stated plainly; **no fabricated copper**.

### Phase 5 — Functional prototype (`app/`, `docs/prototype.md`)
- Pipeline: jog-press → capture → cloud vision → 240×280 viewfinder+caption → speak.
- **Read-before-PWM guard encoded in code:** the shared V+ rail powers the EEPROM *and* the LED
  ring, and LED dimming PWMs V+ — so `enable_power_pwm()` raises `SequencingError` unless the ID
  was read first. The demo proves the guard fires.
- **Graceful degradation:** no-Wi-Fi / no-key / timeout / API-error → clean on-screen error,
  never a crash. Swappable HAL: real drivers vs clearly-logged stubs. **Logic-validated, not
  hardware-tested.**

### Phase 6 — Three.js showcase (`web/`) + iterative red-teaming
- Static, no-build, CDN-pinned three.js r160; consumes the real glTF + the real Phase-5 frames.
- Hardened over several review rounds: creased normals + matte PBR + SAO/bloom; a
  collision-free assembly path (verified `cartridge ∩ core = 2.7 mm³`); the enclosure enlarged
  to **actually fit the Pi Zero 2 W (65 mm)**; a full teardown with leader labels and honest
  designed/representative badges; camera-following light so every face reads; a no-cache server
  so edits are always seen. Dead ends found and fixed: a floating mid-body screw (explode loop
  overwrote seated Z), exposed dovetail rails (closed the socket), parts crossing (re-ordered to
  physical seated-Z).

### Phase 7 — Story & open-source
This README/BUILDLOG, the license decision, and the deploy of `web/`.

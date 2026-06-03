# VARA — Master Build Plan
### A modular handheld perception instrument
*Pokédex soul · instrument-grade body · AI mind · open-source*

> **VARA** — from Sanskrit *वर* (vara): "boon, gift, the chosen thing." A small instrument
> that grants you a new sense each time you choose a cartridge. Neutral, ownable, quietly
> resonant. Pronounced *VAH-rah*.

---

## PART I — INTENT

### 1.1 One-sentence pitch
A handheld instrument you point at the world; slide on a cartridge and it gains a new sense.
The hero cartridge is a **vision/macro lens** — point at a plant, a part, a circuit, a label,
and VARA identifies and explains it. The hero engineering component is the **dovetail rail
connector** every cartridge shares, taken through a real, watchable optimization arc.

### 1.2 The honest goal (read this twice)
We are **not** shipping a polished consumer product. Humane raised $230M+ and still shipped
something reviewers savaged; a solo end-to-end consumer device is a year-of-a-team problem and
the fastest way to stall at 5% forever. Our goal is one **complete, credible engineering pass**
from hypothesis to a set of real artifacts:

- a printable enclosure: **core + ONE finished cartridge** (FreeCAD, PA12-CF ready)
- a real **electronics design** (KiCad; depth set by a capability probe, not by hope)
- a working **functional prototype** on a Raspberry Pi (camera → AI → screen + voice)
- an interactive **Three.js exploded showcase** that tells the whole story in 60 seconds
- the whole thing **documented as an engineer would** — decisions, tradeoffs, dead ends —
  then **open-sourced**.

Every layer is *real but bounded*. The Pi is the real brain; the custom PCB is a documented
design whether or not it's ever fabricated. This honesty is the product's spine, and — for the
job application that seeded this — it is *more* compelling to a robotics lab than fake polish.

### 1.3 Why this is the right project to prove capability
It sits at the exact intersection the 3D-printing-technician-in-a-robotics-lab role lives in:
- **Mechanical** — enclosure, the dovetail mechanism (FreeCAD)
- **Design for AM** — orientation, tolerance, manufacturability in PA12-CF
- **Industrial / communication** — the Three.js showcase
- **Electronics** — KiCad schematic/PCB
- **Integration** — a Pi prototype that actually runs
- **Working with engineers** — the documented, decision-logged process *is* the evidence.

### 1.4 Non-negotiable honesty rules
1. Never claim a tolerance or fit is **tested**. Only ever "**validated-by-design,
   print-ready**." We have no printer in the loop; saying otherwise is a lie that a five-minute
   bench conversation would expose.
2. Document **dead ends and tradeoffs**, not just wins. The record is the deliverable.
3. State assumptions inline. If a number is a guess, mark it a guess.
4. No simulated tool output. If an MCP can't do something, we write down that it can't and
   route around it — we never fake a render or a netlist.

---

## PART II — SCOPE DISCIPLINE (how this doesn't become a graveyard)

- **Core + ONE hero cartridge** get finished. All other cartridges remain **architectural** —
  defined only by conformance to the shared connector spec, never modeled.
- **One hero optimization** (the dovetail). Other parts are designed competently, not
  optimized to death.
- Each **phase yields a standalone artifact** that has value even if we stop there.
- **Phase gate:** after each phase, produce the artifact and STOP for review before the next.
- A hard rule against the most likely failure mode — *"ooh, a thermal cartridge too"* — is:
  write the idea into `docs/future-cartridges.md` and move on. Architecture, not build.

---

## PART III — SYSTEM ARCHITECTURE

### 3.1 Subsystem map
```
                    ┌─────────────────────────────┐
                    │            CORE             │
                    │  ┌───────────────────────┐  │
   cartridge ◀══════╪══╡  DOVETAIL INTERFACE   │  │
   (swappable)      │  │  mech datum + contacts │  │
                    │  └───────────┬───────────┘  │
                    │   compute (Pi)  power (batt+PMIC) │
                    │   display    audio (mic+spk) │
                    │   1 control (jog/scroll+press)│
                    └─────────────────────────────┘
```

### 3.2 Core subsystems (finished)
- **Compute:** Raspberry Pi (Zero 2 W target for size; Pi 4/5 fallback for headroom).
- **Display:** small round or square IPS/OLED (size locked in Phase 1 — it drives the whole
  front-face geometry).
- **Power:** Li-po + protection/PMIC; charge over USB-C. Runtime is a documented estimate.
- **Audio:** MEMS mic + small speaker (the AI talks back; you can talk to it).
- **Control:** exactly **one** primary input — a jog/scroll wheel with press. R1-grade restraint.
- **Cartridge interface:** the dovetail rail (mechanical datum) + electrical contacts.

### 3.3 The cartridge interface contract (the single source of truth)
Every cartridge — built or merely architectural — must conform to:
- **Mechanical envelope:** max cartridge bounding box; the male dovetail profile + datum origin.
- **Retention:** detent geometry + insertion direction + a positive stop.
- **Electrical pinout:** fixed pad order — e.g. `[V+, GND, I²C-SDA, I²C-SCL, ID, INT]` (final
  count set in Phase 1). An **ID line / EEPROM** lets the core auto-detect which cartridge is on.
- **Thermal/clearance:** keep-out zones around contacts; lens optical axis location.

This contract is written once (`docs/connector-spec.md`) and **every part references it**. Change
it in one place, everything downstream updates.

### 3.4 Hero cartridge — vision/macro lens (finished)
Chosen for best **demo legibility** (point-and-identify is instantly understood, maximally
Pokédex) **and** best **printability** (a housing for a Pi camera module + a printed macro-lens
holder + optional ring light — no exotic sensors). Contents: camera module, printed lens barrel,
optional LED ring, ID resistor/EEPROM, male dovetail.

### 3.5 Architectural-only cartridges (documented, NOT built)
Thermal sense · air-quality/environmental instrument · audio/ultrasonic sense. Each gets a
paragraph in `docs/future-cartridges.md` proving the architecture generalizes. Nothing more.

---

## PART IV — THE HERO PART: THE DOVETAIL CONNECTOR

This is the centerpiece. It is the single component we take through the full
"real method + beautiful to watch" optimization arc, and it earns the attention because it
must satisfy five objectives that genuinely fight each other.

### 4.1 Requirements (the multi-objective problem)
1. **Locate precisely** — the cartridge's electrical pads must align to the core's contacts
   within a tolerance the contacts can absorb (pogo-pin travel sets the budget, ~±0.2–0.3 mm).
2. **Slide smooth, lock positive** — low insertion friction, then a **detent click** and a hard
   stop. The *feel* is a real spec, not a nicety.
3. **Survive cycles** — thousands of insert/remove cycles without the fit wearing loose; account
   for PA12-CF wear and creep.
4. **Carry power + data** — contacts stay mated and aligned under the retention force.
5. **Be printable** — survive tolerance stack-up, layer-adhesion anisotropy, orientation, and a
   support strategy that doesn't wreck the sliding faces.

### 4.2 Objectives in tension (why it's a real optimization)
`stiffness ↔ printability` · `retention force ↔ insertion ease` · `tight fit (alignment) ↔ wear
life` · `wall thickness (strength) ↔ size/weight`. There is no single right answer — only a
resolved compromise. That's what makes the "evolution" honest rather than decorative.

### 4.3 Method (real, then made beautiful)
- Build a **fully parametric** dovetail in FreeCAD driven by named variables:
  `dovetail_angle, flank_clearance, detent_depth, rail_length, wall_thk, lead_in_chamfer`.
- Define **evaluation cases** per generation: fit clearance at contacts, estimated retention
  force (simple spring/interference model — state assumptions), printability flags (overhang
  angle on the rail faces vs. print orientation, min wall, support contact on functional faces).
- Iterate **generations**: each is a parameter set + the resulting geometry + a metric row in a
  table. Move toward the resolved compromise; **log why each change was made**.
- (If FreeCAD FEM MCP is available) add a coarse stress check on the detent snap; if not, use a
  documented analytical estimate and say so.

### 4.4 The watchable payoff
- Export each generation's mesh; in Blender, **morph/cut between generations** so the rail visibly
  evolves toward its final form — a short cinematic clip.
- This clip becomes a scene in the Three.js showcase: *"watch the connector evolve."*

### 4.5 Outputs
`cad/connector/` (parametric source + final male & female STLs) · `docs/dovetail-study.md`
(the generation table + reasoning + assumptions) · `anim/dovetail-evolution.*` (the clip).

---

## PART V — PHASED PLAN

> Each phase: **inputs → work → artifact → STOP for review.** Sessions are estimates.

### Phase 0 — Capability probe  *(1 session, DO FIRST)*
Find out what the tools can actually do **before** committing ambition.
- **FreeCAD MCP:** parametric body from a sketch w/ constraints; a boolean; change a driving
  param and confirm regeneration; export STL. Is FEM available?
- **Blender MCP:** import STL; assign material; two keyframes; render a frame; export glTF.
- **KiCad MCP:** create project; add symbols to a schematic; *attempt* footprint placement;
  *attempt* netlist/BOM export. Record the exact depth ceiling.
**Artifact:** `docs/tool-capabilities.md` + a recommendation for how deep Phase 4 can go.

### Phase 1 — Architecture & spec  *(1 session)*
- Lock subsystem choices: Pi model, display size/type, contact count + pinout, battery target.
- Write `docs/architecture.md` and the authoritative `docs/connector-spec.md` (envelope, dovetail
  profile, datum origin, pinout, keep-outs).
**Artifact:** those two docs. Everything downstream references the connector spec.

### Phase 2 — Dovetail optimization study  *(2–3 sessions)* ★ centerpiece
Per Part IV.
**Artifact:** final connector STLs, `docs/dovetail-study.md`, the evolution clip.

### Phase 3 — Mechanical design  *(2–3 sessions)*
- **Core body:** display bezel, battery bay, Pi/board mounts, mic/speaker ports, jog-wheel
  aperture, the **female** rail integrated, USB-C cutout, heat-set insert bosses.
- **Hero vision cartridge:** Pi-camera mount, printed macro-lens barrel, optional LED ring,
  ID-resistor pocket, the **male** rail.
- **Design for PA12-CF (every part):** print orientation, wall thickness, clearances, support
  strategy on functional faces, fastener/heat-set plan, tolerance call-outs.
**Artifact:** printable STLs + `docs/mechanical.md` (the design-for-AM case study).

### Phase 4 — Electronics  *(1–3 sessions; depth = Phase 0 result)*
- **Floor:** schematics — core (compute header, PMIC/charge, display, audio, jog input, cartridge
  connector) and cartridge (camera, ID/EEPROM, LED ring).
- **Stretch (if KiCad MCP allows):** footprints, board outline matched to the enclosure mounts,
  routing, BOM export.
**Artifact:** schematic(s), optional PCB, `docs/electronics.md`.

### Phase 5 — Functional prototype  *(2 sessions)*
- Pi + camera + display + mic/speaker. Software pipeline: **capture → AI vision identify/explain →
  speak + show**. Stub the cartridge-ID read. Keep secrets out of the repo (`.env`).
**Artifact:** `app/` software, a demo video, `docs/prototype.md`.

### Phase 6 — Three.js exploded showcase  *(2–3 sessions)* ★ the wrapper
- Import **real** geometry (decimated glTF from Blender). Hero interaction: device **explodes
  into all parts**, each labeled with what it does + why it's shaped that way. Scenes: the dovetail
  evolution; the cartridge sliding on/off; the point-and-identify story.
- **Quiet Utility** aesthetic: Fraunces + JetBrains Mono, stone/amber, instrument-grade.
- Perf: decimate meshes in Blender first; lazy-load scenes.
**Artifact:** the public web piece — the single shareable link.

### Phase 7 — Story & open-source  *(1 session)*
- README (the engineer's-eye narrative tying every artifact together), build log, LICENSE
  (MIT or CERN-OHL for hardware), contribution notes.
**Artifact:** a repo a stranger understands in five minutes.

---

## PART VI — REPO STRUCTURE
```
vara/
  docs/         architecture, connector-spec, dovetail-study, mechanical,
                electronics, prototype, tool-capabilities, future-cartridges
  cad/          FreeCAD sources + exported STL/glTF   (core/, cartridge/, connector/)
  anim/         Blender scenes + rendered evolution clips
  electronics/  KiCad project, schematic, (optional) PCB, BOM
  app/          Pi prototype software (.env for secrets, never committed)
  web/          Three.js exploded showcase
  README.md     the engineer's-eye story
  LICENSE
```

## PART VII — RISKS (named honestly)
| Risk | Mitigation |
|---|---|
| KiCad MCP is shallow | PCB degrades to a documented schematic. Stated plainly. |
| Can't validate fit without printing | "Validated-by-design, print-ready" only. Never "tested." |
| Scope creep via extra cartridges | Hard rule: one hero cartridge; rest → future-cartridges.md |
| Three.js perf with CAD meshes | Decimate in Blender before glTF export; lazy-load. |
| Display choice churns geometry | Lock display in Phase 1 before any body modeling. |
| Secrets in prototype code | `.env`, gitignored; never commit keys. |

## PART VIII — OPEN DECISIONS (resolve as we build)
- Pi model: Zero 2 W (size) vs Pi 4/5 (headroom).
- Display: round vs square; exact diameter/size (locks front face).
- Contacts: pogo-pin vs edge-card (sets alignment budget) — decide Phase 1.
- License: MIT (permissive) vs CERN-OHL-S (hardware copyleft).

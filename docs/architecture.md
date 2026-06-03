# VARA — System Architecture (Phase 1)

**Date:** 2026-06-03 · **Status:** subsystem choices locked for Phase 2/3 entry.
This document fixes the *system* decisions. The *interface contract* (envelope, datum,
pinout, keep-outs) lives in [`connector-spec.md`](connector-spec.md) — the single source
of truth every part references.

> Honesty note: every current-draw, runtime, and fit number here is a **documented
> estimate** marked *(est.)* or *(guess)*. Nothing is bench-measured — we have no
> hardware or printer in the loop. No fit is "tested," only "validated-by-design."

---

## 1. Subsystem decisions (locked)

| Subsystem | Decision | Key reasoning / tradeoff |
|---|---|---|
| **Compute** | **Raspberry Pi Zero 2 W** | Smallest Pi with WiFi + enough OS to drive camera/SPI/audio. On-device VLM inference is impossible on *any* Pi (see §3), so compute choice is about UX smoothness, not inference — which removes the headroom argument for Pi 4/5 and favors size. |
| **Display** | **1.69" IPS, 240×280, ST7789V-class, SPI** | Taller-than-square aspect splits naturally into **camera viewfinder (top) + result/caption strip (bottom)** — the point-and-identify UX. 1.54" 240×240 kept as drop-in fallback if module sourcing/space forces it. Front-face geometry anchors to this active area (§ connector-spec keep-outs). |
| **Camera** | **In the CORE**, fixed, CSI ribbon to Pi | CSI is high-bandwidth FPC — *cannot* route through 6 low-speed pogo pins. Core holds the eye; the hero cartridge holds **optics only** (macro-lens barrel + LED ring + ID). See §2 — this is the resolved camera decision. |
| **Power** | Single Li-po + **integrated PMIC (IP5306-class)**, USB-C charge | IP5306 gives charge + 5V boost + power-path + button-control + fuel-gauge in one chip — far less board area than MCP73831 + separate boost. Alternative (MCP73831 charger + TPS61023 boost + load switch) documented if we want finer control. |
| **Battery** | **1500 mAh Li-po** (up from 1000–1200 seed) | Runtime math (§4) put 1200 mAh at ~2.9 h active; 1500 mAh buys ~3.5 h *(est.)* for little extra volume. Single cell, 3.7 V nominal. |
| **Audio** | I²S MEMS mic (e.g. SPH0645) + I²S DAC/amp (e.g. MAX98357A) → small speaker | I²S keeps it digital and clean; MAX98357A is a single-chip mono Class-D, tiny. The AI talks; you talk to it. |
| **Control** | One rotary encoder (jog) + push (EC11-class), no other buttons | R1-grade restraint per plan. Long-press = power off via PMIC button line. Scroll = navigate; press = capture/confirm. |
| **Connectivity** | Onboard WiFi (Zero 2 W) | Required — the vision pipeline is a cloud API call (§3). No WiFi = no identify. Stated as a hard dependency. |

---

## 2. The camera-location decision (RESOLVED)

**Question (flagged in the seed):** does the vision cartridge route a camera ribbon
through the dovetail, or does the core hold the camera and the cartridge hold only optics?

**Decision: the CORE holds the camera + CSI. The hero cartridge holds the macro-lens
barrel, optional LED ring, and the ID EEPROM.**

Reasoning:
- **Bandwidth.** Pi camera = CSI-2 over a 15/22-pin FPC ribbon. Forcing that through the
  6-pin pogo interface is impossible; adding a *second* high-density board-to-board
  connector at the dovetail would be fragile, expensive, and would force every cartridge
  to carry that connector. Rejected.
- **Architecture generalizes better.** With the camera in the core, the 6-pin interface
  stays low-bandwidth (power + I²C + detect + interrupt). Other (architectural-only)
  cartridges — thermal MLX90640, air-quality BME688, audio — are all **I²C/low-speed
  sensors that live in the cartridge** and speak over exactly these pins. The vision
  cartridge is the *special* case that reuses the core eye through **swappable optics**,
  exactly like a microscope with interchangeable objectives. That's a coherent instrument
  story, not a compromise.
- **Bonus constraint that earns Phase 2 its keep:** because the cartridge lens barrel
  must sit **optically coaxial** with the fixed core camera, the dovetail's alignment
  budget (±0.3 mm at the mating plane, set by pogo compression) now governs the **optical
  axis** *and* the electrical pads simultaneously. One tolerance, two functions — this is
  a real, honest multi-objective constraint for the dovetail study.

**Consequence for the spec:** `connector-spec.md` defines an **optical axis** location and
its keep-out, in addition to the pad array. The core camera looks out **+Z** (normal to
the mating base plane); the cartridge barrel is coaxial above it.

---

## 3. On-device inference vs. cloud API (documented tradeoff)

**The hero interaction — "point → identify → explain" — is a Vision-Language-Model task.
It runs as a cloud API call (Claude vision-class), not on-device.**

- **Why not on-device:** Zero 2 W = quad A53 @ 1 GHz, 512 MB RAM. A small detector
  (MobileNet-SSD / YOLO-nano) might manage ~1–5 fps of "is there an object / where,"
  but *identifying a plant species and explaining it* needs a large VLM that does not fit
  or run usefully on the Pi. **Critically, this is true of Pi 4/5 as well** — none of them
  run a good VLM locally — so the API decision is independent of Pi model and does not
  argue for the bigger Pi.
- **Pipeline:** capture frame (CSI) → optional lightweight on-device framing/region hint
  → POST image to vision API → receive identification + explanation text → TTS to speaker
  + render caption on the 240×280 strip.
- **Tradeoffs (stated plainly):**
  - ✅ Capability and answer quality far beyond anything on-device.
  - ⚠️ Latency ~1–3 s per query *(est.)*; needs WiFi; not usable offline; recurring API
    cost; an API key that **must live in `.env`, never committed** (Risk table).
- **Honesty:** the prototype (Phase 5) will make a *real* API call against a real image.
  We will not stub the model with canned answers.

---

## 4. Power budget & runtime (estimates — not measured)

Assumptions *(guess/est., to refine against datasheets in Phase 4)*:

| Mode | Draw @ system | Note |
|---|---|---|
| Idle (Pi up, WiFi assoc, screen dim) | ~0.7 W *(est.)* | Zero 2 W floor is ~0.4–0.6 W |
| Active browse (screen on, encoder use) | ~1.2 W *(est.)* | + backlight ~0.15 W |
| Query burst (WiFi TX + CPU + capture) | ~2.5 W for 1–3 s *(est.)* | intermittent |
| Audio playback | +~0.2 W avg *(est.)* | MAX98357A into small speaker |

- Blended "instrument use" average ≈ **1.3 W** *(est.)*.
- Battery: 1500 mAh × 3.7 V = **5.55 Wh**; boost ≈ 85% → **~4.7 Wh usable** *(est.)*.
- **Runtime ≈ 4.7 / 1.3 ≈ 3.5 h continuous active use** *(est.)*.
- Zero 2 W does not deep-sleep well → between sessions, **hard-off via PMIC button**
  (encoder long-press). Don't promise multi-day standby.

---

## 5. Data/signal map (core ↔ cartridge boundary)

```
        CORE                                          CARTRIDGE (hero: vision optics)
  ┌─────────────────────────┐                    ┌──────────────────────────────┐
  │ Pi Zero 2 W             │                    │  macro-lens barrel (coaxial)  │
  │  ├ CSI ── camera ───────┼── looks out +Z ───▶│  (no sensor — optics only)    │
  │  ├ SPI ── 1.69" display │                    │  LED ring  ◀── V+ (PWM dim)   │
  │  ├ I²S ── mic + amp/spk  │   ┌── pogo×6 ──┐   │  ID EEPROM (I²C @0x50)        │
  │  ├ I²C ── (to cartridge) │◀──┤ interface  ├──▶│  CD# tie-to-GND, INT (shutter)│
  │  ├ GPIO ─ encoder       │   └────────────┘   └──────────────────────────────┘
  │  └ PMIC (IP5306) + USB-C │
  └─────────────────────────┘
```
Pinout and mechanical contract: see [`connector-spec.md`](connector-spec.md).

---

## 6. Open decisions remaining after Phase 1

| Item | Status | When it must close |
|---|---|---|
| Exact display module P/N + true active-area dims | starting from 1.69" 240×280 ST7789V generic; datasheet TBD | Phase 3 (drives bezel) |
| LED ring: LED count / driver (direct-PWM vs. tiny constant-current) | budget-capped at ≤150 mA | Phase 4 |
| PMIC final part (IP5306 vs. discrete) | leaning IP5306 | Phase 4 |
| Dovetail profile geometry | seed values in connector-spec §5; **optimized in Phase 2** | Phase 2 |
| License (MIT vs CERN-OHL-S) | deferred | Phase 7 |

---

## 7. Note on Phase 4 depth (updates the Phase 0 finding)

Phase 0 found **no KiCad** in the environment. Per review, **KiCad will be installed**,
so Phase 4 target is upgraded from "documented schematic only" to **schematic +
footprints + BOM** as openable `.kicad_sch` / `.kicad_pcb`, validated/exported via
`kicad-cli`. Full routing is optional. It remains a **design, not a verified board** —
no fabricated/tested claims. (See the dated addendum in `tool-capabilities.md`.)

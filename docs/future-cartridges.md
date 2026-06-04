# Future cartridges — architecture only (NOT built)

Scope discipline: **one** hero cartridge gets finished — the vision/macro
lens. Every other cartridge idea lives here as *architecture only*, to prove the platform
generalises without becoming a graveyard of half-built modules. Nothing below is modelled,
and nothing below should be modelled unless a future phase explicitly re-opens scope.

The test each must pass: **does it conform to the frozen interface contract**
(`connector-spec.md` v0.2) without changing it? The contract gives every cartridge:
`V+ (3V3 switched ≤150 mA) · GND · I²C SDA · I²C SCL · CD# · INT`, an EEPROM ID at `0x50`,
the dual-rail dovetail envelope, and the ±0.28 mm alignment budget. If a sense fits in that
envelope, the architecture holds.

| Cartridge (architectural) | Sensor (representative) | How it uses the 6-pin contract | Why it fits unchanged |
|---|---|---|---|
| **Thermal sense** | MLX90640 32×24 IR array | I²C sensor on SDA/SCL; INT = frame-ready; powered from V+ | I²C @ ≤1 MHz, low-bandwidth — exactly what the contract carries. No optics needed (its own lens). |
| **Air-quality / environment** | BME688 (gas/VOC/T/RH/P) | I²C on SDA/SCL; V+ powers it; INT optional | Pure I²C, microwatts. The instrument "smells" instead of seeing. |
| **Audio / ultrasonic** | I²S or analog MEMS + a tiny MCU exposing I²C | MCU does the DSP, presents results over I²C; INT on detection | The 6-pin bus can't carry raw I²S fast enough → a cartridge-side MCU summarises and speaks I²C. Documents the contract's *limit* honestly. |

**What makes the vision cartridge the special case** (and why it was chosen as the hero):
it is the only one that *reuses the core's eye* through swappable optics, like a microscope
objective — so it exercises the optical-axis coaxiality constraint (the ±0.28 mm budget
governing the bore, not just the pads). The others are self-contained I²C sensors and are, if
anything, *easier* — which is the point: the hard case is built, the rest follow by contract.

**The audio cartridge is the honest edge case.** Raw audio/ultrasonic streaming exceeds the
6-pin low-speed contract, so that cartridge would need a small MCU to do on-cartridge DSP and
report over I²C. That's not a flaw in the architecture — it's the architecture telling you
where the boundary is. CSI-bandwidth senses (more cameras, depth) stay in the core, like the
vision camera does.

> None of this is built. It exists to show the connector contract was designed once and holds.

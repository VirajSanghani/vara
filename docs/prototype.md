# VARA — Functional Prototype (Phase 5)

**Date:** 2026-06-03 · Code: `app/` · Run: `python3 -m app.demo` (off-Pi) / `python3 -m app.main` (Pi).

> ## ⚠️ Honesty banner
> The pipeline is **logic-validated**, not **hardware-tested**. On this machine, camera,
> display, audio, control, cartridge, and the vision API are all **stubs** (each logs
> "STUB …" at startup). Stubs are structured as swappable drop-ins for the real drivers — they
> are **not** presented as working hardware, and the demo prints "LOGIC-VALIDATED … NOT
> hardware-tested." Secrets live in a **gitignored `.env`** (`.env.example` provided); no key
> is committed.

---

## 1. The pipeline
```
[jog press] → camera.capture() → display.show_viewfinder()
            → display.show_thinking() → vision.identify()  ──ok──→ display.show_result() + tts.speak()
                                                           └─err─→ display.show_error()  + tts.speak()
```
- **No on-device VLM** (Phase 1): `identify+explain` is a **cloud API call** (Anthropic Claude
  vision) with a cached system prompt. The Pi only captures, renders, and speaks.
- **Display** = the 240×280 viewfinder + caption split (architecture.md). Real ST7789 and the
  stub render the **identical** PIL layout — so `app/samples/*.png` are what the panel shows.

## 2. Cartridge init — the read-before-PWM contract (carried from Phase 4)
The shared V+ rail powers **both** the ID EEPROM and the LED ring, and LED dimming PWMs the V+
load switch (which power-cycles the EEPROM). So the order is mandatory:
```
init: cartridge.read_id()   # 1. read EEPROM @0x50 while V+ is steady
      cartridge.enable_power_pwm(0.6)   # 2. ONLY THEN may V+ be PWM'd for the LED
```
This is **enforced in code**: `enable_power_pwm()` raises `SequencingError` if `read_id()`
hasn't run. The demo proves the guard fires (`app/demo.py` step 2). A real driver must
preserve this ordering — the guard exists so a refactor can't silently break it.

## 3. What runs vs. what's stubbed

| Subsystem | Real driver (on Pi) | Stub (here) |
|---|---|---|
| Camera | `picamera2` (CSI) | synthetic test frame |
| Display | `ST7789` 240×280 SPI | identical PIL layout → PNG in `app/_out/` |
| Audio/TTS | `espeak-ng` via I²S amp | console + `tts_transcript.txt` |
| Control | `gpiozero` EC11 encoder | scripted events / stdin |
| Cartridge | `smbus2` EEPROM @0x50 + PWM | fake EEPROM record (ordering still enforced) |
| Vision | Anthropic Claude vision (needs key + Wi-Fi) | canned result, source="stub" |

Selection is automatic and **logged**: a subsystem runs real only if its lib imports and
`VARA_FORCE_STUBS` is off; otherwise stub. Never silently faked.

## 4. Handled failure modes (graceful degradation — verified in the demo)
Each maps to a typed `VisionError` → a clean error screen + short spoken message → return to
idle. **None crash the app.**

| Condition | Detected by | User sees |
|---|---|---|
| No Wi-Fi / host unreachable | socket preflight + `APIConnectionError` | "Offline — no network" |
| No API key | missing `ANTHROPIC_API_KEY` at startup | "No API key set" (degraded mode, per scan) |
| API timeout | `APITimeoutError` (timeout 12 s) | "Timed out — retry" |
| API/service error | `APIError` | "Service error — retry" |

Sample frames: `app/samples/sample_result.png` (success), `sample_error_offline.png`
(degradation), `sample_boot.png`. Full set regenerates to `app/_out/` via `python3 -m app.demo`.

## 5. Demo trace (logic path)
`python3 -m app.demo` runs: cartridge init (ID→PWM) → guard check (raises as expected) →
success scan → timeout → offline → no-key. 13 frames + a TTS transcript are produced; every
degradation path shows a clean error and continues.

## 6. Honest limitations
1. **Not hardware-tested** — no camera frame, panel, audio, I²C, or live API call was exercised
   on real hardware here. The real-driver classes are written against the documented APIs
   (`picamera2`, `ST7789`, `gpiozero`, `smbus2`, `anthropic`) but **unrun on a Pi**.
2. The **real vision call is unexercised** (no key in this environment); the success path used
   the stub. With a key + network, `RealVisionClient` is the default and the stub is bypassed.
3. GPIO pin numbers / overlays (SPI, I²C, I²S, camera) must be confirmed on the device.
4. Power sequencing of the IP5306 (auto-on, the shared button) is modeled in firmware logic,
   not validated electrically.

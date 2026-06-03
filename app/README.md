# VARA prototype — run & flash

The functional pipeline: **jog-press → camera capture → cloud vision identify → viewfinder +
caption on the 1.69″ display → speak**. The brain is a real Raspberry Pi Zero 2 W; identify+
explain is a cloud API call (no on-device VLM — Phase 1). See `../docs/prototype.md` for what
runs vs. what's stubbed and the handled failure modes.

## Off-Pi logic demo (no hardware)
```bash
pip install pillow anthropic          # only these needed for the demo
python3 -m app.demo                   # exercises init + a scan + every failure mode
```
Renders display frames to `app/_out/` and a TTS transcript. **Logic-validated, not
hardware-tested** — camera/display/audio/cartridge/vision are stubs (logged at startup).
Sample frames are committed in `app/samples/`.

## Run on a real Raspberry Pi Zero 2 W
1. **Flash** Raspberry Pi OS (Bookworm, 64-bit Lite) with Raspberry Pi Imager; set Wi-Fi +
   SSH in the imager (Wi-Fi is required — the vision call needs network).
2. **Enable interfaces:** `sudo raspi-config` → enable **SPI** (display), **I2C** (cartridge
   EEPROM), **I2S** (audio), and the **camera**.
3. **Wire** per `../electronics/` (SPI display, I²S mic+amp, EC11 on GPIO5/6/16, USB-C PMIC,
   CSI camera, 6-pin pogo). Pin map = `../electronics/netlist.csv`.
4. **Install:**
   ```bash
   sudo apt install -y espeak-ng python3-picamera2
   pip install -r app/requirements.txt st7789 gpiozero smbus2
   cp .env.example .env && nano .env        # paste ANTHROPIC_API_KEY
   ```
5. **Run:** `python3 -m app.main`  (jog press = scan, long-press = shutdown).
   For boot-on-power, wrap in a `systemd` service.

Missing any Pi library → that subsystem auto-falls-back to its **stub** (logged), so the app
still starts. No `ANTHROPIC_API_KEY` → degraded mode showing a clean "No API key" screen.

## Layout
```
app/
  config.py      .env load + REAL/STUB selection (logged)
  state.py       pipeline states + typed vision errors
  vision.py      cloud client (RealVisionClient + StubVisionClient)
  pipeline.py    cartridge init (ID→PWM) + scan loop + degradation
  main.py        real-device entry           demo.py  off-Pi logic demo
  hal/           camera · display · audio · control · cartridge  (interface + real + stub)
```

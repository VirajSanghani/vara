"""Logic-path demo (off-Pi). Forces STUB HAL and exercises:
  - cartridge init ordering (ID read → THEN V+ PWM) + the guard that enforces it
  - a successful scan (stub vision)
  - each graceful-degradation failure mode (timeout, offline, no-key)

Produces display frames in app/_out/ and a TTS transcript. This is LOGIC-VALIDATED, not
hardware-tested: camera/display/audio/cartridge/vision are all stubs (clearly logged).

Run:  python3 -m app.demo
"""
from __future__ import annotations
import logging
from .config import Config
from .hal.camera import StubCamera
from .hal.display import StubDisplay
from .hal.audio import StubTts
from .hal.cartridge import StubCartridge, SequencingError
from .vision import StubVisionClient
from .state import VisionResult, VisionTimeout, NetworkUnavailable, NoApiKey
from .pipeline import Pipeline


def banner(t): print(f"\n=== {t} ===")


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    cfg = Config()
    cfg.force_stubs = True
    cam, disp, tts = StubCamera(), StubDisplay(cfg), StubTts(cfg.out_dir)
    cart = StubCartridge()

    banner("1) Cartridge init — must read ID, THEN PWM V+")
    pipe = Pipeline(cfg, cam, disp, tts, cart, StubVisionClient())
    pipe.init_cartridge()

    banner("2) Guard check — PWM before ID read must RAISE (proves read-before-PWM is enforced)")
    fresh = StubCartridge()
    try:
        fresh.enable_power_pwm(0.6)
        print("  ✗ FAIL: guard did not fire")
    except SequencingError as e:
        print(f"  ✓ guard fired: {e}")

    banner("3) Successful scan (stub vision)")
    pipe.vision = StubVisionClient(VisionResult(
        "Monstera deliciosa",
        "A tropical aroid whose split leaves let wind and light pass to the leaves below.",
        source="stub"))
    pipe.scan()

    banner("4) Degradation — API timeout")
    pipe.vision = StubVisionClient(raises=VisionTimeout()); pipe.scan()
    banner("5) Degradation — offline / no network")
    pipe.vision = StubVisionClient(raises=NetworkUnavailable()); pipe.scan()
    banner("6) Degradation — no API key")
    pipe.vision = StubVisionClient(raises=NoApiKey()); pipe.scan()

    banner("frames written")
    for p in sorted(cfg.out_dir.glob("frame_*.png")):
        print("  ", p.name)
    print("\nLOGIC-VALIDATED (stubbed camera/display/audio/cartridge/vision) — NOT hardware-tested.")


if __name__ == "__main__":
    main()

"""VARA entry point (real device). Run on a Zero 2 W:  python3 -m app.main

Picks REAL drivers where libs are present, STUBS otherwise (logged). If no API key is set,
runs in a degraded mode that shows a clean 'No API key' screen on each scan — never crashes.
"""
from __future__ import annotations
import logging, sys
from .config import Config, hardware_available
from .hal import build_hal
from .hal.control import GpioControl, StubControl, Event
from .vision import RealVisionClient, StubVisionClient
from .state import NoApiKey
from .pipeline import Pipeline


def build_control(cfg):
    if not cfg.force_stubs and hardware_available().get("control"):
        try:
            return GpioControl()
        except Exception as e:
            logging.warning("encoder real driver failed (%s) → stdin stub", e)
    # off-Pi fallback: ENTER = press, 'q' + ENTER = long-press (shutdown)
    def stdin_events():
        print("[control STUB] ENTER = scan, 'q'+ENTER = quit")
        for line in sys.stdin:
            yield Event.LONG_PRESS if line.strip() == "q" else Event.PRESS
    return StubControl(stdin_events())


def build_vision(cfg):
    try:
        return RealVisionClient(cfg)
    except NoApiKey:
        logging.warning("no ANTHROPIC_API_KEY → degraded mode (scans show 'No API key')")
        return StubVisionClient(raises=NoApiKey())   # clean error per scan, no crash


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    cfg = Config()
    control = build_control(cfg)
    is_real_control = isinstance(control, GpioControl)
    camera, display, tts, cartridge, report = build_hal(cfg, control=is_real_control)
    logging.info("HAL modes: %s", report)
    vision = build_vision(cfg)
    Pipeline(cfg, camera, display, tts, cartridge, vision).run(control)


if __name__ == "__main__":
    main()

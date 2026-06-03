"""HAL factory — picks REAL vs STUB per subsystem, logging each choice explicitly.

A subsystem runs REAL only if (a) not force_stubs and (b) its driver lib imported. Otherwise
STUB. Stubs are never presented as working hardware (see each module's startup log line).
"""
from __future__ import annotations
import logging
from .camera import PiCamera2Camera, StubCamera
from .display import ST7789Display, StubDisplay
from .audio import EspeakTts, StubTts
from .cartridge import I2cCartridge, StubCartridge

log = logging.getLogger("vara.hal")


def build_hal(cfg, *, control):
    """Return (camera, display, tts, cartridge, control, mode_report)."""
    from ..config import hardware_available
    avail = {} if cfg.force_stubs else hardware_available()
    if cfg.force_stubs:
        log.warning("VARA_FORCE_STUBS=1 → all subsystems STUBBED")

    def pick(name, real_factory, stub_factory):
        if avail.get(name):
            try:
                return real_factory(), "real"
            except Exception as e:
                log.warning("%s real driver failed (%s) → STUB", name, e)
        return stub_factory(), "stub"

    camera, m_cam = pick("camera", PiCamera2Camera, StubCamera)
    display, m_disp = pick("display", lambda: ST7789Display(cfg), lambda: StubDisplay(cfg))
    tts, m_tts = pick("audio", EspeakTts, lambda: StubTts(cfg.out_dir))
    cartridge, m_cart = pick("cartridge", I2cCartridge, StubCartridge)
    report = {"camera": m_cam, "display": m_disp, "tts": m_tts,
              "cartridge": m_cart, "control": "real" if control else "stub"}
    return camera, display, tts, cartridge, report

"""The VARA pipeline: cartridge init (ID-then-PWM) + the scan loop.

  init:  read EEPROM ID  →  (only then) enable V+ PWM for the LED ring
  scan:  press → capture → viewfinder → vision API → result+speak  (errors → clean error state)
"""
from __future__ import annotations
import logging
from .state import State, VisionError
from .hal.control import Event

log = logging.getLogger("vara.pipeline")


class Pipeline:
    def __init__(self, cfg, camera, display, tts, cartridge, vision):
        self.cfg, self.camera, self.display = cfg, camera, display
        self.tts, self.cartridge, self.vision = tts, cartridge, vision
        self.state = State.BOOTING
        self.cartridge_info = None

    # ---- cartridge init: ORDER IS THE CONTRACT (read ID, THEN PWM) ----
    def init_cartridge(self):
        self.display.show_boot()
        # 1) read the ID while V+ is steady
        self.cartridge_info = self.cartridge.read_id()
        if self.cartridge_info:
            log.info("cartridge mounted: '%s' (type %d)",
                     self.cartridge_info.name, self.cartridge_info.cartridge_type)
        # 2) ONLY NOW may we PWM V+ for the LED ring (guard enforces this)
        try:
            self.cartridge.enable_power_pwm(duty=0.6)
        except Exception as e:                       # SequencingError would be a code bug
            log.error("V+ enable failed: %s", e)
        self.state = State.IDLE

    # ---- one scan ----
    def scan(self):
        self.state = State.CAPTURING
        frame = self.camera.capture()
        self.display.show_viewfinder(frame)
        self.state = State.THINKING
        self.display.show_thinking(frame)
        try:
            result = self.vision.identify(frame)
        except VisionError as e:                     # graceful degradation — never crash
            self.state = State.ERROR
            log.warning("scan degraded: %s (%s)", type(e).__name__, e)
            self.display.show_error(e.user_msg, "Point and press to try again.")
            self.tts.speak(e.user_msg)
            return None
        self.state = State.RESULT
        self.display.show_result(result.title, result.detail, frame)
        self.tts.speak(f"{result.title}. {result.detail}")
        log.info("identified: %s (source=%s)", result.title, result.source)
        return result

    # ---- event loop ----
    def run(self, control):
        self.init_cartridge()
        log.info("ready — state=%s", self.state.value)
        for ev in control.events():
            if ev is Event.PRESS:
                self.scan()
                self.state = State.IDLE
            elif ev is Event.LONG_PRESS:
                log.info("long-press → shutdown")
                break
            # rotate events would scroll history/brightness — out of prototype scope
        self.camera.close()

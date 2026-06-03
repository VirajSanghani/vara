"""Control HAL. Real = EC11 jog encoder + push (gpiozero). Stub = scripted/stdin events.

The single primary control (Phase 1). Press = scan; long-press = shutdown; rotate = navigate.
"""
from __future__ import annotations
import enum, logging
log = logging.getLogger("vara.control")


class Event(enum.Enum):
    PRESS = "press"
    LONG_PRESS = "long_press"
    ROTATE_CW = "cw"
    ROTATE_CCW = "ccw"


class Control:
    def events(self):
        """Yield Event values until shutdown."""
        raise NotImplementedError


class GpioControl(Control):  # REAL — gpiozero on the Pi
    def __init__(self):
        from gpiozero import RotaryEncoder, Button  # noqa
        import queue
        self.q = queue.Queue()
        self.enc = RotaryEncoder(5, 6, max_steps=0)
        self.btn = Button(16, hold_time=1.5)
        self.enc.when_rotated_clockwise = lambda: self.q.put(Event.ROTATE_CW)
        self.enc.when_rotated_counter_clockwise = lambda: self.q.put(Event.ROTATE_CCW)
        self.btn.when_held = lambda: self.q.put(Event.LONG_PRESS)
        self.btn.when_released = lambda: self.q.put(Event.PRESS) if not self.btn.was_held else None
        log.info("control: REAL EC11 (GPIO5/6 + SW GPIO16)")

    def events(self):
        while True:
            ev = self.q.get()
            yield ev
            if ev is Event.LONG_PRESS:
                break


class StubControl(Control):  # STUB — replays a scripted event sequence (for the demo)
    def __init__(self, script):
        self.script = list(script)
        log.warning("control: STUB (scripted events: %s)", [e.value for e in self.script])

    def events(self):
        yield from self.script

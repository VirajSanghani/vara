"""Camera HAL. Real = picamera2 (CSI, fixed in core). Stub = synthetic test frame.

Per Phase 1: the camera is in the CORE on CSI; the cartridge holds only optics.
"""
from __future__ import annotations
import io, logging
log = logging.getLogger("vara.camera")


class Camera:
    """Interface: capture() -> JPEG/PNG bytes."""
    def capture(self) -> bytes: raise NotImplementedError
    def close(self): pass


class PiCamera2Camera(Camera):  # REAL — runs only on a Pi with the CSI camera
    def __init__(self):
        from picamera2 import Picamera2          # noqa: real driver
        self.cam = Picamera2()
        self.cam.configure(self.cam.create_still_configuration())
        self.cam.start()
        log.info("camera: REAL picamera2 (CSI)")

    def capture(self) -> bytes:
        buf = io.BytesIO()
        self.cam.capture_file(buf, format="jpeg")
        return buf.getvalue()

    def close(self):
        try: self.cam.stop()
        except Exception: pass


class StubCamera(Camera):  # STUB — synthetic frame so the logic path runs off-Pi
    """Generates a labelled test pattern. NOT a real capture."""
    def __init__(self, w=480, h=480):
        self.w, self.h = w, h
        log.warning("camera: STUB (synthetic frame — not a real capture)")

    def capture(self) -> bytes:
        from PIL import Image, ImageDraw
        img = Image.new("RGB", (self.w, self.h), (40, 60, 70))
        d = ImageDraw.Draw(img)
        for i in range(0, self.w, 40):
            d.line([(i, 0), (i, self.h)], fill=(55, 75, 85), width=1)
        d.ellipse([self.w*0.3, self.h*0.3, self.w*0.7, self.h*0.7], outline=(180, 200, 120), width=6)
        d.text((12, 12), "STUB CAMERA FRAME", fill=(220, 220, 220))
        buf = io.BytesIO(); img.save(buf, format="JPEG"); return buf.getvalue()

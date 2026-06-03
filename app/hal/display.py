"""Display HAL. Real = ST7789 1.69" 240x280 SPI. Stub = renders the SAME PIL layout to PNG.

Layout (architecture.md): top `viewfinder_h` px = camera frame; remainder = caption strip
(title + detail/status). Both real and stub build the identical PIL image — only the final
"push to panel vs save PNG" differs, so what you see in _out/ is what the panel would show.
"""
from __future__ import annotations
import logging
from pathlib import Path
log = logging.getLogger("vara.display")

STONE = (28, 28, 26); AMBER = (212, 140, 46); INK = (235, 232, 224); MUTE = (150, 150, 140)
ERRC = (200, 90, 70)


def _render(cfg, *, frame_bytes=None, title="", detail="", status="", error=False):
    """Build the 240x280 split-layout image (shared by real + stub)."""
    from PIL import Image, ImageDraw
    W, H, VF = cfg.disp_w, cfg.disp_h, cfg.viewfinder_h
    img = Image.new("RGB", (W, H), STONE)
    d = ImageDraw.Draw(img)
    # viewfinder (top)
    if frame_bytes:
        import io
        fr = Image.open(io.BytesIO(frame_bytes)).convert("RGB")
        side = min(fr.size); fr = fr.crop((0, 0, side, side)).resize((W, VF))
        img.paste(fr, (0, 0))
    else:
        d.rectangle([0, 0, W, VF], fill=(18, 20, 22))
    d.line([(0, VF), (W, VF)], fill=AMBER, width=2)
    # caption strip (bottom)
    if error:
        d.text((10, VF + 14), "! " + title, fill=ERRC)
        d.text((10, VF + 42), detail, fill=MUTE)
    else:
        d.text((10, VF + 10), title or status, fill=AMBER)
        # wrap detail
        words, line, y = detail.split(), "", VF + 36
        for w in words:
            if len(line) + len(w) > 34:
                d.text((10, y), line, fill=INK); y += 16; line = w
            else:
                line = (line + " " + w).strip()
        if line: d.text((10, y), line, fill=INK)
    if status and not error:
        d.text((10, H - 16), status, fill=MUTE)
    return img


class Display:
    def show_boot(self): ...
    def show_viewfinder(self, frame_bytes): ...
    def show_thinking(self, frame_bytes): ...
    def show_result(self, title, detail, frame_bytes): ...
    def show_error(self, title, detail): ...


class ST7789Display(Display):  # REAL — SPI panel on a Pi
    def __init__(self, cfg):
        import ST7789  # noqa
        self.cfg = cfg
        self.panel = ST7789.ST7789(width=cfg.disp_w, height=cfg.disp_h, rotation=0,
                                   port=0, cs=0, dc=25, rst=24, backlight=13, spi_speed_hz=40_000_000)
        log.info("display: REAL ST7789 240x280 SPI")

    def _push(self, img): self.panel.display(img)
    def show_boot(self): self._push(_render(self.cfg, status="VARA"))
    def show_viewfinder(self, fb): self._push(_render(self.cfg, frame_bytes=fb, status="press to scan"))
    def show_thinking(self, fb): self._push(_render(self.cfg, frame_bytes=fb, status="identifying..."))
    def show_result(self, t, dt, fb): self._push(_render(self.cfg, frame_bytes=fb, title=t, detail=dt, status="OK"))
    def show_error(self, t, dt): self._push(_render(self.cfg, title=t, detail=dt, error=True))


class StubDisplay(Display):  # STUB — same layout saved as PNG so the logic is visible off-Pi
    def __init__(self, cfg):
        self.cfg = cfg; self.n = 0
        log.warning("display: STUB (renders frames to %s — not a real panel)", cfg.out_dir)

    def _save(self, img, tag):
        self.n += 1
        p = Path(self.cfg.out_dir) / f"frame_{self.n:02d}_{tag}.png"
        img.save(p); log.info("display[STUB] -> %s", p.name); return p

    def show_boot(self): self._save(_render(self.cfg, status="VARA"), "boot")
    def show_viewfinder(self, fb): self._save(_render(self.cfg, frame_bytes=fb, status="press to scan"), "viewfinder")
    def show_thinking(self, fb): self._save(_render(self.cfg, frame_bytes=fb, status="identifying..."), "thinking")
    def show_result(self, t, dt, fb): self._save(_render(self.cfg, frame_bytes=fb, title=t, detail=dt, status="OK"), "result")
    def show_error(self, t, dt): self._save(_render(self.cfg, title=t, detail=dt, error=True), "error")

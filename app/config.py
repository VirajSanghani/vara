"""VARA prototype config + HAL selection.

Loads .env (no python-dotenv dependency), holds runtime config, and decides — explicitly,
with logging — whether each subsystem runs on REAL hardware or a STUB. Stubs are never
presented as working hardware; the chosen mode is logged at startup and surfaced in
docs/prototype.md.
"""
from __future__ import annotations
import os, logging
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger("vara.config")
APP_DIR = Path(__file__).resolve().parent
REPO_DIR = APP_DIR.parent


def load_dotenv(path: Path | None = None) -> dict:
    """Minimal KEY=VALUE .env reader. Secrets stay here; .env is gitignored."""
    path = path or (REPO_DIR / ".env")
    env = {}
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    # real env vars override the file
    for k in ("ANTHROPIC_API_KEY", "VARA_MODEL", "VARA_FORCE_STUBS"):
        if k in os.environ:
            env[k] = os.environ[k]
    return env


def hardware_available() -> dict:
    """Probe for the real driver libs. Absent → that subsystem uses its stub."""
    avail = {}
    for name, mod in {
        "camera": "picamera2", "display": "ST7789",
        "audio": "subprocess", "control": "gpiozero", "cartridge": "smbus2",
    }.items():
        try:
            __import__(mod)
            avail[name] = True
        except Exception:
            avail[name] = False
    return avail


@dataclass
class Config:
    env: dict = field(default_factory=load_dotenv)
    # display: 1.69" ST7789, 240x280, viewfinder + caption split (architecture.md)
    disp_w: int = 240
    disp_h: int = 280
    viewfinder_h: int = 180          # top region = live frame; remainder = caption strip
    model: str = "claude-haiku-4-5"  # fast vision identify; override via VARA_MODEL
    api_timeout_s: float = 12.0
    out_dir: Path = APP_DIR / "_out"
    force_stubs: bool = False

    def __post_init__(self):
        self.model = self.env.get("VARA_MODEL", self.model)
        self.force_stubs = self.env.get("VARA_FORCE_STUBS", "0") in ("1", "true", "True")
        self.out_dir.mkdir(exist_ok=True)

    @property
    def api_key(self) -> str | None:
        return self.env.get("ANTHROPIC_API_KEY") or None

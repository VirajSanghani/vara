"""TTS HAL. Real = espeak-ng/piper via the I2S amp (MAX98357A). Stub = print + transcript."""
from __future__ import annotations
import logging, shutil, subprocess
from pathlib import Path
log = logging.getLogger("vara.audio")


class Tts:
    def speak(self, text: str): raise NotImplementedError


class EspeakTts(Tts):  # REAL — needs espeak-ng + the I2S audio path configured
    def __init__(self):
        if not shutil.which("espeak-ng"):
            raise RuntimeError("espeak-ng not installed")
        log.info("tts: REAL espeak-ng")

    def speak(self, text: str):
        subprocess.run(["espeak-ng", "-s", "150", text], check=False)


class StubTts(Tts):  # STUB — prints and appends to a transcript file
    def __init__(self, out_dir: Path):
        self.path = Path(out_dir) / "tts_transcript.txt"
        log.warning("tts: STUB (console + %s — no audio out)", self.path.name)

    def speak(self, text: str):
        print(f"  🔊 [TTS] {text}")
        with open(self.path, "a") as f:
            f.write(text + "\n")

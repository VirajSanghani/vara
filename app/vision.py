"""Cloud vision client. No on-device VLM (Phase 1): identify+explain is a cloud API call.

RealVisionClient uses the Anthropic SDK (Claude vision) with a cached system prompt.
Every failure maps to a typed VisionError so the pipeline can show a clean error state.
StubVisionClient returns a canned result for the off-Pi logic demo — explicitly source="stub".
"""
from __future__ import annotations
import base64, logging, socket
from .state import VisionResult, NoApiKey, NetworkUnavailable, VisionTimeout, VisionAPIError

log = logging.getLogger("vara.vision")

SYSTEM = ("You are VARA, a handheld perception instrument. The user points you at an object. "
          "Identify it in 2-5 words, then explain what it is in ONE short sentence a curious "
          "person would enjoy. Reply EXACTLY as 'TITLE | DETAIL' with no other text.")


def _online(host="api.anthropic.com", port=443, timeout=3.0) -> bool:
    try:
        socket.create_connection((host, port), timeout=timeout).close()
        return True
    except OSError:
        return False


class VisionClient:
    def identify(self, image_bytes: bytes) -> VisionResult: raise NotImplementedError


class RealVisionClient(VisionClient):
    def __init__(self, cfg):
        if not cfg.api_key:
            raise NoApiKey()                       # caught at startup → degraded mode
        import anthropic
        self.cfg = cfg
        self.client = anthropic.Anthropic(api_key=cfg.api_key, timeout=cfg.api_timeout_s)
        self._anthropic = anthropic
        log.info("vision: REAL Anthropic %s (timeout %.0fs)", cfg.model, cfg.api_timeout_s)

    def identify(self, image_bytes: bytes) -> VisionResult:
        if not _online():
            raise NetworkUnavailable()
        b64 = base64.standard_b64encode(image_bytes).decode()
        try:
            msg = self.client.messages.create(
                model=self.cfg.model, max_tokens=200,
                # cache the static system prompt — repeated scans reuse it (claude-api best practice)
                system=[{"type": "text", "text": SYSTEM,
                         "cache_control": {"type": "ephemeral"}}],
                messages=[{"role": "user", "content": [
                    {"type": "image", "source": {"type": "base64",
                     "media_type": "image/jpeg", "data": b64}},
                    {"type": "text", "text": "Identify this."}]}],
            )
            text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()
        except self._anthropic.APITimeoutError:
            raise VisionTimeout()
        except self._anthropic.APIConnectionError:
            raise NetworkUnavailable()
        except self._anthropic.APIError as e:
            raise VisionAPIError(str(e))
        title, _, detail = text.partition("|")
        return VisionResult(title.strip() or "Unknown", detail.strip() or text, source="api")


class StubVisionClient(VisionClient):
    """Canned identification for the off-Pi logic demo. NOT a real API call."""
    def __init__(self, result=None, raises=None):
        self._result = result or VisionResult(
            "Monstera deliciosa",
            "A tropical aroid whose split leaves let wind and light pass to lower foliage.",
            source="stub")
        self._raises = raises   # optionally simulate a failure mode
        log.warning("vision: STUB (canned result — no real API call)")

    def identify(self, image_bytes: bytes) -> VisionResult:
        if self._raises:
            raise self._raises
        return self._result

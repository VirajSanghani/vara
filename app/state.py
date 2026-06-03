"""Pipeline state machine + the vision result/error types."""
from __future__ import annotations
import enum
from dataclasses import dataclass


class State(enum.Enum):
    BOOTING = "booting"
    IDLE = "idle"            # waiting for jog-encoder press
    CAPTURING = "capturing"  # camera grab
    THINKING = "thinking"    # vision API call in flight
    RESULT = "result"        # identification shown + spoken
    ERROR = "error"          # handled failure, clean message on display


@dataclass
class VisionResult:
    title: str               # short identification, e.g. "Monstera deliciosa"
    detail: str              # one/two-sentence explanation
    source: str = "api"      # "api" or "stub" — never claim stub == real call


# --- typed errors so the pipeline can degrade gracefully per failure mode ---
class VisionError(Exception):
    """Base; carries a short, display-safe user message."""
    user_msg = "Couldn't identify"

class NoApiKey(VisionError):
    user_msg = "No API key set"

class NetworkUnavailable(VisionError):
    user_msg = "Offline — no network"

class VisionTimeout(VisionError):
    user_msg = "Timed out — retry"

class VisionAPIError(VisionError):
    user_msg = "Service error — retry"

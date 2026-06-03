"""VARA hero vision cartridge (Phase 3 mechanical).

Consumes the resolved Gen-6 MALE rails (connector-spec v0.2) via dovetail_lib.male_rails.
[STUDY] geometry is NOT re-opened. Optics-only cartridge: the core holds the camera; this
cartridge holds the macro-lens barrel (optically coaxial — the ±0.28 mm budget governs
this alignment), an optional LED-ring recess, the EEPROM-ID pocket, and flat pogo pads.

Frame = connector datum frame. Rails occupy Z∈[0, engage_depth]; the cartridge body sits
above the mouth plane (Z ≥ engage_depth). +Z points OUT toward the subject (lens + LEDs).
"""
from __future__ import annotations
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "connector"))
from build123d import *
from dovetail_lib import DEFAULTS, male_rails, derived
from genparams import GENS

CONN = dict(DEFAULTS); CONN.update(GENS[6])
_d = derived(CONN)
H = CONN["engage_depth"]                 # mouth plane Z=4
OFF = CONN["rail_offset"]
FLOOR_W = 2 * _d["floor_half"]
OPT_X, OPT_Y = 15.0, 0.0
PAD_X = 6.0

P = dict(
    plate_thk=3.0,                       # backing plate above the mouth
    body_x0=0.0, body_x1=26.0,           # match rail span (X)
    body_yh=17.8,                        # half-height (≤17.8 keeps Y≤35.6 < 36 envelope)
    barrel_od=12.0, barrel_id=8.0, barrel_h=12.0,   # macro-lens barrel (bore = optical path)
    led_ring_od=16.0, led_ring_id=12.5, led_ring_depth=2.0,
    eeprom_w=5.0, eeprom_l=4.0, eeprom_depth=1.6, eeprom_x=22.0,
    pad_d=2.0, pad_pitch=2.54, pad_n=6, pad_recess=0.3,
    fillet_r=1.5,
)


def build_cartridge():
    p = P
    z0 = H                                       # plate bottom at the mouth plane
    z1 = H + p["plate_thk"]
    cx = (p["body_x0"] + p["body_x1"]) / 2

    body = male_rails(CONN)                      # rails, Z∈[0,H], with seating dimples
    # backing plate (Z above mouth)
    plate = Pos(cx, 0, (z0 + z1) / 2) * Box(p["body_x1"] - p["body_x0"], 2 * p["body_yh"], p["plate_thk"])
    body = body + plate
    # weld tabs over each rail column (Z 3.4–4.6) so rails fuse to the plate (no float)
    for s in (+1, -1):
        body = body + Pos(cx, s * OFF, H) * Box(p["body_x1"] - p["body_x0"], FLOOR_W, 1.2)

    # ---- macro-lens barrel (coaxial with optical axis), bore = optical path ----
    body = body + Pos(OPT_X, OPT_Y, z1 + p["barrel_h"] / 2) * Cylinder(p["barrel_od"] / 2, p["barrel_h"])
    body = body - Pos(OPT_X, OPT_Y, (z0 + z1 + p["barrel_h"]) / 2) \
        * Cylinder(p["barrel_id"] / 2, (z1 + p["barrel_h"]) - z0 + 1.0)

    # ---- LED-ring recess around the barrel base (faces +Z, toward subject) ----
    ring = Pos(OPT_X, OPT_Y, z1 - p["led_ring_depth"] / 2 + 0.01) \
        * (Cylinder(p["led_ring_od"] / 2, p["led_ring_depth"]) - Cylinder(p["led_ring_id"] / 2, p["led_ring_depth"] + 0.1))
    body = body - ring

    # ---- EEPROM-ID pocket (underside, Z=mouth face) near the pad strip ----
    body = body - Pos(p["eeprom_x"], 0, z0 + p["eeprom_depth"] / 2 - 0.01) \
        * Box(p["eeprom_l"], p["eeprom_w"], p["eeprom_depth"] + 0.02)

    # ---- flat pogo pad seats (underside, X=6, along Y) ----
    n = p["pad_n"]
    for i in range(n):
        py = (i - (n - 1) / 2) * p["pad_pitch"]
        body = body - Pos(PAD_X, py, z0 + p["pad_recess"] / 2 - 0.01) \
            * Cylinder(p["pad_d"] / 2 + 0.1, p["pad_recess"] + 0.02)

    try:   # ease the outer top edges (cosmetic + handling)
        body = fillet(body.edges().filter_by(Axis.Z).group_by(SortBy.LENGTH)[-1], p["fillet_r"])
    except Exception:
        pass
    return body


model = build_cartridge()


def _opt_path_clear(shape):
    # the barrel bore (optical path) must be open end-to-end at (15,0)
    test = Pos(OPT_X, OPT_Y, H + 8) * Cylinder((P["barrel_id"] - 1) / 2, 30)
    inter = shape & test
    v = inter.volume if inter is not None else 0.0
    assert v < 5.0, f"optical path obstructed in barrel bore: {v:.1f} mm³"

def _pads_exposed(shape):
    # nothing may protrude past the mating plane (z=H) over the pad strip → pads stay flat
    test = Pos(PAD_X, 0, H - 0.6) * Box(8.0, 16.0, 1.2)
    inter = shape & test
    v = inter.volume if inter is not None else 0.0
    # rails are outboard (Y±13); pad strip (Y±6.35) should be clear below the plate
    assert v < 2.0, f"structure intrudes pad strip below mating plane: {v:.1f} mm³"

def _envelope(shape):
    bb = shape.bounding_box().size
    assert bb.X <= 32 and bb.Y <= 36 and bb.Z <= 26, \
        f"cartridge envelope exceeded: {bb.X:.1f}x{bb.Y:.1f}x{bb.Z:.1f} > 32x36x26"

def _rails_fused(shape):
    assert shape.solids() and len(shape.solids()) == 1, \
        f"cartridge is {len(shape.solids())} solids — rails/barrel not fused"

def _valid(shape):
    iv = shape.is_valid; iv = iv() if callable(iv) else iv
    assert iv, "cartridge solid invalid"

REQUIREMENTS = [_valid, _opt_path_clear, _pads_exposed, _envelope, _rails_fused]

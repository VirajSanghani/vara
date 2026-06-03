"""VARA dovetail connector — parametric builder (Phase 2 study).

Dual-rail dovetail. The two rails sit OUTBOARD at Y = ±rail_offset so the central
channel stays clear for the pad array (Y = ±6.35) and the optical bore (Ø14 @ Y=0),
per the frozen connector-spec [CONTRACT]. Only the [STUDY] cross-section evolves here.

Local frame (matches connector-spec datum):
  X = slide axis, rail spans X∈[0, rail_length]; X=0 is the positive-stop datum.
  Y = lateral.   Z = engagement depth; mouth (opening) at Z=engage_depth, floor at Z=0.
The male rail is WIDER at the floor (Z=0) than at the mouth → captive against +Z pull-off.

dovetail_angle convention: flank angle from the base plane (Z=0).
  90° = vertical prismatic wall (no capture); <90° = undercut dovetail.
"""
from __future__ import annotations
import math
from build123d import *

PA12_CF_DENSITY = 1.10e-3  # g/mm^3 (≈1.10 g/cm³, estimate)

DEFAULTS = dict(
    dovetail_angle=55.0,   # [STUDY] deg from base plane
    flank_clearance=0.20,  # [STUDY] per-side male↔female gap (mm)
    detent_depth=0.60,     # [STUDY] snap engagement (mm)
    rail_length=24.0,      # [STUDY] bearing length along X (mm)
    wall_thk=2.4,          # [STUDY] female wall thickness (mm)
    lead_in_chamfer=1.0,   # [STUDY] mouth lead-in (mm)
    engage_depth=4.0,      # [STUDY] Z engagement depth (mm)
    mouth_w=4.0,           # [STUDY] per-rail mouth width (mm)
    rail_offset=13.0,      # [STUDY] Y center of each rail (mm)
    plate_thk=2.0,         # cartridge backing plate (mm)
    detent_pos=2.5,        # X of detent (mm) — clicks just before X=0 stop
    detent_w=4.0,          # axial width of detent bump (mm)
    finger=False,          # [STUDY] dedicated cantilever snap finger?
    finger_len=12.0,       # cantilever length (mm)
    finger_thk=1.2,        # cantilever thickness (mm)
    finger_root_fillet=0.6,  # PROTECTED functional fillet at the finger root (mm) — see
                             # dovetail-study §9: real stress concentration the beam model
                             # understates. Do NOT reduce for packaging.
)


def derived(p):
    a = math.radians(p["dovetail_angle"])
    floor_half = p["mouth_w"] / 2 + p["engage_depth"] / math.tan(a)
    mouth_half = p["mouth_w"] / 2
    return dict(floor_half=floor_half, mouth_half=mouth_half)


def _trapezoid(yc, mouth_half, floor_half, h, grow=0.0):
    """Trapezoid in (Y,Z): wide floor at Z=0, narrow mouth at Z=h. grow = per-side offset."""
    fh = floor_half + grow
    mh = mouth_half + grow
    pts = [
        (yc - fh, 0.0), (yc + fh, 0.0),
        (yc + mh, h), (yc - mh, h),
    ]
    return Plane.YZ * Polygon(*pts, align=None)


def _rail(yc, p, d, grow=0.0):
    sk = _trapezoid(yc, d["mouth_half"], d["floor_half"], p["engage_depth"], grow)
    return extrude(sk, amount=p["rail_length"])  # X∈[0, rail_length]


# ─── Reusable primitives — the single source of truth consumed by BOTH the standalone
#     connector AND the Phase-3 host bodies (core socket, cartridge rails). ───

def male_rails(params=None):
    """Male rails (both, with seating dimples) in the connector frame, X∈[0,rail_length].
    No backing plate — the host (cartridge body) provides backing."""
    p = dict(DEFAULTS); p.update(params or {}); d = derived(p)
    h = p["engage_depth"]
    rails = _rail(+p["rail_offset"], p, d) + _rail(-p["rail_offset"], p, d)
    for s in (+1, -1):
        dimple_y = s * p["rail_offset"] + s * (d["mouth_half"] - p["detent_depth"] / 2)
        rails = rails - (Pos(p["detent_pos"], dimple_y, h - 0.8)
                         * Box(p["detent_w"] + 0.2, p["detent_depth"] + 0.4, 1.4))
    return rails


def socket_cut(params=None):
    """Everything to SUBTRACT from a host body to form the female socket: the grown-male
    groove + (if finger) the finger-freeing slots WITH the protected root fillet."""
    p = dict(DEFAULTS); p.update(params or {}); d = derived(p)
    h, c, off = p["engage_depth"], p["flank_clearance"], p["rail_offset"]
    cut = _rail(+off, p, d, grow=c) + _rail(-off, p, d, grow=c)
    cut = cut + (Pos(0, 0, -c) * cut)  # clearance under the floor
    if p["finger"]:
        fz_lo, fz_hi = -p["wall_thk"], h
        for s in (+1, -1):
            slot_y = s * off + s * (d["floor_half"] + c + p["wall_thk"] / 2 + 0.01)
            slot = Pos(p["detent_pos"], slot_y, (fz_lo + fz_hi) / 2) \
                * Box(p["finger_len"], 0.8, fz_hi - fz_lo + 0.2)
            # PROTECTED finger-root fillet: round the slot's vertical (Z) ends so the
            # finger meets the body on a radius, not a sharp stress riser.
            if p["finger_root_fillet"] > 0:
                try:
                    ends = slot.edges().filter_by(Axis.Z).group_by(Axis.X)
                    slot = fillet(ends[0] + ends[-1], p["finger_root_fillet"])
                except Exception:
                    pass
            cut = cut + slot
    return cut


def detent_add(params=None):
    """Detent bumps (both rails) to ADD to a host body after the socket is cut."""
    p = dict(DEFAULTS); p.update(params or {}); d = derived(p)
    h, c, off = p["engage_depth"], p["flank_clearance"], p["rail_offset"]
    bumps = None
    # bump protrudes detent_depth into the groove AND embeds 0.4 mm into the finger face
    # (so it unions solidly with the finger root — not a floating box).
    embed = 0.4
    bw = p["detent_depth"] + embed
    for s in (+1, -1):
        face = s * (off + d["mouth_half"] + c)              # finger inner face (groove edge)
        bump_y = face - s * (bw / 2 - embed)                 # center, embedded into finger
        b = Pos(p["detent_pos"], bump_y, h - 0.8) * Box(p["detent_w"], bw, 1.2)
        bumps = b if bumps is None else bumps + b
    return bumps


def build_dovetail(params=None, part="both"):
    p = dict(DEFAULTS); p.update(params or {}); d = derived(p)
    h, L = p["engage_depth"], p["rail_length"]
    off = p["rail_offset"]

    # ---- MALE: rails (+ dimples) + backing plate, lead-in chamfer ----
    male = male_rails(p)
    plate_w = 2 * (off + d["floor_half"])
    male = male + Pos(L / 2, 0, h + p["plate_thk"] / 2) * Box(L, plate_w, p["plate_thk"])
    if p["lead_in_chamfer"] > 0:
        try:
            male = chamfer(male.edges().filter_by(Axis.Y).group_by(Axis.X)[-1],
                           p["lead_in_chamfer"])
        except Exception:
            pass

    # ---- FEMALE: block − socket_cut + detent bumps (composed from the same primitives) ----
    fy = 2 * (off + d["floor_half"]) + 2 * p["wall_thk"]
    fz_lo, fz_hi = -p["wall_thk"], h
    female = Pos(L / 2, 0, (fz_lo + fz_hi) / 2) * Box(L + 2 * p["wall_thk"], fy, fz_hi - fz_lo)
    female = female - socket_cut(p) + detent_add(p)

    if part == "male":
        return male
    if part == "female":
        return female
    return Compound(children=[female, Pos(0, 0, 6.0) * male])


def requirements_for(params=None):
    """Assert-style geometric gates (forge REQUIREMENTS). Geometry correctness only;
    alignment & stress live in analysis.py (analytical estimates)."""
    p = dict(DEFAULTS)
    if params:
        p.update(params)
    d = derived(p)
    inner_edge = p["rail_offset"] - d["floor_half"]  # nearest rail face to Y=0

    def req_captive(shape):
        assert d["floor_half"] > d["mouth_half"] + 0.1, \
            "not captive: floor not wider than mouth (no +Z capture)"

    def req_clearance(shape):
        assert p["flank_clearance"] > 0, "no flank clearance → press fit, won't slide"

    def req_central_channel_clear(shape):
        # central channel must clear optical bore (Ø14 → r=7) and pads (±6.35)
        assert inner_edge >= 7.0, \
            f"rail intrudes optical bore: inner edge {inner_edge:.2f} < 7.0 mm"

    def req_envelope(shape):
        male = build_dovetail(p, "male")
        bb = male.bounding_box().size
        assert bb.Y <= 36.0 and bb.X <= 32.0 and bb.Z <= 26.0, \
            f"cartridge envelope exceeded: {bb.X:.1f}x{bb.Y:.1f}x{bb.Z:.1f} > 32x36x26"

    def req_min_wall(shape):
        assert p["wall_thk"] >= 1.2, f"female wall {p['wall_thk']} < 1.2 mm (unprintable)"
        if p["finger"]:
            assert p["finger_thk"] >= 0.8, f"snap finger {p['finger_thk']} < 0.8 mm"

    def req_solids_valid(shape):
        for nm in ("male", "female"):
            s = build_dovetail(p, nm)
            iv = s.is_valid
            iv = iv() if callable(iv) else iv      # property in build123d 0.10
            assert iv, f"{nm} solid invalid"
            assert s.volume > 100, f"{nm} volume implausibly small"

    return [req_captive, req_clearance, req_central_channel_clear,
            req_envelope, req_min_wall, req_solids_valid]


if __name__ == "__main__":
    for nm in ("male", "female", "both"):
        s = build_dovetail(part=nm)
        bb = s.bounding_box()
        v = getattr(s, "volume", None)
        print(f"{nm:6s} bbox {bb.size.X:.1f}x{bb.size.Y:.1f}x{bb.size.Z:.1f}  vol={v}")

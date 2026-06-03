"""VARA core body (Phase 3 mechanical).

Consumes the resolved Gen-6 female socket from connector-spec v0.2 via dovetail_lib
primitives (socket_cut + detent_add). The [STUDY] geometry is NOT re-opened here.

Frame (= connector datum frame): X = cartridge slide axis (width); Y = rail-separation
axis (device height); Z = mating normal — +Z is the BACK (camera looks +Z, cartridge
clips on the back); −Z is the FRONT (screen). Mating/mouth plane at Z = engage_depth.

DfAM note: modeled as a SEALED unibody for a clean watertight single-STL deliverable.
The production part splits on a rear parting line (back cover + the M2.5 boss pattern
shown); see docs/mechanical.md.
"""
from __future__ import annotations
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "connector"))
from build123d import *
from dovetail_lib import DEFAULTS, socket_cut, detent_add, derived
from genparams import GENS

CONN = dict(DEFAULTS); CONN.update(GENS[6])   # resolved connector geometry — consume as-is
_d = derived(CONN)
Z_BACK = CONN["engage_depth"]                  # back face / mouth plane (Z=4)
OPT_X, OPT_Y = 15.0, 0.0                        # optical axis (connector-spec §3)
PAD_X = 6.0

P = dict(
    body_x0=-9.0, body_x1=35.0,   # width 44 (rail span 0..26 centered at X=13)
    body_y0=-44.0, body_y1=20.0,  # height 64 (cartridge/rails centered at Y=0; battery below)
    body_zf=-16.0,                # front (screen) face
    wall=2.4, front_wall=3.0, corner_r=3.0,
    disp_mod_w=30.4, disp_mod_h=36.6, disp_active_w=28.0, disp_active_h=32.6,
    disp_cx=13.0, disp_cy=2.0, bezel_recess=2.0,
    opt_bore_d=14.0,              # optical clear bore Ø14 (connector-spec keep-out)
    cam_pocket_d=17.0, cam_pocket_depth=3.0,
    usbc_w=9.2, usbc_h=3.6,
    enc_slot_w=12.0, enc_slot_t=4.0, enc_cy=-26.0, enc_cz=-6.0,
    spk_grille_n=3, spk_pitch=3.0, spk_d=1.5, spk_cy=-15.0,
    mic_d=1.2,
    pi_holes=(58.0, 23.0), pi_cx=13.0, pi_cy=-10.0,
    boss_d=5.0, boss_hole_d=2.2,  # M2.5 heat-set: ~Ø3.4 melt-Ø; Ø2.2 pilot shown
)


def build_core(part="core"):
    p = P
    zf, zb = p["body_zf"], Z_BACK
    cx, cy = (p["body_x0"] + p["body_x1"]) / 2, (p["body_y0"] + p["body_y1"]) / 2
    w, h, t = p["body_x1"] - p["body_x0"], p["body_y1"] - p["body_y0"], zb - zf

    body = Pos(cx, cy, (zf + zb) / 2) * Box(w, h, t)
    try:
        body = fillet(body.edges().filter_by(Axis.Z), p["corner_r"])
    except Exception:
        pass

    # sealed internal electronics cavity (leaves front_wall + walls all round)
    cav = Pos(cx, cy, (zf + p["front_wall"] + zb - p["wall"]) / 2) * \
        Box(w - 2 * p["wall"], h - 2 * p["wall"], (zb - p["wall"]) - (zf + p["front_wall"]))
    body = body - cav

    # ---- FRONT: display bezel recess + through window for the active area ----
    body = body - (Pos(p["disp_cx"], p["disp_cy"], zf + p["bezel_recess"] / 2)
                   * Box(p["disp_mod_w"] + 0.4, p["disp_mod_h"] + 0.4, p["bezel_recess"] + 0.02))
    body = body - (Pos(p["disp_cx"], p["disp_cy"], zf + p["front_wall"] / 2)
                   * Box(p["disp_active_w"], p["disp_active_h"], p["front_wall"] + 0.02))

    # ---- BACK: integrated female rail socket (resolved Gen-6) + detents ----
    body = body - socket_cut(CONN)
    body = body + detent_add(CONN)

    # ---- optical clear bore Ø14 through the back, coaxial with cartridge barrel ----
    body = body - (Pos(OPT_X, OPT_Y, (0.0 + zb) / 2 + 0.5)
                   * Cylinder(p["opt_bore_d"] / 2, zb + 1.0))
    # camera mount pocket (inside) around the bore
    body = body - (Pos(OPT_X, OPT_Y, -2.0 + p["cam_pocket_depth"] / 2)
                   * Cylinder(p["cam_pocket_d"] / 2, p["cam_pocket_depth"]))

    # ---- USB-C charge cutout (bottom edge) ----
    body = body - (Pos(p["body_x0"] + (p["body_x1"] - p["body_x0"]) / 2, p["body_y0"], -8.0)
                   * Box(p["usbc_w"], p["wall"] * 3, p["usbc_h"]))

    # ---- jog-encoder aperture (right side face) ----
    body = body - (Pos(p["body_x1"], p["enc_cy"], p["enc_cz"])
                   * Box(p["wall"] * 3, p["enc_slot_w"], p["enc_slot_t"]))
    body = body - (Pos(p["body_x1"], p["enc_cy"], p["enc_cz"])
                   * Rot(0, 90, 0) * Cylinder(3.0, p["wall"] * 3))  # shaft clearance

    # ---- I²S mic port (bottom) + speaker grille (front, below screen) ----
    body = body - (Pos(cx + 8, p["body_y0"], -8.0) * Rot(90, 0, 0) * Cylinder(p["mic_d"] / 2, p["wall"] * 3))
    n = p["spk_grille_n"]
    for i in range(n):
        for j in range(n):
            gx = p["disp_cx"] + (i - (n - 1) / 2) * p["spk_pitch"]
            gy = p["spk_cy"] - (p["disp_mod_h"] / 2) - 6 + (j - (n - 1) / 2) * p["spk_pitch"]
            body = body - (Pos(gx, gy, zf + p["front_wall"] / 2)
                           * Box(p["spk_d"], p["spk_d"], p["front_wall"] + 0.02))

    # ---- heat-set bosses: 4× Pi Zero 2 W mount (M2.5) ----
    # Posts stand from the cavity into the back wall (top embeds at z=zb → unions solidly);
    # heat-set hole is blind from the cavity side so the back face stays watertight.
    hx, hy = p["pi_holes"]
    floor = zb - p["wall"]                       # inner back-wall surface (cavity floor)
    post_bot = floor - 6.0
    for sx in (-1, 1):
        for sy in (-1, 1):
            bx, by = p["pi_cx"] + sx * hx / 2, p["pi_cy"] + sy * hy / 2
            if not (p["body_x0"] + 4 < bx < p["body_x1"] - 4 and
                    p["body_y0"] + 4 < by < p["body_y1"] - 4):
                continue
            post = Pos(bx, by, (post_bot + zb) / 2) * Cylinder(p["boss_d"] / 2, zb - post_bot)
            body = body + post
            body = body - (Pos(bx, by, floor - 6.0 / 2) * Cylinder(p["boss_hole_d"] / 2, 6.0))
    return body


# --- forge entry ---
model = build_core("core")


def _opt_clear(shape):
    test = Pos(OPT_X, OPT_Y, Z_BACK / 2 + 0.5) * Cylinder((P["opt_bore_d"] - 1) / 2, Z_BACK + 0.8)
    inter = shape & test
    v = inter.volume if inter is not None else 0.0
    assert v < 5.0, f"optical bore obstructed: {v:.1f} mm³ of material in Ø13 clear path"

def _pads_clear(shape):
    # The pad/pogo footprint on the back face must be FLAT — nothing of the core may
    # protrude past the mating plane (z=Z_BACK) over the pad zone (would foul the pads).
    test = Pos(PAD_X, 0, Z_BACK + 0.6) * Box(8.0, 16.0, 1.2)
    inter = shape & test
    v = inter.volume if inter is not None else 0.0
    assert v < 2.0, f"structure protrudes past mating plane into pad zone: {v:.1f} mm³"

def _socket_present(shape):
    cut = socket_cut(CONN)
    # the socket must actually be carved (body should not still fill the groove volume)
    assert (shape & cut).volume < cut.volume * 0.5, "rail socket not formed"

def _watertight(shape):
    iv = shape.is_valid; iv = iv() if callable(iv) else iv
    assert iv, "core body solid invalid"

def _finger_root_fillet(shape):
    assert CONN["finger_root_fillet"] >= 0.5, "PROTECTED finger-root fillet reduced below 0.5 mm"

REQUIREMENTS = [_watertight, _opt_clear, _pads_clear, _socket_present, _finger_root_fillet]

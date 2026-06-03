"""VARA showcase geometry — detailed, dimensionally-honest parts for the web teardown.

These are higher-detail VISUAL variants that realise the full intended design (back cover,
M2.5 screws, jog wheel, USB-C, glass, lens ring, LED ring) — consistent with the build plan.
The connector geometry is consumed from dovetail_lib (the frozen [STUDY]); the Phase-3
validated STLs in cad/core, cad/cartridge are untouched.

HONESTY: core/back-cover/cartridge/screws/wheel/rings/pogo = parts WE designed, exact dims.
Pi / display / battery / camera / EEPROM = representative bodies at REAL datasheet dimensions
(not fabricated by us, never a routed PCB).

Frame = connector datum (mm): core X[-9,35] Y[-44,20]; Z = -16 (front/screen) .. +4 (back/mating).
"""
import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "connector"))
from build123d import *
from forge.export import export_glb
from dovetail_lib import DEFAULTS, derived, socket_cut, detent_add, male_rails
from genparams import GENS

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "web", "assets", "models")
CONN = dict(DEFAULTS); CONN.update(GENS[6]); D = derived(CONN)

def save(shape, name, tol=0.05):
    if not hasattr(shape, "wrapped"):
        shape = Compound(children=list(shape))
    export_glb(shape, os.path.join(OUT, name + ".glb"), tolerance=tol, angular_tolerance=0.12)
    print("  ->", name + ".glb")

def chamf(s, sel, r):
    try: return chamfer(sel, r)
    except Exception: return s

def fil(s, sel, r):
    try: return fillet(sel, r)
    except Exception: return s

# device envelope
X0, X1, Y0, Y1 = -9.0, 35.0, -44.0, 20.0
CX, CY = (X0 + X1) / 2, (Y0 + Y1) / 2
WALL = 2.4
ZF = -16.0                      # front face
ZSPLIT = -3.0                   # front-housing / back-cover parting line
ZB = 4.0                        # back/mating plane
CR = 4.0                        # body corner radius
SCREWS = [(-3.5, -39.5), (29.5, -39.5), (-3.5, 15.5), (29.5, 15.5)]  # back-cover screw centres


# ───────────────────────── fasteners ─────────────────────────
def m25_shcs(length=7.0):
    """M2.5 socket-head cap screw, ISO 4762: head Ø4.5×2.5, hex socket 2.0AF, shank Ø2.5.
    Built head-up at z∈[0,2.5], shank down to z=-length."""
    head = Pos(0, 0, 1.25) * Cylinder(4.5 / 2, 2.5)
    head = fil(head, head.edges().filter_by(GeomType.CIRCLE).group_by(Axis.Z)[-1], 0.4)
    socket = Pos(0, 0, 2.5 - 0.6) * extrude(RegularPolygon(2.0 / 2, 6), amount=-1.6)
    shank = Pos(0, 0, -length / 2) * Cylinder(2.5 / 2, length)
    return (head + shank) - socket
save(m25_shcs(7.0), "screw", tol=0.04)


# ───────────────────────── core: front housing ─────────────────────────
def core_front():
    body = Pos(CX, CY, (ZF + ZSPLIT) / 2) * Box(X1 - X0, Y1 - Y0, ZSPLIT - ZF)
    body = fil(body, body.edges().filter_by(Axis.Z), CR)
    # hollow cavity, open at the +Z (back) parting line
    cav = Pos(CX, CY, (ZF + WALL + ZSPLIT) / 2 + 0.6) * \
        Box(X1 - X0 - 2 * WALL, Y1 - Y0 - 2 * WALL, (ZSPLIT - (ZF + 3.0)) + 4)
    body = body - cav
    # screen: glass seat recess on the front (Z=ZF), 33×39, 1.6 deep
    body = body - (Pos(13, 1, ZF + 0.8) * Box(33, 39, 1.6 + 0.02))
    body = chamf(body, body.edges().filter_by(Axis.Z).group_by(SortBy.LENGTH)[-1], 0.0)
    # USB-C recess + port (bottom edge, Y0)
    body = body - (Pos(13, Y0, -9) * Box(11, 5, 4))
    body = chamf(body, body.edges().group_by(Axis.Y)[0].filter_by(Axis.X), 0.6)
    # jog-wheel pocket (right side, X1)
    body = body - (Pos(X1 - 1.5, -26, -7) * Box(5, 13, 9))
    body = body - (Pos(X1, -26, -7) * Rot(0, 90, 0) * Cylinder(5.6, 6))
    # power button hole (right side, upper)
    body = body - (Pos(X1, 8, -7) * Rot(0, 90, 0) * Cylinder(1.8, 8))
    # speaker grille: ring of small holes on the front, below the screen
    for k in range(8):
        a = k / 8 * 2 * math.pi
        gx, gy = 13 + 6 * math.cos(a), -34 + 6 * math.sin(a)
        body = body - (Pos(gx, gy, ZF + 1.5) * Cylinder(0.6, 4))
    body = body - (Pos(13, -34, ZF + 1.5) * Cylinder(0.6, 4))
    # mic pinhole (bottom)
    body = body - (Pos(22, Y0, -9) * Rot(90, 0, 0) * Cylinder(0.5, 6))
    # internal screw bosses (receive the 4 back-cover screws)
    for sx, sy in SCREWS:
        body = body + Pos(sx, sy, ZSPLIT - 6) * Cylinder(3.4, 12)
        body = body - (Pos(sx, sy, ZSPLIT - 3) * Cylinder(1.05, 8))   # pilot for heat-set/thread
    return body
save(core_front(), "core_front", tol=0.04)


# ───────────────────────── core: back cover (with the socket) ─────────────────────────
def core_back():
    cov = Pos(CX, CY, (ZSPLIT + ZB) / 2) * Box(X1 - X0, Y1 - Y0, ZB - ZSPLIT)
    cov = fil(cov, cov.edges().filter_by(Axis.Z), CR)
    cov = cov - socket_cut(CONN) + detent_add(CONN)              # integrated female rail socket
    cov = cov - (Pos(15, 0, 1) * Cylinder(14 / 2, 9))            # optical bore Ø14
    # 4 screw counterbores (head pocket Ø4.8×2.6 from +Z) + clearance through
    for sx, sy in SCREWS:
        cov = cov - (Pos(sx, sy, ZB - 1.3) * Cylinder(4.8 / 2, 2.8))
        cov = cov - (Pos(sx, sy, 0) * Cylinder(2.8 / 2, 12))
    # debossed "VARA" wordmark on the back face
    try:
        txt = Pos(13, 17, ZB - 0.3) * extrude(Text("VARA", 4.0, font_style=FontStyle.BOLD), amount=-0.6)
        cov = cov - txt
    except Exception: pass
    return cov
save(core_back(), "core_back", tol=0.04)


# ───────────────────────── screen glass ─────────────────────────
def glass():
    g = Pos(13, 1, ZF + 0.8) * Box(32.6, 38.6, 1.5)
    g = fil(g, g.edges().filter_by(Axis.Z), 1.2)
    return g
save(glass(), "glass", tol=0.03)


# ───────────────────────── jog wheel ─────────────────────────
def wheel():
    w = Pos(X1 + 0.5, -26, -7) * Rot(0, 90, 0) * Cylinder(5.4, 4.5)
    w = chamf(w, w.edges().filter_by(GeomType.CIRCLE), 0.5)
    return w
save(wheel(), "wheel", tol=0.03)

def button():
    b = Pos(X1 + 0.4, 8, -7) * Rot(0, 90, 0) * Cylinder(1.7, 1.6)
    return b
save(button(), "button", tol=0.04)


# ───────────────────────── cartridge (detailed v2) ─────────────────────────
def cartridge():
    h, off = CONN["engage_depth"], CONN["rail_offset"]
    z0, z1 = h, h + 3.0
    body = male_rails(CONN)
    plate = Pos(13, 0, (z0 + z1) / 2) * Box(26, 2 * 17.8, 3.0)
    plate = fil(plate, plate.edges().filter_by(Axis.Z), 2.5)
    body = body + plate
    for s in (+1, -1):
        body = body + Pos(13, s * off, h) * Box(26, 2 * D["floor_half"], 1.2)
    # barrel + outer flange (the lens housing), bore = optical path
    body = body + Pos(15, 0, z1 + 6) * Cylinder(6.0, 12)
    body = body + Pos(15, 0, z1 + 1.2) * Cylinder(8.2, 2.4)          # base flange
    body = body - Pos(15, 0, z1 + 7) * Cylinder(4.0, 16)            # through bore
    body = chamf(body, body.edges().filter_by(GeomType.CIRCLE).group_by(Axis.Z)[-1], 0.6)
    return body
save(cartridge(), "cartridge", tol=0.035)

def lensring():
    """Knurled retaining ring at the barrel mouth (knurl applied as a texture in the render)."""
    z = CONN["engage_depth"] + 3.0 + 12
    r = Pos(15, 0, z) * (Cylinder(6.6, 2.2) - Cylinder(4.2, 3))
    return r
save(lensring(), "lensring", tol=0.03)

def ledring():
    """6 LEDs on a thin ring PCB around the barrel base (optional ring light)."""
    z = CONN["engage_depth"] + 3.0 + 2.6
    ring = Pos(15, 0, z) * (Cylinder(8.0, 0.8) - Cylinder(6.4, 1))
    leds = None
    for k in range(6):
        a = k / 6 * 2 * math.pi
        led = Pos(15 + 7.2 * math.cos(a), 7.2 * math.sin(a), z + 0.6) * Box(1.6, 1.5, 0.7)
        leds = led if leds is None else leds + led
    return Compound(children=[ring, leds])
save(ledring(), "ledring", tol=0.05)


# ───────────────────────── internals (representative, REAL dims) ─────────────────────────
def pi():
    """Raspberry Pi Zero 2 W — 65×30×1.0 mm, holes Ø2.75 @ 58×23, header 2×20, SoC, cans."""
    bz = -6
    pcb = Pos(13, -6, bz) * Box(30, 65, 1.0)                        # mounted vertically (Y long)
    for sx in (-1, 1):
        for sy in (-1, 1):
            pcb = pcb - (Pos(13 + sx * 23 / 2, -6 + sy * 58 / 2, bz) * Cylinder(2.75 / 2, 3))
    hdr = Pos(13, -6 + 58 / 2 - 3.5, bz + 0.5 + 4.2) * Box(5.08, 50.8, 8.5)   # 40-pin header
    soc = Pos(13, -6, bz - 0.5 - 0.6) * Box(12, 12, 1.2)            # SoC (under side)
    wifi = Pos(13, -6 - 20, bz + 0.5 + 0.6) * Box(11, 12, 1.2)      # WiFi module can
    hdmi = Pos(13 - 15 + 3.5, -6 + 12, bz + 0.5 + 1.5) * Box(7.5, 3.2, 3)
    usb = Pos(13 - 15 + 3.5, -6 - 2, bz + 0.5 + 1.3) * Box(7.5, 2.6, 2.6)
    return Compound(children=[pcb, hdr, soc, wifi, hdmi, usb])
save(pi(), "pi", tol=0.05)

def display():
    """1.69\" module: 30.4×36.6 glass, 1.5 mm, + FPC tail + driver lump."""
    g = Pos(13, 2, -13.6) * Box(30.4, 36.6, 1.5)
    fpc = Pos(13, 2 - 18.3 - 4, -13.0) * Box(12, 8, 0.3)
    drv = Pos(13, 2 - 18.3 - 4, -13.0) * Box(8, 4, 1.0)
    return Compound(children=[g, fpc, drv])
save(display(), "display", tol=0.05)

def battery():
    cell = Pos(13, -26, -6) * Box(34, 50, 6)
    cell = fil(cell, cell.edges().filter_by(Axis.Z), 1.5)
    tab = Pos(13, -26 + 25 + 1.5, -6) * Box(8, 3, 1)
    return Compound(children=[cell, tab])
save(battery(), "battery", tol=0.05)

def camera():
    """RPi camera v2-ish: 25×24 board + 8.5×8.5×5 lens housing + lens, + CSI ribbon stub."""
    board = Pos(15, 0, -2) * Box(25, 24, 1.0)
    hous = Pos(15, 0, 0.4) * Box(8.5, 8.5, 4.5)
    lens = Pos(15, 0, 3.0) * Cylinder(3.6, 2.2)
    csi = Pos(15, -16, -2) * Box(6, 12, 0.4)
    return Compound(children=[board, hous, lens, csi])
save(camera(), "camera", tol=0.04)

def pogo():
    """6 pogo pins in a small connector housing (the contacts we designed)."""
    hous = Pos(6, 0, 5.0) * Box(4.5, 17, 3.2)
    hous = hous - (Pos(6, 0, 5.0) * Box(2.5, 15, 4))
    pins = [hous]
    for i in range(6):
        y = -6.35 + i * 2.54
        pins.append(Pos(6, y, 5.2) * Cylinder(0.55, 3.4) + Pos(6, y, 6.9) * Sphere(0.55))
    return Compound(children=pins)
save(pogo(), "pogo", tol=0.06)

def eeprom():
    chip = Pos(22, 0, 4.7) * Box(2.9, 2.8, 1.1)
    return chip
save(eeprom(), "eeprom", tol=0.06)

print("done.")

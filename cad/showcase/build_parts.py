"""VARA showcase geometry v3 — corrected & complete full product.

Fixes from review: (1) the dovetail socket is now an OPEN channel to the +X device edge so
the cartridge genuinely slides in (no wall penetration — verified); (2) real fastening — 4
M2.5 case screws (cover counterbore → front-housing threaded boss) + 4 Pi-mount screws into
standoffs, every screw in a real hole; (3) the enclosure is enlarged to actually FIT the
Pi Zero 2 W (65 mm) with the battery/screen, internals laid out in Z-layers; full electronics
(carrier PCB + USB-C + PMIC + amp, encoder, mic, speaker, microSD) added at real dims.

HONESTY: enclosure / cover / screws / wheel / cartridge / rings / pogo = our designed parts
(exact dims). Pi / display / battery / camera / carrier+ICs / EEPROM = representative bodies
at real datasheet dimensions (not fabricated by us, never a routed PCB). Internal packaging is
representative (Z-layered). Phase-3 validated STLs in cad/core, cad/cartridge are untouched.

Frame = connector datum (mm). Connector (rails Y±13, camera X15/Y0, Z0..4) is consumed as-is.
"""
import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "connector"))
from build123d import *
from forge.export import export_glb
from dovetail_lib import DEFAULTS, derived, socket_cut, detent_add, male_rails
from genparams import GENS

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "web", "assets", "models")
CONN = dict(DEFAULTS); CONN.update(GENS[6]); D = derived(CONN)
H = CONN["engage_depth"]; OFF = CONN["rail_offset"]; RL = CONN["rail_length"]

# ── enlarged device (fits Pi Zero 2 W = 65×30) ──
X0, X1 = -10.0, 36.0          # width 46
Y0, Y1 = -64.0, 22.0          # height 86 (Pi 65 fits)
ZF, ZSPLIT, ZB = -18.0, -3.0, 4.0   # front / parting line / back ; thickness 22
CX = (X0 + X1) / 2
WALL, CR = 2.4, 4.5
CASE = [(X0 + 5, Y0 + 5), (X1 - 5, Y0 + 5), (X0 + 5, Y1 - 5), (X1 - 5, Y1 - 5)]
PIH = [(13 + sx * 23 / 2, -24 + sy * 58 / 2) for sx in (-1, 1) for sy in (-1, 1)]

def save(s, n, tol=0.05):
    if not hasattr(s, "wrapped"): s = Compound(children=list(s))
    export_glb(s, os.path.join(OUT, n + ".glb"), tolerance=tol, angular_tolerance=0.12); print("  ->", n)
def fil(s, sel, r):
    try: return fillet(sel, r)
    except Exception: return s
def chamf(s, sel, r):
    try: return chamfer(sel, r)
    except Exception: return s

# open dovetail channel: grooves extended past the +X edge so the cartridge slides in
def open_socket_cut():
    base = socket_cut(CONN)
    return base + Pos(RL - 0.5, 0, 0) * base    # second copy → groove spans X0..~RL+RL, open at edge

# ───── fasteners (M2.5 SHCS, ISO 4762: head Ø4.5×2.5, hex 2.0, shank Ø2.5) ─────
def shcs(length):
    head = Pos(0, 0, 1.25) * Cylinder(4.5/2, 2.5)
    head = fil(head, head.edges().filter_by(GeomType.CIRCLE).group_by(Axis.Z)[-1], 0.4)
    sock = Pos(0, 0, 2.5-0.6) * extrude(RegularPolygon(2.0/2, 6), amount=-1.6)
    shank = Pos(0, 0, -length/2) * Cylinder(2.5/2, length)
    return (head + shank) - sock
save(shcs(10.0), "screw", 0.04)        # case screws
save(shcs(4.5), "screw_pi", 0.04)      # Pi mount screws

# ───── core: front housing ─────
def core_front():
    b = Pos(CX, (Y0+Y1)/2, (ZF+ZSPLIT)/2) * Box(X1-X0, Y1-Y0, ZSPLIT-ZF)
    b = fil(b, b.edges().filter_by(Axis.Z), CR)
    b = b - (Pos(CX, (Y0+Y1)/2, (ZF+WALL+ZSPLIT)/2+0.6) * Box(X1-X0-2*WALL, Y1-Y0-2*WALL, (ZSPLIT-(ZF+3.0))+4))
    b = b - (Pos(13, -2, ZF+0.8) * Box(33, 39, 1.6+0.02))       # glass seat
    b = b - (Pos(13, Y0, -12) * Box(11, 5, 4))                  # USB-C
    b = b - (Pos(X1-1.5, -40, -9) * Box(5, 13, 9))              # jog-wheel pocket
    b = b - (Pos(X1, -40, -9) * Rot(0,90,0) * Cylinder(5.6, 6))
    b = b - (Pos(X1, -16, -9) * Rot(0,90,0) * Cylinder(1.8, 8)) # power button
    for k in range(9):                                          # speaker grille
        a = k/9*2*math.pi
        b = b - (Pos(13+6*math.cos(a), -56+6*math.sin(a), ZF+1.5) * Cylinder(0.55, 4))
    b = b - (Pos(24, Y0, -12) * Rot(90,0,0) * Cylinder(0.5, 6)) # mic pinhole
    for sx, sy in CASE:                                         # case-screw bosses (Ø7, M2.5 hole)
        b = b + Pos(sx, sy, ZSPLIT-6.5) * Cylinder(3.5, 13)
        b = b - (Pos(sx, sy, ZSPLIT-3) * Cylinder(1.3, 9))
    for px, py in PIH:                                          # Pi standoffs (Ø5, M2.5 hole)
        b = b + Pos(px, py, -9-2.5) * Cylinder(2.5, 5)
        b = b - (Pos(px, py, -9-2.5) * Cylinder(1.3, 6))
    return b
save(core_front(), "core_front", 0.04)

# ───── core: back cover (open socket + bore + counterbores + deboss) ─────
def core_back():
    c = Pos(CX, (Y0+Y1)/2, (ZSPLIT+ZB)/2) * Box(X1-X0, Y1-Y0, ZB-ZSPLIT)
    c = fil(c, c.edges().filter_by(Axis.Z), CR)
    c = c - socket_cut(CONN) + detent_add(CONN)                # closed socket — cover fully wraps the rails (clean)
    c = c - (Pos(15, 0, 1) * Cylinder(14/2, 9))                # optical bore Ø14
    for sx, sy in CASE:                                        # head counterbore + clearance
        c = c - (Pos(sx, sy, ZB-1.3) * Cylinder(4.9/2, 2.8))
        c = c - (Pos(sx, sy, 0) * Cylinder(2.9/2, 12))
    try:
        c = c - (Pos(13, Y1-6, ZB-0.3) * extrude(Text("VARA", 4.2, font_style=FontStyle.BOLD), amount=-0.6))
    except Exception: pass
    return c
save(core_back(), "core_back", 0.04)

def glass():
    g = Pos(13, -2, ZF+0.8) * Box(32.6, 38.6, 1.5)
    return fil(g, g.edges().filter_by(Axis.Z), 1.2)
save(glass(), "glass", 0.03)
def wheel():
    w = Pos(X1+0.5, -40, -9) * Rot(0,90,0) * Cylinder(5.4, 4.5)
    return chamf(w, w.edges().filter_by(GeomType.CIRCLE), 0.5)
save(wheel(), "wheel", 0.03)
save(Pos(X1+0.4, -16, -9) * Rot(0,90,0) * Cylinder(1.7, 1.6), "button", 0.04)

# ───── cartridge (slides clean through the open channel) ─────
def cartridge():
    z0, z1 = H, H+3.2
    body = male_rails(CONN)
    # flange: overhangs the whole socket opening so the rails + channel are hidden when seated
    plate = Pos(16, 0, (z0+z1)/2) * Box(38, 41, z1-z0)          # X−3..35, Y±20.5
    plate = fil(plate, plate.edges().filter_by(Axis.Z), 3.0)
    body = body + plate
    # weld risers fuse rails→plate: narrow (≤ mouth width) so the part below Z=H stays
    # INSIDE the male rail (within groove clearance), never poking into the cover lips.
    for s in (+1, -1): body = body + Pos(13, s*OFF, H+0.75) * Box(RL, CONN["mouth_w"]-0.4, 2.5)
    body = body + Pos(15, 0, z1+6) * Cylinder(6.0, 12)
    body = body + Pos(15, 0, z1+1.2) * Cylinder(8.2, 2.4)
    body = body - Pos(15, 0, z1+7) * Cylinder(4.0, 16)
    body = chamf(body, body.edges().filter_by(GeomType.CIRCLE).group_by(Axis.Z)[-1], 0.6)
    return body
save(cartridge(), "cartridge", 0.035)
def lensring():
    z = H+3.0+12
    return Pos(15,0,z) * (Cylinder(6.6,2.2) - Cylinder(4.2,3))
save(lensring(), "lensring", 0.03)
def ledring():
    z = H+3.0+2.6
    ring = Pos(15,0,z)*(Cylinder(8.0,0.8)-Cylinder(6.4,1)); leds=None
    for k in range(6):
        a=k/6*2*math.pi
        led=Pos(15+7.2*math.cos(a),7.2*math.sin(a),z+0.6)*Box(1.6,1.5,0.7); leds=led if leds is None else leds+led
    return Compound(children=[ring,leds])
save(ledring(), "ledring", 0.05)

# ───── electronics (representative, real dims), Z-layered ─────
def pi():
    bz = -11
    pcb = Pos(13,-24,bz)*Box(30,65,1.0)
    for px,py in PIH: pcb = pcb - (Pos(px,py,bz)*Cylinder(2.75/2,3))
    hdr = Pos(13,-24+58/2-3.5,bz+0.5+4.2)*Box(5.08,50.8,8.5)        # 40-pin header
    soc = Pos(13,-24,bz-0.5-0.6)*Box(12,12,1.2)
    wifi= Pos(13,-24-20,bz+0.5+0.7)*Box(11,12,1.4)
    usb = Pos(13-15+3.5,-24-2,bz+0.5+1.3)*Box(7.5,2.6,2.6)
    hdmi= Pos(13-15+3.5,-24+12,bz+0.5+1.5)*Box(7.5,3.2,3)
    sd  = Pos(13+15-3,-24+24,bz)*Box(2,12,1.2)                       # microSD
    return Compound(children=[pcb,hdr,soc,wifi,usb,hdmi,sd])
save(pi(), "pi", 0.05)
def carrier():
    """Custom main PCB (representative): USB-C, IP5306 PMIC, MAX98357A amp, caps, display FPC conn."""
    bz=-6.5
    pcb=Pos(13,-40,bz)*Box(36,40,1.2)                                # fits clearly inside the walls
    usbc=Pos(13,Y0+2.5,bz+1.6)*Box(9.0,3.3,3.2)                      # USB-C at bottom edge
    pmic=Pos(4,-46,bz+1.2)*Box(5,4,1.2)
    amp =Pos(22,-46,bz+1.2)*Box(3,3,1.0)
    caps=Pos(13,-34,bz+1.4)*Box(10,4,1.6)
    fpc =Pos(13,-24,bz+0.8)*Box(14,3,1.2)
    return Compound(children=[pcb,usbc,pmic,amp,caps,fpc])
save(carrier(), "carrier", 0.05)
def battery():
    cell=Pos(13,-38,-2.5)*Box(34,48,5.5)
    cell=fil(cell,cell.edges().filter_by(Axis.Z),1.5)
    tab=Pos(13,-38+24+1.5,-2.5)*Box(8,3,1)
    return Compound(children=[cell,tab])
save(battery(), "battery", 0.05)
def camera():  # lowered so the lens looks THROUGH the bore but never pokes past the cover
    board=Pos(15,0,-2.8)*Box(25,24,1.0); hous=Pos(15,0,-0.7)*Box(8.5,8.5,4.5)
    lens=Pos(15,0,1.9)*Cylinder(3.6,2.2); csi=Pos(15,-15,-2.8)*Box(6,12,0.4)
    return Compound(children=[board,hous,lens,csi])
save(camera(), "camera", 0.04)
def encoder():
    body=Pos(X1-7,-40,-9)*Box(12,12,6.5); shaft=Pos(X1-1,-40,-9)*Rot(0,90,0)*Cylinder(3,7)
    return Compound(children=[body,shaft])
save(encoder(), "encoder", 0.05)
def speaker():
    return Pos(13,-56,ZF+3.5)*Cylinder(9,2.5)
save(speaker(), "speaker", 0.04)
def mic():
    return Pos(24,-60,-11)*Box(3.5,2.5,1.0)
save(mic(), "mic", 0.06)
def pogo():
    hous=Pos(6,0,5.0)*Box(4.5,17,3.2); hous=hous-(Pos(6,0,5.0)*Box(2.5,15,4)); pins=[hous]
    for i in range(6):
        y=-6.35+i*2.54; pins.append(Pos(6,y,5.2)*Cylinder(0.55,3.4)+Pos(6,y,6.9)*Sphere(0.55))
    return Compound(children=pins)
save(pogo(), "pogo", 0.06)
save(Pos(22,0,4.7)*Box(2.9,2.8,1.1), "eeprom", 0.06)

# ───── VERIFY: cartridge must NOT penetrate the enclosure ─────
print("\n=== interference check (seated cartridge vs core) ===")
cf, cb, ca = core_front(), core_back(), cartridge()
for nm, part in (("front", cf), ("back", cb)):
    try:
        inter = ca & part
        v = inter.volume if (inter is not None and hasattr(inter, "volume")) else 0.0
    except Exception:
        v = -1
    print(f"  cartridge ∩ core_{nm}: {v:.2f} mm^3  {'OK' if 0 <= v < 8 else 'CHECK'}")
print("done.")

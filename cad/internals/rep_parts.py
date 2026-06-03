"""Representative internal components for the showcase's full-product breakdown.

HONESTY: every part here EXCEPT the pogo pins is a DIMENSIONAL STAND-IN for an off-the-shelf
component — real bounding dimensions, simplified body, NOT fabricated by us and NOT a routed
PCB. The pogo pins are the contacts we actually designed (connector-spec v0.2). Built in the
connector/part frame (mm) at each component's real internal location, so they load in place.
"""
import os, sys
from build123d import *
from forge.export import export_glb

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "web", "assets", "models")
os.makedirs(OUT, exist_ok=True)

def save(shape, name, tol=0.04):
    if not hasattr(shape, "wrapped"):       # ShapeList → wrap as a Compound
        shape = Compound(children=list(shape))
    p = os.path.join(OUT, name + ".glb")
    export_glb(shape, p, tolerance=tol, angular_tolerance=0.18)
    print("  ->", name + ".glb")

# --- core internals (representative unless noted) ---
# Pi Zero 2 W: 65x30 mm board, mounted vertically (Y) inside the cavity.
pi = Pos(13, -6, -6) * Box(30, 60, 3.2)
pi += Pos(13, 18, -4.2) * Box(16, 5, 2)        # 40-pin header stub
save(pi, "pi")

# 1.69" display: board behind the front window; the screen face gets a REAL frame in JS.
disp = Pos(13, 2, -13.6) * Box(31, 38, 2.0)
save(disp, "display")

# Li-po 1500 mAh pouch.
batt = Pos(13, -26, -6) * Box(34, 50, 6)
save(batt, "battery")

# Camera module + lens + a short CSI ribbon (representative).
cam = Pos(15, 0, -1) * Box(25, 24, 4)
cam += Pos(15, 0, 1.6) * Cylinder(4.2, 3.5)                       # lens stack
cam += Pos(15, -16, -1) * Box(6, 12, 0.5)                         # CSI ribbon stub
save(cam, "camera")

# Pogo pins — DESIGNED (real), the cartridge contacts. 6 @ 2.54 mm pitch at X=6, Z mating.
pin_list = []
for i in range(6):
    y = -6.35 + i * 2.54
    pin = Pos(6, y, 5.2) * Cylinder(0.6, 3.2) + Pos(6, y, 6.7) * Sphere(0.6)  # body + crown
    pin_list.append(pin)
save(Compound(children=pin_list), "pogo", tol=0.12)

# --- cartridge internals (representative) ---
# Macro-lens optics inside the barrel (two elements).
optics = Pos(15, 0, 9) * Cylinder(5.6, 1.6)
optics += Pos(15, 0, 13) * Cylinder(5.2, 1.4)
save(optics, "optics")

# ID EEPROM (SOT-23-ish chip) in the underside pocket.
ee = Pos(22, 0, 4.7) * Box(3.0, 4.0, 1.0)
save(ee, "eeprom")

print("done.")

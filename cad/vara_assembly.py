"""VARA core + hero vision cartridge — assembled (Phase 3).

Both parts live in the shared connector datum frame, so they mate directly. The cartridge
is shown lifted +Z (semi-exploded) so the rail mate reads clearly. Quiet-Utility palette:
stone core, amber cartridge.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "core"))
sys.path.insert(0, os.path.join(HERE, "cartridge"))
from build123d import *
import core_body, vision_cartridge

core = core_body.build_core()
cart = vision_cartridge.build_cartridge()

core.color = Color(0.62, 0.60, 0.55)     # stone
cart.color = Color(0.85, 0.55, 0.18)     # amber

model = Compound(children=[core, Pos(0, 0, 8.0) * cart])

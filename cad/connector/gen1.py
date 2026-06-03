"""Generation 1 driver — see docs/dovetail-study.md and genparams.py for the reasoning."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dovetail_lib import build_dovetail, requirements_for, DEFAULTS
from genparams import GENS

GEN = 1
PARAMS = dict(DEFAULTS); PARAMS.update(GENS[GEN])
model = build_dovetail(PARAMS, "both")
REQUIREMENTS = requirements_for(PARAMS)

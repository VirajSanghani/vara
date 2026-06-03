"""VARA dovetail — FIRST-ORDER ANALYTICAL ESTIMATES (alignment + detent stress).

  ⚠️  THESE ARE HAND-CALCULATIONS, NOT FEA. No FEM tool is available in this environment
      (see docs/tool-capabilities.md). Material constants are ESTIMATES from typical
      CF-PA12 ranges, not a measured datasheet. Treat every number as order-of-magnitude
      design guidance, "validated-by-design," never tested. Marginal results are KEPT and
      reported — they drive the next generation, they are not silently discarded.

────────────────────────────────────────────────────────────────────────────────────────
MODEL 1 — Alignment (lateral Y error at a feature inside the rail bearing span)
────────────────────────────────────────────────────────────────────────────────────────
For a feature at axial position X_f WITHIN the bearing span [0, rail_length], the worst-case
lateral position error is bounded by clearance + dimensional tolerance, NOT amplified by
rail tilt: a straight rail constrained to ±c at both span ends keeps every interior point
within ±c (a linear offset between two end values each ≤ c stays ≤ c). Angular amplification
only occurs for features OUTSIDE the bearing span — so the design rule is "keep pads (X=6)
and optical axis (X=15) inside the bearing length."

    E_align = flank_clearance + (print_tol_male + print_tol_female)        [worst-case, mm]
            = flank_clearance + 2·print_tol           (assume both halves equal)
    Budget (set by pogo compression in connector-spec §3.1):  E_align ≤ 0.30 mm
    (RSS alternative, less conservative: flank_clearance + sqrt(2)·print_tol — also reported.)

────────────────────────────────────────────────────────────────────────────────────────
MODEL 2 — Detent snap (straight cantilever beam, point load at free end)
────────────────────────────────────────────────────────────────────────────────────────
Classic snap-fit straight-beam relations (e.g. Bayer/BASF snap-fit design guide):

    peak bending strain     ε_max = 3·t·δ / (2·L²)
    deflection force        F     = E·b·t³·δ / (4·L³)          (= 3EIδ/L³, I = b·t³/12)
    insertion force         F_ins = F·(μ + tanθ)/(1 − μ·tanθ)   (shallow lead ramp θ)
    retention force         F_ret = F·(μ + tanβ)/(1 − μ·tanβ)   (steep retain ramp β)

  t = beam thickness (bending dir), δ = deflection at snap, L = beam length, b = beam width.
  Gen1 has NO finger: the female mouth-lip wall itself flexes → L=engage_depth, t=wall_thk.
  Gen2+ use a dedicated finger → L=finger_len, t=finger_thk.
  There are TWO beams (one detent per rail) → reported insertion/retention forces are ×2.

  Safety factors:  SF_yield      = ε_yield / ε_max          (target ≥ 2 for cycle durability)
                   SF_interlayer = (k_interlayer·ε_yield)/ε_max   (if beam bends across layers)
"""
import math
from dovetail_lib import DEFAULTS, derived
from genparams import GENS

# ---- material / process ESTIMATES (CF-PA12 on FDM) — NOT a measured datasheet ----
E_FLEX_MPA      = 5000.0   # flexural modulus, est. (CF-PA12 spans ~3000–8000 MPa)
EPS_YIELD       = 0.025    # strain at yield/break, est. (CF fill embrittles vs neat PA12)
K_INTERLAYER    = 0.50     # interlayer (Z) knockdown, est. (~40–60% of in-plane)
MU              = 0.25     # PA12-CF self-friction coeff, est.
THETA_INSERT    = 30.0     # lead-in ramp angle, deg
BETA_RETAIN     = 60.0     # retention ramp angle, deg
N_BEAMS         = 2        # one detent per rail
OPTICAL_X       = 15.0     # connector-spec §3 (must stay inside bearing)
PAD_X           = 6.0
BUDGET_MM       = 0.30


def resolve(gen):
    p = dict(DEFAULTS); p.update(GENS[gen])
    return p


def alignment(p):
    tol = p["print_tol"]
    E_worst = p["flank_clearance"] + 2 * tol
    E_rss = p["flank_clearance"] + math.sqrt(2) * tol
    inside = (OPTICAL_X < p["rail_length"]) and (PAD_X < p["rail_length"])
    return dict(E_worst=E_worst, E_rss=E_rss, inside_bearing=inside,
                pass_worst=E_worst <= BUDGET_MM and inside)


def detent(p):
    if p["finger"]:
        L, t = p["finger_len"], p["finger_thk"]
    else:  # Gen1: the stiff mouth-lip wall flexes
        L, t = p["engage_depth"], p["wall_thk"]
    b = p["detent_w"]
    d = p["detent_depth"]
    eps = 3 * t * d / (2 * L ** 2)
    F = E_FLEX_MPA * b * t ** 3 * d / (4 * L ** 3)  # N, per beam
    ti, tb = math.tan(math.radians(THETA_INSERT)), math.tan(math.radians(BETA_RETAIN))
    F_ins = F * (MU + ti) / (1 - MU * ti) * N_BEAMS
    F_ret = F * (MU + tb) / (1 - MU * tb) * N_BEAMS
    return dict(L=L, t=t, eps=eps, eps_pct=eps * 100,
                SF_yield=EPS_YIELD / eps, SF_inter=K_INTERLAYER * EPS_YIELD / eps,
                F_ins=F_ins, F_ret=F_ret)


def verdict(al, de):
    ok_align = al["pass_worst"]
    ok_stress = de["SF_yield"] >= 2.0 and de["SF_inter"] >= 2.0
    if ok_align and ok_stress:
        return "PASS"
    tags = []
    if not ok_align: tags.append("align")
    if de["SF_yield"] < 2.0: tags.append("stress")
    elif de["SF_inter"] < 2.0: tags.append("interlayer")
    return "FAIL:" + "+".join(tags)


if __name__ == "__main__":
    print(f"{'gen':>3} {'c':>5} {'tol':>5} | {'E_w':>5} {'≤.30':>5} | "
          f"{'L':>4} {'t':>4} {'δ':>5} {'ε%':>6} {'SFy':>5} {'SFz':>5} "
          f"{'Fins':>6} {'Fret':>6} | verdict")
    print("-" * 92)
    for g in sorted(GENS):
        p = resolve(g); al = alignment(p); de = detent(p)
        print(f"{g:>3} {p['flank_clearance']:>5.2f} {p['print_tol']:>5.3f} | "
              f"{al['E_worst']:>5.2f} {'yes' if al['E_worst']<=BUDGET_MM else 'NO':>5} | "
              f"{de['L']:>4.0f} {de['t']:>4.1f} {p['detent_depth']:>5.2f} "
              f"{de['eps_pct']:>6.2f} {de['SF_yield']:>5.2f} {de['SF_inter']:>5.2f} "
              f"{de['F_ins']:>6.1f} {de['F_ret']:>6.1f} | {verdict(al, de)}")

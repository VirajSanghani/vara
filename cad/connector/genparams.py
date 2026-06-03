"""The six generations — each a parameter DELTA off DEFAULTS that fixes a SPECIFIC
problem the previous generation exposed. Reasoning lives in docs/dovetail-study.md.

`print_tol` = assumed per-part FDM dimensional tolerance (one-sided, mm) — an ESTIMATE,
not measured. Tightens at Gen3 when we declare a calibrated-printer requirement.
"""

GENS = {
    1: dict(  # baseline = connector-spec seed values
        print_tol=0.10,
    ),
    2: dict(  # fix: detent over-strains on the stiff lip wall → dedicated cantilever finger
        finger=True, finger_len=12.0, finger_thk=1.2,
        print_tol=0.10,
    ),
    3: dict(  # fix: alignment fails (clearance+tol > 0.3) → tighten clearance + declare print-tol req
        finger=True, finger_len=12.0, finger_thk=1.2,
        flank_clearance=0.15, print_tol=0.075,
    ),
    4: dict(  # fix: marginal fit binds + finger interlayer SF<2 → lower detent, ease insertion (lead-in/crown)
        finger=True, finger_len=12.0, finger_thk=1.2,
        flank_clearance=0.15, detent_depth=0.45, lead_in_chamfer=1.2, print_tol=0.075,
    ),
    5: dict(  # fix: need alignment MARGIN + interlayer SF≥2 under print orientation → thinner/longer finger, tighter c
        finger=True, finger_len=13.0, finger_thk=1.0,
        flank_clearance=0.12, detent_depth=0.45, lead_in_chamfer=1.2, print_tol=0.075,
    ),
    6: dict(  # resolved compromise: balance retention (2 fingers) ↔ strain ↔ alignment, longer bearing
        finger=True, finger_len=13.0, finger_thk=1.1,
        flank_clearance=0.13, detent_depth=0.50, lead_in_chamfer=1.2,
        rail_length=26.0, print_tol=0.075,
    ),
}

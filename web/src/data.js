// VARA showcase content — every "why" is pulled from the engineering docs.
// Numbers are first-order analytical estimates (validated-by-design, not hardware-tested).

// Feature callouts for the EXPLODE scene. pos = anchor in the CAD part frame (mm):
// core X[-9,35] Y[-44,20] Z[-16(front/screen)..+4(back/mating)]; cartridge above Z=4.
export const PARTS = {
  core: [
    { id: 'bezel', pos: [13, 6, -16], title: 'Display bezel — 1.69″ 240×280',
      what: 'Shows the viewfinder and the result caption.',
      why: 'The taller-than-square panel splits into live view + caption — that split IS the point-and-identify UX.' },
    { id: 'bore', pos: [15, 0, 4], title: 'Optical bore — Ø14, coaxial',
      what: 'The fixed core camera looks out through here.',
      why: 'Coaxial with the cartridge lens. The dovetail’s ±0.28 mm alignment budget governs THIS, not just the pads.' },
    { id: 'socket', pos: [13, 13, 3], title: 'Female rail socket (dual)',
      what: 'Receives and locates the cartridge.',
      why: 'Two rails flank the centre — a single central rail would collide with the pad array and the optical bore.' },
    { id: 'fillet', pos: [2.5, 13, 3], title: 'Snap-finger root fillet — functional',
      what: 'Roots the detent cantilever to the wall.',
      why: 'Beam theory understates the real root stress concentration, so this fillet keeps peak stress in check. Protected — not reduced for packaging.' },
    { id: 'usbc', pos: [13, -44, -8], title: 'USB-C + IP5306 PMIC',
      what: 'Charge in; one chip does charge + 5 V boost + power-path + button.',
      why: 'Battery area sets the lower body; runtime ≈ 3.5 h (estimate).' },
  ],
  cartridge: [
    { id: 'barrel', pos: [15, 0, 16], title: 'Macro-lens barrel — optics only',
      what: 'A swappable lens on the core’s perception; the bore is the optical path.',
      why: 'The camera+CSI stays in the core — CSI is far too fast for the 6-pin pogo. The cartridge changes the SENSE, not the sensor.' },
    { id: 'malerail', pos: [6, 13, 2], title: 'Male rail',
      what: 'Slides into the core and locks with a detent.',
      why: 'Resolved across 6 generations of optimization → see the Evolution scene.' },
    { id: 'pads', pos: [6, 0, 4.2], title: 'Pogo pads ×6 — the whole contract',
      what: 'V+, GND, I²C SDA/SCL, CD#, INT.',
      why: 'The entire cartridge interface in 6 low-speed contacts (connector-spec v0.2).' },
    { id: 'led', pos: [15, 8, 7], title: 'LED ring (optional)',
      what: 'Ring light around the lens.',
      why: 'Runs on the switched V+ rail, ≤150 mA — dimmed by PWM-ing V+ after the EEPROM ID is read.' },
  ],
};

// Full-product breakdown — internal components, exploded on the mating axis (part +Z).
// kind:'designed' = real geometry we authored; kind:'rep' = dimensional stand-in for an
// off-the-shelf part (NOT fabricated by us, NOT a routed PCB). pos = marker anchor (part mm),
// exZ = fully-exploded offset along the mating axis, mat = material key.
export const INTERNALS = [
  { id: 'display', model: 'display', pos: [13, 2, -14], exZ: -42, mat: 'screen', kind: 'rep',
    title: '1.69″ display — 240×280',
    what: 'Shows the live viewfinder and the result caption.',
    why: 'Representative body — a stand-in for the off-the-shelf panel. The frame on its face is a REAL Phase-5 render, not a mock-up.' },
  { id: 'pi', model: 'pi', pos: [13, 12, -6], exZ: -27, mat: 'pcb', kind: 'rep',
    title: 'Raspberry Pi Zero 2 W',
    what: 'The brain: capture → cloud vision → display + speak.',
    why: 'Representative body — the real module, not a PCB we laid out. KiCad here couldn’t route a board (Phase 4), so we never imply one.' },
  { id: 'battery', model: 'battery', pos: [13, -26, -6], exZ: -56, mat: 'cell', kind: 'rep',
    title: 'Li-po — 1500 mAh',
    what: 'Powers the device; runtime ≈ 3.5 h (estimate).',
    why: 'Representative pouch — a dimensional stand-in for an off-the-shelf cell.' },
  { id: 'camera', model: 'camera', pos: [15, 0, -1], exZ: -13, mat: 'black', kind: 'rep',
    title: 'Camera module + CSI',
    what: 'Fixed in the core; looks out the optical bore.',
    why: 'Representative module. Carried on the CSI ribbon (NOT the pogo) — CSI is far too fast for the 6-pin contract.' },
  { id: 'pogo', model: 'pogo', pos: [6, 0, 7], exZ: 14, mat: 'gold', kind: 'designed',
    title: 'Pogo pins ×6',
    what: 'Spring contacts carrying V+, GND, I²C SDA/SCL, CD#, INT.',
    why: 'DESIGNED by us — the real contract geometry (connector-spec v0.2), not a bought part.' },
  { id: 'optics', model: 'optics', pos: [15, 0, 11], exZ: 78, mat: 'glass', kind: 'rep',
    title: 'Macro-lens optics',
    what: 'Lens elements inside the cartridge barrel.',
    why: 'Representative — the barrel that holds and aligns them IS our designed geometry.' },
  { id: 'eeprom', model: 'eeprom', pos: [22, 0, 5], exZ: 62, mat: 'black', kind: 'rep',
    title: 'ID EEPROM @ 0x50',
    what: 'Tells the core which cartridge is mounted.',
    why: 'Representative chip; the ID scheme + pad layout are ours (connector-spec §4.1).' },
];

// FULL TEARDOWN — every component, grouped core-side / cart-side, fanned on the mating axis.
// exZ = explode offset (part +Z → world up). side = which way the leader label points.
// kind 'designed' = real geometry we authored; 'rep' = dimensional stand-in (off-the-shelf,
// not fabricated by us, never a routed PCB). anchor = a point on the part (part mm).
export const COMPONENTS = [
  // ---- core side ----
  { id: 'optics', model: 'optics', group: 'cart', mat: 'glass', kind: 'rep', exZ: 80, side: 1,
    anchor: [15, 0, 12], title: 'Macro-lens optics',
    what: 'Lens elements inside the cartridge barrel.',
    why: 'Representative — the barrel that holds and aligns them IS our designed geometry.' },
  { id: 'cartridge', model: 'cartridge', group: 'cart', mat: 'amber', kind: 'designed', exZ: 58, side: -1,
    anchor: [9, 13, 9], title: 'Vision cartridge',
    what: 'Re-aims perception — a macro lens on the core’s eye.',
    why: 'Optics only; the camera stays in the core (CSI is too fast for the 6-pin pogo). The male rail was resolved across 6 generations — see the Connector scene.' },
  { id: 'eeprom', model: 'eeprom', group: 'cart', mat: 'black', kind: 'rep', exZ: 44, side: 1,
    anchor: [22, 0, 5], title: 'ID EEPROM @ 0x50',
    what: 'Tells the core which cartridge is mounted.',
    why: 'Representative chip; the ID scheme + pad layout are ours (connector-spec §4.1).' },
  { id: 'pogo', model: 'pogo', group: 'core', mat: 'gold', kind: 'designed', exZ: 20, side: -1,
    anchor: [6, 4, 7], title: 'Pogo pins ×6',
    what: 'Spring contacts: V+, GND, I²C SDA/SCL, CD#, INT.',
    why: 'DESIGNED — the real contract geometry (connector-spec v0.2), not a bought part.' },
  { id: 'core', model: 'core', group: 'core', mat: 'stone', kind: 'designed', exZ: 0, side: 1,
    anchor: [24, -8, -6], title: 'Core body',
    what: 'Perceives — houses the camera, Pi, display, audio and power.',
    why: 'Camera coaxial to the cartridge lens (±0.28 mm budget); dual female rail sockets flank the centre; the snap-finger root fillet is functional. 44×64×20 mm — sized by the 35.6 mm rail span, not styled thin.' },
  { id: 'camera', model: 'camera', group: 'core', mat: 'black', kind: 'rep', exZ: -20, side: -1,
    anchor: [15, 6, 1], title: 'Camera + CSI',
    what: 'Fixed in the core; looks out the optical bore.',
    why: 'Representative module, on the CSI ribbon — NOT the pogo (CSI is far too fast for the 6-pin contract).' },
  { id: 'display', model: 'display', group: 'core', mat: 'screen', kind: 'rep', exZ: -40, side: 1,
    anchor: [13, 11, -14], title: '1.69″ display — 240×280',
    what: 'Live viewfinder + result caption.',
    why: 'Representative body. The frame on its face is a REAL Phase-5 render, not a mock-up.' },
  { id: 'pi', model: 'pi', group: 'core', mat: 'pcb', kind: 'rep', exZ: -58, side: -1,
    anchor: [13, 14, -6], title: 'Raspberry Pi Zero 2 W',
    what: 'The brain: capture → cloud vision → display + speak.',
    why: 'Representative body — the real module, not a PCB we laid out (KiCad couldn’t route; Phase 4). We never imply a board.' },
  { id: 'battery', model: 'battery', group: 'core', mat: 'cell', kind: 'rep', exZ: -74, side: -1,
    anchor: [13, -28, -6], title: 'Li-po — 1500 mAh',
    what: 'Powers the device; runtime ≈ 3.5 h (estimate).',
    why: 'Representative pouch — a dimensional stand-in for an off-the-shelf cell.' },
];

export const FORM_NOTE =
  'VARA is 44 × 64 × 20 mm — chunky by consequence, not by style: the 35.6 mm dovetail rail span ' +
  'plus the display set the size. An honest instrument, not a phone pretending to be thin.';

// CONNECTOR EVOLUTION — the 6 generations with real analytical numbers (dovetail-study.md).
export const GENS = [
  { g: 1, verdict: 'FAIL', tag: 'baseline',
    change: 'Spec seed values, detent flexes the stiff lip wall.',
    metrics: { 'ε peak': '13.5 %', 'SF yield': '0.09', 'insert': '1253 N', 'align': '0.40 mm' },
    note: 'Catastrophic: ~5× over yield strain and 1253 N to insert — it would shatter before assembling. Alignment also blows the ±0.30 mm budget.' },
  { g: 2, verdict: 'FAIL', tag: 'cantilever finger',
    change: 'Give the detent its own dedicated cantilever snap-finger.',
    metrics: { 'ε peak': '0.75 %', 'SF yield': '3.33', 'SF interlayer': '1.67', 'align': '0.40 mm' },
    note: 'In-plane stress fixed (SF 3.3). But the finger fails the FDM interlayer case (1.67 < 2), and alignment is still 0.40.' },
  { g: 3, verdict: 'FAIL', tag: 'tighten clearance',
    change: 'Clearance 0.20→0.15 mm + declare a ±0.075 mm print-tolerance requirement.',
    metrics: { 'ε peak': '0.75 %', 'SF interlayer': '1.67', 'align': '0.30 mm', 'margin': 'zero' },
    note: 'Alignment lands EXACTLY on the budget — marginal, kept as a finding. Interlayer still fails.' },
  { g: 4, verdict: 'PASS', tag: 'lower detent',
    change: 'Detent depth 0.60→0.45 mm; grow the lead-in.',
    metrics: { 'ε peak': '0.56 %', 'SF interlayer': '2.22', 'insert': '4.4 N', 'retention': '15.7 N' },
    note: 'First PASS — interlayer clears 2.0. But alignment margin is still zero.' },
  { g: 5, verdict: 'PASS', tag: 'buy margin',
    change: 'Finger 12×1.2→13×1.0 mm; clearance 0.15→0.12 mm.',
    metrics: { 'SF yield': '6.26', 'SF interlayer': '3.13', 'align': '0.27 mm', 'retention': '7.2 N' },
    note: 'Real alignment margin at last (0.27 < 0.30). Cost: the lock went soft — 7.2 N retention.' },
  { g: 6, verdict: 'RESOLVED', tag: 'resolved compromise',
    change: 'Finger t 1.0→1.1, detent 0.45→0.50, rail 24→26 mm.',
    metrics: { 'SF yield': '5.12', 'SF interlayer': '2.56', 'insert': '2.9 N', 'retention': '10.6 N', 'align': '0.28 mm' },
    note: 'Trade a little strain margin back for feel: easy 2.9 N insert, firm 10.6 N lock, both SFs ≥ 2, alignment 0.28 < 0.30. Resolved.' },
];

export const STORY = [
  { k: 'core perceives', t: 'The core is the eye.',
    d: 'Camera, compute (Pi Zero 2 W), display, audio, power — a complete perception instrument on its own.' },
  { k: 'cartridge = a lens on perception', t: 'A cartridge grants a new sense.',
    d: 'The hero vision cartridge is pure optics — a macro lens that nests over the core’s eye, like a microscope objective. Slide it on via the dovetail.' },
  { k: 'capture → identify → speak', t: 'Point and press.',
    d: 'Jog-press → capture → cloud vision identifies & explains → caption on screen + spoken aloud. No on-device VLM — it’s a cloud call (Phase 1).' },
];

// Phase-5 sample frames (real renders from the prototype's display layout).
export const FRAMES = [
  { src: 'assets/frames/sample_boot.png', cap: 'boot' },
  { src: 'assets/frames/sample_viewfinder.png', cap: 'capture — press to scan' },
  { src: 'assets/frames/sample_thinking.png', cap: 'identifying… (cloud call)' },
  { src: 'assets/frames/sample_result.png', cap: 'result — shown + spoken' },
  { src: 'assets/frames/sample_error_offline.png', cap: 'offline → clean error, no crash' },
];

export const HONESTY =
  'Numbers are first-order analytical estimates — validated-by-design, not hardware-tested. ' +
  'No printer or live hardware was in the loop.';

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

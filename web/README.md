# VARA showcase (web/)

The interactive exploded showcase — the wrapper that makes the whole build legible in ~60 s.
Static Three.js, **no build step**. It consumes the **real** project geometry and data:

- `assets/models/core.glb`, `cartridge.glb` — the Phase-3 printable parts (build123d → glTF).
- `assets/models/gen1…6.glb` — the Phase-2 dovetail evolution set.
- `assets/frames/*.png` — the Phase-5 prototype's real display renders.
- numbers in `src/data.js` come straight from `docs/dovetail-study.md` (analytical estimates).

## Three scenes
1. **Explode** — core ↔ cartridge separate; tappable markers give *what* each feature does
   **and why it's shaped that way** (rail span drove the form, the optical bore is coaxial,
   the finger-root fillet is functional, …).
2. **Connector** — step/play through the 6 generations, G1 (ε 13.5 %, 1253 N, FAIL) →
   G6 (SF 5.1, 2.9 N insert, 10.6 N retention, RESOLVED), numbers updating live.
3. **Identify** — the product story + the cartridge sliding on + the capture→identify→speak
   loop using the real Phase-5 frames.

## Run / deploy
It's plain static files — serve the folder over HTTP (ES modules need http, not `file://`):
```bash
cd web && python3 -m http.server 8000   # → http://localhost:8000
```
Deploy by uploading `web/` to any static host (GitHub Pages, Netlify, Cloudflare Pages, S3).
That URL is the single shareable link.

## Notes
- **Three.js r160 loads from the jsdelivr CDN** (pinned) via an import map — keeps the artifact
  light. For a fully offline/self-contained copy, vendor `three.module.js` + the four addons
  (`GLTFLoader`, `OrbitControls`, `CSS2DRenderer`, `RoomEnvironment`) and repoint the import map.
- **Perf:** meshes are already light (≤ ~95 KB each, no decimation needed); evolution GLBs and
  frames lazy-load on first entry to each scene; pixel ratio is capped (1.5× on mobile, 2× otherwise).
- **Graceful degradation:** a WebGL check shows a clean fallback message; layout reflows for mobile.
- **Honesty in the UI:** a persistent footer states the numbers are first-order analytical
  estimates — validated-by-design, not hardware-tested.

## Files
```
index.html        shell + import map + scene panels
src/styles.css    Quiet Utility theme (Fraunces + JetBrains Mono, stone/amber)
src/main.js       renderer, materials, the 3 scenes, lazy loading, camera moves
src/data.js       part callouts (what/why), gen metrics, story, honesty text
assets/           models/ (real glTF) · frames/ (real Phase-5 renders)
```

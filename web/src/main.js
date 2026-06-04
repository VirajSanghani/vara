import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { toCreasedNormals } from 'three/addons/utils/BufferGeometryUtils.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { SAOPass } from 'three/addons/postprocessing/SAOPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { PARTS_V3, SCREWS, SCREWS_PI, FORM_NOTE, GENS, STORY, FRAMES, HONESTY } from './data.js';

const $ = (s) => document.querySelector(s);
const isMobile = matchMedia('(max-width:780px)').matches;

try { const c = document.createElement('canvas'); if (!(c.getContext('webgl2') || c.getContext('webgl'))) throw 0; }
catch (e) { $('#nowebgl').classList.remove('hidden'); $('#loader').classList.add('gone'); throw new Error('no webgl'); }

$('#honesty').textContent = HONESTY; $('#formnote').textContent = FORM_NOTE;

// ---- renderer ----
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, isMobile ? 1.6 : 2));
renderer.setSize(innerWidth, innerHeight);
renderer.setClearColor(0x000000, 0);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.1;
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
$('#webgl').appendChild(renderer.domElement);

const labelRenderer = new CSS2DRenderer();
labelRenderer.setSize(innerWidth, innerHeight);
$('#labels').appendChild(labelRenderer.domElement);

const scene = new THREE.Scene();
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
scene.environmentIntensity = 0.72;

const camera = new THREE.PerspectiveCamera(36, innerWidth / innerHeight, 0.1, 6000);
camera.position.set(150, 110, 200);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true; controls.dampingFactor = 0.06; controls.enablePan = true;
controls.screenSpacePanning = true; controls.rotateSpeed = 0.62; controls.zoomSpeed = 0.85;
controls.minDistance = 42; controls.maxDistance = 820;
controls.minPolarAngle = 0.02; controls.maxPolarAngle = Math.PI * 0.985;   // allow viewing the underside

// ---- lighting ----
const key = new THREE.DirectionalLight(0xfff0db, 1.9); key.position.set(95, 155, 115); key.castShadow = true;
key.shadow.mapSize.set(2048, 2048); key.shadow.bias = -0.0004; key.shadow.normalBias = 0.7;
Object.assign(key.shadow.camera, { near: 20, far: 760, left: -150, right: 150, top: 200, bottom: -200 });
scene.add(key);
const rim = new THREE.DirectionalLight(0xaccde8, 1.1); rim.position.set(-115, 75, -135); scene.add(rim);
const under = new THREE.DirectionalLight(0xdfe6f0, 0.6); under.position.set(-30, -150, -40); scene.add(under); // lifts the underside
scene.add(new THREE.HemisphereLight(0xf2eee4, 0x45453d, 0.55));                                                // brighter ambient floor
const head = new THREE.DirectionalLight(0xffffff, 0.5); scene.add(head); scene.add(head.target);              // camera-following headlight

// ---- procedural textures ----
function noiseTex(rep, lo, hi) {
  const s = 256, c = document.createElement('canvas'); c.width = c.height = s;
  const x = c.getContext('2d'), d = x.createImageData(s, s);
  for (let i = 0; i < s * s; i++) { const v = lo + Math.floor(Math.random() * (hi - lo)); d.data[i*4]=d.data[i*4+1]=d.data[i*4+2]=v; d.data[i*4+3]=255; }
  x.putImageData(d, 0, 0); const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(rep, rep); return t;
}
function knurlNormal() {           // diamond-knurl height → normal map
  const s = 128, c = document.createElement('canvas'); c.width = c.height = s;
  const x = c.getContext('2d'), d = x.createImageData(s, s), f = Math.PI * 2 * 10 / s;
  const h = (i, j) => (Math.sin((i + j) * f) + Math.sin((i - j) * f));
  for (let j = 0; j < s; j++) for (let i = 0; i < s; i++) {
    const dx = h(i + 1, j) - h(i - 1, j), dy = h(i, j + 1) - h(i, j - 1);
    const nx = -dx * 0.5, ny = -dy * 0.5, nz = 1, l = Math.hypot(nx, ny, nz), o = (j * s + i) * 4;
    d.data[o] = (nx / l * 0.5 + 0.5) * 255; d.data[o+1] = (ny / l * 0.5 + 0.5) * 255; d.data[o+2] = (nz / l * 0.5 + 0.5) * 255; d.data[o+3] = 255;
  }
  x.putImageData(d, 0, 0); const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(6, 6); return t;
}
const speckle = noiseTex(7, 150, 210), knurl = knurlNormal();

// ---- materials ----
const nylon = (color) => new THREE.MeshStandardMaterial({ color, metalness: 0.05, roughness: 0.7, roughnessMap: speckle });
const MATS = {
  stone: nylon(0x78766e), amber: nylon(0xc6822f), evo: nylon(0x8d8a80),
  screen: new THREE.MeshStandardMaterial({ color: 0x0c0c10, metalness: 0.2, roughness: 0.42 }),
  pcb: new THREE.MeshStandardMaterial({ color: 0x1f3a2b, metalness: 0.15, roughness: 0.58 }),
  cell: new THREE.MeshStandardMaterial({ color: 0x929698, metalness: 0.6, roughness: 0.4 }),
  black: new THREE.MeshStandardMaterial({ color: 0x141416, metalness: 0.3, roughness: 0.48 }),
  gold: new THREE.MeshStandardMaterial({ color: 0xd7a23a, metalness: 0.9, roughness: 0.28 }),
  chip: new THREE.MeshStandardMaterial({ color: 0x17171a, metalness: 0.3, roughness: 0.45 }),
  metalS: new THREE.MeshStandardMaterial({ color: 0xc9c9cf, metalness: 1, roughness: 0.3 }),
  metalA: new THREE.MeshStandardMaterial({ color: 0x4c4c52, metalness: 0.92, roughness: 0.38, normalMap: knurl, normalScale: new THREE.Vector2(0.5, 0.5) }),
  glass: new THREE.MeshPhysicalMaterial({ color: 0x20242a, metalness: 0, roughness: 0.06, transmission: 0.86, thickness: 1.4, ior: 1.5, clearcoat: 1, clearcoatRoughness: 0.06, transparent: true }),
};

const loader = new GLTFLoader();
const load = (url) => new Promise((res, rej) => loader.load(url, (g) => res(g.scene), undefined, rej));
const CREASE = THREE.MathUtils.degToRad(34);
function applyMat(obj, mat) {
  obj.traverse((o) => {
    if (o.isMesh) {
      try { o.geometry = toCreasedNormals(o.geometry, CREASE); } catch (e) { o.geometry.computeVertexNormals?.(); }
      o.material = mat; o.castShadow = true; o.receiveShadow = true;
    }
  });
}

// ---- groups ----
const ZUP = -Math.PI / 2;
const device = new THREE.Group(); device.rotation.x = ZUP; scene.add(device);
const coreGroup = new THREE.Group(), cartGroup = new THREE.Group(); device.add(coreGroup, cartGroup);
let explodeT = 0, explodeTarget = 0, slideP = 0, slideTarget = 0, scene_ = 'explode';
const explodables = [], leaders = []; let ground;

function openCallout(p, el) {
  leaders.forEach((m) => m.el.classList.remove('active')); if (el) el.classList.add('active');
  const c = $('#callout'); c.classList.remove('hidden');
  const badge = p.kind === 'rep' ? '<span class="kind rep">representative</span>' : p.kind === 'designed' ? '<span class="kind des">designed</span>' : '';
  c.querySelector('h3').innerHTML = p.title + badge;
  c.querySelector('.what').textContent = p.what; c.querySelector('.why').textContent = p.why;
}
$('#calloutClose').onclick = () => { $('#callout').classList.add('hidden'); leaders.forEach((m) => m.el.classList.remove('active')); };

function addLeader(obj, comp) {
  const a = comp.anchor, lx = comp.side > 0 ? (isMobile ? 40 : 54) : (isMobile ? -34 : -44), lead = [lx, a[1], a[2]];
  const line = new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(...a), new THREE.Vector3(...lead)]),
    new THREE.LineBasicMaterial({ color: 0xd68a2e, transparent: true, opacity: 0.5 }));
  obj.add(line);
  const dotEl = document.createElement('div'); dotEl.className = 'leaddot';
  const dot = new CSS2DObject(dotEl); dot.position.set(...a); obj.add(dot);
  const el = document.createElement('div'); el.className = 'leadlabel';
  el.innerHTML = `<span class="ll-name">${comp.title}</span>` + (comp.kind ? `<span class="ll-kind ${comp.kind}">${comp.kind === 'rep' ? 'rep' : 'designed'}</span>` : '');
  el.addEventListener('click', (e) => { e.stopPropagation(); openCallout(comp, el); });
  const lbl = new CSS2DObject(el); lbl.position.set(...lead); obj.add(lbl);
  leaders.push({ el, dotEl, line });
}

function frameCamera() {
  explodables.forEach(({ obj }) => obj.position.set(0, 0, 0));
  const box = new THREE.Box3().setFromObject(device); device.position.sub(box.getCenter(new THREE.Vector3()));
  const b2 = new THREE.Box3().setFromObject(device);
  ground = new THREE.Mesh(new THREE.PlaneGeometry(900, 900), new THREE.ShadowMaterial({ opacity: 0.36 }));
  ground.rotation.x = -Math.PI / 2; ground.position.y = b2.min.y - 1; ground.receiveShadow = true; scene.add(ground);
  controls.target.set(0, 0, 0);
}

// ---- evolution ----
const evoGroup = new THREE.Group(); evoGroup.rotation.x = ZUP; scene.add(evoGroup); evoGroup.visible = false;
const genMeshes = {}; let evoLoaded = false, curGen = 1, evoPlaying = false, evoTimer = 0;
async function ensureEvolution() {
  if (evoLoaded) return; evoLoaded = true;
  for (let i = 1; i <= 6; i++) { const g = await load(`assets/models/gen${i}.glb`); applyMat(g, MATS.evo.clone()); g.visible = false; evoGroup.add(g); genMeshes[i] = g; }
  const c = new THREE.Box3().setFromObject(genMeshes[6]).getCenter(new THREE.Vector3());
  evoGroup.children.forEach((ch) => ch.position.sub(c)); showGen(1);
}
function showGen(n) {
  curGen = n; for (let i = 1; i <= 6; i++) if (genMeshes[i]) genMeshes[i].visible = (i === n);
  const d = GENS[n - 1];
  $('#genReadout').innerHTML = `<div class="gen-head"><span class="gen-num">G${d.g}</span><span class="gen-tag">${d.tag}</span><span class="gen-verdict v-${d.verdict}">${d.verdict}</span></div><div class="gen-change">${d.change}</div><div class="gen-metrics">${Object.entries(d.metrics).map(([k, v]) => `<span class="metric">${k} <b>${v}</b></span>`).join('')}</div><div class="gen-note">${d.note}</div>`;
  $('#genSlider').value = n;
}

// ---- identify DOM ----
$('#storySteps').innerHTML = STORY.map((s, i) => `<div class="story-step" data-i="${i}"><div class="story-k">${s.k}</div><div class="story-t">${s.t}</div><div class="story-d">${s.d}</div></div>`).join('');
$('#frameStrip').innerHTML = FRAMES.map((f) => `<div class="frame"><img src="${f.src}" alt="${f.cap}" loading="lazy"/><span>${f.cap}</span></div>`).join('');

const camViews = isMobile ? {
  explode: { pos: [80, 175, 360], tgt: [-4, 0, 0] }, evolution: { pos: [55, 42, 122], tgt: [0, 0, 0] }, identify: { pos: [165, 70, 215], tgt: [0, -10, 0] },
} : {
  explode: { pos: [175, 215, 340], tgt: [-28, 4, 0] }, evolution: { pos: [70, 48, 92], tgt: [0, 0, 0] }, identify: { pos: [185, 80, 165], tgt: [0, -8, 0] },
};
let camTween = null;
function flyTo(v) { camTween = { pos: new THREE.Vector3(...v.pos), tgt: new THREE.Vector3(...v.tgt) }; }
controls.addEventListener('start', () => { camTween = null; });

// view presets (device centred at origin; back/cartridge faces +Y, screen faces −Y)
const VIEWS = {
  iso: { pos: [205, 175, 280], tgt: [0, 0, 0] }, screen: { pos: [0, -330, 60], tgt: [0, 0, 0] },
  back: { pos: [0, 330, 60], tgt: [0, 0, 0] }, side: { pos: [340, 60, 40], tgt: [0, 0, 0] },
};
document.querySelectorAll('#viewnav button').forEach((b) => b.addEventListener('click', () => flyTo(VIEWS[b.dataset.view])));

let storyStep = 0, storyTimer = 0;
function highlightStory() { document.querySelectorAll('.story-step').forEach((s, i) => s.classList.toggle('on', i === storyStep)); }

async function setScene(name) {
  scene_ = name;
  document.querySelectorAll('#scenenav button').forEach((b) => b.classList.toggle('active', b.dataset.scene === name));
  ['explode', 'evolution', 'identify'].forEach((s) => $(`#panel-${s}`).classList.toggle('hidden', s !== name));
  $('#callout').classList.add('hidden');
  device.visible = (name !== 'evolution'); evoGroup.visible = (name === 'evolution'); if (ground) ground.visible = (name !== 'evolution');
  $('#viewnav').classList.toggle('hidden', name === 'evolution');
  if (name === 'evolution') await ensureEvolution();
  explodeTarget = name === 'explode' ? (parseInt($('#explodeSlider').value) / 100) : 0;
  if (name === 'identify') { slideTarget = 0; slideP = 1; storyStep = 0; storyTimer = 0; highlightStory(); }
  flyTo(camViews[name]);
}
document.querySelectorAll('#scenenav button').forEach((b) => b.addEventListener('click', () => setScene(b.dataset.scene)));
$('#explodeSlider').addEventListener('input', (e) => { explodeTarget = e.target.value / 100; });
$('#genSlider').addEventListener('input', (e) => { evoPlaying = false; $('#genPlay').textContent = '▶ play'; showGen(+e.target.value); });
$('#genPrev').onclick = () => showGen(Math.max(1, curGen - 1));
$('#genNext').onclick = () => showGen(Math.min(6, curGen + 1));
$('#genPlay').onclick = () => { evoPlaying = !evoPlaying; $('#genPlay').textContent = evoPlaying ? '❚❚ pause' : '▶ play'; evoTimer = 0; if (evoPlaying && curGen === 6) showGen(1); };

// ---- boot ----
(async function init() {
  const objs = await Promise.all(PARTS_V3.map((c) => load(`assets/models/${c.id}.glb`)));
  PARTS_V3.forEach((comp, i) => {
    const o = objs[i]; o.name = comp.id; applyMat(o, MATS[comp.mat] || MATS.evo);
    (comp.group === 'cart' ? cartGroup : coreGroup).add(o);
    explodables.push({ obj: o, exZ: comp.exZ, base: o.position.clone() });
    if (comp.label) addLeader(o, comp);
    if (comp.id === 'display') {
      const tex = new THREE.TextureLoader().load('assets/frames/sample_result.png'); tex.colorSpace = THREE.SRGBColorSpace;
      const plane = new THREE.Mesh(new THREE.PlaneGeometry(27, 32), new THREE.MeshBasicMaterial({ map: tex, toneMapped: false }));
      plane.position.set(13, -2, -16.55); plane.rotation.y = Math.PI; o.add(plane);
    }
  });
  // case screws (back cover → front bosses) + Pi-mount screws — each in its real hole
  const sc = await load('assets/models/screw.glb'); applyMat(sc, MATS.metalS);
  SCREWS.forEach((p, i) => {
    const s = sc.clone(); s.name = 'screw_case'; s.position.set(...p); coreGroup.add(s); explodables.push({ obj: s, exZ: 32, base: s.position.clone() });
    if (i === 0) addLeader(s, { anchor: [0, 0, 1.5], side: 1, kind: 'designed', title: 'M2.5 screws ×4', what: 'Fix the back cover to the front housing.', why: 'DESIGNED fasteners — socket-head cap screws, ISO 4762 dimensions. Each seats in a cover counterbore and threads into a front-housing boss.' });
  });
  const scp = await load('assets/models/screw_pi.glb'); applyMat(scp, MATS.metalS);
  SCREWS_PI.forEach((p) => { const s = scp.clone(); s.name = 'screw_pi'; s.position.set(...p); coreGroup.add(s); explodables.push({ obj: s, exZ: -54, base: s.position.clone() }); });
  frameCamera(); $('#loader').classList.add('gone'); setScene('explode');
})().catch((e) => { console.error(e); $('#loader').innerHTML = 'Failed to load geometry.<br>Serve over http (not file://).'; });

// ---- postprocessing: AO + subtle screen bloom ----
const composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene, camera));
const sao = new SAOPass(scene, camera); sao.params.saoIntensity = 0.009; sao.params.saoScale = 14; sao.params.saoKernelRadius = 28; sao.params.saoBias = 0.4; sao.enabled = !isMobile;
composer.addPass(sao);
const bloom = new UnrealBloomPass(new THREE.Vector2(innerWidth, innerHeight), 0.32, 0.7, 0.9); composer.addPass(bloom);
composer.addPass(new OutputPass());

// ---- loop ----
const clock = new THREE.Clock();
function animate() {
  requestAnimationFrame(animate);
  const dt = Math.min(clock.getDelta(), 0.05);
  explodeT += (explodeTarget - explodeT) * Math.min(1, dt * 6);
  slideP += (slideTarget - slideP) * Math.min(1, dt * 1.25);
  explodables.forEach(({ obj, exZ, base }) => { obj.position.z = base.z + exZ * explodeT; });
  if (scene_ === 'identify') {
    // hover-align then seat: lift clear, translate over the socket, descend in — no wall clipping
    const p = slideP, SPLIT = 0.34, LIFT = 30, SLIDE = 50;
    cartGroup.position.set(p > SPLIT ? SLIDE * (p - SPLIT) / (1 - SPLIT) : 0, 0, p > SPLIT ? LIFT : LIFT * (p / SPLIT));
  } else cartGroup.position.set(0, 0, 0);
  const la = scene_ === 'explode' ? Math.min(1, Math.max(0, explodeT * 2.2 - 0.25)) : 0;
  leaders.forEach((m) => { m.el.style.opacity = la; m.dotEl.style.opacity = la; if (m.line) m.line.material.opacity = la * 0.5; });
  if (ground) ground.material.opacity = 0.36 * (1 - Math.min(1, explodeT * 1.4));
  if (scene_ === 'evolution' && evoPlaying) { evoTimer += dt; if (evoTimer > 1.7) { evoTimer = 0; if (curGen < 6) showGen(curGen + 1); else { evoPlaying = false; $('#genPlay').textContent = '▶ play'; } } }
  if (scene_ === 'identify') { storyTimer += dt; if (storyTimer > 2.6 && storyStep < STORY.length - 1) { storyTimer = 0; storyStep++; highlightStory(); } }
  if (camTween) { camera.position.lerp(camTween.pos, 0.045); controls.target.lerp(camTween.tgt, 0.045); if (camera.position.distanceTo(camTween.pos) < 1.5) camTween = null; }
  controls.update();
  head.position.copy(camera.position); head.target.position.copy(controls.target); // headlight tracks view
  composer.render();
  labelRenderer.render(scene, camera);
}
animate();

addEventListener('resize', () => {
  camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight); composer.setSize(innerWidth, innerHeight);
  labelRenderer.setSize(innerWidth, innerHeight);
});

import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { toCreasedNormals } from 'three/addons/utils/BufferGeometryUtils.js';
import { COMPONENTS, FORM_NOTE, GENS, STORY, FRAMES, HONESTY } from './data.js';

const $ = (s) => document.querySelector(s);
const isMobile = matchMedia('(max-width:780px)').matches;

try { const c = document.createElement('canvas'); if (!(c.getContext('webgl2') || c.getContext('webgl'))) throw 0; }
catch (e) { $('#nowebgl').classList.remove('hidden'); $('#loader').classList.add('gone'); throw new Error('no webgl'); }

$('#honesty').textContent = HONESTY;
$('#formnote').textContent = FORM_NOTE;

// ---- renderer / scene / camera ----
const host = $('#webgl');
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, isMobile ? 1.5 : 2));
renderer.setSize(innerWidth, innerHeight);
renderer.setClearColor(0x000000, 0);                 // CSS gradient shows through
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.12;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
host.appendChild(renderer.domElement);

const labelRenderer = new CSS2DRenderer();
labelRenderer.setSize(innerWidth, innerHeight);
$('#labels').appendChild(labelRenderer.domElement);

const scene = new THREE.Scene();
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
scene.environmentIntensity = 0.5;

const camera = new THREE.PerspectiveCamera(36, innerWidth / innerHeight, 0.1, 6000);
camera.position.set(150, 110, 200);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true; controls.dampingFactor = 0.06;
controls.enablePan = true; controls.screenSpacePanning = true;
controls.rotateSpeed = 0.62; controls.zoomSpeed = 0.85; controls.panSpeed = 0.6;
controls.minDistance = 45; controls.maxDistance = 760;
controls.minPolarAngle = 0.12; controls.maxPolarAngle = Math.PI * 0.9;
controls.target.set(0, 0, 0);

// ---- studio lighting: warm key (shadow) + cool rim + soft fill + IBL ----
const key = new THREE.DirectionalLight(0xfff0db, 2.4);
key.position.set(90, 150, 110); key.castShadow = true;
key.shadow.mapSize.set(2048, 2048); key.shadow.bias = -0.0004; key.shadow.normalBias = 0.6;
Object.assign(key.shadow.camera, { near: 20, far: 700, left: -140, right: 140, top: 180, bottom: -180 });
scene.add(key);
const rim = new THREE.DirectionalLight(0xa9cbe6, 1.2); rim.position.set(-110, 70, -130); scene.add(rim);
const fill = new THREE.DirectionalLight(0xfff4e6, 0.45); fill.position.set(-70, -10, 90); scene.add(fill);
scene.add(new THREE.HemisphereLight(0xece8df, 0x14140f, 0.28));

// ---- materials (matte PA12-CF with microfacet speckle) ----
function speckleTex() {
  const s = 256, c = document.createElement('canvas'); c.width = c.height = s;
  const ctx = c.getContext('2d'), img = ctx.createImageData(s, s);
  for (let i = 0; i < s * s; i++) { const v = 148 + Math.floor(Math.random() * 74); img.data[i*4]=img.data[i*4+1]=img.data[i*4+2]=v; img.data[i*4+3]=255; }
  ctx.putImageData(img, 0, 0);
  const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(7, 7); return t;
}
const speckle = speckleTex();
const nylon = (color) => new THREE.MeshStandardMaterial({ color, metalness: 0.04, roughness: 0.66, roughnessMap: speckle });
const MATS = {
  stone: nylon(0x77756d), amber: nylon(0xc6822f), evo: nylon(0x8d8a80),
  screen: new THREE.MeshStandardMaterial({ color: 0x111116, metalness: 0.1, roughness: 0.5 }),
  pcb: new THREE.MeshStandardMaterial({ color: 0x1f3a2b, metalness: 0.1, roughness: 0.6 }),
  cell: new THREE.MeshStandardMaterial({ color: 0x8e9296, metalness: 0.55, roughness: 0.4 }),
  black: new THREE.MeshStandardMaterial({ color: 0x141416, metalness: 0.25, roughness: 0.5 }),
  gold: new THREE.MeshStandardMaterial({ color: 0xd7a23a, metalness: 0.88, roughness: 0.3 }),
  glass: new THREE.MeshStandardMaterial({ color: 0x9fb6c4, metalness: 0, roughness: 0.1 }),
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

// ---- groups: device(rot Z-up→Y-up) → coreGroup + cartGroup ----
const ZUP = -Math.PI / 2;
const device = new THREE.Group(); device.rotation.x = ZUP; scene.add(device);
const coreGroup = new THREE.Group(); const cartGroup = new THREE.Group();
device.add(coreGroup, cartGroup);

let explodeT = 0, explodeTarget = 0, slideP = 0, slideTarget = 0, scene_ = 'explode';
const explodables = [];     // {obj, exZ}
const leaders = [];         // {el, dotEl, line}
let ground;

function openCallout(p, el) {
  leaders.forEach((m) => m.el.classList.remove('active')); if (el) el.classList.add('active');
  const c = $('#callout'); c.classList.remove('hidden');
  const badge = p.kind === 'rep' ? '<span class="kind rep">representative</span>'
              : p.kind === 'designed' ? '<span class="kind des">designed</span>' : '';
  c.querySelector('h3').innerHTML = p.title + badge;
  c.querySelector('.what').textContent = p.what;
  c.querySelector('.why').textContent = p.why;
}
$('#calloutClose').onclick = () => { $('#callout').classList.add('hidden'); leaders.forEach((m) => m.el.classList.remove('active')); };

function addLeader(obj, comp) {
  const a = comp.anchor, lx = comp.side > 0 ? (isMobile ? 40 : 54) : (isMobile ? -34 : -44);
  const lead = [lx, a[1], a[2]];
  const line = new THREE.Line(
    new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(...a), new THREE.Vector3(...lead)]),
    new THREE.LineBasicMaterial({ color: 0xd68a2e, transparent: true, opacity: 0.5 }));
  obj.add(line);
  const dotEl = document.createElement('div'); dotEl.className = 'leaddot';
  const dot = new CSS2DObject(dotEl); dot.position.set(...a); obj.add(dot);
  const el = document.createElement('div'); el.className = 'leadlabel';
  el.innerHTML = `<span class="ll-name">${comp.title}</span>` +
    (comp.kind ? `<span class="ll-kind ${comp.kind}">${comp.kind === 'rep' ? 'rep' : 'designed'}</span>` : '');
  el.addEventListener('click', (e) => { e.stopPropagation(); openCallout(comp, el); });
  const lbl = new CSS2DObject(el); lbl.position.set(...lead); obj.add(lbl);
  leaders.push({ el, dotEl, line });
}

function frameCamera() {
  explodables.forEach(({ obj }) => obj.position.set(0, 0, 0));
  const box = new THREE.Box3().setFromObject(device);
  const c = box.getCenter(new THREE.Vector3());
  device.position.sub(c);
  // contact-shadow ground just under the assembled device
  const b2 = new THREE.Box3().setFromObject(device);
  ground = new THREE.Mesh(new THREE.PlaneGeometry(800, 800), new THREE.ShadowMaterial({ opacity: 0.34 }));
  ground.rotation.x = -Math.PI / 2; ground.position.y = b2.min.y - 1; ground.receiveShadow = true;
  scene.add(ground);
  controls.target.set(0, 0, 0);
}

// ---- evolution ----
const evoGroup = new THREE.Group(); evoGroup.rotation.x = ZUP; scene.add(evoGroup); evoGroup.visible = false;
const genMeshes = {}; let evoLoaded = false, curGen = 1, evoPlaying = false, evoTimer = 0;
async function ensureEvolution() {
  if (evoLoaded) return; evoLoaded = true;
  for (let i = 1; i <= 6; i++) { const g = await load(`assets/models/gen${i}.glb`); applyMat(g, MATS.evo.clone()); g.visible = false; evoGroup.add(g); genMeshes[i] = g; }
  const box = new THREE.Box3().setFromObject(genMeshes[6]); const c = box.getCenter(new THREE.Vector3());
  evoGroup.children.forEach((ch) => ch.position.sub(c)); showGen(1);
}
function showGen(n) {
  curGen = n; for (let i = 1; i <= 6; i++) if (genMeshes[i]) genMeshes[i].visible = (i === n);
  const d = GENS[n - 1];
  $('#genReadout').innerHTML =
    `<div class="gen-head"><span class="gen-num">G${d.g}</span><span class="gen-tag">${d.tag}</span>
       <span class="gen-verdict v-${d.verdict}">${d.verdict}</span></div>
     <div class="gen-change">${d.change}</div>
     <div class="gen-metrics">${Object.entries(d.metrics).map(([k, v]) => `<span class="metric">${k} <b>${v}</b></span>`).join('')}</div>
     <div class="gen-note">${d.note}</div>`;
  $('#genSlider').value = n;
}

// ---- identify DOM ----
$('#storySteps').innerHTML = STORY.map((s, i) =>
  `<div class="story-step" data-i="${i}"><div class="story-k">${s.k}</div><div class="story-t">${s.t}</div><div class="story-d">${s.d}</div></div>`).join('');
$('#frameStrip').innerHTML = FRAMES.map((f) => `<div class="frame"><img src="${f.src}" alt="${f.cap}" loading="lazy"/><span>${f.cap}</span></div>`).join('');

// ---- scene mgmt + camera fly (cancels on user interaction) ----
const camViews = isMobile ? {
  explode: { pos: [70, 150, 320], tgt: [-4, -14, 0] },     // model in the upper area, panel below
  evolution: { pos: [55, 42, 122], tgt: [0, 0, 0] },
  identify: { pos: [150, 72, 200], tgt: [0, -16, 0] },
} : {
  explode: { pos: [138, 168, 262], tgt: [-22, 2, 0] },
  evolution: { pos: [70, 48, 92], tgt: [0, 0, 0] },
  identify: { pos: [165, 78, 150], tgt: [0, -4, 0] },
};
let camTween = null;
function flyTo(v) { camTween = { pos: new THREE.Vector3(...v.pos), tgt: new THREE.Vector3(...v.tgt) }; }
controls.addEventListener('start', () => { camTween = null; });   // never fight the user

let storyStep = 0, storyTimer = 0;
function highlightStory() { document.querySelectorAll('.story-step').forEach((s, i) => s.classList.toggle('on', i === storyStep)); }

async function setScene(name) {
  scene_ = name;
  document.querySelectorAll('#scenenav button').forEach((b) => b.classList.toggle('active', b.dataset.scene === name));
  ['explode', 'evolution', 'identify'].forEach((s) => $(`#panel-${s}`).classList.toggle('hidden', s !== name));
  $('#callout').classList.add('hidden');
  device.visible = (name !== 'evolution'); evoGroup.visible = (name === 'evolution');
  if (ground) ground.visible = (name !== 'evolution');
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
  const objs = await Promise.all(COMPONENTS.map((c) => load(`assets/models/${c.model}.glb`)));
  COMPONENTS.forEach((comp, i) => {
    const o = objs[i]; applyMat(o, MATS[comp.mat] || MATS.evo);
    (comp.group === 'cart' ? cartGroup : coreGroup).add(o);
    explodables.push({ obj: o, exZ: comp.exZ });
    addLeader(o, comp);
    if (comp.id === 'display') {                       // a REAL Phase-5 frame on the screen face
      const tex = new THREE.TextureLoader().load('assets/frames/sample_result.png');
      tex.colorSpace = THREE.SRGBColorSpace;
      const plane = new THREE.Mesh(new THREE.PlaneGeometry(27, 32), new THREE.MeshBasicMaterial({ map: tex, toneMapped: false }));
      plane.position.set(13, 2, -14.9); plane.rotation.y = Math.PI; o.add(plane);
    }
  });
  frameCamera();
  $('#loader').classList.add('gone');
  setScene('explode');
})().catch((e) => { console.error(e); $('#loader').innerHTML = 'Failed to load geometry.<br>Serve over http (not file://).'; });

// ---- loop ----
const clock = new THREE.Clock();
function animate() {
  requestAnimationFrame(animate);
  const dt = Math.min(clock.getDelta(), 0.05);

  explodeT += (explodeTarget - explodeT) * Math.min(1, dt * 6);
  slideP += (slideTarget - slideP) * Math.min(1, dt * 1.25);
  explodables.forEach(({ obj, exZ }) => { obj.position.z = exZ * explodeT; });

  // identify: assemble the WHOLE cartridge group via hover-align → seat (no wall clipping)
  if (scene_ === 'identify') {
    const p = slideP;                       // 1 = apart, 0 = seated
    const SPLIT = 0.32, LIFT = 26, SLIDE = 48;
    const xo = p > SPLIT ? SLIDE * (p - SPLIT) / (1 - SPLIT) : 0;
    const zo = p > SPLIT ? LIFT : LIFT * (p / SPLIT);
    cartGroup.position.set(xo, 0, zo);
  } else cartGroup.position.set(0, 0, 0);

  // leader labels: fade in with explode, only in explode scene
  const la = scene_ === 'explode' ? Math.min(1, Math.max(0, explodeT * 2.2 - 0.25)) : 0;
  leaders.forEach((m) => { m.el.style.opacity = la; m.dotEl.style.opacity = la; m.line.material.opacity = la * 0.5; });
  if (ground) ground.material.opacity = 0.34 * (1 - Math.min(1, explodeT * 1.4));

  if (scene_ === 'evolution' && evoPlaying) { evoTimer += dt; if (evoTimer > 1.7) { evoTimer = 0; if (curGen < 6) showGen(curGen + 1); else { evoPlaying = false; $('#genPlay').textContent = '▶ play'; } } }
  if (scene_ === 'identify') { storyTimer += dt; if (storyTimer > 2.6 && storyStep < STORY.length - 1) { storyTimer = 0; storyStep++; highlightStory(); } }

  if (camTween) {
    camera.position.lerp(camTween.pos, 0.045);
    controls.target.lerp(camTween.tgt, 0.045);
    if (camera.position.distanceTo(camTween.pos) < 1.5) camTween = null;
  }
  controls.update();
  renderer.render(scene, camera);
  labelRenderer.render(scene, camera);
}
animate();

addEventListener('resize', () => {
  camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight); labelRenderer.setSize(innerWidth, innerHeight);
});

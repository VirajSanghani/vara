import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { PARTS, FORM_NOTE, GENS, STORY, FRAMES, HONESTY } from './data.js';

const $ = (s) => document.querySelector(s);
const isMobile = matchMedia('(max-width:780px)').matches;

// ---- WebGL guard ----
try { const c = document.createElement('canvas'); if (!(c.getContext('webgl2') || c.getContext('webgl'))) throw 0; }
catch (e) { $('#nowebgl').classList.remove('hidden'); $('#loader').classList.add('gone'); throw new Error('no webgl'); }

$('#honesty').textContent = HONESTY;
$('#formnote').textContent = FORM_NOTE;

// ---- renderer / scene / camera ----
const host = $('#webgl');
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
renderer.setPixelRatio(Math.min(devicePixelRatio, isMobile ? 1.5 : 2));
renderer.setSize(innerWidth, innerHeight);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.05;
host.appendChild(renderer.domElement);

const labelRenderer = new CSS2DRenderer();
labelRenderer.setSize(innerWidth, innerHeight);
$('#labels').appendChild(labelRenderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x13130f);
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;

const camera = new THREE.PerspectiveCamera(38, innerWidth / innerHeight, 0.1, 5000);
camera.position.set(120, 90, 160);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true; controls.dampingFactor = 0.08;
controls.minDistance = 60; controls.maxDistance = 480;
controls.target.set(0, 0, 0);

const key = new THREE.DirectionalLight(0xfff1dd, 1.1); key.position.set(80, 130, 90); scene.add(key);
const rim = new THREE.DirectionalLight(0x8fb0c8, 0.5); rim.position.set(-90, 40, -110); scene.add(rim);
scene.add(new THREE.HemisphereLight(0xece8df, 0x14140f, 0.35));

// ---- materials (Quiet Utility: stone core, amber cartridge) ----
const matStone = new THREE.MeshStandardMaterial({ color: 0x6f6d64, metalness: 0.25, roughness: 0.62 });
const matAmber = new THREE.MeshStandardMaterial({ color: 0xc6822f, metalness: 0.3, roughness: 0.5 });
const matEvo = new THREE.MeshStandardMaterial({ color: 0x8d8a80, metalness: 0.2, roughness: 0.6 });

const loader = new GLTFLoader();
const load = (url) => new Promise((res, rej) => loader.load(url, (g) => res(g.scene), undefined, rej));
function applyMat(obj, mat) { obj.traverse((o) => { if (o.isMesh) { o.material = mat; o.geometry.computeVertexNormals?.(); } }); }

// ---- device group (explode + identify scenes) ----
const ZUP = -Math.PI / 2;            // build123d Z-up -> three Y-up
const device = new THREE.Group(); device.rotation.x = ZUP; scene.add(device);
let coreObj, cartObj;
let explodeT = 0, explodeTarget = 0;     // 0..1
let slideX = 0, slideTarget = 0;          // identify slide-on (part X)
const markers = [];
const EXPLODE_GAP = 70;                    // mm along mating axis (+Z part)

function addMarkers(parent, list, mat) {
  list.forEach((p) => {
    const el = document.createElement('div'); el.className = 'marker';
    el.innerHTML = '<i></i>'; el.title = p.title;
    el.addEventListener('click', (e) => { e.stopPropagation(); openCallout(p, el); });
    const m = new CSS2DObject(el); m.position.set(...p.pos); m.visible = false;
    parent.add(m); markers.push({ obj: m, el });
  });
}

function openCallout(p, el) {
  markers.forEach((m) => m.el.classList.remove('active')); el.classList.add('active');
  const c = $('#callout'); c.classList.remove('hidden');
  c.querySelector('h3').textContent = p.title;
  c.querySelector('.what').textContent = p.what;
  c.querySelector('.why').textContent = p.why;
}
$('#calloutClose').onclick = () => { $('#callout').classList.add('hidden'); markers.forEach((m) => m.el.classList.remove('active')); };

function frameCamera() {
  const box = new THREE.Box3().setFromObject(device);
  const c = box.getCenter(new THREE.Vector3()), s = box.getSize(new THREE.Vector3());
  device.position.sub(c); device.position.y += 0;        // recenter group
  controls.target.set(0, 0, 0);
}

// ---- evolution group ----
const evoGroup = new THREE.Group(); evoGroup.rotation.x = ZUP; scene.add(evoGroup); evoGroup.visible = false;
const genMeshes = {}; let evoLoaded = false, curGen = 1, evoPlaying = false, evoTimer = 0;

async function ensureEvolution() {
  if (evoLoaded) return; evoLoaded = true;
  for (let i = 1; i <= 6; i++) {
    const g = await load(`assets/models/gen${i}.glb`); applyMat(g, matEvo.clone());
    g.visible = false; evoGroup.add(g); genMeshes[i] = g;
  }
  const box = new THREE.Box3().setFromObject(genMeshes[6]); const c = box.getCenter(new THREE.Vector3());
  evoGroup.children.forEach((ch) => ch.position.sub(c));
  showGen(1);
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

// ---- identify scene DOM ----
$('#storySteps').innerHTML = STORY.map((s, i) =>
  `<div class="story-step" data-i="${i}"><div class="story-k">${s.k}</div>
     <div class="story-t">${s.t}</div><div class="story-d">${s.d}</div></div>`).join('');
$('#frameStrip').innerHTML = FRAMES.map((f) =>
  `<div class="frame"><img src="${f.src}" alt="${f.cap}" loading="lazy"/><span>${f.cap}</span></div>`).join('');

// ---- scenes ----
const camViews = {
  explode: { pos: [120, 90, 165], tgt: [0, 0, 0] },
  evolution: { pos: [70, 45, 90], tgt: [0, 0, 0] },
  identify: { pos: [150, 70, 140], tgt: [0, 0, 0] },
};
let camTween = null;
function flyTo(v) { camTween = { pos: new THREE.Vector3(...v.pos), tgt: new THREE.Vector3(...v.tgt), t: 0 }; }

let scene_ = 'explode';
async function setScene(name) {
  scene_ = name;
  document.querySelectorAll('#scenenav button').forEach((b) => b.classList.toggle('active', b.dataset.scene === name));
  ['explode', 'evolution', 'identify'].forEach((s) => $(`#panel-${s}`).classList.toggle('hidden', s !== name));
  $('#callout').classList.add('hidden');
  device.visible = (name !== 'evolution');
  evoGroup.visible = (name === 'evolution');
  markers.forEach((m) => { m.obj.visible = (name === 'explode'); });
  if (name === 'evolution') await ensureEvolution();
  explodeTarget = name === 'explode' ? (parseInt($('#explodeSlider').value) / 100) : (name === 'identify' ? 0 : explodeTarget);
  if (name === 'identify') { slideTarget = 0; slideX = 1; runStory(); }  // start slid-out, animate in
  flyTo(camViews[name]);
}
document.querySelectorAll('#scenenav button').forEach((b) => b.addEventListener('click', () => setScene(b.dataset.scene)));

// explode slider
$('#explodeSlider').addEventListener('input', (e) => { explodeTarget = e.target.value / 100; });
// evolution controls
$('#genSlider').addEventListener('input', (e) => { evoPlaying = false; $('#genPlay').textContent = '▶ play'; showGen(+e.target.value); });
$('#genPrev').onclick = () => showGen(Math.max(1, curGen - 1));
$('#genNext').onclick = () => showGen(Math.min(6, curGen + 1));
$('#genPlay').onclick = () => { evoPlaying = !evoPlaying; $('#genPlay').textContent = evoPlaying ? '❚❚ pause' : '▶ play'; evoTimer = 0; if (evoPlaying && curGen === 6) showGen(1); };

// identify story stepping
let storyStep = 0, storyTimer = 0;
function runStory() { storyStep = 0; storyTimer = 0; highlightStory(); }
function highlightStory() { document.querySelectorAll('.story-step').forEach((s, i) => s.classList.toggle('on', i === storyStep)); }

// ---- boot ----
(async function init() {
  [coreObj, cartObj] = await Promise.all([load('assets/models/core.glb'), load('assets/models/cartridge.glb')]);
  applyMat(coreObj, matStone); applyMat(cartObj, matAmber);
  device.add(coreObj); device.add(cartObj);
  addMarkers(coreObj, PARTS.core); addMarkers(cartObj, PARTS.cartridge);
  frameCamera();
  $('#loader').classList.add('gone');
  setScene('explode');
})().catch((e) => { console.error(e); $('#loader').innerHTML = 'Failed to load geometry. <br>Serve over http (not file://).'; });

// ---- loop ----
const clock = new THREE.Clock();
function animate() {
  requestAnimationFrame(animate);
  const dt = Math.min(clock.getDelta(), 0.05);

  // explode + slide tweens (part +Z = mating axis; part +X = slide axis)
  explodeT += (explodeTarget - explodeT) * Math.min(1, dt * 6);
  slideX += (slideTarget - slideX) * Math.min(1, dt * 3);
  if (cartObj) {
    cartObj.position.z = explodeT * EXPLODE_GAP;          // explode along mating axis
    cartObj.position.x = (scene_ === 'identify') ? slideX * 46 : 0;  // slide-on in identify
  }
  markers.forEach((m) => m.el.style.opacity = (scene_ === 'explode') ? Math.min(1, explodeT * 2 + 0.15) : 0);

  // evolution autoplay
  if (scene_ === 'evolution' && evoPlaying) {
    evoTimer += dt;
    if (evoTimer > 1.7) { evoTimer = 0; if (curGen < 6) showGen(curGen + 1); else { evoPlaying = false; $('#genPlay').textContent = '▶ play'; } }
  }
  // identify story autostep
  if (scene_ === 'identify') {
    storyTimer += dt;
    if (storyTimer > 2.6 && storyStep < STORY.length - 1) { storyTimer = 0; storyStep++; highlightStory(); }
  }

  // camera fly
  if (camTween) {
    camTween.t += dt * 1.4;
    const k = Math.min(1, camTween.t); const e = k < .5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2;
    camera.position.lerp(camTween.pos, e * 0.12 + 0.02);
    controls.target.lerp(camTween.tgt, 0.08);
    if (k >= 1 && camera.position.distanceTo(camTween.pos) < 2) camTween = null;
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

"""Build a single animated glTF of the full VARA assembly for the <model-viewer> page.

Each part is a node that translates from its exploded offset → seated over a looping clip
(assemble → hold → disassemble). A parent node applies the Z-up→Y-up rotation. Materials are
baked in (model-viewer needs them). Geometry is read from the Phase-6 showcase part GLBs via
trimesh; the glTF + animation are authored with pygltflib.

Output: web/assembly/assembly.glb
"""
import os, struct, math
import numpy as np
import trimesh
import pygltflib as g

HERE = os.path.dirname(__file__)
MODELS = os.path.join(HERE, "..", "..", "web", "assets", "models")
OUT = os.path.join(HERE, "..", "..", "web", "assembly")
os.makedirs(OUT, exist_ok=True)

def srgb_lin(hexcol):
    r = ((hexcol >> 16) & 255) / 255; gg = ((hexcol >> 8) & 255) / 255; b = (hexcol & 255) / 255
    f = lambda c: round(c ** 2.2, 4)
    return [f(r), f(gg), f(b), 1.0]

# material key → (baseColor sRGB hex, metallic, roughness)
MAT = {
    "stone": (0x78766e, 0.05, 0.7), "amber": (0xc6822f, 0.05, 0.6),
    "pcb": (0x1f3a2b, 0.15, 0.58), "screen": (0x0c0c10, 0.2, 0.42),
    "black": (0x161618, 0.3, 0.5), "gold": (0xd7a23a, 0.9, 0.3),
    "cell": (0x929698, 0.55, 0.42), "chip": (0x18181a, 0.3, 0.45),
    "metalS": (0xc9c9cf, 1.0, 0.3), "metalA": (0x55555c, 0.9, 0.4),
    "glass": (0x9fb6c4, 0.0, 0.12),
}

CASE = [(-5, -59, 1.5), (31, -59, 1.5), (-5, 17, 1.5), (31, 17, 1.5)]
PIH = [(1.5, -53, -9.5), (24.5, -53, -9.5), (1.5, 5, -9.5), (24.5, 5, -9.5)]

# (label, glb file, exZ, base xyz, material) — exZ matches the showcase teardown
PARTS = [
    ("glass", "glass", -88, (0, 0, 0), "glass"), ("display", "display", -72, (0, 0, 0), "screen"),
    ("speaker", "speaker", -72, (0, 0, 0), "black"), ("camera", "camera", -12, (0, 0, 0), "black"),
    ("pi", "pi", -54, (0, 0, 0), "pcb"), ("carrier", "carrier", -38, (0, 0, 0), "pcb"),
    ("battery", "battery", -24, (0, 0, 0), "cell"), ("core_front", "core_front", 0, (0, 0, 0), "stone"),
    ("wheel", "wheel", 0, (0, 0, 0), "metalA"), ("button", "button", 0, (0, 0, 0), "metalA"),
    ("encoder", "encoder", 0, (0, 0, 0), "black"), ("mic", "mic", 0, (0, 0, 0), "chip"),
    ("pogo", "pogo", 40, (0, 0, 0), "gold"), ("core_back", "core_back", 24, (0, 0, 0), "stone"),
    ("eeprom", "eeprom", 52, (0, 0, 0), "chip"), ("cartridge", "cartridge", 70, (0, 0, 0), "amber"),
    ("ledring", "ledring", 86, (0, 0, 0), "pcb"), ("lensring", "lensring", 102, (0, 0, 0), "metalA"),
]
for i, b in enumerate(CASE): PARTS.append((f"screw{i}", "screw", 32, b, "metalS"))
for i, b in enumerate(PIH): PARTS.append((f"piscrew{i}", "screw_pi", -54, b, "metalS"))

# ---- build the binary blob + accessors ----
blob = bytearray()
gltf = g.GLTF2()
def pad4():
    while len(blob) % 4: blob.append(0)
def add_view(data, target=None):
    pad4(); off = len(blob); blob.extend(data)
    gltf.bufferViews.append(g.BufferView(buffer=0, byteOffset=off, byteLength=len(data), target=target))
    return len(gltf.bufferViews) - 1
def add_acc(data, count, ctype, atype, target=None, mn=None, mx=None):
    bv = add_view(data, target)
    a = g.Accessor(bufferView=bv, componentType=ctype, count=count, type=atype)
    if mn is not None: a.min = mn; a.max = mx
    gltf.accessors.append(a); return len(gltf.accessors) - 1

FLOAT, UINT = 5126, 5125
ARRAY, ELEM = 34962, 34963

# shared animation time accessor (assemble → hold → disassemble, loops)
times = np.array([0.0, 2.6, 4.0, 6.4], dtype=np.float32)
time_acc = add_acc(times.tobytes(), len(times), FLOAT, "SCALAR", mn=[float(times.min())], mx=[float(times.max())])

# materials (dedupe by key)
mat_idx = {}
for key, (hexc, met, rough) in MAT.items():
    gltf.materials.append(g.Material(
        pbrMetallicRoughness=g.PbrMetallicRoughness(baseColorFactor=srgb_lin(hexc), metallicFactor=met, roughnessFactor=rough),
        name=key, doubleSided=True))
    mat_idx[key] = len(gltf.materials) - 1

geom_cache = {}
def load_geom(fname):
    if fname in geom_cache: return geom_cache[fname]
    m = trimesh.load(os.path.join(MODELS, fname + ".glb"), force="mesh")
    v = np.asarray(m.vertices, dtype=np.float32)
    n = np.asarray(m.vertex_normals, dtype=np.float32)
    f = np.asarray(m.faces, dtype=np.uint32).reshape(-1)
    geom_cache[fname] = (v, n, f); return geom_cache[fname]

device_children = []
for label, fname, exZ, base, matkey in PARTS:
    v, n, f = load_geom(fname)
    pos = add_acc(v.tobytes(), len(v), FLOAT, "VEC3", ARRAY,
                  mn=v.min(0).tolist(), mx=v.max(0).tolist())
    nrm = add_acc(n.tobytes(), len(n), FLOAT, "VEC3", ARRAY)
    idx = add_acc(f.tobytes(), len(f), UINT, "SCALAR", ELEM)
    gltf.meshes.append(g.Mesh(primitives=[g.Primitive(
        attributes=g.Attributes(POSITION=pos, NORMAL=nrm), indices=idx, material=mat_idx[matkey])]))
    mesh_i = len(gltf.meshes) - 1
    bx, by, bz = base
    seated = (bx, by, bz)
    expl = (bx, by, bz + exZ)
    node = g.Node(mesh=mesh_i, translation=list(expl), name=label)   # rest = exploded → frames the full spread
    gltf.nodes.append(node); ni = len(gltf.nodes) - 1
    device_children.append(ni)
    # translation animation: exploded → seated → seated → exploded (loops)
    tr = np.array([expl, seated, seated, expl], dtype=np.float32).reshape(-1)
    out = add_acc(tr.tobytes(), 4, FLOAT, "VEC3")
    if not gltf.animations:
        gltf.animations.append(g.Animation(samplers=[], channels=[]))
    anim = gltf.animations[0]
    anim.samplers.append(g.AnimationSampler(input=time_acc, output=out, interpolation="LINEAR"))
    si = len(anim.samplers) - 1
    anim.channels.append(g.AnimationChannel(sampler=si, target=g.AnimationChannelTarget(node=ni, path="translation")))

# parent "device" node: Z-up (build123d) → Y-up (glTF), rotation −90° about X
device = g.Node(name="VARA", children=device_children, rotation=[-0.70710678, 0.0, 0.0, 0.70710678])
gltf.nodes.append(device); dev_i = len(gltf.nodes) - 1
gltf.scenes.append(g.Scene(nodes=[dev_i])); gltf.scene = 0
gltf.buffers.append(g.Buffer(byteLength=len(blob)))
gltf.set_binary_blob(bytes(blob))
path = os.path.join(OUT, "assembly.glb")
gltf.save(path)
print("wrote", path, f"({os.path.getsize(path)//1024} KB), {len(PARTS)} parts, "
      f"{len(gltf.animations[0].channels)} animated nodes")

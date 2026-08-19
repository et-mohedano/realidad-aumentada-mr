from pathlib import Path
import json, math, struct
import numpy as np
import cv2
from PIL import Image
from shapely.geometry import Polygon
from shapely.ops import triangulate
import trimesh
from trimesh.visual.material import PBRMaterial

ROOT = Path(__file__).resolve().parent
IMG_PATH = ROOT / 'assets' / 'logo_original.png'
OUT_GLB = ROOT / 'assets' / 'logo_mr_3d.glb'
OUT_PNG = ROOT / 'assets' / 'logo_transparente.png'

# Institutional tones sampled/normalized from the supplied logo.
WINE = (123, 29, 46, 255)   # #7B1D2E
GOLD = (203, 171, 128, 255) # approx. supplied gold
BG = np.array([230,230,230], dtype=np.int16)

img = Image.open(IMG_PATH).convert('RGBA')
rgba = np.array(img)
rgb = rgba[..., :3].astype(np.int16)

# Transparent poster: remove the light-gray background and thin black border.
alpha = np.full(rgb.shape[:2], 255, dtype=np.uint8)
d_bg = np.linalg.norm(rgb - BG, axis=2)
alpha[d_bg < 18] = 0
# Remove near-black 1px screenshot border if present.
near_black = np.max(rgb, axis=2) < 35
alpha[near_black] = 0
out_rgba = rgba.copy()
out_rgba[..., 3] = alpha
Image.fromarray(out_rgba).save(OUT_PNG)

# Classify pixels into wine, gold, background and black using nearest centers.
centers = np.array([
    [121, 25, 59],
    [203, 171, 128],
    [230, 230, 230],
    [14, 14, 14],
], dtype=np.float32)
flat = np.array(img.convert('RGB')).reshape(-1, 3).astype(np.float32)
dist = ((flat[:,None,:] - centers[None,:,:])**2).sum(axis=2)
cls = dist.argmin(axis=1).reshape(img.height, img.width)


def extract_polygons(class_id, epsilon=2.0, min_area=250):
    mask = (cls == class_id).astype(np.uint8) * 255
    contours, hierarchy = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    if hierarchy is None:
        return []
    hierarchy = hierarchy[0]
    polygons = []
    for i, cnt in enumerate(contours):
        if hierarchy[i][3] != -1:
            continue
        if cv2.contourArea(cnt) < min_area:
            continue
        ext = cv2.approxPolyDP(cnt, epsilon, True).reshape(-1, 2)
        holes = []
        child = hierarchy[i][2]
        while child != -1:
            if cv2.contourArea(contours[child]) > 80:
                hole = cv2.approxPolyDP(contours[child], epsilon, True).reshape(-1, 2)
                holes.append(hole)
            child = hierarchy[child][0]
        p = Polygon(ext, holes)
        if not p.is_valid:
            p = p.buffer(0)
        if not p.is_empty:
            if p.geom_type == 'Polygon':
                polygons.append(p)
            else:
                polygons.extend([g for g in p.geoms if g.area >= min_area])
    return polygons


def to_world(x, y, scale):
    # Logo upright in XY plane, with depth in Z; glTF uses Y-up.
    wx = (x - img.width/2.0) * scale
    wy = (img.height/2.0 - y) * scale
    return float(wx), float(wy)


def extrude_polygon(poly: Polygon, depth: float, scale: float, z_offset: float = 0.0):
    z0 = z_offset - depth/2
    z1 = z_offset + depth/2
    vertices = []
    faces = []
    vmap = {}

    def vid(x, y, z):
        key = (round(float(x), 7), round(float(y), 7), round(float(z), 7))
        if key not in vmap:
            vmap[key] = len(vertices)
            vertices.append([x, y, z])
        return vmap[key]

    # Triangulate the polygon face; only keep triangles fully covered by polygon.
    for tri in triangulate(poly):
        if not poly.covers(tri):
            continue
        pts = list(tri.exterior.coords)[:-1]
        wpts = [to_world(x, y, scale) for x, y in pts]
        # Front face (+Z)
        fi = [vid(x, y, z1) for x, y in wpts]
        faces.append(fi)
        # Back face (-Z), reversed winding
        bi = [vid(x, y, z0) for x, y in reversed(wpts)]
        faces.append(bi)

    # Side walls for exterior and holes.
    rings = [poly.exterior] + list(poly.interiors)
    for ring in rings:
        coords = list(ring.coords)
        for a, b in zip(coords[:-1], coords[1:]):
            ax, ay = to_world(a[0], a[1], scale)
            bx, by = to_world(b[0], b[1], scale)
            a0, b0 = vid(ax, ay, z0), vid(bx, by, z0)
            a1, b1 = vid(ax, ay, z1), vid(bx, by, z1)
            faces.append([a0, b0, b1])
            faces.append([a0, b1, a1])

    mesh = trimesh.Trimesh(vertices=np.asarray(vertices), faces=np.asarray(faces), process=True)
    mesh.remove_unreferenced_vertices()
    mesh.fix_normals()
    return mesh

# Build model approximately 62 cm wide with 4.2 cm depth.
scale = 0.62 / img.width
depth = 0.042
wine_polys = extract_polygons(0)
gold_polys = extract_polygons(1)

wine_mat = PBRMaterial(
    name='Vino_MR',
    baseColorFactor=np.array(WINE, dtype=np.uint8),
    metallicFactor=0.16,
    roughnessFactor=0.42,
)
gold_mat = PBRMaterial(
    name='Dorado_MR',
    baseColorFactor=np.array(GOLD, dtype=np.uint8),
    metallicFactor=0.12,
    roughnessFactor=0.50,
)

scene = trimesh.Scene()
scene.graph.update(frame_to='LogoRoot', frame_from='world', matrix=np.eye(4))

idx = 0
for poly in gold_polys:
    mesh = extrude_polygon(poly, depth=depth, scale=scale, z_offset=0.0)
    mesh.visual.material = gold_mat
    scene.add_geometry(mesh, node_name=f'Gold_{idx}', geom_name=f'Gold_{idx}', parent_node_name='LogoRoot')
    idx += 1

idx = 0
for poly in wine_polys:
    # Tiny forward offset adds visual layering between the two colors.
    mesh = extrude_polygon(poly, depth=depth*1.05, scale=scale, z_offset=0.004)
    mesh.visual.material = wine_mat
    scene.add_geometry(mesh, node_name=f'Wine_{idx}', geom_name=f'Wine_{idx}', parent_node_name='LogoRoot')
    idx += 1

# Export GLB.
glb = trimesh.exchange.gltf.export_glb(scene, include_normals=True)
OUT_GLB.write_bytes(glb)


def parse_glb(data: bytes):
    magic, version, length = struct.unpack_from('<III', data, 0)
    assert magic == 0x46546C67 and version == 2
    offset = 12
    chunks = []
    while offset < length:
        clen, ctype = struct.unpack_from('<II', data, offset)
        offset += 8
        payload = data[offset:offset+clen]
        offset += clen
        chunks.append((ctype, payload))
    return chunks


def build_glb(chunks):
    body = bytearray()
    for ctype, payload in chunks:
        padbyte = b' ' if ctype == 0x4E4F534A else b'\x00'
        while len(payload) % 4:
            payload += padbyte
        body += struct.pack('<II', len(payload), ctype)
        body += payload
    header = struct.pack('<III', 0x46546C67, 2, 12 + len(body))
    return header + body


def add_rotation_animation(path: Path):
    data = path.read_bytes()
    chunks = parse_glb(data)
    json_idx = next(i for i,(t,_) in enumerate(chunks) if t == 0x4E4F534A)
    bin_idx = next(i for i,(t,_) in enumerate(chunks) if t == 0x004E4942)
    doc = json.loads(chunks[json_idx][1].decode('utf-8').rstrip(' \x00'))
    binary = bytearray(chunks[bin_idx][1])

    root_index = None
    for i, node in enumerate(doc.get('nodes', [])):
        if node.get('name') == 'LogoRoot':
            root_index = i
            node.pop('matrix', None)
            node['translation'] = [0,0,0]
            node['rotation'] = [0,0,0,1]
            node['scale'] = [1,1,1]
            break
    if root_index is None:
        raise RuntimeError('LogoRoot node not found')

    # 12-second continuous rotation around Y.
    times = np.array([0, 3, 6, 9, 12], dtype='<f4')
    angles = np.deg2rad([0, 90, 180, 270, 360])
    rots = np.array([[0, math.sin(a/2), 0, math.cos(a/2)] for a in angles], dtype='<f4')

    def append_aligned(blob: bytes):
        while len(binary) % 4:
            binary.append(0)
        off = len(binary)
        binary.extend(blob)
        return off, len(blob)

    t_off, t_len = append_aligned(times.tobytes())
    r_off, r_len = append_aligned(rots.tobytes())

    doc.setdefault('bufferViews', [])
    t_bv = len(doc['bufferViews'])
    doc['bufferViews'].append({'buffer':0, 'byteOffset':t_off, 'byteLength':t_len})
    r_bv = len(doc['bufferViews'])
    doc['bufferViews'].append({'buffer':0, 'byteOffset':r_off, 'byteLength':r_len})

    doc.setdefault('accessors', [])
    t_acc = len(doc['accessors'])
    doc['accessors'].append({
        'bufferView': t_bv, 'byteOffset': 0, 'componentType': 5126,
        'count': int(len(times)), 'type': 'SCALAR',
        'min': [float(times.min())], 'max': [float(times.max())]
    })
    r_acc = len(doc['accessors'])
    doc['accessors'].append({
        'bufferView': r_bv, 'byteOffset': 0, 'componentType': 5126,
        'count': int(len(rots)), 'type': 'VEC4'
    })

    doc['animations'] = [{
        'name': 'Giro360',
        'samplers': [{'input': t_acc, 'output': r_acc, 'interpolation': 'LINEAR'}],
        'channels': [{'sampler':0, 'target': {'node': root_index, 'path':'rotation'}}]
    }]
    doc['buffers'][0]['byteLength'] = len(binary)

    json_bytes = json.dumps(doc, separators=(',', ':')).encode('utf-8')
    chunks[json_idx] = (0x4E4F534A, json_bytes)
    chunks[bin_idx] = (0x004E4942, bytes(binary))
    path.write_bytes(build_glb(chunks))

add_rotation_animation(OUT_GLB)

print(f'Generated: {OUT_GLB}')
print(f'Generated: {OUT_PNG}')
print(f'Polygons: wine={len(wine_polys)}, gold={len(gold_polys)}')

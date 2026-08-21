
from pathlib import Path
import math, json, struct
import numpy as np
import trimesh

OUT = Path('/mnt/data/mr_ar_logo_variantes_v6')
ASSETS = OUT / 'assets'
ASSETS.mkdir(parents=True, exist_ok=True)

def rgba(h, a=255):
    h=h.lstrip('#')
    return np.array([int(h[i:i+2],16) for i in (0,2,4)] + [a], dtype=np.uint8)

STONE1=rgba('#b8aa92'); STONE2=rgba('#c7b89f'); STONE3=rgba('#a99b84')
PLASTER=rgba('#f3f0eb'); TRIM=rgba('#7b1d2e'); RAIL=rgba('#dddddd')
ROOF=rgba('#3d3d3f'); FACE=rgba('#f7f5f0'); BLACK=rgba('#222222')
BASE=rgba('#b99e84'); GREEN=rgba('#5b6f38'); GOLD=rgba('#b98739'); LIGHT=rgba('#f1d99b'); WHITE=rgba('#f5f1ea')

scene = trimesh.Scene()
generated_meshes=[]
logo_geoms=[]
name_counter=0

def add(mesh, name=None, color=None):
    global name_counter
    if color is not None:
        mesh.visual.vertex_colors = np.tile(color, (len(mesh.vertices),1))
    if name is None:
        name=f'obj_{name_counter}'; name_counter+=1
    scene.add_geometry(mesh, node_name=name)
    generated_meshes.append(mesh)
    return mesh

def box(ext, pos, color, name=None):
    m=trimesh.creation.box(ext)
    m.apply_translation(pos)
    return add(m,name,color)

def cyl(r,h,pos,color,sections=16,name=None):
    m=trimesh.creation.cylinder(radius=r,height=h,sections=sections)
    m.apply_translation(pos)
    return add(m,name,color)

def tapered_prism(cx, cz, y0, y1, bottom, top, color, name=None):
    bx,bz=bottom; tx,tz=top
    verts=[]
    for y,sx,sz in [(y0,bx,bz),(y1,tx,tz)]:
        verts.extend([
            [cx-sx/2,y,cz-sz/2],[cx+sx/2,y,cz-sz/2],
            [cx+sx/2,y,cz+sz/2],[cx-sx/2,y,cz+sz/2],
        ])
    faces=[[0,1,2],[0,2,3],[4,6,5],[4,7,6],[0,4,5],[0,5,1],[1,5,6],[1,6,2],[2,6,7],[2,7,3],[3,7,4],[3,4,0]]
    m=trimesh.Trimesh(np.array(verts,float), np.array(faces,int), process=True)
    return add(m,name,color)

# Base
box((5.4,0.16,5.4),(0,0.08,0),BASE,'base')
box((5.5,0.06,5.5),(0,0.03,0),TRIM,'base_red_trim')
for x in (-2.0,2.0):
    for z in (-2.0,2.0):
        s=trimesh.creation.icosphere(subdivisions=1,radius=0.28)
        s.apply_scale((1.5,0.55,1.1)); s.apply_translation((x,0.28,z)); add(s,color=GREEN)

# Pillars
pillar_centers=[(-1.55,-1.55),(1.55,-1.55),(-1.55,1.55),(1.55,1.55)]
for i,(x,z) in enumerate(pillar_centers):
    tapered_prism(x,z,0.16,8.48,(0.72,0.72),(0.46,0.46),STONE1,f'pillar_{i}')

stone_colors=[STONE1,STONE2,STONE3]
rows=13
for pi,(cx,cz) in enumerate(pillar_centers):
    outward_x = -1 if cx<0 else 1
    outward_z = -1 if cz<0 else 1
    for face_axis in ('x','z'):
        for r in range(rows):
            y=0.55+r*0.57
            for c in range(2):
                w=0.30 if (r+c)%2==0 else 0.26
                h=0.22+0.02*((r+c)%3)
                d=0.035
                off=(-0.18 if c==0 else 0.18) + (0.03 if r%2 else -0.03)
                color=stone_colors[(r+c+pi)%len(stone_colors)]
                if face_axis=='x':
                    x=cx + outward_x*(0.34 - r*0.008)
                    z=cz+off
                    box((d,h,w),(x,y,z),color)
                else:
                    x=cx+off
                    z=cz + outward_z*(0.34 - r*0.008)
                    box((w,h,d),(x,y,z),color)

# Platforms and body
box((2.38,0.12,2.38),(0,1.72,0),PLASTER,'platform_low')
box((2.48,0.08,2.48),(0,1.64,0),TRIM,'platform_low_trim')
box((2.38,0.12,2.38),(0,3.45,0),PLASTER,'platform_mid')
box((2.48,0.08,2.48),(0,3.37,0),TRIM,'platform_mid_trim')

box((2.10,1.70,2.10),(0,4.28,0),PLASTER,'body_lower')
box((2.22,0.07,2.22),(0,3.43,0),TRIM,'body_lower_trim')
box((2.22,0.07,2.22),(0,5.13,0),TRIM,'body_mid_trim')
box((2.10,2.05,2.10),(0,6.18,0),PLASTER,'body_clock')
box((2.22,0.07,2.22),(0,7.21,0),TRIM,'body_clock_trim')

# Rails

def rail_front_back(y0,z,width=1.72,height=0.72):
    box((width,0.045,0.035),(0,y0,z),RAIL)
    box((width,0.045,0.035),(0,y0+height,z),RAIL)
    for i in range(10):
        x=-width/2+i*(width/9)
        box((0.028,height,0.028),(x,y0+height/2,z),RAIL)

def rail_side(y0,x,depth=1.72,height=0.72):
    box((0.035,0.045,depth),(x,y0,0),RAIL)
    box((0.035,0.045,depth),(x,y0+height,0),RAIL)
    for i in range(10):
        z=-depth/2+i*(depth/9)
        box((0.028,height,0.028),(x,y0+height/2,z),RAIL)
for y0 in (0.52,2.12):
    rail_front_back(y0,1.12); rail_front_back(y0,-1.12); rail_side(y0,1.12); rail_side(y0,-1.12)

# Clock faces

def clock_face(side):
    y=6.48
    if side=='+z':
        box((1.12,1.12,0.06),(0,y,1.08),STONE2); box((0.96,0.96,0.025),(0,y,1.115),FACE)
        basis=lambda u,v,w:(u,y+v,1.13+w)
    elif side=='-z':
        box((1.12,1.12,0.06),(0,y,-1.08),STONE2); box((0.96,0.96,0.025),(0,y,-1.115),FACE)
        basis=lambda u,v,w:(-u,y+v,-1.13-w)
    elif side=='+x':
        box((0.06,1.12,1.12),(1.08,y,0),STONE2); box((0.025,0.96,0.96),(1.115,y,0),FACE)
        basis=lambda u,v,w:(1.13+w,y+v,-u)
    else:
        box((0.06,1.12,1.12),(-1.08,y,0),STONE2); box((0.025,0.96,0.96),(-1.115,y,0),FACE)
        basis=lambda u,v,w:(-1.13-w,y+v,u)
    for i in range(12):
        ang=i*2*math.pi/12; u=math.sin(ang)*0.35; v=math.cos(ang)*0.35
        if side in ('+z','-z'):
            m=trimesh.creation.box((0.028,0.12,0.018)); m.apply_translation(basis(u,v,0)); m.apply_transform(trimesh.transformations.rotation_matrix(-ang,[0,0,1],point=basis(u,v,0)))
        else:
            m=trimesh.creation.box((0.018,0.12,0.028)); m.apply_translation(basis(u,v,0)); m.apply_transform(trimesh.transformations.rotation_matrix(-ang,[1,0,0],point=basis(u,v,0)))
        add(m,color=BLACK)
    for length,thick,ang in [(0.31,0.035,math.radians(4)),(0.23,0.027,math.radians(-58))]:
        if side in ('+z','-z'):
            h=trimesh.creation.box((thick,length,0.025)); h.apply_translation(basis(0,length*0.18,0.012)); h.apply_transform(trimesh.transformations.rotation_matrix(ang,[0,0,1],point=basis(0,0,0.012)))
        else:
            h=trimesh.creation.box((0.025,length,thick)); h.apply_translation(basis(0,length*0.18,0.012)); h.apply_transform(trimesh.transformations.rotation_matrix(ang,[1,0,0],point=basis(0,0,0.012)))
        add(h,color=BLACK)
for side in ('+z','-z','+x','-x'): clock_face(side)

# Top section, more like original: square canopy, symmetric, with white scalloped trim
box((2.28,0.08,2.28),(0,7.27,0),TRIM,'cupola_base')
for x in (-0.90,0.90):
    for z in (-0.90,0.90):
        box((0.055,0.80,0.055),(x,7.70,z),RAIL)
# top red perimeter just under canopy
for z in (-0.99,0.99): box((1.95,0.05,0.05),(0,7.56,z),TRIM)
for x in (-0.99,0.99): box((0.05,0.05,1.95),(x,7.56,0),TRIM)
# dark flat canopy slab
box((2.12,0.08,2.12),(0,8.02,0),ROOF,'canopy_slab')
# shallow hipped roof centered above slab
# use four low triangular prisms approximated by frustum
verts = np.array([
    [-0.95,8.06,-0.95],[0.95,8.06,-0.95],[0.95,8.06,0.95],[-0.95,8.06,0.95],
    [-0.45,8.42,-0.45],[0.45,8.42,-0.45],[0.45,8.42,0.45],[-0.45,8.42,0.45]
], float)
faces = np.array([[0,1,2],[0,2,3],[4,6,5],[4,7,6],[0,4,5],[0,5,1],[1,5,6],[1,6,2],[2,6,7],[2,7,3],[3,7,4],[3,4,0]])
roof = trimesh.Trimesh(verts, faces, process=True)
add(roof,'hip_roof',ROOF)
# white scalloped trim on all four sides
for side in ('front','back','left','right'):
    coords=[]
    if side in ('front','back'):
        z = 1.02 if side=='front' else -1.02
        for x in np.linspace(-0.82,0.82,8):
            coords.append((x,7.92,z))
    else:
        x = 1.02 if side=='right' else -1.02
        for z in np.linspace(-0.82,0.82,8):
            coords.append((x,7.92,z))
    for i,(x,y,z) in enumerate(coords):
        s=trimesh.creation.icosphere(subdivisions=1, radius=0.075)
        s.apply_scale((1.0,0.55,1.0)); s.apply_translation((x,y,z)); add(s,color=WHITE)
# small central finial
cyl(0.032,0.18,(0,8.56,0),BLACK,14,'finial')

# Lanterns should be separated from the tower, not connected
# Placed around the base with a small gap from the monument

def lantern(x,z):
    cyl(0.035,1.15,(x,0.72,z),BLACK,12)
    box((0.22,0.28,0.22),(x,1.35,z),BLACK)
    box((0.16,0.20,0.16),(x,1.35,z),LIGHT)
    r=trimesh.creation.cone(radius=0.18,height=0.18,sections=4)
    r.apply_transform(trimesh.transformations.rotation_matrix(math.pi/4,[0,1,0]))
    r.apply_translation((x,1.58,z)); add(r,color=BLACK)
for x,z in [(0,-2.25),(0,2.25),(-2.25,0),(2.25,0)]: lantern(x,z)

# Embed logo on all four clock faces
logo_path=Path('/mnt/data/mr_ar_logo_variantes_v2/assets/logo_mr_3d.glb')
if logo_path.exists():
    logo_scene=trimesh.load(logo_path,force='scene')
    scale=0.82/max(logo_scene.extents[0],1e-6)
    center=logo_scene.bounds.mean(axis=0)
    placements = [
        ((0, 4.27,  1.13), 0.0, 'front'),
        ((0, 4.27, -1.13), math.pi, 'back'),
        ((1.13, 4.27,  0), -math.pi/2, 'right'),
        ((-1.13,4.27,  0), math.pi/2, 'left'),
    ]
    for face_pos, angle_y, face_name in placements:
        for k,g in logo_scene.geometry.items():
            gg=g.copy()
            gg.apply_translation(-center)
            gg.apply_scale(scale)
            if angle_y != 0.0:
                gg.apply_transform(trimesh.transformations.rotation_matrix(angle_y,[0,1,0]))
            gg.apply_translation(face_pos)
            scene.add_geometry(gg,node_name=f'embedded_logo_{face_name}_{k}')
            logo_geoms.append(gg)

# Bitmap text
FONT5 = {
'2':["11110","00001","00001","11110","10000","10000","11111"],
'0':["01110","10001","10011","10101","11001","10001","01110"],
'6':["01110","10000","10000","11110","10001","10001","01110"],
'D':["11110","10001","10001","10001","10001","10001","11110"],
'O':["01110","10001","10001","10001","10001","10001","01110"],
'I':["11111","00100","00100","00100","00100","00100","11111"],
'N':["10001","11001","11001","10101","10011","10011","10001"],
'F':["11111","10000","10000","11110","10000","10000","10000"],
'R':["11110","10001","10001","11110","10100","10010","10001"],
'M':["10001","11011","10101","10101","10001","10001","10001"],
'E':["11111","10000","10000","11110","10000","10000","11111"],
' ':["00000"]*7,
}

def add_bitmap_text(text, target_width, center_y, front_z, color, depth=0.10, name='text'):
    text=text.upper(); cols = len(text)*5 + max(0,len(text)-1); cell = target_width / cols; total_h = 7*cell
    x0 = -target_width/2 + cell/2; y0 = center_y + total_h/2 - cell/2; idx=0
    for ci,ch in enumerate(text):
        pattern=FONT5.get(ch,FONT5[' '])
        for row,line in enumerate(pattern):
            for col,v in enumerate(line):
                if v=='1':
                    x = x0 + (ci*6 + col)*cell; y = y0 - row*cell
                    box((cell*0.82,cell*0.82,depth),(x,y,front_z),color,f'{name}_{idx}'); idx+=1

add_bitmap_text('2DO INFORME', 3.35, 10.95, 0.22, GOLD, depth=0.11, name='txt_informe')
add_bitmap_text('2026', 1.55, 10.18, 0.24, TRIM, depth=0.12, name='txt_2026')

# Normalize scale
minb,maxb=scene.bounds; cx=(minb[0]+maxb[0])/2; cz=(minb[2]+maxb[2])/2
for g in scene.geometry.values(): g.apply_translation((-cx,-minb[1],-cz))
minb,maxb=scene.bounds; height=maxb[1]-minb[1]; S=2.35/height
for g in scene.geometry.values(): g.apply_scale(S)
minb,maxb=scene.bounds
for g in scene.geometry.values(): g.apply_translation((0,-minb[1],0))

# Export and embed animation so it also rotates in AR
final_scene=trimesh.Scene()
combined=trimesh.util.concatenate(generated_meshes)
final_scene.add_geometry(combined,node_name='reloj_monumento')
for i,gg in enumerate(logo_geoms): final_scene.add_geometry(gg,node_name=f'logo_{i}')
export = final_scene.export(file_type='gltf')
gltf = json.loads(export['model.gltf'].decode('utf-8'))
combined_bin = bytearray(); offsets=[]
for i,b in enumerate(gltf['buffers']):
    blob = export[b['uri']]
    while len(combined_bin)%4: combined_bin += b'\x00'
    offsets.append(len(combined_bin)); combined_bin += blob
for bv in gltf['bufferViews']:
    bi=bv.get('buffer',0); bv['byteOffset']=offsets[bi]+bv.get('byteOffset',0); bv['buffer']=0
while len(combined_bin)%4: combined_bin += b'\x00'
time_offset=len(combined_bin)
TIMES=np.array([0.,6.,12.,18.,24.],dtype=np.float32); combined_bin += TIMES.tobytes()
while len(combined_bin)%4: combined_bin += b'\x00'
rot_offset=len(combined_bin)
ROTS=np.array([[0.,0.,0.,1.],[0., math.sin(math.radians(45)),0.,math.cos(math.radians(45))],[0.,1.,0.,0.],[0., math.sin(math.radians(135)),0.,math.cos(math.radians(135))],[0.,0.,0.,-1.]],dtype=np.float32)
combined_bin += ROTS.tobytes()
idx_bv_time=len(gltf['bufferViews']); gltf['bufferViews'].append({'buffer':0,'byteOffset':time_offset,'byteLength':TIMES.nbytes})
idx_bv_rot=len(gltf['bufferViews']); gltf['bufferViews'].append({'buffer':0,'byteOffset':rot_offset,'byteLength':ROTS.nbytes})
idx_acc_time=len(gltf['accessors']); gltf['accessors'].append({'bufferView':idx_bv_time,'componentType':5126,'count':len(TIMES),'type':'SCALAR','min':[float(TIMES.min())],'max':[float(TIMES.max())]})
idx_acc_rot=len(gltf['accessors']); gltf['accessors'].append({'bufferView':idx_bv_rot,'componentType':5126,'count':len(ROTS),'type':'VEC4'})
gltf['animations']=[{'name':'GiroLentoAR','samplers':[{'input':idx_acc_time,'output':idx_acc_rot,'interpolation':'LINEAR'}],'channels':[{'sampler':0,'target':{'node':0,'path':'rotation'}}]}]
for b in gltf.get('buffers',[]): b.pop('uri',None)
gltf['buffers']=[{'byteLength':len(combined_bin)}]
json_data=json.dumps(gltf,separators=(',',':')).encode('utf-8')
while len(json_data)%4: json_data += b' '
while len(combined_bin)%4: combined_bin += b'\x00'
out_path=ASSETS/'reloj_monumento_ar_v6.glb'
with open(out_path,'wb') as f:
    total=12+8+len(json_data)+8+len(combined_bin)
    f.write(struct.pack('<III',0x46546C67,2,total)); f.write(struct.pack('<I4s',len(json_data),b'JSON')); f.write(json_data); f.write(struct.pack('<I4s',len(combined_bin),b'BIN\x00')); f.write(combined_bin)
print('wrote', out_path, out_path.stat().st_size)

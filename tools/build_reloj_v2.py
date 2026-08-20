from pathlib import Path
import math
import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont
import cv2
from shapely.geometry import Polygon
from shapely.ops import unary_union

OUT = Path('/mnt/data/mr_ar_logo_variantes_v3')
ASSETS = OUT / 'assets'
ASSETS.mkdir(parents=True, exist_ok=True)

# ---------- colors ----------
def rgba(h, a=255):
    h=h.lstrip('#')
    return np.array([int(h[i:i+2],16) for i in (0,2,4)] + [a], dtype=np.uint8)

STONE1=rgba('#b8aa92'); STONE2=rgba('#c7b89f'); STONE3=rgba('#a99b84')
PLASTER=rgba('#f3f0eb'); TRIM=rgba('#7b1d2e'); RAIL=rgba('#dddddd')
ROOF=rgba('#3d3d3f'); FACE=rgba('#f7f5f0'); BLACK=rgba('#222222')
BASE=rgba('#b99e84'); GREEN=rgba('#5b6f38'); GOLD=rgba('#b98739'); WHITE=rgba('#ffffff')

scene = trimesh.Scene()
name_counter=0
generated_meshes=[]
logo_geoms=[]

def add(mesh, name=None, color=None):
    global name_counter
    if color is not None:
        try:
            mesh.visual.vertex_colors = np.tile(color, (len(mesh.vertices),1))
        except Exception:
            pass
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

def tapered_prism(cx, cz, y0, y1, bottom, top, color, name):
    # square frustum centered around (cx,cz), wider at base
    bx,bz=bottom; tx,tz=top
    verts=[]
    for y,sx,sz in [(y0,bx,bz),(y1,tx,tz)]:
        verts.extend([
            [cx-sx/2,y,cz-sz/2],[cx+sx/2,y,cz-sz/2],
            [cx+sx/2,y,cz+sz/2],[cx-sx/2,y,cz+sz/2],
        ])
    faces=[
        [0,1,2],[0,2,3],[4,6,5],[4,7,6],
        [0,4,5],[0,5,1],[1,5,6],[1,6,2],
        [2,6,7],[2,7,3],[3,7,4],[3,4,0]
    ]
    m=trimesh.Trimesh(np.array(verts,float),np.array(faces,int),process=True)
    return add(m,name,color)

# ---------- base ----------
box((5.4,0.16,5.4),(0,0.08,0),BASE,'base')
box((5.5,0.06,5.5),(0,0.03,0),TRIM,'base_red_trim')
# slight clipped-square effect with grass corners
for x in (-2.0,2.0):
    for z in (-2.0,2.0):
        s=trimesh.creation.icosphere(subdivisions=1,radius=0.28)
        s.apply_scale((1.5,0.55,1.1)); s.apply_translation((x,0.28,z)); add(s,color=GREEN)

# ---------- four perfectly symmetric tapered stone pillars ----------
pillar_centers=[(-1.55,-1.55),(1.55,-1.55),(-1.55,1.55),(1.55,1.55)]
for i,(x,z) in enumerate(pillar_centers):
    tapered_prism(x,z,0.16,8.35,(0.72,0.72),(0.46,0.46),STONE1,f'pillar_{i}')

# stone facing blocks on outward faces, mirrored symmetrically
stone_colors=[STONE1,STONE2,STONE3]
rows=13
for pi,(cx,cz) in enumerate(pillar_centers):
    outward_x = -1 if cx<0 else 1
    outward_z = -1 if cz<0 else 1
    for face_axis in ('x','z'):
        for r in range(rows):
            y=0.55+r*0.57
            # 2 stones per row, alternate offset
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

# ---------- platforms ----------
box((2.38,0.12,2.38),(0,1.72,0),PLASTER,'platform_low')
box((2.48,0.08,2.48),(0,1.64,0),TRIM,'platform_low_trim')
box((2.38,0.12,2.38),(0,3.45,0),PLASTER,'platform_mid')
box((2.48,0.08,2.48),(0,3.37,0),TRIM,'platform_mid_trim')

# ---------- centered white tower body ----------
box((2.10,1.70,2.10),(0,4.28,0),PLASTER,'body_lower')
box((2.22,0.07,2.22),(0,3.43,0),TRIM,'body_lower_trim')
box((2.22,0.07,2.22),(0,5.13,0),TRIM,'body_mid_trim')
box((2.10,2.05,2.10),(0,6.18,0),PLASTER,'body_clock')
box((2.22,0.07,2.22),(0,7.21,0),TRIM,'body_clock_trim')

# ---------- symmetric railings ----------
def rail_front_back(y0,z,width=1.72,height=0.72):
    box((width,0.045,0.035),(0,y0,z),RAIL)
    box((width,0.045,0.035),(0,y0+height,z),RAIL)
    n=10
    for i in range(n):
        x=-width/2+i*(width/(n-1))
        box((0.028,height,0.028),(x,y0+height/2,z),RAIL)

def rail_side(y0,x,depth=1.72,height=0.72):
    box((0.035,0.045,depth),(x,y0,0),RAIL)
    box((0.035,0.045,depth),(x,y0+height,0),RAIL)
    n=10
    for i in range(n):
        z=-depth/2+i*(depth/(n-1))
        box((0.028,height,0.028),(x,y0+height/2,z),RAIL)

for y0 in (0.52,2.12):
    rail_front_back(y0,1.12); rail_front_back(y0,-1.12); rail_side(y0,1.12); rail_side(y0,-1.12)

# ---------- clock faces, four sides ----------
def clock_face(side):
    # side: +z, -z, +x, -x
    y=6.48; face_size=0.96; depth=0.035
    # border + face as shallow boxes, then marks/hands as raised boxes
    if side=='+z':
        box((1.12,1.12,0.06),(0,y,1.08),STONE2)
        box((0.96,0.96,0.025),(0,y,1.115),FACE)
        basis=lambda u,v,w:(u,y+v,1.13+w)
        mark_ext=lambda h:(0.028,h,0.018)
        hand_ext=lambda w,h:(w,h,0.02)
        rot_axis='z'
    elif side=='-z':
        box((1.12,1.12,0.06),(0,y,-1.08),STONE2)
        box((0.96,0.96,0.025),(0,y,-1.115),FACE)
        basis=lambda u,v,w:(-u,y+v,-1.13-w)
        mark_ext=lambda h:(0.028,h,0.018)
        hand_ext=lambda w,h:(w,h,0.02)
        rot_axis='z'
    elif side=='+x':
        box((0.06,1.12,1.12),(1.08,y,0),STONE2)
        box((0.025,0.96,0.96),(1.115,y,0),FACE)
        basis=lambda u,v,w:(1.13+w,y+v,-u)
        mark_ext=lambda h:(0.018,h,0.028)
        hand_ext=lambda w,h:(0.02,h,w)
        rot_axis='y'
    else:
        box((0.06,1.12,1.12),(-1.08,y,0),STONE2)
        box((0.025,0.96,0.96),(-1.115,y,0),FACE)
        basis=lambda u,v,w:(-1.13-w,y+v,u)
        mark_ext=lambda h:(0.018,h,0.028)
        hand_ext=lambda w,h:(0.02,h,w)
        rot_axis='y'
    # hour marks
    for i in range(12):
        ang=i*2*math.pi/12
        u=math.sin(ang)*0.35; v=math.cos(ang)*0.35
        m=trimesh.creation.box(mark_ext(0.12))
        m.apply_translation(basis(u,v,0))
        # rotate in face plane
        if side in ('+z','-z'):
            m.apply_transform(trimesh.transformations.rotation_matrix(-ang,[0,0,1],point=basis(u,v,0)))
        else:
            m.apply_transform(trimesh.transformations.rotation_matrix(-ang,[1,0,0],point=basis(u,v,0)))
        add(m,color=BLACK)
    # hands: 12:00-ish and 10 minutes
    for length,thick,ang in [(0.31,0.035,math.radians(4)),(0.23,0.027,math.radians(-58))]:
        # Create centered then translate slightly upward in local face Y
        if side in ('+z','-z'):
            h=trimesh.creation.box((thick,length,0.025))
        else:
            h=trimesh.creation.box((0.025,length,thick))
        pos=basis(0,length*0.18,0.012)
        h.apply_translation(pos)
        if side in ('+z','-z'):
            h.apply_transform(trimesh.transformations.rotation_matrix(ang,[0,0,1],point=basis(0,0,0.012)))
        else:
            h.apply_transform(trimesh.transformations.rotation_matrix(ang,[1,0,0],point=basis(0,0,0.012)))
        add(h,color=BLACK)

for side in ('+z','-z','+x','-x'):
    clock_face(side)

# ---------- top open cupola ----------
box((2.28,0.08,2.28),(0,7.27,0),TRIM,'cupola_base')
for x in (-0.92,0.92):
    for z in (-0.92,0.92):
        box((0.055,0.72,0.055),(x,7.68,z),RAIL)
# rail band around cupola
for z in (-0.99,0.99):
    box((1.85,0.045,0.04),(0,7.48,z),TRIM)
for x in (-0.99,0.99):
    box((0.04,0.045,1.85),(x,7.48,0),TRIM)
# roof
roof=trimesh.creation.cone(radius=1.46,height=0.78,sections=4)
roof.apply_transform(trimesh.transformations.rotation_matrix(math.pi/4,[0,1,0]))
roof.apply_translation((0,8.30,0)); add(roof,'roof',ROOF)
cyl(0.055,0.24,(0,8.78,0),ROOF,18,'finial')

# ---------- symmetric lanterns around base ----------
def lantern(x,z):
    # post
    cyl(0.035,1.15,(x,0.72,z),BLACK,12)
    # cap / lamp box
    box((0.22,0.28,0.22),(x,1.35,z),BLACK)
    box((0.16,0.20,0.16),(x,1.35,z),rgba('#f1d99b'))
    roof=trimesh.creation.cone(radius=0.18,height=0.18,sections=4)
    roof.apply_transform(trimesh.transformations.rotation_matrix(math.pi/4,[0,1,0]))
    roof.apply_translation((x,1.58,z)); add(roof,color=BLACK)
for x,z in [(0,-2.1),(0,2.1),(-2.1,0),(2.1,0)]: lantern(x,z)

# ---------- embed existing MR logo on front face ----------
logo_path=Path('/mnt/data/mr_ar_logo_variantes_v2/assets/logo_mr_3d.glb')
if logo_path.exists():
    logo_scene=trimesh.load(logo_path,force='scene')
    # scale to 0.82 m width in construction units relative to tower
    scale=0.82/max(logo_scene.extents[0],1e-6)
    # center logo geometry on its own bounds then place on front white panel
    center=logo_scene.bounds.mean(axis=0)
    for k,g in logo_scene.geometry.items():
        gg=g.copy()
        gg.apply_translation(-center)
        gg.apply_scale(scale)
        gg.apply_translation((0,4.27,1.075+0.055))
        scene.add_geometry(gg,node_name=f'embedded_logo_{k}')
        logo_geoms.append(gg)

# ---------- floating 3D bitmap text ----------
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
    text=text.upper()
    cols = len(text)*5 + max(0,len(text)-1)
    cell = target_width / cols
    total_h = 7*cell
    x0 = -target_width/2 + cell/2
    y0 = center_y + total_h/2 - cell/2
    idx=0
    for ci,ch in enumerate(text):
        pattern=FONT5.get(ch,FONT5[' '])
        for row,line in enumerate(pattern):
            for col,v in enumerate(line):
                if v=='1':
                    x = x0 + (ci*6 + col)*cell
                    y = y0 - row*cell
                    box((cell*0.82,cell*0.82,depth),(x,y,front_z),color,f'{name}_{idx}')
                    idx+=1

# stacked floating title; all geometry is symmetric around x=0
add_bitmap_text('2DO INFORME', 3.35, 10.25, 0.22, GOLD, depth=0.11, name='txt_informe')
add_bitmap_text('2026', 1.55, 9.62, 0.24, TRIM, depth=0.12, name='txt_2026')

# ---------- global center/scale for AR ----------
# Keep x/z centered, floor y=0, total height including text ~2.25 m
minb,maxb=scene.bounds
# center x/z only
cx=(minb[0]+maxb[0])/2; cz=(minb[2]+maxb[2])/2
for g in scene.geometry.values():
    g.apply_translation((-cx,-minb[1],-cz))
minb,maxb=scene.bounds
height=maxb[1]-minb[1]
S=2.25/height
for g in scene.geometry.values():
    g.apply_scale(S)
# floor again
minb,maxb=scene.bounds
for g in scene.geometry.values():
    g.apply_translation((0,-minb[1],0))

# export optimized scene: merge all generated geometry into one vertex-colored mesh
final_scene=trimesh.Scene()
combined=trimesh.util.concatenate(generated_meshes)
final_scene.add_geometry(combined,node_name='reloj_monumento')
for i,gg in enumerate(logo_geoms):
    final_scene.add_geometry(gg,node_name=f'logo_{i}')
out=ASSETS/'reloj_monumento_ar_v2.glb'
out.write_bytes(final_scene.export(file_type='glb'))
print('wrote',out, out.stat().st_size)
print('bounds',final_scene.bounds,'extents',final_scene.extents,'geoms',len(final_scene.geometry))

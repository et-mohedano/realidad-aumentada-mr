
"""Construye V8 a partir del GLB V7.

Uso:
  python build_reloj_v8.py --src ../assets/reloj_monumento_ar_v7.glb --out ../assets/reloj_monumento_ar_v8.glb

Requiere: trimesh, numpy.
"""
from pathlib import Path
import argparse, json, math, struct, tempfile
import numpy as np
import trimesh

BLACK=np.array([34,34,34,255],dtype=np.uint8)

def paint(m,c=BLACK):
    m.visual.vertex_colors=np.tile(c,(len(m.vertices),1)); return m

def face_transform(side, center):
    # Local axes: x = right as seen from outside, y = up, z = outward normal.
    if side == '+z':
        ux=np.array([1.,0.,0.]); vy=np.array([0.,1.,0.]); wz=np.array([0.,0.,1.])
    elif side == '-z':
        ux=np.array([-1.,0.,0.]); vy=np.array([0.,1.,0.]); wz=np.array([0.,0.,-1.])
    elif side == '+x':
        ux=np.array([0.,0.,-1.]); vy=np.array([0.,1.,0.]); wz=np.array([1.,0.,0.])
    elif side == '-x':
        ux=np.array([0.,0.,1.]); vy=np.array([0.,1.,0.]); wz=np.array([-1.,0.,0.])
    else:
        raise ValueError(side)
    T=np.eye(4)
    T[:3,0]=ux; T[:3,1]=vy; T[:3,2]=wz; T[:3,3]=center
    return T

def local_box(extents, center_local=(0,0,0), rot=0.0, color=BLACK):
    m=trimesh.creation.box(extents)
    if rot:
        m.apply_transform(trimesh.transformations.rotation_matrix(rot,[0,0,1]))
    m.apply_translation(center_local)
    return paint(m,color)

def new_clock_features():
    pieces=[]
    centers = {
        '+z': np.array([0.0, 1.369,  0.241]),
        '-z': np.array([0.0, 1.369, -0.241]),
        '+x': np.array([0.241,1.369,  0.0]),
        '-x': np.array([-0.241,1.369, 0.0]),
    }
    tick_radius = 0.074
    tick_depth = 0.0046
    tick_w = 0.0062
    tick_h = 0.025
    # Chosen to keep the same "circular" appearance on all four faces.
    minute_len, minute_thick, minute_ang = 0.066, 0.0115, math.radians(4)
    hour_len, hour_thick, hour_ang = 0.044, 0.0085, math.radians(-58)
    hub_size = 0.007

    for side, center in centers.items():
        T=face_transform(side, center)
        # 12 hour markers arranged circularly
        for i in range(12):
            ang=i*2*math.pi/12
            u=math.sin(ang)*tick_radius
            v=math.cos(ang)*tick_radius
            tick = local_box((tick_w,tick_h,tick_depth), center_local=(u,v,0), rot=-ang)
            tick.apply_transform(T)
            pieces.append(tick)
        # Minute hand
        minute = local_box((minute_thick,minute_len,tick_depth), center_local=(0, minute_len*0.18, 0.001), rot=minute_ang)
        minute.apply_transform(T)
        pieces.append(minute)
        # Hour hand
        hour = local_box((hour_thick,hour_len,tick_depth), center_local=(0, hour_len*0.18, 0.0014), rot=hour_ang)
        hour.apply_transform(T)
        pieces.append(hour)
        # Small center hub
        hub = local_box((hub_size,hub_size,tick_depth), center_local=(0,0,0.0018))
        hub.apply_transform(T)
        pieces.append(hub)
    return pieces

def is_old_clock_part(p):
    c=np.array(p.centroid); b=np.array(p.bounds); ext=b[1]-b[0]
    if not (1.29 < c[1] < 1.46):
        return False
    if ext.max() > 0.09:
        return False
    cols=np.asarray(p.visual.face_colors)
    rgb=np.mean(cols[:,:3],axis=0)
    if rgb.max() > 70:
        return False
    on_z = (abs(abs(c[2])-0.239) < 0.03 and abs(c[0]) < 0.10)
    on_x = (abs(abs(c[0])-0.239) < 0.03 and abs(c[2]) < 0.10)
    return on_z or on_x

def edit_geometry(src: Path, tmp_out: Path):
    scene=trimesh.load(src,force='scene')
    g=scene.geometry['geometry_0']
    parts=g.split(only_watertight=False)
    cleaned=[p for p in parts if not is_old_clock_part(p)]
    removed=len(parts)-len(cleaned)
    if removed < 40:
        raise RuntimeError(f'Se detectaron muy pocas piezas del reloj para sustituir: {removed}')
    cleaned.extend(new_clock_features())
    newg=trimesh.util.concatenate(cleaned); newg.metadata.update(g.metadata)
    scene.geometry['geometry_0']=newg
    scene.export(tmp_out)


def inject_animation(src: Path, out: Path):
    raw=src.read_bytes(); magic,version,total=struct.unpack_from('<III',raw,0)
    if magic!=0x46546C67 or version!=2: raise ValueError('Se esperaba GLB v2')
    pos=12; json_blob=None; bin_blob=None
    while pos<len(raw):
        ln,typ=struct.unpack_from('<I4s',raw,pos); pos+=8
        blob=bytearray(raw[pos:pos+ln]); pos+=ln
        if typ==b'JSON': json_blob=blob
        elif typ==b'BIN\x00': bin_blob=blob
    if json_blob is None or bin_blob is None: raise ValueError('GLB incompleto')
    gltf=json.loads(bytes(json_blob).decode('utf-8').rstrip(' \x00'))
    gltf['animations']=[a for a in gltf.get('animations',[]) if a.get('name')!='GiroLentoAR']

    while len(bin_blob)%4: bin_blob+=b'\x00'
    time_offset=len(bin_blob)
    times=np.array([0.,6.,12.,18.,24.],dtype=np.float32); bin_blob+=times.tobytes()
    while len(bin_blob)%4: bin_blob+=b'\x00'
    rot_offset=len(bin_blob)
    rots=np.array([
        [0.,0.,0.,1.],
        [0.,math.sin(math.radians(45)),0.,math.cos(math.radians(45))],
        [0.,1.,0.,0.],
        [0.,math.sin(math.radians(135)),0.,math.cos(math.radians(135))],
        [0.,0.,0.,-1.]
    ],dtype=np.float32); bin_blob+=rots.tobytes()
    while len(bin_blob)%4: bin_blob+=b'\x00'

    bvs=gltf.setdefault('bufferViews',[]); accs=gltf.setdefault('accessors',[])
    bv_t=len(bvs); bvs.append({'buffer':0,'byteOffset':time_offset,'byteLength':times.nbytes})
    bv_r=len(bvs); bvs.append({'buffer':0,'byteOffset':rot_offset,'byteLength':rots.nbytes})
    ac_t=len(accs); accs.append({'bufferView':bv_t,'componentType':5126,'count':len(times),'type':'SCALAR','min':[0.0],'max':[24.0]})
    ac_r=len(accs); accs.append({'bufferView':bv_r,'componentType':5126,'count':len(rots),'type':'VEC4'})
    gltf['animations'].append({'name':'GiroLentoAR','samplers':[{'input':ac_t,'output':ac_r,'interpolation':'LINEAR'}], 'channels':[{'sampler':0,'target':{'node':0,'path':'rotation'}}]})
    gltf['buffers'][0]['byteLength']=len(bin_blob); gltf['buffers'][0].pop('uri',None)

    jb=json.dumps(gltf,separators=(',',':')).encode('utf-8')
    while len(jb)%4: jb+=b' '
    total=12+8+len(jb)+8+len(bin_blob)
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('wb') as f:
        f.write(struct.pack('<III',0x46546C67,2,total))
        f.write(struct.pack('<I4s',len(jb),b'JSON')); f.write(jb)
        f.write(struct.pack('<I4s',len(bin_blob),b'BIN\x00')); f.write(bin_blob)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--src',type=Path,required=True,help='GLB V7 de entrada')
    ap.add_argument('--out',type=Path,required=True,help='GLB V8 de salida')
    args=ap.parse_args()
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td)/'v8_geometry.glb'
        edit_geometry(args.src,tmp)
        inject_animation(tmp,args.out)
    print('wrote',args.out,args.out.stat().st_size)

if __name__=='__main__':
    main()

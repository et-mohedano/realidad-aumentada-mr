"""Construye V7 a partir del GLB V6.

Uso:
  python build_reloj_v7.py --src ../assets/reloj_monumento_ar_v6.glb --out ../assets/reloj_monumento_ar_v7.glb

Requiere: trimesh, numpy.
"""
from pathlib import Path
import argparse, json, math, os, struct, tempfile
import numpy as np
import trimesh

BLACK=np.array([34,34,34,255],dtype=np.uint8)

def paint(m,c=BLACK):
    m.visual.vertex_colors=np.tile(c,(len(m.vertices),1)); return m

def beam(p0,p1,t=.011):
    p0=np.array(p0,float); p1=np.array(p1,float); v=p1-p0; L=np.linalg.norm(v)
    m=trimesh.creation.box(extents=[L,t,t])
    T=trimesh.geometry.align_vectors([1,0,0],v/L); T[:3,3]=(p0+p1)/2
    m.apply_transform(T); return paint(m)

def edit_geometry(src: Path, tmp_out: Path):
    scene=trimesh.load(src,force='scene')
    # V6 stores the monument body in geometry_0.
    g=scene.geometry['geometry_0']
    parts=g.split(only_watertight=False)

    def is_old_lamp_part(p):
        c=p.centroid; b=p.bounds
        if b[0,1] < 0.14 or b[1,1] > 0.39: return False
        cardinal=((abs(c[0])<0.04 and abs(abs(c[2])-0.475)<0.035) or
                  (abs(c[2])<0.04 and abs(abs(c[0])-0.475)<0.035))
        if not cardinal: return False
        cols=np.asarray(p.visual.face_colors); rgb=np.mean(cols[:,:3],axis=0)
        return (rgb.max()<80) or (rgb[0]>200 and rgb[1]>180 and rgb[2]<190)

    old=[p for p in parts if is_old_lamp_part(p)]
    base=[p for p in parts if not is_old_lamp_part(p)]
    body=[p for p in old if p.bounds[0,1]>.24]
    template=[p.copy() for p in body if abs(p.centroid[0])<.04 and p.centroid[2]<-.43]
    if len(template)!=3:
        raise RuntimeError(f'No se encontró la plantilla esperada del farol V6 (partes={len(template)})')
    tmin=np.min(np.vstack([p.bounds[0] for p in template]),0)
    tmax=np.max(np.vstack([p.bounds[1] for p in template]),0)
    tc=(tmin+tmax)/2

    new=[]; pc=.3274; y=1.155
    for sx,sz in [(-1,-1),(1,-1),(-1,1),(1,1)]:
        # Montaje en la cara exterior izquierda/derecha de cada pilar.
        target=np.array([sx*0.486,y,sz*pc])
        ang=-sx*math.pi/2
        R=trimesh.transformations.rotation_matrix(ang,[0,1,0],point=tc)
        delta=target-tc
        for p in template:
            q=p.copy(); q.apply_transform(R); q.apply_translation(delta); new.append(q)

        xsurf=sx*(pc+0.0760); xinner=target[0]-sx*0.027; arm_y=y+.004
        new.append(beam([xsurf,arm_y,sz*pc],[xinner,arm_y,sz*pc],.012))
        new.append(beam([xsurf,arm_y-.055,sz*pc],[xinner,arm_y-.010,sz*pc],.008))

    newg=trimesh.util.concatenate(base+new); newg.metadata.update(g.metadata)
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
    ap.add_argument('--src',type=Path,required=True,help='GLB V6 de entrada')
    ap.add_argument('--out',type=Path,required=True,help='GLB V7 de salida')
    args=ap.parse_args()
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td)/'v7_geometry.glb'
        edit_geometry(args.src,tmp)
        inject_animation(tmp,args.out)
    print('wrote',args.out,args.out.stat().st_size)

if __name__=='__main__': main()

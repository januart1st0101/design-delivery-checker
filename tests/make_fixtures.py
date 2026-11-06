"""Original tiny spec-based fixtures. No downloaded assets or third-party scripts."""
import base64,json,struct,zlib
from pathlib import Path

def png():
    def chunk(k,v):return struct.pack('>I',len(v))+k+v+struct.pack('>I',zlib.crc32(k+v)&0xffffffff)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',1,1,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(b'\0\xff\0\0'))+chunk(b'IEND',b'')
def gltf():
    b=struct.pack('<9f3H',0,0,0,1,0,0,0,1,0,0,1,2)
    d={'asset':{'version':'2.0'},'buffers':[{'uri':'triangle.bin','byteLength':len(b)}],'bufferViews':[{'buffer':0,'byteOffset':0,'byteLength':36,'target':34962},{'buffer':0,'byteOffset':36,'byteLength':6,'target':34963}], 'accessors':[{'bufferView':0,'componentType':5126,'count':3,'type':'VEC3','min':[0,0,0],'max':[1,1,0]},{'bufferView':1,'componentType':5123,'count':3,'type':'SCALAR'}], 'meshes':[{'primitives':[{'attributes':{'POSITION':0},'indices':1,'material':0}]}],'nodes':[{'name':'群組','children':[1]},{'name':'三角形','mesh':0}],'scenes':[{'nodes':[0]}],'scene':0,'images':[{'uri':'貼圖.png'}],'textures':[{'source':0}],'materials':[{'pbrMetallicRoughness':{'baseColorTexture':{'index':0}}}]}
    return d,b

def glb(d,b):
    data=json.dumps(d,separators=(',',':'),ensure_ascii=False).encode();data+=b' '*((-len(data))%4);b+=b'\0'*((-len(b))%4)
    return struct.pack('<4sII',b'glTF',2,12+8+len(data)+8+len(b))+struct.pack('<II',len(data),0x4e4f534a)+data+struct.pack('<II',len(b),0x004e4942)+b

def put(root,name,data):
    f=root/name;f.parent.mkdir(parents=True,exist_ok=True)
    f.write_bytes(data if isinstance(data,bytes) else data.encode('utf-8'))

def build(root):
    root=Path(root)
    d,b=gltf();put(root,'normal3d/三角形.gltf',json.dumps(d,ensure_ascii=False));put(root,'normal3d/triangle.bin',b);put(root,'normal3d/貼圖.png',png())
    embedded=json.loads(json.dumps(d));embedded['buffers'][0].pop('uri');embedded['images']=[{'uri':'data:image/png;base64,'+base64.b64encode(png()).decode()}]
    put(root,'normal3d/embedded.glb',glb(embedded,b))
    viewimage=json.loads(json.dumps(embedded));viewimage['buffers'][0]['byteLength']=44+len(png());viewimage['bufferViews'].append({'buffer':0,'byteOffset':44,'byteLength':len(png())});viewimage['images']=[{'bufferView':2,'mimeType':'image/png'}]
    put(root,'normal3d/view-image.glb',glb(viewimage,b+b'\0\0'+png()))
    obj='mtllib sample.mtl\no sample\ng group one two\nv 0 0 0\nv 1 0 0\nv 0 1 0\nusemtl matte\nf 1 2 3\n'
    put(root,'normal3d/model.obj',obj);put(root,'normal3d/sample.mtl','newmtl matte\nKd 1 1 1\nmap_Kd -s 1 1 1 "貼圖.png"\n')
    put(root,'normal3d/no-material.obj','g a b\nv 0 0 0\nv 1 0 0\nv 0 1 0\nf -3 -2 -1\n')
    missing=json.loads(json.dumps(d));missing['images'][0]['uri']='不存在.png'
    put(root,'missing/缺素材.gltf',json.dumps(missing,ensure_ascii=False));put(root,'missing/triangle.bin',b)
    put(root,'missing/model.obj',obj);put(root,'missing/sample.mtl','newmtl matte\nmap_Kd missing.png\n')
    missingbin=json.loads(json.dumps(embedded));missingbin['images']=[{'uri':'missing.png'}];put(root,'missing/缺素材.glb',glb(missingbin,b))
    head='%YAML 1.1\n%TAG !u! tag:unity3d.com,2011:\n'
    for name,broken in [('unity-normal',False),('unity-issues',True)]:
        r=root/name
        put(r,'Packages/manifest.json','{"dependencies":{}}');put(r,'ProjectSettings/ProjectVersion.txt','m_EditorVersion: 2022.3.0f1\n')
        scene=head+'--- !u!1 &1\nGameObject:\n  m_Component: []\n  m_Name: Synthetic\n  m_EditorClassIdentifier: \n'
        scene+='  m_Builtin: {fileID: 10303, guid: 0000000000000000f000000000000000, type: 0}\n  m_Local: {fileID: 1}\n  m_Null: {fileID: 0}\n'
        scene+='  m_Material: {fileID: 2100000, guid: '+('b'*32 if broken else 'a'*32)+', type: 2}\n'
        if broken:scene+='  m_Shader: {fileID: 4800000, guid: '+('c'*32)+', type: 3}\n  m_Texture: {fileID: 2800000, guid: '+('d'*32)+', type: 3}\n'
        put(r,'Assets/Scene.unity',scene);put(r,'Assets/Scene.unity.meta','fileFormatVersion: 2\nguid: '+'1'*32+'\n')
        put(r,'Assets/Mat.mat',head+'--- !u!21 &2100000\nMaterial:\n  m_Name: Matte\n  m_Shader: {fileID: 46, guid: 0000000000000000f000000000000000, type: 0}\n')
        put(r,'Assets/Mat.mat.meta','fileFormatVersion: 2\nguid: '+'a'*32+'\n')
        if broken:
            put(r,'Assets/Duplicate.mat',head+'--- !u!21 &2100000\nMaterial:\n  m_Name: Duplicate\n');put(r,'Assets/Duplicate.mat.meta','fileFormatVersion: 2\nguid: '+'a'*32+'\n')
            put(r,'Assets/NoMeta.txt','source asset')
        put(r,'ProjectSettings/GraphicsSettings.asset',head+'--- !u!30 &1\nGraphicsSettings:\n  m_CustomRenderPipeline: {fileID: 0}\n')
    for version,ext in [(1,'psd'),(2,'psb')]:
        # Adobe header, empty color/resource/layer sections, raw planar 1x1 RGB.
        psd=struct.pack('>4sH6xHIIHH',b'8BPS',version,3,1,1,8,3)+struct.pack('>II',0,0)+(struct.pack('>I',0) if version==1 else struct.pack('>Q',0))+b'\0\0'+b'\x80\xa0\x90'
        put(root,'unverified/自製色塊.'+ext,psd)
    put(root,'unverified/README.txt','Real PSD/PSB generated from Adobe specification; native-layer parser is not implemented. No FBX/AI fixture is claimed.\n')
    return root
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);a=p.parse_args()
    if a.output.exists() and any(a.output.iterdir()):p.error('請使用全新／空資料夾，避免覆寫')
    build(a.output)

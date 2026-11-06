"""Partial glTF 2.0/GLB structural, reference and uncompressed geometry checker."""
import json,struct,math
from collections import Counter
from .common import LimitError
SIZE={5120:1,5121:1,5122:2,5123:2,5125:4,5126:4}
DIMS={'SCALAR':(1,1),'VEC2':(1,2),'VEC3':(1,3),'VEC4':(1,4),'MAT2':(2,2),'MAT3':(3,3),'MAT4':(4,4)}
def integer(x,minimum=0):
    if isinstance(x,bool) or not isinstance(x,int) or x<minimum:raise ValueError('integer')
    return x

def check(c,f,raw):
    def emit(sev,rule,evidence,ref=''):
        c.issue(sev,rule,f,ref,evidence,'該部分可能無法正確載入' if sev=='ERROR' else '未完全驗證', '確認匯出內容與對應格式規格')
    binary=None
    if raw.startswith(b'glTF'):
        if len(raw)<12:raise ValueError('GLB header')
        magic,version,total=struct.unpack_from('<4sII',raw)
        if version!=2:
            emit('NOT_CHECKED','GLB_VERSION','僅支援 GLB version 2');c.record(f,'GLB','未支援版本');return
        if total!=len(raw):raise ValueError('GLB length')
        chunks=[];offset=12
        while offset<len(raw):
            if offset+8>len(raw):raise ValueError('chunk header')
            length,kind=struct.unpack_from('<II',raw,offset);offset+=8
            if length%4 or offset+length>len(raw):raise ValueError('chunk bounds')
            chunks.append((kind,raw[offset:offset+length]));offset+=length
        if not chunks or chunks[0][0]!=0x4e4f534a:raise ValueError('JSON first')
        if len([1 for k,_ in chunks if k==0x4e4f534a])!=1 or len([1 for k,_ in chunks if k==0x004e4942])>1:raise ValueError('duplicate chunks')
        if any(k==0x004e4942 for k,_ in chunks):
            if len(chunks)<2 or chunks[1][0]!=0x004e4942:raise ValueError('BIN order')
            binary=chunks[1][1]
        if any(k not in (0x4e4f534a,0x004e4942) for k,_ in chunks):emit('NOT_CHECKED','GLB_CHUNK','未知 GLB chunk 未解析')
        doc=json.loads(chunks[0][1].decode('utf-8'))
        form='GLB'
    else:doc=json.loads(raw.decode('utf-8-sig'));form='glTF'
    if not isinstance(doc,dict) or not isinstance(doc.get('asset'),dict):raise ValueError('asset')
    if doc['asset'].get('version')!='2.0' or doc['asset'].get('minVersion','2.0')!='2.0':
        emit('NOT_CHECKED','GLTF_VERSION','僅實作 glTF 2.0');c.record(f,form,'未支援版本');return
    def arr(key):
        v=doc.get(key,[])
        if not isinstance(v,list) or any(not isinstance(x,dict) for x in v):raise ValueError('array of object')
        if len(v)>100000:raise LimitError('object count')
        return v
    buffers,views,accessors,meshes,nodes,scenes,materials,textures,images,samplers=[arr(k) for k in ('buffers','bufferViews','accessors','meshes','nodes','scenes','materials','textures','images','samplers')]
    def idx(seq,i,loc):
        integer(i)
        if i>=len(seq):emit('ERROR','GLTF_INDEX',loc+' 超出索引範圍',str(i));return None
        return seq[i]
    skin_items=arr('skins');camera_items=arr('cameras')
    compressed_views=any('extensions' in v for v in views)
    all_ext=set(doc.get('extensionsUsed',[]))|set(doc.get('extensionsRequired',[]))
    def visit(x):
        if isinstance(x,dict):
            ex=x.get('extensions',{})
            if isinstance(ex,dict):all_ext.update(ex.keys())
            for y in x.values():visit(y)
        elif isinstance(x,list):
            for y in x:visit(y)
    visit(doc)
    for ex in sorted(all_ext):emit('NOT_CHECKED','GLTF_EXTENSION','extension 無解碼／語意驗證：'+str(ex))
    payload=[]
    for n,b in enumerate(buffers):
        length=integer(b['byteLength'],1)
        data=c.resource(f,b['uri']) if 'uri' in b else (binary if n==0 else None)
        if data is None:
            emit('NOT_CHECKED','BUFFER_UNAVAILABLE',f'buffer[{n}] 資料未取得')
        elif len(data)<length:emit('ERROR','BUFFER_SHORT',f'buffer[{n}] 宣告 {length} bytes，實際 {len(data)}')
        elif 'uri' not in b and len(data)>length+3:emit('ERROR','GLB_BIN_LENGTH','BIN padding 超過3 bytes')
        payload.append(data)
    vinfo=[]
    for n,v in enumerate(views):
        bi=integer(v['buffer']);off=integer(v.get('byteOffset',0));size=integer(v['byteLength'],1);b=idx(buffers,bi,f'bufferView[{n}].buffer')
        if b and off+size>b['byteLength']:emit('ERROR','VIEW_RANGE',f'bufferView[{n}] 超出宣告 buffer 範圍')
        stride=v.get('byteStride')
        if stride is not None and (integer(stride)<4 or stride>252 or stride%4):emit('ERROR','VIEW_STRIDE',f'bufferView[{n}] stride 無效')
        vinfo.append((bi,off,size,stride))
    def segment(vi,off,end):
        integer(vi);integer(off)
        if vi>=len(vinfo):emit('ERROR','GLTF_INDEX','bufferView 索引超限',str(vi));return None
        bi,start,size,_=vinfo[vi]
        if end>size:emit('ERROR','ACCESSOR_RANGE','accessor／sparse 超出 bufferView');return None
        if bi>=len(payload) or payload[bi] is None:return None
        b=payload[bi]
        if start+end>len(b):emit('ERROR','ACCESSOR_RANGE','accessor 超出實際 buffer');return None
        return b[start+off:start+end]
    infos=[]
    for n,a in enumerate(accessors):
        comp=a['componentType'];ct=integer(a['count'],1);kind=a['type'];off=integer(a.get('byteOffset',0))
        if ct>1000000:raise LimitError('accessor count')
        if comp not in SIZE or kind not in DIMS:raise ValueError('accessor type')
        cs=SIZE[comp];cols,rows=DIMS[kind];column=((rows*cs+3)//4*4 if cols>1 else rows*cs);size=column*(cols-1)+rows*cs
        blob=None;stride=column*cols
        if 'bufferView' in a:
            vi=integer(a['bufferView']);v=idx(views,vi,'accessor.bufferView')
            if v is not None:
                stride=v.get('byteStride',column*cols)
                if stride<column*cols or stride%cs or off%cs or (v.get('byteOffset',0)+off)%cs:emit('ERROR','ACCESSOR_ALIGNMENT',f'accessor[{n}] stride／對齊不符')
                blob=segment(vi,off,off+stride*(ct-1)+size)
        elif off:emit('ERROR','ACCESSOR_OFFSET','無 bufferView 的 accessor 不得指定 byteOffset')
        sparse={}
        if 'sparse' in a:
            sp=a['sparse'];sc=integer(sp['count'],1)
            if sc>ct:raise ValueError('sparse count')
            si=sp['indices'];sv=sp['values'];st=si['componentType']
            if st not in (5121,5123,5125):raise ValueError('sparse index')
            ib=segment(si['bufferView'],si.get('byteOffset',0),si.get('byteOffset',0)+sc*SIZE[st]);vb=segment(sv['bufferView'],sv.get('byteOffset',0),sv.get('byteOffset',0)+(sc-1)*column*cols+size)
            if ib is not None and vb is not None:
                fmt={5121:'B',5123:'H',5125:'I'}[st];last=-1
                for k in range(sc):
                    v=struct.unpack_from('<'+fmt,ib,k*SIZE[st])[0]
                    if v<=last or v>=ct:emit('ERROR','SPARSE_INDEX','sparse 索引未遞增或超出 accessor')
                    last=v;sparse[v]=vb[k*column*cols:k*column*cols+size]
            else:emit('NOT_CHECKED','SPARSE_UNAVAILABLE','sparse 資料不可用')
        infos.append((ct,comp,kind,blob,stride,sparse,'bufferView' in a))
    decoded_cache={};decode_work=0
    def values(ai,allowed,loc):
        nonlocal decode_work
        a=idx(accessors,ai,loc)
        if a is None:return None
        ct,comp,kind,blob,stride,sp,hasview=infos[ai]
        if (comp,kind) not in allowed:emit('ERROR','ACCESSOR_SEMANTIC',loc+' 型別不符');return None
        if blob is None and hasview:return None
        if ai in decoded_cache:return decoded_cache[ai]
        decode_work+=ct*DIMS[kind][1]
        if decode_work>2000000:raise LimitError('total decoded components')
        fmt={5121:'B',5123:'H',5125:'I',5126:'f'}[comp];nc=DIMS[kind][1]
        result=[struct.unpack_from('<'+fmt*nc,sp.get(k,blob[k*stride:k*stride+SIZE[comp]*nc] if blob is not None else bytes(SIZE[comp]*nc))) for k in range(ct)]
        decoded_cache[ai]=result
        return result
    checked_positions=set();index_max={}
    primitives=verts=triangles=decoded=0
    for mi,mesh in enumerate(meshes):
        if not isinstance(mesh.get('primitives'),list) or any(not isinstance(x,dict) for x in mesh['primitives']):raise ValueError('mesh primitives')
        for primitive in mesh['primitives']:
            primitives+=1
            if primitives>10000:raise LimitError('primitive count')
            attrs=primitive.get('attributes',{})
            if not isinstance(attrs,dict):raise ValueError('attributes')
            for name,ai in attrs.items():idx(accessors,ai,'primitive.attributes.'+name)
            for target in primitive.get('targets',[]):
                for name,ai in target.items():idx(accessors,ai,'morph target.'+name)
            if 'material' in primitive:idx(materials,primitive['material'],'primitive.material')
            compressed=bool(primitive.get('extensions')) or compressed_views
            geometry_ready=False
            pos=attrs.get('POSITION');nverts=None
            if pos is not None and idx(accessors,pos,'POSITION') is not None:
                nverts=accessors[pos]['count'];verts+=nverts
                if not compressed:
                    coords=values(pos,{(5126,'VEC3')},'POSITION')
                    if coords is not None:
                        geometry_ready=True
                        decoded+=len(coords)
                        if pos not in checked_positions:
                            checked_positions.add(pos)
                            if any(not math.isfinite(x) for v in coords for x in v):emit('ERROR','POSITION_NONFINITE','頂點含非有限浮點值')
                            for bound,fn in [('min',min),('max',max)]:
                                expect=accessors[pos].get(bound)
                                if not isinstance(expect,list) or len(expect)!=3:emit('ERROR','POSITION_BOUNDS','POSITION 缺少有效 min/max')
                                elif any(not math.isclose(expect[k],fn(v[k] for v in coords),rel_tol=1e-5,abs_tol=1e-6) for k in range(3)):emit('ERROR','POSITION_BOUNDS','POSITION min/max 與 buffer 不一致')
            mode=integer(primitive.get('mode',4))
            if mode>6:emit('ERROR','PRIMITIVE_MODE','primitive mode 超限')
            elements=nverts or 0
            if 'indices' in primitive:
                ai=primitive['indices'];a=idx(accessors,ai,'primitive.indices')
                if a is None:geometry_ready=False
                if a:
                    elements=a['count']
                    if not compressed:
                        iv=values(ai,{(5121,'SCALAR'),(5123,'SCALAR'),(5125,'SCALAR')},'indices')
                        if iv is not None and nverts is not None:
                            if ai not in index_max:index_max[ai]=max(v[0] for v in iv)
                            if index_max[ai]>=nverts:
                                geometry_ready=False
                                emit('ERROR','GEOMETRY_INDEX','頂點索引超出 POSITION 數量')
                        else:geometry_ready=False
            if not compressed and geometry_ready:
                if mode==4:
                    if elements%3:emit('ERROR','TRIANGLE_COUNT','TRIANGLES 數量不是3的倍數')
                    else:triangles+=elements//3
                elif mode in (5,6):triangles+=max(0,elements-2)
            elif compressed:emit('NOT_CHECKED','COMPRESSED_GEOMETRY','壓縮／extension 幾何未解碼，數量僅宣告值')
    # Core texture references, deliberately not arbitrary extension semantics.
    for t in textures:
        if 'source' in t:idx(images,t['source'],'texture.source')
        if 'sampler' in t:idx(samplers,t['sampler'],'texture.sampler')
    for mat in materials:
        pbr=mat.get('pbrMetallicRoughness',{})
        if not isinstance(pbr,dict):raise ValueError('pbr material')
        for obj in [pbr.get('baseColorTexture'),pbr.get('metallicRoughnessTexture'),mat.get('normalTexture'),mat.get('occlusionTexture'),mat.get('emissiveTexture')]:
            if obj is not None:idx(textures,obj['index'],'material texture')
    for n,img in enumerate(images):
        content=None
        if 'uri' in img and 'bufferView' in img:emit('ERROR','IMAGE_SOURCE','圖片同時有 uri 與 bufferView')
        if 'uri' in img:content=c.resource(f,img['uri'])
        elif 'bufferView' in img:
            vi=img['bufferView'];view=idx(views,vi,'image.bufferView')
            if view is not None:content=segment(vi,0,view['byteLength'])
            if 'mimeType' not in img:emit('ERROR','IMAGE_MIME','bufferView 圖片缺 mimeType')
        else:emit('ERROR','IMAGE_SOURCE','圖片沒有來源')
        if content is not None and not (content.startswith(b'\x89PNG\r\n\x1a\n') or content.startswith(b'\xff\xd8')):
            emit('NOT_CHECKED','IMAGE_ENCODING','非本版辨識 PNG/JPEG 檔頭，未解碼圖片')
    if images:emit('NOT_CHECKED','IMAGE_PIXELS','已查來源與檔頭，未解碼像素／色彩設定')
    names=Counter(n.get('name') for n in nodes if isinstance(n.get('name'),str) and n.get('name'))
    parents=[0]*len(nodes);edges=[]
    for n,node in enumerate(nodes):
        for child in node.get('children',[]):
            if idx(nodes,child,'node.children') is not None:parents[child]+=1;edges.append((n,child))
        if 'mesh' in node:idx(meshes,node['mesh'],'node.mesh')
        for key in ('skin','camera'):
            if key in node:idx(skin_items if key=='skin' else camera_items,node[key],'node.'+key)
    if any(x>1 for x in parents):emit('ERROR','NODE_PARENT','節點有多個父節點')
    incoming=parents[:];queue=[n for n,x in enumerate(incoming) if not x];adj={n:[] for n in range(len(nodes))}
    for a,b in edges:adj[a].append(b)
    seen=0
    while queue:
        n=queue.pop();seen+=1
        for child in adj[n]:
            incoming[child]-=1
            if not incoming[child]:queue.append(child)
    if seen<len(nodes):emit('ERROR','NODE_CYCLE','節點階層有循環')
    for scene in scenes:
        for n in scene.get('nodes',[]):idx(nodes,n,'scene.nodes')
    if 'scene' in doc:idx(scenes,doc['scene'],'default scene')
    emit('INFO','GLTF_UNITS','glTF 2.0 公尺、右手座標、+Y向上；不推測資產實際正面')
    emit('NOT_CHECKED','GLTF_SCOPE','非完整 Khronos Validator；動畫、skin語意、變換、渲染結果未驗證；空節點與重複名稱不判壞檔')
    c.record(f,form,'部分支援：核心結構／引用／未壓縮幾何',dict(declared_vertices=verts,decoded_positions=decoded,primitives=primitives,triangles_uncompressed=triangles,nodes=len(nodes),named_nodes=sum(names.values()),repeated_name_groups=sum(v>1 for v in names.values()),root_nodes=sum(v==0 for v in parents),materials=len(materials),images=len(images)))

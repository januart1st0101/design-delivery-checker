"""Wavefront subset; legal groups and material-free geometry remain valid."""
import math,shlex

def tokens(line):
    # Backslashes in Windows references are literal, never shell execution.
    lex=shlex.shlex(line,posix=True);lex.whitespace_split=True;lex.commenters='#';lex.escape=''
    return list(lex)

def material(c,f,data):
    names=set();current=None
    for n,line in enumerate(data.decode('utf-8-sig').splitlines(),1):
        t=tokens(line)
        if not t:continue
        if t[0]=='newmtl':
            if len(t)<2:raise ValueError('newmtl')
            current=' '.join(t[1:]);names.add(current)
        elif t[0].lower().startswith('map_') or t[0].lower() in ('bump','disp','decal','refl','norm'):
            i=1;unknown=False
            fixed={'-blendu':1,'-blendv':1,'-boost':1,'-mm':2,'-texres':1,'-clamp':1,'-bm':1,'-imfchan':1,'-type':1,'-cc':1}
            while i<len(t) and t[i].startswith('-'):
                opt=t[i];i+=1
                if opt in ('-o','-s','-t'):
                    count=0
                    while i<len(t) and count<3:
                        try:float(t[i])
                        except ValueError:break
                        i+=1;count+=1
                    if not count:raise ValueError('map option')
                elif opt in fixed:
                    i+=fixed[opt]
                else:unknown=True;break
            if unknown:
                c.issue('NOT_CHECKED','MTL_OPTION',f,evidence=f'第{n}行：未知 map option',impact='未可靠解析路徑',suggestion='確認該匯出器的MTL選項');continue
            if i>=len(t):raise ValueError('map path')
            c.resolve(f,' '.join(t[i:]))
    return names

def check(c,f,data):
    if f.suffix.lower()=='.mtl':
        names=material(c,f,data);c.record(f,'MTL','材質名／map引用子集',dict(materials=len(names)));return
    counts={'v':0,'vt':0,'vn':0};faces=groups=0;declared=set();used=set();libraries=False
    for n,line in enumerate(data.decode('utf-8-sig').splitlines(),1):
        t=tokens(line)
        if not t:continue
        op=t[0]
        if op in counts:
            minimum={'v':3,'vt':1,'vn':3}[op]
            if len(t)<minimum+1 or any(not math.isfinite(float(x)) for x in t[1:]):raise ValueError('coordinates')
            counts[op]+=1
        elif op=='f':
            if len(t)<4:raise ValueError('face')
            faces+=1
            for vertex in t[1:]:
                parts=vertex.split('/')
                if len(parts)>3 or not parts[0]:raise ValueError('face syntax')
                for val,kind in zip(parts,('v','vt','vn')):
                    if not val:continue
                    idx=int(val);total=counts[kind]
                    if not idx or idx>total or idx< -total:
                        c.issue('ERROR','OBJ_INDEX',f,val,f'第{n}行 {kind} 索引超限','幾何可能無法讀取','重新匯出或修正索引')
        elif op in ('g','o'):groups+=1
        elif op=='mtllib':
            libraries=True
            for raw in t[1:]:
                target=c.resolve(f,raw)
                if target:
                    try:declared.update(material(c,target,c.read(target)))
                    except (UnicodeError,ValueError):c.issue('ERROR','MTL_PARSE',target,evidence='材質檔解析失敗',impact='無法核對材質',suggestion='檢查MTL格式')
        elif op=='usemtl':
            if len(t)>1:used.add(' '.join(t[1:]))
        elif op in ('curv','curv2','surf','parm','trim','hole','scrv','sp','bmat','step'):
            c.issue('NOT_CHECKED','OBJ_FREEFORM',f,evidence=f'第{n}行：自由曲線／曲面未實作',impact='非網格幾何未驗證',suggestion='使用原軟體或另匯出網格')
        elif op not in ('s','l','p','vp','usemap','maplib','bevel','c_interp','d_interp','lod','shadow_obj','trace_obj','ctech','stech','end','con'):
            c.issue('NOT_CHECKED','OBJ_DIRECTIVE',f,evidence=f'第{n}行：未支援語句',impact='未驗證該語句',suggestion='確認匯出器格式')
    for name in sorted(used-declared):
        c.issue('WARNING','OBJ_MATERIAL_UNRESOLVED',f,name,'usemtl 未對上可讀的 newmtl','可能缺材質；非無材質群組錯誤','核對MTL引用與材質名')
    c.issue('NOT_CHECKED','OBJ_SCOPE',f,evidence='未驗證UV品質、曲面、退化／非流形拓樸、像素與渲染；OBJ單位／正面未定義',impact='非完整幾何品質保證',suggestion='依交付政策以原軟體確認；不可猜單位')
    c.record(f,'OBJ','頂點／face索引、MTL與map引用子集',dict(vertices=counts['v'],uvs=counts['vt'],normals=counts['vn'],faces=faces,group_object_declarations=groups))

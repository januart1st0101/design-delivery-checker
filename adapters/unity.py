"""Static Unity text serialization subset. Never imports or starts Unity."""
import json,re
from .common import LimitError
GUID=re.compile(r'^guid:\s*([0-9a-fA-F]{32})\s*$',re.M)
ANCHOR=re.compile(r'^--- !u!\d+ &(-?\d+)(?: stripped)?\s*$',re.M)
BUILTINS={'0000000000000000e000000000000000','0000000000000000f000000000000000'}

def scope(c,f):
    roots=[r for r in c.unity_roots if f.is_relative_to(r)]
    return max(roots,key=lambda x:len(x.parts)) if roots else c.root

def prepare(c):
    for f in c.paths:
        if f.suffix.lower()!='.meta':continue
        if f.is_symlink():c.index_incomplete=True;continue
        try:txt=c.text(f)
        except (OSError,UnicodeError,LimitError):
            c.index_incomplete=True
            c.issue('NOT_CHECKED','UNITY_META_UNREADABLE',f,evidence='meta索引未完整讀取',impact='不能把未索引GUID當確定遺失',suggestion='檢查範圍／讀取限制');continue
        gs=GUID.findall(txt)
        if len(gs)!=1:
            c.issue('ERROR','UNITY_META_GUID',f,evidence='meta 須有唯一的32位十六進位頂層guid',impact='GUID索引無法可靠建立',suggestion='由原專案備份確認meta；不要自動重建');continue
        g=gs[0].lower();asset=f.with_suffix('');c.guid.setdefault((scope(c,f),g),[]).append(asset)
        if not asset.exists():c.issue('WARNING','UNITY_ORPHAN_META',f,g,'meta 對應的資產／資料夾不存在','可能未完整交付','確認原始專案，不重建meta')
    for (_,guid),assets in c.guid.items():
        if len(assets)>1:
            for a in assets:c.issue('ERROR','UNITY_DUP_GUID',a,guid,'相同GUID對應：'+', '.join(c.rel(x) for x in assets),'Unity可能辨識成錯誤資產','人工確認正確meta來源；不可自動重建')
    for project in c.unity_roots:
        c.issue('INFO','UNITY_PROJECT',project,evidence='識別 Assets / Packages / ProjectSettings',impact='以文字序列化子集檢查',suggestion='保留meta與Packages資訊')
        manifest=project/'Packages/manifest.json'
        try:
            manifest_data=json.loads(c.text(manifest))
            if not isinstance(manifest_data,dict):raise ValueError('manifest root')
            dependencies=manifest_data.get('dependencies',{})
            if not isinstance(dependencies,dict):raise ValueError('manifest dependencies')
            if dependencies:
                c.packages_unknown.add(project)
                c.issue('NOT_CHECKED','UNITY_PACKAGE_CONTENT',manifest,evidence='宣告Package依賴；不下載或讀Library快取，僅索引交付包內meta',impact='未找到的GUID可能來自未隨附Package，不能一概判缺檔',suggestion='另提供允許檢查的完整Package內容或以Unity確認')
        except FileNotFoundError:c.issue('WARNING','UNITY_MANIFEST_MISSING',manifest,evidence='缺少manifest.json',impact='Package依賴不明',suggestion='確認交付Packages');c.packages_unknown.add(project)
        except (ValueError,UnicodeError,LimitError,OSError):c.issue('NOT_CHECKED','UNITY_MANIFEST_UNREADABLE',manifest,evidence='manifest無法解析',impact='Package依賴不明',suggestion='提供可讀manifest');c.packages_unknown.add(project)
        for f in c.paths:
            if f.is_relative_to(project/'Assets') and f.suffix!='.meta' and not f.is_symlink() and not f.with_name(f.name+'.meta').is_file():
                c.issue('WARNING','UNITY_META_MISSING',f,evidence='Assets內檔案未附meta',impact='GUID可能在重匯入時改變',suggestion='補回原始meta；不要自動產生')
        # Static policy: custom pipeline assignment alone cannot establish compatibility.
        for name in ('GraphicsSettings.asset','QualitySettings.asset'):
            f=project/'ProjectSettings'/name
            if f in c.paths:
                c.issue('NOT_CHECKED','UNITY_PIPELINE_COMPATIBILITY',f,evidence='僅有靜態設定；不推斷shader與渲染管線相容性',impact='無法保證材質呈現正常',suggestion='在原Unity版本檢查Graphics/Quality與實際渲染')

def check(c,f,data):
    if not data.startswith(b'%YAML'):
        c.record(f,'Unity serialized candidate','未支援二進位或未知序列化')
        c.issue('NOT_CHECKED','UNITY_BINARY',f,evidence='非可辨識Unity文字序列化；未掃二進位字串',impact='引用未驗證',suggestion='在原Unity中另存文字序列化副本後檢查');return
    txt=data.decode('utf-8-sig')
    if not txt.startswith('%YAML 1.1') or '%TAG !u! tag:unity3d.com,2011:' not in txt:raise ValueError('Unity YAML signature')
    anchors=ANCHOR.findall(txt);local=set(anchors)
    if len(anchors)!=len(local):c.issue('ERROR','UNITY_DUP_FILEID',f,evidence='文字文件有重複anchor fileID',impact='本地引用不明確',suggestion='核對來源序列化檔')
    refs=0;span=[]
    for match in re.finditer(r'\{[^{}]{0,2048}\}',txt,re.S):
        body=match[0];fid=re.search(r'\bfileID:\s*(-?\d+)\b',body)
        if not fid:continue
        refs+=1;span.append((match.start(),match.end()));fileid=fid[1]
        gm=re.search(r'\bguid:\s*([0-9a-fA-F]+)',body);guid=gm[1].lower() if gm else None
        context=txt[max(0,match.start()-500):match.start()]
        keys=re.findall(r'^\s*([\w]+):',context,re.M);key=keys[-1] if keys else ''
        kind='SHADER' if 'shader' in key.lower() else 'TEXTURE' if any(x in key.lower() for x in ('texture','texenv')) else 'MATERIAL' if 'material' in key.lower() else 'ASSET'
        evidence='文字引用 '+key+'；fileID='+fileid
        if fileid=='0':continue # Explicit null is legal; no assumption of missing material.
        if guid in BUILTINS:
            c.issue('INFO','UNITY_BUILTIN',f,guid,evidence+'；Unity內建資源','不依賴包內meta','於實際Unity版本確認');continue
        if guid=='0'*32:
            c.issue('NOT_CHECKED','UNITY_ZERO_GUID',f,guid,evidence+'；非零fileID搭配零GUID','不確定內建／本地語意','以Unity確認');continue
        if guid:
            if len(guid)!=32:c.issue('ERROR','UNITY_GUID_INVALID',f,guid,evidence,'GUID格式無效','核對序列化來源');continue
            assets=c.guid.get((scope(c,f),guid),[])
            if not assets:
                if scope(c,f) in c.packages_unknown or c.index_incomplete or not c.unity_roots:
                    c.issue('WARNING','UNITY_'+kind+'_UNRESOLVED_CANDIDATE',f,guid,evidence+'；可能屬未隨附Package','缺資產候選，非確定遺失','提供Package內容後再檢查')
                    c.issue('NOT_CHECKED','UNITY_PACKAGE_GUID',f,guid,'Package外部GUID歸屬無法判斷','不能當作確定缺檔','以原專案確認')
                else:c.issue('ERROR','UNITY_'+kind+'_GUID_MISSING',f,guid,evidence+'；已掃描meta無對應','缺資產候選（非實機結論）','補回原始資產/meta或提供Package資料')
            elif len(assets)==1:
                asset=assets[0]
                try:
                    blob=c.read(asset)
                    if blob.startswith(b'%YAML'):
                        ids=set(ANCHOR.findall(blob.decode('utf-8-sig')))
                        if fileid not in ids:c.issue('WARNING','UNITY_EXTERNAL_FILEID_CANDIDATE',f,guid,evidence+'；對應文字檔無此anchor','匯入產生子資產或引用遺失候選','以Unity查核子資產，不自行修復')
                    else:c.issue('NOT_CHECKED','UNITY_IMPORTED_FILEID',f,guid,evidence+'；GUID已找到，但匯入子資產無法可靠靜態驗證','fileID未驗證','在Unity確認匯入結果')
                except (OSError,LimitError):c.issue('NOT_CHECKED','UNITY_ASSET_BLOCKED',f,guid,evidence,'對應資產未讀取','確認限制')
        elif fileid not in local:c.issue('ERROR','UNITY_LOCAL_FILEID_MISSING',f,fileid,evidence+'；同一文字檔沒有anchor','本地物件引用可能中斷','核對原場景／Prefab')
    for match in re.finditer(r'\bfileID:',txt):
        if not any(a<=match.start()<b for a,b in span):
            c.issue('NOT_CHECKED','UNITY_REFERENCE_SYNTAX',f,evidence='有非支援flow-mapping的fileID語句',impact='引用語法未完整解析',suggestion='以原Unity或完整YAML解析器確認');break
    c.issue('NOT_CHECKED','UNITY_STATIC_SCOPE',f,evidence='只解析Unity YAML flow引用與anchor；不執行腳本、不匯入、不驗證畫面或完整YAML語意',impact='非Unity開啟成功保證；空/null引用可能合法',suggestion='經同意另在原軟體確認')
    c.record(f,'Unity text','GUID／fileID靜態引用子集',dict(anchors=len(anchors),references=refs))

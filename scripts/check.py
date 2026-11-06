#!/usr/bin/env python3
"""Read-only design-delivery checker; Python 3.10+, no third-party dependencies."""
import argparse
from collections import Counter
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import struct
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from adapters.common import Context,LimitError
from adapters import gltf,obj,unity,limited
VERSION='0.1.0'
SKIP={'.git','.svn','node_modules','__pycache__'}
UNITY_CACHE={'Library','Temp','Logs','obj'}

def collect(c):
    stop=False;directories=0
    def unreadable(error):
        c.issue('NOT_CHECKED','SCAN_UNREADABLE',Path(error.filename) if error.filename else c.root,evidence='無法列舉目錄',impact='範圍未完整掃描',suggestion='檢查讀取權限');c.index_incomplete=True
    for base,dirs,files in os.walk(c.root,followlinks=False,onerror=unreadable):
        directories+=1
        if directories>c.max_files:
            c.issue('NOT_CHECKED','SCAN_LIMIT',c.root,evidence='目錄數上限，剩餘未掃描',impact='報告不完整',suggestion='縮小範圍');break
        dirs.sort();files.sort()
        if all((Path(base)/n).is_dir() for n in ('Assets','Packages','ProjectSettings')):c.unity_roots.append(Path(base))
        for name in list(dirs):
            path=Path(base)/name
            if name in SKIP or (Path(base) in c.unity_roots and name in UNITY_CACHE) or path.is_symlink():
                dirs.remove(name)
                c.issue('NOT_CHECKED','SCOPE_SKIPPED',path,evidence='建置快取／版本控制目錄或 symlink 未掃描',impact='該目錄不在檢查範圍',suggestion='檢查來源交付資料，保留原目錄')
        for name in files:
            path=Path(base)/name
            if len(c.paths)>=c.max_files:
                c.issue('NOT_CHECKED','SCAN_LIMIT',c.root,evidence='檔案數上限，剩餘目錄未掃描',impact='報告不完整',suggestion='縮小範圍或明確提高上限');stop=True;break
            c.paths.append(path)
        if stop:break

def scan(input_path,max_bytes=16*1024*1024,total_bytes=64*1024*1024,max_files=2000):
    src=Path(input_path)
    if src.is_symlink():raise ValueError('請直接指定非 symlink 的輸入')
    src=src.resolve()
    if not src.exists():raise ValueError('輸入不存在')
    c=Context(src if src.is_dir() else src.parent,max_bytes,total_bytes,max_files)
    if src.is_dir():collect(c)
    else:c.paths=[src]
    if any(i['rule_id']=='SCAN_LIMIT' or (i['rule_id']=='SCOPE_SKIPPED' and any(x in i['file'].split('/') for x in ('Assets','Packages'))) for i in c.issues):c.index_incomplete=True
    unity.prepare(c)
    for f in c.paths:
        if f.is_symlink():c.issue('NOT_CHECKED','SYMLINK_SKIPPED',f,evidence='未追蹤 symlink',impact='未讀取',suggestion='使用實體交付檔案');c.record(f,'unknown','symlink未追蹤');continue
        suffix=f.suffix.lower()
        try:header=c.secure_bytes(f,512)
        except (OSError,LimitError):
            c.issue('NOT_CHECKED','HEADER_UNREADABLE',f,evidence='無法安全讀取檔頭',impact='未辨識內容',suggestion='檢查檔案類型／權限');c.record(f,'unknown','檔頭未讀取');continue
        magic=header.startswith((b'glTF',b'8BPS',b'Kaydara FBX Binary  ',b'; FBX'))
        json_gltf=header.lstrip().startswith(b'{') and b'"asset"' in header and b'"version"' in header
        # Resources are inventoried, not presented as fully inspected assets.
        if not magic and not json_gltf and suffix not in {'.gltf','.glb','.obj','.mtl','.fbx','.ai','.psd','.psb','.unity','.prefab','.mat','.asset','.controller','.meta','.json'}:
            c.record(f,'resource','未檢查（輔助資源／未支援格式）')
            if f==src:c.issue('NOT_CHECKED','FORMAT_UNSUPPORTED',f,evidence='未知格式；沒有可用adapter',impact='未驗證',suggestion='提供已支援格式或安排原軟體確認')
            continue
        try:
            data=c.read(f)
            if data.startswith(b'glTF') or json_gltf or suffix in ('.gltf','.glb'):gltf.check(c,f,data)
            elif suffix in ('.obj','.mtl'):obj.check(c,f,data)
            elif suffix in ('.fbx','.ai','.psd','.psb') or data.startswith((b'8BPS',b'Kaydara FBX Binary  ',b'; FBX')):limited.check(c,f,data)
            elif suffix in ('.unity','.prefab','.mat','.asset','.controller'):unity.check(c,f,data)
            elif suffix=='.meta':c.record(f,'Unity meta','GUID 索引，非匯入驗證')
            elif suffix=='.json':c.record(f,'JSON resource','僅 Unity package manifest 在專案檢查時讀取')
        except LimitError:
            c.issue('NOT_CHECKED','READ_LIMIT',f,evidence='讀取限制或超出安全範圍',impact='未完成檢查',suggestion='縮小範圍／明確提高限制');c.record(f,suffix,'未驗證')
        except (ValueError,UnicodeError,KeyError,TypeError,IndexError,OverflowError,RecursionError,AttributeError,struct.error):
            c.issue('ERROR','PARSE_INVALID',f,evidence='對應解析器無法讀取此結構',impact='不能完成該格式檢查',suggestion='確認檔案未損壞及支援範圍');c.record(f,suffix,'無法解析')
        except OSError:
            c.issue('NOT_CHECKED','READ_FAILED',f,evidence='檔案無法讀取',impact='未驗證',suggestion='檢查讀取權限');c.record(f,'unknown','讀取失敗')
    integrity=[]
    for f,data in c.cache.items():
        expected=hashlib.sha256(data).hexdigest()
        try:
            # Reuse security path check; bounded reread to detect concurrent changes.
            after=c.secure_bytes(f,c.max_bytes)
            same=hashlib.sha256(after).hexdigest()==expected
        except (OSError,LimitError):same=False
        integrity.append(dict(file=c.rel(f),sha256_before=expected,unchanged=same))
        if not same:c.issue('WARNING','INPUT_CHANGED',f,evidence='檢查期間內容變更',impact='報告可能不一致',suggestion='停止其他編輯後重跑')
    counts={s:sum(i['severity']==s for i in c.issues) for s in ('ERROR','WARNING','INFO','NOT_CHECKED')}
    return dict(report_version=VERSION,created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),scope=dict(input=src.name,kind='directory' if src.is_dir() else 'file',paths='relative-to-input-root',limits=dict(max_file_bytes=max_bytes,max_total_bytes=total_bytes,max_files=max_files),read_only=True),overview=dict(counts=counts,conclusion='發現需處理或未驗證項目' if counts['ERROR'] or counts['WARNING'] else '已執行範圍內未發現問題；未驗證項不代表通過'),files=c.files,issues=c.issues,not_checked=[i for i in c.issues if i['severity']=='NOT_CHECKED'],recommendations=['依 ERROR／WARNING 逐項確認，NOT_CHECKED 需另行驗證。','同名素材僅候選，不自動重新連結。','字型可用性與授權須由交付雙方確認；本機缺字型不等於收件方缺字型。'],integrity=integrity)

def markdown(r):
    def cell(v):
        v=str(v).replace('\\','\\\\')
        for char in '[]`*_':v=v.replace(char,'\\'+char)
        return v.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('|','&#124;').replace('\n',' ')
    out=f"# 設計檔交付健檢\n\n報告版本：{r['report_version']}｜時間：{r['created_at']}\n\n範圍：{cell(r['scope']['input'])}（{r['scope']['kind']}）；路徑均相對於檢查根目錄。\n\n## 總覽\n\n{r['overview']['conclusion']}\n\n"
    out+='、'.join(f"{k}: {v}" for k,v in r['overview']['counts'].items())+'\n\n## 各檔格式及檢查覆蓋\n\n| 檔案 | 格式 | 覆蓋 | 統計 |\n|---|---|---|---|\n'
    for f in r['files']:out+='| '+' | '.join(cell(f[k]) for k in ('file','format','coverage','statistics'))+' |\n'
    out+='\n## 問題表\n\n| 嚴重度 | 規則ID | 相對檔案位置 | 引用對象 | 證據 | 影響 | 建議 |\n|---|---|---|---|---|---|---|\n'
    for issue in r['issues']:out+='| '+' | '.join(cell(issue[k]) for k in ('severity','rule_id','file','reference','evidence','impact','suggestion'))+' |\n'
    if not r['issues']:out+='\n已執行範圍內未發現問題；各檔覆蓋限制仍適用。\n'
    out+='\n## 未驗證項\n\n'+(''.join('- '+cell(i['file'])+'：'+cell(i['evidence'])+'\n' for i in r['not_checked']) or '沒有額外列出的 NOT_CHECKED；各格式能力限制仍適用。\n')
    out+='\n## 建議\n\n'+''.join('- '+x+'\n' for x in r['recommendations'])
    out+=f"\n已讀取檔案內容 SHA-256 比對：{sum(i['unchanged'] for i in r['integrity'])}/{len(r['integrity'])} 未改變。工具不修改原檔；此比對也可能揭露其他程式同時編輯。\n"
    return out

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('input',type=Path,help='單檔、專案或混合資料夾')
    p.add_argument('--output',required=True,type=Path,help='新報告檔名前綴；資料夾輸入時須在資料夾外')
    p.add_argument('--max-file-mb',type=int,default=16);p.add_argument('--max-total-mb',type=int,default=64);p.add_argument('--max-files',type=int,default=2000)
    a=p.parse_args()
    if min(a.max_file_mb,a.max_total_mb,a.max_files)<=0:p.error('限制須為正整數')
    try:
        src=a.input.resolve();dest=a.output.resolve()
        if src.is_dir() and dest.is_relative_to(src):raise ValueError('報告必須輸出到輸入資料夾外')
        paths=[Path(str(dest)+ext) for ext in ('.json','.md')]
        if any(x.exists() or x.is_symlink() for x in paths):raise ValueError('輸出已存在；請另取報告名稱')
        r=scan(a.input,a.max_file_mb*1024*1024,a.max_total_mb*1024*1024,a.max_files)
        dest.parent.mkdir(parents=True,exist_ok=True)
        for target,content in zip(paths,[json.dumps(r,ensure_ascii=False,indent=2),markdown(r)]):
            with target.open('x',encoding='utf-8') as stream:stream.write(content)
    except (ValueError,OSError):p.exit(2,'錯誤：輸入、輸出路徑或存取條件不符合要求；未修改來源。\n')
    print('完成 Markdown 與 JSON 報告；ERROR='+str(r['overview']['counts']['ERROR']))
    return 1 if r['overview']['counts']['ERROR'] else 0
if __name__=='__main__':sys.exit(main())

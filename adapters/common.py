"""Bounded read-only context, portable reference resolver and fixed issue schema."""
import base64
import hashlib
import os
from pathlib import Path, PureWindowsPath
import re
import stat
from urllib.parse import unquote,urlsplit

class LimitError(Exception): pass
class Context:
    def __init__(self,root,max_bytes=16*1024*1024,total_bytes=64*1024*1024,max_files=2000):
        self.root=root;self.max_bytes=max_bytes;self.total_bytes=total_bytes;self.max_files=max_files
        self.cache={};self.used=0;self.issues=[];self.files=[];self.paths=[];self.guid={};self.unity_roots=[];self.packages_unknown=set();self.index_incomplete=False
    def rel(self,p):
        try:return Path(p).relative_to(self.root).as_posix()
        except ValueError:return '<outside-root>'
    def safe(self,s):
        s=str(s).replace(str(self.root),'<ROOT>')
        probe=unquote(s)
        if re.match(r'^(?:[A-Za-z]:[\\/]|/|\\\\)',probe):return '<ABSOLUTE>/'+re.split(r'[\\/]',probe)[-1][:100]
        if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*://',probe):return '<REMOTE>/' + urlsplit(probe).path.rsplit('/',1)[-1][:100]
        return ''.join(c if ord(c)>=32 else ' ' for c in s)[:1000]
    def issue(self,severity,rule,file,reference='',evidence='',impact='',suggestion=''):
        self.issues.append(dict(severity=severity,rule_id=rule,file=self.rel(file),reference=self.safe(reference),evidence=self.safe(evidence),impact=impact,suggestion=suggestion))
    def secure_bytes(self,path,limit):
        path=Path(path)
        if not path.resolve().is_relative_to(self.root):raise LimitError('outside root')
        parts=path.relative_to(self.root).parts
        if not parts:raise LimitError('not file')
        if os.open in os.supports_dir_fd and hasattr(os,'O_NOFOLLOW'):
            handles=[]
            try:
                fd=os.open(self.root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW);handles.append(fd)
                for name in parts[:-1]:
                    fd=os.open(name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd);handles.append(fd)
                leaf=os.open(parts[-1],os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=fd);handles.append(leaf)
                if not stat.S_ISREG(os.fstat(leaf).st_mode):raise LimitError('not regular file')
                with os.fdopen(os.dup(leaf),'rb') as stream:return stream.read(limit+1)
            finally:
                for fd in reversed(handles):os.close(fd)
        # Portable fallback; use only on quiescent source trees, not a hostile concurrent writer.
        part=self.root
        for name in parts:
            part=part/name
            if part.is_symlink():raise LimitError('symlink')
        if not path.is_file():raise FileNotFoundError()
        with path.open('rb') as stream:return stream.read(limit+1)
    def read(self,path):
        path=Path(path)
        if path in self.cache:return self.cache[path]
        resolved=path.resolve()
        if not resolved.is_relative_to(self.root):raise LimitError('root 外部資源禁止讀取')
        # Deny any symlink traversal, including in-root links: no implicit linking/search.
        part=self.root
        for component in path.relative_to(self.root).parts:
            part=part/component
            if part.is_symlink():raise LimitError('symlink 不在本版讀取範圍')
        if not path.is_file():raise FileNotFoundError()
        size=path.stat().st_size
        if size>self.max_bytes or self.used+size>self.total_bytes:raise LimitError('檔案或累計讀取超過限制')
        data=self.secure_bytes(path,self.max_bytes)
        if len(data)>self.max_bytes or self.used+len(data)>self.total_bytes:raise LimitError('讀取時檔案增長超過限制')
        self.used+=len(data);self.cache[path]=data;return data
    def text(self,path):return self.read(path).decode('utf-8-sig')
    def resolve(self,owner,raw,uri=False):
        raw=str(raw);s=unquote(raw) if uri else raw
        if '\x00' in s: self.issue('ERROR','PATH_NUL',owner,raw,'路徑含NUL','無法解析','重新匯出正確引用');return None
        absolute=PureWindowsPath(s).is_absolute() or s.startswith(('/', '\\')) or bool(re.match(r'^[A-Za-z]:',s))
        remote=bool(urlsplit(s).scheme) and not absolute
        if remote:
            self.issue('WARNING','PATH_REMOTE',owner,raw,'遠端資源未連線讀取','離線交付依賴外部來源','將資源合法打包後重新檢查');return None
        if absolute:
            self.issue('WARNING','PATH_ABSOLUTE',owner,raw,'絕對路徑已遮蔽，未讀取','不可攜／可能含私人位置','改用包內相對路徑');return None
        if '\\' in s:
            self.issue('WARNING','PATH_SEPARATOR',owner,raw,'反斜線路徑','跨平台路徑風險','使用相對正斜線路徑')
            s=s.replace('\\','/')
        target=Path(os.path.abspath(owner.parent/s))
        if not target.is_relative_to(self.root):
            self.issue('NOT_CHECKED','PATH_ESCAPE',owner,raw,'解析結果在 root 外，未搜尋','引用不可驗證','另提供完整交付根目錄；不可自動接回');return None
        cur=self.root;case=False
        for part in target.relative_to(self.root).parts:
            if cur.is_symlink():break
            if not cur.is_dir():break
            names=set()
            for x in cur.iterdir():
                names.add(x.name)
                if len(names)>self.max_files:raise LimitError('directory entry limit')
            if part not in names:
                matches=sorted(n for n in names if n.casefold()==part.casefold())
                if len(matches)==1:part=matches[0];case=True
                elif len(matches)>1:
                    self.issue('ERROR','PATH_AMBIGUOUS',owner,raw,'多個大小寫候選','無法可靠解析','明確修正引用');return None
                else:
                    self.issue('ERROR','REF_MISSING',owner,raw,'解析位置：'+self.rel(target),'交付包可能缺素材','確認並人工補齊，不自動重新連結');return None
            cur=cur/part
        if case:self.issue('WARNING','PATH_CASE',owner,raw,'實際位置：'+self.rel(cur),'大小寫敏感系統可能找不到','對齊實際檔名大小寫')
        try:self.read(cur)
        except FileNotFoundError:
            self.issue('ERROR','REF_MISSING',owner,raw,'解析位置：'+self.rel(target),'引用檔案不存在','確認素材與匯出設定');return None
        except (LimitError,OSError):
            self.issue('NOT_CHECKED','REF_BLOCKED',owner,raw,'解析位置：'+self.rel(target)+'；受安全限制','資源內容未驗證','明確調整範圍或讀取上限後重跑');return None
        return cur
    def resource(self,owner,uri):
        if not isinstance(uri,str):raise ValueError('URI must be a string')
        if uri.startswith('data:'):
            if len(uri)>self.max_bytes*2:raise LimitError('data URI 超限')
            head,sep,body=uri.partition(',')
            if not sep:raise ValueError('data URI malformed')
            data=base64.b64decode(body,validate=True) if head.endswith(';base64') else unquote(body).encode('latin1')
            if len(data)>self.max_bytes or self.used+len(data)>self.total_bytes:raise LimitError('內嵌資源超限')
            self.used+=len(data);return data
        target=self.resolve(owner,uri,True)
        return self.read(target) if target else None
    def record(self,file,format,coverage,stats=None):
        self.files.append(dict(file=self.rel(file),format=format,coverage=coverage,statistics=stats or {}))

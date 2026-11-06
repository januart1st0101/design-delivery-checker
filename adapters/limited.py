"""Honest header classification only. No native FBX/AI/PSD parser is bundled."""
import struct

def check(c,f,data):
    ext=f.suffix.lower();form=ext[1:].upper();details=''
    if data.startswith(b'8BPS') or ext in ('.psd','.psb'):
        if len(data)<26 or data[:4]!=b'8BPS':raise ValueError('PSD signature/header')
        version=struct.unpack_from('>H',data,4)[0]
        if version not in (1,2):details='未知 PSD/PSB header 版本 '+str(version)
        else:
            _,_,channels,height,width,depth,mode=struct.unpack('>4sH6xHIIHH',data[:26])
            details=f'8BPS header version={version}，{width}×{height}，channels={channels}，depth={depth}；僅辨識檔頭'
        form='PSD/PSB'
    elif ext=='.fbx' or data.startswith((b'Kaydara FBX Binary  ',b'; FBX')):
        form='FBX'
        if data.startswith(b'Kaydara FBX Binary  \x00\x1a\x00') and len(data)>=27:details='binary FBX header version='+str(struct.unpack_from('<I',data,23)[0])
        elif data.lstrip().startswith(b'; FBX'):details='疑似 ASCII FBX header；未解析節點或版本結構'
        else:details='無法辨識FBX結構；副檔名不能證明格式'
    elif ext=='.ai':
        details=('PDF相容候選；PDF內容不代表完整AI原生編輯內容' if data.startswith(b'%PDF-') else 'PostScript相容候選；未解析AI原生內容' if data.startswith(b'%!PS-Adobe-') else '無法辨識可讀相容結構')
    c.record(f,form,'未支援原生驗證；僅檔頭分類',dict(classification=details))
    c.issue('NOT_CHECKED','NATIVE_PARSER_UNAVAILABLE',f,evidence=details,impact='外部／內嵌素材、材質／節點、單位及字型狀態均未驗證；不得因無外部檔而報遺失',suggestion='依能力矩陣安排後續解析器；或經使用者同意在原軟體檢查')
    if ext in ('.ai','.psd','.psb') or form=='PSD/PSB':
        c.issue('NOT_CHECKED','FONT_STATUS_UNKNOWN',f,evidence='字型嵌入／已轉外框／未嵌入／引用名稱均無法判斷',impact='不能當作字型齊全或字型遺失',suggestion='原軟體檢查字型與素材面板；不自動下載字型')

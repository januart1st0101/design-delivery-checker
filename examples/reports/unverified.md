# 設計檔交付健檢

報告版本：0.1.0｜時間：2026-11-01T05:05:40+00:00

範圍：unverified（directory）；路徑均相對於檢查根目錄。

## 總覽

已執行範圍內未發現問題；未驗證項不代表通過

ERROR: 0、WARNING: 0、INFO: 0、NOT_CHECKED: 4

## 各檔格式及檢查覆蓋

| 檔案 | 格式 | 覆蓋 | 統計 |
|---|---|---|---|
| README.txt | resource | 未檢查（輔助資源／未支援格式） | {} |
| 自製色塊.psb | PSD/PSB | 未支援原生驗證；僅檔頭分類 | {'classification': '8BPS header version=2，1×1，channels=3，depth=8；僅辨識檔頭'} |
| 自製色塊.psd | PSD/PSB | 未支援原生驗證；僅檔頭分類 | {'classification': '8BPS header version=1，1×1，channels=3，depth=8；僅辨識檔頭'} |

## 問題表

| 嚴重度 | 規則ID | 相對檔案位置 | 引用對象 | 證據 | 影響 | 建議 |
|---|---|---|---|---|---|---|
| NOT\_CHECKED | NATIVE\_PARSER\_UNAVAILABLE | 自製色塊.psb |  | 8BPS header version=2，1×1，channels=3，depth=8；僅辨識檔頭 | 外部／內嵌素材、材質／節點、單位及字型狀態均未驗證；不得因無外部檔而報遺失 | 依能力矩陣安排後續解析器；或經使用者同意在原軟體檢查 |
| NOT\_CHECKED | FONT\_STATUS\_UNKNOWN | 自製色塊.psb |  | 字型嵌入／已轉外框／未嵌入／引用名稱均無法判斷 | 不能當作字型齊全或字型遺失 | 原軟體檢查字型與素材面板；不自動下載字型 |
| NOT\_CHECKED | NATIVE\_PARSER\_UNAVAILABLE | 自製色塊.psd |  | 8BPS header version=1，1×1，channels=3，depth=8；僅辨識檔頭 | 外部／內嵌素材、材質／節點、單位及字型狀態均未驗證；不得因無外部檔而報遺失 | 依能力矩陣安排後續解析器；或經使用者同意在原軟體檢查 |
| NOT\_CHECKED | FONT\_STATUS\_UNKNOWN | 自製色塊.psd |  | 字型嵌入／已轉外框／未嵌入／引用名稱均無法判斷 | 不能當作字型齊全或字型遺失 | 原軟體檢查字型與素材面板；不自動下載字型 |

## 未驗證項

- 自製色塊.psb：8BPS header version=2，1×1，channels=3，depth=8；僅辨識檔頭
- 自製色塊.psb：字型嵌入／已轉外框／未嵌入／引用名稱均無法判斷
- 自製色塊.psd：8BPS header version=1，1×1，channels=3，depth=8；僅辨識檔頭
- 自製色塊.psd：字型嵌入／已轉外框／未嵌入／引用名稱均無法判斷

## 建議

- 依 ERROR／WARNING 逐項確認，NOT_CHECKED 需另行驗證。
- 同名素材僅候選，不自動重新連結。
- 字型可用性與授權須由交付雙方確認；本機缺字型不等於收件方缺字型。

已讀取檔案內容 SHA-256 比對：2/2 未改變。工具不修改原檔；此比對也可能揭露其他程式同時編輯。

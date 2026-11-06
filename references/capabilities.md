# 能力矩陣 — 0.1.0 / 第一階段

「已實作並測試」僅指表列子功能，所有格式的整體驗證均不等於原軟體或完整標準驗證器。

| 格式 | 整體狀態 | 已實作並測試 | 部分支援／未支援 | fixture |
|---|---|---|---|---|
| glTF 2.0 / GLB 2 | 部分支援 | JSON/GLB長度與chunk邊界；buffer/view/accessor範圍；核心引用索引；POSITION float VEC3解碼與min/max；unsigned索引；稀疏索引越界；PNG/JPEG來源；材質texture引用；節點循環；合法群組 | 非完整schema；其他accessor語意、矩陣數據解碼、動畫、skin、變換、extension解碼、像素解碼／渲染未驗證；壓縮只列NOT_CHECKED | 原創三角形，外部圖片／data URI／BIN bufferView圖片；正常與缺素材GLB |
| OBJ / MTL | 部分支援 | v/vt/vn與face索引（含負索引）；群組/無材質物件；mtllib/usemtl/newmtl；常見map選項及引號空白路徑；引用存在／大小寫 | 自由曲面、UV品質、非流形、退化幾何、line/point索引、所有匯出器選項未完整驗證；無內定單位 | 原創文字OBJ/MTL與PNG |
| Unity文字專案 | 部分支援 | Assets/Packages/ProjectSettings辨識；頂層meta GUID、重複GUID、缺meta候選、缺資產候選；flow-mapping GUID/fileID與local anchor；內建e/f GUID及null引用；不同專案GUID索引隔離 | 支援Unity YAML1.1＋Unity tag的靜態子集；非完整YAML解析／Editor載入；Package未隨附GUID只列候選；匯入子資產、二進位、shader管線相容性／實際畫面未驗證；未宣稱支援特定Editor版本 | 原創文字序列化單元fixtures，並非聲稱經Unity Editor輸出或開啟 |
| FBX ASCII / binary | 未支援原生驗證 | **無原生解析測試** | 只做檔頭分類，binary可讀header版本；不是節點／材質／貼圖／單位驗證。未驗證任何FBX版本。後續選定ufbx，見路線圖 | 無合法原生fixture，本版不宣稱已驗證FBX |
| Illustrator AI | 未支援原生驗證 | **無原生解析測試** | 只分類PDF／PostScript相容候選；不代表PDF解析成功或完整AI編輯內容。連結、字型名、嵌入／轉外框／未嵌入全部未知 | 無AI fixture，不改名PDF假冒AI |
| PSD / PSB | 未支援原生驗證 | 8BPS header v1/v2分類測試（不是圖層解析測試） | 沒有智慧型物件、素材／字型引用原生解析。嵌入素材不可因外部檔不存在而報缺失。新／未知版本列未驗證 | 依Adobe規格自製真正1×1 raw RGB PSD/PSB；不冒充有圖層／文字／連結的測試 |
| 其他資源／格式 | 未支援內容驗證 | 盤點相對檔名；已引用資源可查存在 | 圖片像素、字型環境、其他設計軟體檔案未驗證；單檔未知格式明列NOT_CHECKED | 任意文字資源，不稱格式驗證fixture |

所有來源都不會修改。索引、路徑及格式支援聲明均以tests中的行為測試為界。

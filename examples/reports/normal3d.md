# 設計檔交付健檢

報告版本：0.1.0｜時間：2026-11-01T05:05:21+00:00

範圍：normal3d（directory）；路徑均相對於檢查根目錄。

## 總覽

已執行範圍內未發現問題；未驗證項不代表通過

ERROR: 0、WARNING: 0、INFO: 3、NOT_CHECKED: 8

## 各檔格式及檢查覆蓋

| 檔案 | 格式 | 覆蓋 | 統計 |
|---|---|---|---|
| embedded.glb | GLB | 部分支援：核心結構／引用／未壓縮幾何 | {'declared\_vertices': 3, 'decoded\_positions': 3, 'primitives': 1, 'triangles\_uncompressed': 1, 'nodes': 2, 'named\_nodes': 2, 'repeated\_name\_groups': 0, 'root\_nodes': 1, 'materials': 1, 'images': 1} |
| model.obj | OBJ | 頂點／face索引、MTL與map引用子集 | {'vertices': 3, 'uvs': 0, 'normals': 0, 'faces': 1, 'group\_object\_declarations': 2} |
| no-material.obj | OBJ | 頂點／face索引、MTL與map引用子集 | {'vertices': 3, 'uvs': 0, 'normals': 0, 'faces': 1, 'group\_object\_declarations': 1} |
| sample.mtl | MTL | 材質名／map引用子集 | {'materials': 1} |
| triangle.bin | resource | 未檢查（輔助資源／未支援格式） | {} |
| view-image.glb | GLB | 部分支援：核心結構／引用／未壓縮幾何 | {'declared\_vertices': 3, 'decoded\_positions': 3, 'primitives': 1, 'triangles\_uncompressed': 1, 'nodes': 2, 'named\_nodes': 2, 'repeated\_name\_groups': 0, 'root\_nodes': 1, 'materials': 1, 'images': 1} |
| 三角形.gltf | glTF | 部分支援：核心結構／引用／未壓縮幾何 | {'declared\_vertices': 3, 'decoded\_positions': 3, 'primitives': 1, 'triangles\_uncompressed': 1, 'nodes': 2, 'named\_nodes': 2, 'repeated\_name\_groups': 0, 'root\_nodes': 1, 'materials': 1, 'images': 1} |
| 貼圖.png | resource | 未檢查（輔助資源／未支援格式） | {} |

## 問題表

| 嚴重度 | 規則ID | 相對檔案位置 | 引用對象 | 證據 | 影響 | 建議 |
|---|---|---|---|---|---|---|
| NOT\_CHECKED | IMAGE\_PIXELS | embedded.glb |  | 已查來源與檔頭，未解碼像素／色彩設定 | 未完全驗證 | 確認匯出內容與對應格式規格 |
| INFO | GLTF\_UNITS | embedded.glb |  | glTF 2.0 公尺、右手座標、+Y向上；不推測資產實際正面 | 未完全驗證 | 確認匯出內容與對應格式規格 |
| NOT\_CHECKED | GLTF\_SCOPE | embedded.glb |  | 非完整 Khronos Validator；動畫、skin語意、變換、渲染結果未驗證；空節點與重複名稱不判壞檔 | 未完全驗證 | 確認匯出內容與對應格式規格 |
| NOT\_CHECKED | OBJ\_SCOPE | model.obj |  | 未驗證UV品質、曲面、退化／非流形拓樸、像素與渲染；OBJ單位／正面未定義 | 非完整幾何品質保證 | 依交付政策以原軟體確認；不可猜單位 |
| NOT\_CHECKED | OBJ\_SCOPE | no-material.obj |  | 未驗證UV品質、曲面、退化／非流形拓樸、像素與渲染；OBJ單位／正面未定義 | 非完整幾何品質保證 | 依交付政策以原軟體確認；不可猜單位 |
| NOT\_CHECKED | IMAGE\_PIXELS | view-image.glb |  | 已查來源與檔頭，未解碼像素／色彩設定 | 未完全驗證 | 確認匯出內容與對應格式規格 |
| INFO | GLTF\_UNITS | view-image.glb |  | glTF 2.0 公尺、右手座標、+Y向上；不推測資產實際正面 | 未完全驗證 | 確認匯出內容與對應格式規格 |
| NOT\_CHECKED | GLTF\_SCOPE | view-image.glb |  | 非完整 Khronos Validator；動畫、skin語意、變換、渲染結果未驗證；空節點與重複名稱不判壞檔 | 未完全驗證 | 確認匯出內容與對應格式規格 |
| NOT\_CHECKED | IMAGE\_PIXELS | 三角形.gltf |  | 已查來源與檔頭，未解碼像素／色彩設定 | 未完全驗證 | 確認匯出內容與對應格式規格 |
| INFO | GLTF\_UNITS | 三角形.gltf |  | glTF 2.0 公尺、右手座標、+Y向上；不推測資產實際正面 | 未完全驗證 | 確認匯出內容與對應格式規格 |
| NOT\_CHECKED | GLTF\_SCOPE | 三角形.gltf |  | 非完整 Khronos Validator；動畫、skin語意、變換、渲染結果未驗證；空節點與重複名稱不判壞檔 | 未完全驗證 | 確認匯出內容與對應格式規格 |

## 未驗證項

- embedded.glb：已查來源與檔頭，未解碼像素／色彩設定
- embedded.glb：非完整 Khronos Validator；動畫、skin語意、變換、渲染結果未驗證；空節點與重複名稱不判壞檔
- model.obj：未驗證UV品質、曲面、退化／非流形拓樸、像素與渲染；OBJ單位／正面未定義
- no-material.obj：未驗證UV品質、曲面、退化／非流形拓樸、像素與渲染；OBJ單位／正面未定義
- view-image.glb：已查來源與檔頭，未解碼像素／色彩設定
- view-image.glb：非完整 Khronos Validator；動畫、skin語意、變換、渲染結果未驗證；空節點與重複名稱不判壞檔
- 三角形.gltf：已查來源與檔頭，未解碼像素／色彩設定
- 三角形.gltf：非完整 Khronos Validator；動畫、skin語意、變換、渲染結果未驗證；空節點與重複名稱不判壞檔

## 建議

- 依 ERROR／WARNING 逐項確認，NOT_CHECKED 需另行驗證。
- 同名素材僅候選，不自動重新連結。
- 字型可用性與授權須由交付雙方確認；本機缺字型不等於收件方缺字型。

已讀取檔案內容 SHA-256 比對：8/8 未改變。工具不修改原檔；此比對也可能揭露其他程式同時編輯。

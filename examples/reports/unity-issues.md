# 設計檔交付健檢

報告版本：0.1.0｜時間：2026-11-01T05:05:37+00:00

範圍：unity-issues（directory）；路徑均相對於檢查根目錄。

## 總覽

發現需處理或未驗證項目

ERROR: 5、WARNING: 1、INFO: 3、NOT_CHECKED: 5

## 各檔格式及檢查覆蓋

| 檔案 | 格式 | 覆蓋 | 統計 |
|---|---|---|---|
| Assets/Duplicate.mat | Unity text | GUID／fileID靜態引用子集 | {'anchors': 1, 'references': 0} |
| Assets/Duplicate.mat.meta | Unity meta | GUID 索引，非匯入驗證 | {} |
| Assets/Mat.mat | Unity text | GUID／fileID靜態引用子集 | {'anchors': 1, 'references': 1} |
| Assets/Mat.mat.meta | Unity meta | GUID 索引，非匯入驗證 | {} |
| Assets/NoMeta.txt | resource | 未檢查（輔助資源／未支援格式） | {} |
| Assets/Scene.unity | Unity text | GUID／fileID靜態引用子集 | {'anchors': 1, 'references': 6} |
| Assets/Scene.unity.meta | Unity meta | GUID 索引，非匯入驗證 | {} |
| Packages/manifest.json | JSON resource | 僅 Unity package manifest 在專案檢查時讀取 | {} |
| ProjectSettings/GraphicsSettings.asset | Unity text | GUID／fileID靜態引用子集 | {'anchors': 1, 'references': 1} |
| ProjectSettings/ProjectVersion.txt | resource | 未檢查（輔助資源／未支援格式） | {} |

## 問題表

| 嚴重度 | 規則ID | 相對檔案位置 | 引用對象 | 證據 | 影響 | 建議 |
|---|---|---|---|---|---|---|
| ERROR | UNITY\_DUP\_GUID | Assets/Duplicate.mat | aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa | 相同GUID對應：Assets/Duplicate.mat, Assets/Mat.mat | Unity可能辨識成錯誤資產 | 人工確認正確meta來源；不可自動重建 |
| ERROR | UNITY\_DUP\_GUID | Assets/Mat.mat | aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa | 相同GUID對應：Assets/Duplicate.mat, Assets/Mat.mat | Unity可能辨識成錯誤資產 | 人工確認正確meta來源；不可自動重建 |
| INFO | UNITY\_PROJECT | . |  | 識別 Assets / Packages / ProjectSettings | 以文字序列化子集檢查 | 保留meta與Packages資訊 |
| WARNING | UNITY\_META\_MISSING | Assets/NoMeta.txt |  | Assets內檔案未附meta | GUID可能在重匯入時改變 | 補回原始meta；不要自動產生 |
| NOT\_CHECKED | UNITY\_PIPELINE\_COMPATIBILITY | ProjectSettings/GraphicsSettings.asset |  | 僅有靜態設定；不推斷shader與渲染管線相容性 | 無法保證材質呈現正常 | 在原Unity版本檢查Graphics/Quality與實際渲染 |
| NOT\_CHECKED | UNITY\_STATIC\_SCOPE | Assets/Duplicate.mat |  | 只解析Unity YAML flow引用與anchor；不執行腳本、不匯入、不驗證畫面或完整YAML語意 | 非Unity開啟成功保證；空/null引用可能合法 | 經同意另在原軟體確認 |
| INFO | UNITY\_BUILTIN | Assets/Mat.mat | 0000000000000000f000000000000000 | 文字引用 m\_Shader；fileID=46；Unity內建資源 | 不依賴包內meta | 於實際Unity版本確認 |
| NOT\_CHECKED | UNITY\_STATIC\_SCOPE | Assets/Mat.mat |  | 只解析Unity YAML flow引用與anchor；不執行腳本、不匯入、不驗證畫面或完整YAML語意 | 非Unity開啟成功保證；空/null引用可能合法 | 經同意另在原軟體確認 |
| INFO | UNITY\_BUILTIN | Assets/Scene.unity | 0000000000000000f000000000000000 | 文字引用 m\_Builtin；fileID=10303；Unity內建資源 | 不依賴包內meta | 於實際Unity版本確認 |
| ERROR | UNITY\_MATERIAL\_GUID\_MISSING | Assets/Scene.unity | bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb | 文字引用 m\_Material；fileID=2100000；已掃描meta無對應 | 缺資產候選（非實機結論） | 補回原始資產/meta或提供Package資料 |
| ERROR | UNITY\_SHADER\_GUID\_MISSING | Assets/Scene.unity | cccccccccccccccccccccccccccccccc | 文字引用 m\_Shader；fileID=4800000；已掃描meta無對應 | 缺資產候選（非實機結論） | 補回原始資產/meta或提供Package資料 |
| ERROR | UNITY\_TEXTURE\_GUID\_MISSING | Assets/Scene.unity | dddddddddddddddddddddddddddddddd | 文字引用 m\_Texture；fileID=2800000；已掃描meta無對應 | 缺資產候選（非實機結論） | 補回原始資產/meta或提供Package資料 |
| NOT\_CHECKED | UNITY\_STATIC\_SCOPE | Assets/Scene.unity |  | 只解析Unity YAML flow引用與anchor；不執行腳本、不匯入、不驗證畫面或完整YAML語意 | 非Unity開啟成功保證；空/null引用可能合法 | 經同意另在原軟體確認 |
| NOT\_CHECKED | UNITY\_STATIC\_SCOPE | ProjectSettings/GraphicsSettings.asset |  | 只解析Unity YAML flow引用與anchor；不執行腳本、不匯入、不驗證畫面或完整YAML語意 | 非Unity開啟成功保證；空/null引用可能合法 | 經同意另在原軟體確認 |

## 未驗證項

- ProjectSettings/GraphicsSettings.asset：僅有靜態設定；不推斷shader與渲染管線相容性
- Assets/Duplicate.mat：只解析Unity YAML flow引用與anchor；不執行腳本、不匯入、不驗證畫面或完整YAML語意
- Assets/Mat.mat：只解析Unity YAML flow引用與anchor；不執行腳本、不匯入、不驗證畫面或完整YAML語意
- Assets/Scene.unity：只解析Unity YAML flow引用與anchor；不執行腳本、不匯入、不驗證畫面或完整YAML語意
- ProjectSettings/GraphicsSettings.asset：只解析Unity YAML flow引用與anchor；不執行腳本、不匯入、不驗證畫面或完整YAML語意

## 建議

- 依 ERROR／WARNING 逐項確認，NOT_CHECKED 需另行驗證。
- 同名素材僅候選，不自動重新連結。
- 字型可用性與授權須由交付雙方確認；本機缺字型不等於收件方缺字型。

已讀取檔案內容 SHA-256 比對：8/8 未改變。工具不修改原檔；此比對也可能揭露其他程式同時編輯。

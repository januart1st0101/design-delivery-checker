# 測試與交付記錄 — 2026-11-01

本紀錄對應 0.1.0 第一階段的本機測試。核心只用Python標準函式庫。

## 真正執行

- Python 3.12 執行 `python3 -m unittest discover -s tests -v`：**57項測試全部通過**，原始輸出見[RUN.txt](RUN.txt)。另確認CLI --help與退出碼0/1/2。
- skill-creator quick_validate：Skill is valid。此主機缺PyYAML，使用臨時Ruby YAML.safe_load轉接讀frontmatter；轉接不包含在套件或運作依賴內。
- 獨立forward-testing：另一代理執行測試並自建probe，發現巢狀壞結構／manifest可能中止、矩陣padding範圍、obj目錄漏掃、缺buffer仍列三角形，以及重複解碼工作量。已修正並增加回歸測試；獨立代理重跑原probe確認主要修正。另發現invalid indices accessor的統計角落，也已修正並由第57項測試確認。
- 四類報告重新由本版腳本實際產生，Markdown與JSON同一資料來源。
- 來源整樹hash測試前後一致；已讀檔案在報告中另有SHA-256及末次重讀比對。工具未執行素材內腳本、未下載素材／解析器、未啟動原軟體。
- 自製PSD另以可用Pillow解碼：PSD、1×1、RGB、像素(128,160,144)。這只獨立證明該PSD不是改副檔名的假檔；Pillow不是本版依賴，不代表原生圖層／字型／智慧型物件檢查已實作。PSB依Adobe規格生成，測試限header分類。

## 測試範圍

正常與缺素材glTF/GLB/OBJ/MTL、中文檔名、負索引／無材質群組、外部／data URI／bufferView圖片、索引／buffer範圍、MAT3欄padding、稀疏索引、材質／texture／node引用、節點循環、壓縮明列未解碼、未知版本、壞檔、單檔／混合批次、Unity GUID/fileID／缺meta／重複／built-in／Package／二進位／跨專案索引、大小寫、絕對／遠端／百分比編碼路徑遮蔽、symlink、FIFO、讀取／解碼／primitive上限、唯讀hash、固定報告欄位、Markdown不產生活動圖片、CLI防覆寫與輸出範圍。

沒有FBX或AI原生fixture，因此沒有這些格式原生解析通過宣稱。自製Unity文字fixtures只是結構單元案例，未以Editor完整載入；不宣稱實機畫面正常。

## 四類實際報告

- normal3d：{"ERROR": 0, "WARNING": 0, "INFO": 3, "NOT_CHECKED": 8}
- missing：{"ERROR": 4, "WARNING": 0, "INFO": 2, "NOT_CHECKED": 5}
- unity-issues：{"ERROR": 5, "WARNING": 1, "INFO": 3, "NOT_CHECKED": 5}
- unverified：{"ERROR": 0, "WARNING": 0, "INFO": 0, "NOT_CHECKED": 4}

正常3D亦保留NOT_CHECKED，不能稱全部驗證通過。缺素材出現四個引用錯誤，其中一份MTL也在OBJ鏈及獨立檢查中各有證據；不是宣稱四個不同素材。Unity重複GUID對各受影響檔案各列一項，並將材質／shader／texture缺GUID分開。原生格式未驗證以真實自製PSD/PSB展示，不拿假AI／FBX當fixture。

## 已知限制與發布前步驟

能力矩陣是唯一支援邊界；glTF非完整Validator、OBJ非所有方言、Unity非完整YAML／匯入／渲染驗證。FBX只選型ufbx，尚未導入；AI／PSD原生連結及字型仍NOT_CHECKED。無外部搜尋，不自動修復。安全讀取有平台差異，詳細見references/rules.md。

MIT為草稿，著作權人待確認。確認後才建立倉庫、替換README網址、審閱打包內容、推送並在乾淨環境測試安裝；本次沒有執行任何公開發布。

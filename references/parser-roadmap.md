# 分階段解析器決策

本版運作依賴：Python 3.10+ 標準函式庫。沒有pip依賴或內附二進位；本版不會自動下載／安裝以下任何候選。

## FBX — 選定 ufbx，未整合

下一階段固定候選基線：ufbx **0.23.1**，採其雙授權中的 **MIT** 選項，保留原作者聲明。這是來源研究與選型，不是已供本版使用的解析器。

[上游README](https://github.com/ufbx/ufbx/blob/main/README.md)宣告ASCII／binary自3000起；[changelog](https://github.com/ufbx/ufbx/blob/main/misc/changelog.md)記錄對<3000或>7700警告及0.23.1安全修正。[授權](https://github.com/ufbx/ufbx/blob/main/LICENSE)允許MIT選項。未來導入時仍須核對固定版本原始碼、實際版本邊界、限制外部檔案open callback、關閉不需要的cache/XML讀取、加入記憶體／時間限制，再用合法ASCII/binary各版本fixture實測。本工具目前對所有FBX版本都是NOT_CHECKED，不能援引上游範圍當作自己的支援聲明。

## PSD/PSB — 候選 psd-tools，未整合

候選基線 **psd-tools 1.26.0**、MIT。上游可讀低階PSD/PSB結構，智慧型物件／linked-layer有API，但並不代表本套件已驗證引用。正式導入前需固定所有傳遞依賴、保留授權並審核untrusted-file建議，以合法外部連結／嵌入智慧型物件及字型狀態fixtures測試。現有自製PSD/PSB只測檔頭分類，沒有任何原生圖層解析宣稱。

## AI — 未選定完整原生解析器

不能用PDF parser的資訊冒充AI原生內容。後續可針對PDF相容子集選定有授權的PDF解析器並另作能力／fixture驗證；外部連結、嵌入、轉外框及字型引用須有可追溯證據。遇到不公開或無法解析的原生內容，依使用者同意在Illustrator的Links／字型檢查介面確認；本版不啟動Illustrator。

檢查器擴充方式：新增adapters模組→在CLI分流→加入同一問題結構→合法fixture與正反測試→更新能力矩陣。未完成測試的功能維持NOT_CHECKED，不提供假開關或假修復。

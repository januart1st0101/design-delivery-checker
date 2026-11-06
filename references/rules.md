# 規則與安全邊界

固定報告頂層：report_version → created_at（UTC ISO8601）→ scope → overview → files → issues → not_checked → recommendations → integrity。Markdown順序同樣為版本/時間/範圍、總覽、各檔及覆蓋、問題表、未驗證項、建議。

每個問題固定 severity、rule_id、file、reference、evidence、impact、suggestion。ERROR是本工具發現結構／索引／可定位引用問題；WARNING是交付風險或候選；INFO提供依據；NOT_CHECKED代表未驗證，絕不算通過。Unity GUID缺失仍稱候選，因靜態檔不代表Editor匯入結果。

主要規則家族：PATH_*（絕對／遠端／大小寫／根目錄外）、REF_*（缺檔／受限）、GLTF_*、BUFFER_*、VIEW_*、ACCESSOR_*、SPARSE_*、POSITION_*、GEOMETRY_INDEX、NODE_*、OBJ_*、MTL_*、UNITY_*、NATIVE_PARSER_UNAVAILABLE、FONT_STATUS_UNKNOWN、READ_LIMIT、SCAN_LIMIT。對應精確證據及影響在每份報告中生成。

路徑同時保留reference（相對引用原文）和evidence中的解析位置；絕對／遠端原文因隱私以<ABSOLUTE>/檔名、<REMOTE>/檔名遮蔽，不儲存憑證或query。一般相對路徑不因遮蔽而改寫。Windows反斜線做警告後按分隔符解析；不自動重新連結。..只允許正規化後仍留在root內，不讀根外。大小寫檢查依目錄實際列名，不依賴macOS不分大小寫的exists結果。

單檔scope為其父資料夾，但只解析該檔及其引用，不自動掃父資料夾所有檔案建立Unity索引。資料夾scope為指定root，輸出必須在root外且不得覆寫既有檔案。沒有外部搜尋／候選自動接回功能。要檢查另外的素材資料夾，須由使用者重新指定足夠的交付root，而非工具偷偷擴大範圍。

每檔16MiB、累計完整讀取64MiB、最多2000檔／目錄；小檔頭嗅探另讀最多513 bytes，用於分流而非內容驗證。每個accessor最多一百萬元素、各glTF主要物件陣列最多十萬項；每檔最多解碼二百萬個分量、一萬個primitive，已解碼accessor會快取，避免重複建立大型陣列。data URI同樣受讀取上限限制；不解壓壓縮extension。這些上限避免一般誤用，不是OS層CPU／記憶體沙箱；惡意巨量目錄列舉仍建議在隔離環境執行。

不跟隨檔案或目錄symlink（即使仍在root內）；POSIX使用dir_fd＋O_NOFOLLOW逐級開啟，Windows等平台採正規化邊界／symlink檢查fallback，對有敵意的同時改檔不是完整沙箱。根目錄不可是symlink。未知格式不執行；不讀遠端URL、不下載工具、依賴、素材或字型，不啟動原軟體。

僅在已辨識Unity專案根層跳過Library、Temp、Logs、obj；一般目錄的obj仍掃描。另跳過.git、.svn、node_modules、__pycache__，全部列NOT_CHECKED。無法列舉的目錄亦列未驗證。不刪快取或重建meta。索引因限制未讀完整時不把未知GUID一概報確定缺失；Package只讀manifest與交付包中可讀meta，不下載或讀Library快取。

完整讀過的檔案記錄SHA-256並在最後安全重讀比對；原創fixture測試另比對整個來源樹hash，證明工具不改來源。這不等於判定程式外部所有資產從未被其他程式修改。請以靜止的交付副本檢查。

單位：glTF按規格公尺、右手、Y-up；OBJ、原生FBX（未解析）不猜單位或正面。名稱政策不預設唯一，空節點／群組與無材質物件合法。像素／字型／授權／原生渲染結果不能用檔案存在取代驗證。

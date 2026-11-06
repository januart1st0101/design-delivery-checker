# 設計檔交付健檢 design-delivery-checker

**0.1.0 公開預覽版。** 唯讀檢查單檔、專案或混合資料夾，依格式自動分流，不必湊齊所有格式。結果分ERROR / WARNING / INFO / NOT_CHECKED；無錯誤只代表「已執行範圍內未發現問題」。

[閱讀圖文教學](https://github.com/januart1st0101/design-delivery-checker/blob/main/article.md) · [下載完整 Skill ZIP](https://github.com/januart1st0101/design-delivery-checker/raw/refs/heads/main/design-delivery-checker.zip)

## 真正完成哪些

| 格式 | 本版支援深度 |
|---|---|
| glTF 2.0 / GLB 2 | 核心結構、buffer/view/accessor與幾何索引範圍、外部／data URI／bufferView圖片來源、材質貼圖引用、節點階層、可解碼的未壓縮三角形統計；非完整規格／渲染驗證 |
| OBJ / MTL | face索引、群組、無材質物件、MTL與常見map引用、相對路徑／大小寫；自由曲面等列未驗證 |
| Unity文字 | 專案結構、meta GUID、重複GUID與缺meta、flow引用的GUID/fileID候選、內建資源／Package分類；匯入子資產、二進位、管線相容性與畫面列未驗證 |
| FBX、AI、PSD/PSB | **原生解析未完成**，只有可辨識檔頭的分類。FBX無原生fixture；AI無fixture；PSD/PSB有真正自製小色塊但只測檔頭。不能作素材／字型完整性保證 |

完整的「已實作並測試／部分支援／未支援」見[能力矩陣](references/capabilities.md)。FBX已選定後續ufbx解析方案，詳見[路線圖及授權](references/parser-roadmap.md)。沒有自動下載、安裝或假功能按鈕。

## 安裝與確認

核心只需Python **3.10+**標準函式庫，無API金鑰、無pip依賴。這裡的Python程式不會連網。Codex本身仍依使用者帳號及設定運作。

依[OpenAI官方格式](https://learn.chatgpt.com/docs/build-skills)（2026-11-01核對），將整個資料夾複製至 `~/.agents/skills/design-delivery-checker/`；專案限定則放到該專案 `.agents/skills/design-delivery-checker/`。必須一併保留adapters、scripts、references，不能只複製SKILL.md。已有同名技能時先審閱版本，不直接覆蓋。

技能選單應能找到「設計檔交付健檢」，或明確輸入 `$design-delivery-checker`。未出現時重新啟動Codex。成功確認方式：對examples/fixtures/normal3d執行，實際產生Markdown＋JSON，並有NOT_CHECKED範圍說明；只回一句「可以交付」不是成功。

可請 `$skill-installer` 從 [GitHub 倉庫](https://github.com/januart1st0101/design-delivery-checker) 的根目錄安裝完整套件。

## 自然語言用法

```text
用設計檔交付健檢檢查這個資料夾，找缺貼圖、外部素材與字型風險，不要改檔；不能驗的請列出。
```

```text
使用 $design-delivery-checker 檢查這一個GLB，只檢查它和根目錄內的引用。報告放在另外的資料夾，不要上傳任何資產。
```

```text
用設計檔交付健檢掃這個Unity專案，區分缺材質、缺貼圖、缺shader、Package未驗證與渲染管線相容性，不要刪Library或重建meta。
```

第一個例句中的字型風險，在本版AI/PSD會明確回答「無法判斷」，不是假裝已讀字型。以後原生解析器有實測後才擴大支援。

## CLI

在套件根目錄：

```sh
python3 scripts/check.py --help
python3 scripts/check.py examples/fixtures/normal3d --output output/normal3d
python3 scripts/check.py examples/fixtures/missing --output output/missing
python3 scripts/check.py examples/fixtures/unity-issues --output output/unity
python3 scripts/check.py examples/fixtures/unverified --output output/unverified
```

輸出 `<前綴>.md` 和 `<前綴>.json`；不覆寫既有檔案。輸入資料夾時報告必須在它外面。本例output是fixtures外，符合規則。單檔預設根目錄為父資料夾，但不額外全面掃描父資料夾；Unity完整GUID索引要提供專案根目錄。

退出碼：0無ERROR（仍可能有WARNING/NOT_CHECKED）、1有ERROR且已寫報告、2輸入／輸出條件錯誤。限制可明確設定 `--max-file-mb`、`--max-total-mb`、`--max-files`；預設16MiB／64MiB／2000。超限會列未驗證，不把略過視為通過。

## 報告預覽

| 類別 | 實際報告 | 預期觀察 |
|---|---|---|
| 正常3D | [Markdown](examples/reports/normal3d.md) · [JSON](examples/reports/normal3d.json) | 外部與內嵌引用存在；仍列動畫／渲染等未驗證 |
| 缺素材 | [Markdown](examples/reports/missing.md) · [JSON](examples/reports/missing.json) | glTF/GLB/MTL的引用缺失 |
| Unity引用問題 | [Markdown](examples/reports/unity-issues.md) · [JSON](examples/reports/unity-issues.json) | 缺GUID、重複GUID、缺meta候選，內建引用不誤報 |
| 無法驗證原生格式 | [Markdown](examples/reports/unverified.md) · [JSON](examples/reports/unverified.json) | 真正自製PSD/PSB，只辨識檔頭，原生素材／字型未驗證 |

每份報告固定含時間／範圍、總覽、各檔覆蓋、問題表、未驗證項及建議。問題表固定為「嚴重度、規則ID、相對檔案位置、引用對象、證據、影響、建議」。

## 測試與fixture來源

```sh
python3 -m unittest discover -s tests -v
# 需要重新生成一份測試素材時，指定全新資料夾；這不是修復使用者專案。
python3 tests/make_fixtures.py /path/to/new-fixtures
```

fixtures皆為自製：三角形glTF/GLB、OBJ/MTL、PNG、Unity文字引用案例、依Adobe規格生成的PSD/PSB。沒有改副檔名冒充AI/FBX，也未把Unity文字單元案例說成Editor輸出。壓縮extension的負測試只有測「應標未解碼」，不聲稱壓縮bitstream有效。詳見[fixture來源](examples/FIXTURES.md)及[測試報告](tests/RESULTS.md)。

## 隱私與限制

不改原檔、不重連、不執行輸入腳本、不啟動原軟體、不抓遠端素材或字型、不自動公開GitHub。預設跳過快取／版本控制目錄並列出；不刪Library或.meta。

只讀指定根目錄內的相對引用，拒絕symlink及根目錄外讀取。沒有外部搜尋功能；跨資料夾檢查須由使用者另指定完整交付root。絕對／遠端引用會遮蔽私人路徑及URL憑證；報告仍可能包含你輸入檔案的相對名稱與素材資訊，分享前請審閱。詳細安全界線及平台差異見[規則](references/rules.md)。

不是完整glTF Validator、Unity Editor或Adobe原生解析器，不保證實際畫面。缺GUID可能來自未隨附Package；匯入子資產fileID另列未驗證。Shader缺引用與管線不相容是不同問題，後者本版只能列NOT_CHECKED。字型可用性與授權不能由本機有無字型決定。

## 授權

此公開預覽版尚未指定開源授權。

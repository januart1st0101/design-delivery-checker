# 原創測試資料

由tests/make_fixtures.py生成；沒有下載第三方檔案、圖像或字型。

- glTF/GLB：一個3頂點三角形，unsigned short索引，合法空群組、場景、材質與PNG引用。GLB包含BIN與data URI圖片，另一GLB用bufferView圖片。missing版本故意移除被引用圖片。PNG為zlib壓縮1×1紅像素。
- OBJ/MTL：3頂點、三角形、合法多group與負索引；一個無材質物件。MTL引用中文檔名PNG及常見map選項；缺素材版本故意引用不存在檔案。
- Unity：依Unity文字序列化結構生成最小單元測試內容，涵蓋GUID、local fileID、null與built-in參照。這不是經Unity Editor認證可開啟的完整遊戲專案；沒有腳本或真實Package依賴。
- PSD/PSB：Adobe公開規格的真正8BPS header v1/v2、空color/resources/layer段與raw planar 1×1 RGB。沒有文字、智慧型物件或外部素材，所以只能測「檔頭分類與誠實列未驗證」，不能證明原生引用解析。PSD另以可用Pillow驗證可讀像素，結果記在測試報告；Pillow非核心依賴。
- 不包含FBX或AI fixture；沒有對這兩種格式作原生解析通過宣稱。測試中的壞檔／超限／故意錯誤結構只驗證拒絕行為。

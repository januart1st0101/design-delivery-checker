# 一手來源與核對日期

核對：2026-11-01。以下為設計依據，沒有複製上游解析程式或測試素材。

- [OpenAI Build skills](https://learn.chatgpt.com/docs/build-skills)：SKILL.md name/description、資源目錄、.agents/skills與明確呼叫。技能初始化與驗證使用本機skill-creator。
- [Khronos glTF 2.0規格](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html)：GLB、buffer、accessor、稀疏索引、場景階層與座標。工具不是Khronos Validator。
- [Unity文字場景範例](https://docs.unity3d.com/es/2018.3/Manual/YAMLSceneExample.html)：Unity YAML標頭、anchor與fileID引用。本版僅靜態子集，沒有據此宣稱所有Editor版本相容。
- [ufbx上游](https://github.com/ufbx/ufbx/blob/main/README.md)、[授權](https://github.com/ufbx/ufbx/blob/main/LICENSE)、[版本紀錄](https://github.com/ufbx/ufbx/blob/main/misc/changelog.md)：未來FBX解析器的選型依據。
- [Adobe Photoshop File Formats](https://www.adobe.com/devnet-apps/photoshop/fileformatashtml/)：自製PSD/PSB檔頭、長度段與raw RGB測試檔的結構依據。
- [psd-tools文件](https://psd-tools.readthedocs.io/en/latest/)、[授權](https://github.com/psd-tools/psd-tools/blob/main/LICENSE)：下一階段候選，尚未安裝或整合。

OBJ/MTL本版只作文字網格與常見貼圖引用子集，不宣稱完全涵蓋Wavefront或各DCC匯出器方言；未知語句／map option明列未驗證。

# 文件与证据索引（Qoder 侧）

时间 Asia/Shanghai。核验方式均为实际读取文件或实际计算哈希，不是引用摘要。

## E 盘工作区

- `E:/Qoder_RF11_Sim/AGENTS.md`：本侧规则（E 盘产出、D 盘只读、两代理分开、GitHub 上传范围）。
- `E:/Qoder_RF11_Sim/memory/`：CURRENT_STATE.md、DECISIONS.md、OPEN_QUESTIONS.md、ARTIFACTS.md、
  README.md、logs/。
- `E:/Qoder_RF11_Sim/reference/codex_memory_snapshot_20261017/`：Codex 记忆 16 份只读快照 +
  `PROVENANCE.md`（逐文件 SHA256 与 D 盘原件一致；唯一未复制项为 Codex 自身的 memory/AGENTS.md）。
- `E:/Qoder_RF11_Sim/work/sysinfo/get_memory_state.ps1`：机器状态只读采集脚本。
- `E:/Qoder_RF11_Sim/work/pylib/`：gdstk 1.0.1（cp314 wheel），仅本工作区使用，未改系统 Python。

## V24 原始数据核验产物（`work/hfss_al_sio2/`）

| 文件 | 内容 | SHA256（前 16 位） |
| --- | --- | --- |
| `v24_gds_inventory.json` | 两份 GDS 的 cell、层多边形数、面积、顶点数、bbox、unit/precision | `9e7dccf7aeb70277` |
| `v24_layer_analysis.json` | 逐层逐图形全量分析 | `ac3c407e626440d9` |
| `v24_layer_assignment.json` | 16 个 Via 的晶圆面直径与逐层金属包围（cover/near） | `1550bda37f7a28bc` |
| `v24_device_split.json` | 以 L3 大图行为器件窗口的分层清点 | `ca2481e3f9eeb70e` |
| `v24_structure_by_device.json` | 窗口法逐器件清点（含 L1 17/21/21/18 的不等计数） | `d1e33f03bcc6e82a` |
| `v24_dev1_model_data.json` | DEV1 全部顶点表（晶圆面，含 Via 连通与 PAD 开窗） | `7b655c4e833d1624` |
| `仿真输入规格_20261017.md` | 层叠候选、材料假设与敏感性扫描、求解与验收链 | `07620f2e7779eae5` |

对应脚本同名 `.py`。本轮新增、尚未运行完的：`v24_device_assignment_full.py`
（最近中心分配，输出 `v24_device_assignment_full.json`，结果 L1 18/22/22/18）与
`v24_device_functional_sets.py`（功能图形与工艺标记分离 + 指纹比对，**待运行**）。

## D 盘只读来源（不修改）

- V24 制版 GDS：`D:/Codex_RF11_Project/outputs/ASML_100D_OCTAGON_4IN1_7P2_CHROME_V24/`
  `ASML_100D_OCTAGON_4L_STACKED_EXTERNAL_BAR_ONLY_REVIEW_V24.gds`
  SHA256 `d5d2a4daff0d6608f3ddb23c61d13621e2a1f7cabe900989d072a7c05bdf6b51`（2026-10-17 重算，与记录一致）。
- 同目录透光功能数据 `ASML_100D_OCTAGON_4IN1_7P2_TONE_D_CLEAR_FEATURES_L1_V24.gds`（164 多边形）。
- 旧铜/PI 论文稿：`D:/Codex_RF11_Project/workspaces/20260928_thesis/outputs/`
  `微变压器的设计和工艺研究_章节合并与润色版_20260929.docx`
  SHA256 `f45af7cd2d490a47d5c088e3b1c5f7cb1b22cea192bbf22d18002522201a5b83`（2026-10-17 重算，与记录一致）。
- 旧 RF11 HFSS 构建脚本：`D:/.../hfss_2mm_refinement/scripts/Build_NCOCT_RF11_RF06_DENSE_HFSS2018.py`
  （520 行，HFSS 2018；可复用 API 框架，绕组坐标为硬编码点列，几何不可复用；
  第 513 行保存路径含历史 C 盘绝对路径，复用前必须改到 E 盘）。

## 交付状态

`E:/Qoder_RF11_Sim/outputs/` 目前为空：没有新电磁结果、没有新交付文档。GitHub 首次推送尚未发生。

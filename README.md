# 磁隔离变压器 · Qoder 侧工作区（E:/Qoder_RF11_Sim）

本目录是 **Qoder 侧**的项目档案，与 Codex 侧的 `D:/Codex_RF11_Project` 分开维护：
两边互不覆盖；同一事实出现分歧时，以用户最新明确答复和原始文件核验为准，并在
`memory/CURRENT_STATE.md` 标注分歧点。

- 规则与边界：`AGENTS.md`
- 记忆档案：`memory/`（当前状态、决策、待核实、文件索引、按日日志）
- 上游历史快照（只读参照，不在此仓库重复上传）：`reference/codex_memory_snapshot_20261017/`
- 工作产物：`work/`（分析脚本、提取数据、规格说明）
- 交付物：`outputs/`

## 远端仓库

`https://github.com/yt2088168886-star/Qoder-.git`，分支 `main`，私有仓库。

推送范围只含小型记忆文档、日志、方法与规格说明、分析脚本和小型索引。**不推送**原始 GDS、
HFSS 工程与结果缓存、实测原始数据、论文 Word 全文、顶点级图形/网表 JSON、Codex 记忆快照、
作者姓名等个人标识、设备账号与令牌。每次同步的实际文件与 SHA256 记录在
`memory/remote_push_manifest.json`，同步结果与 commit SHA 记录在 `memory/sync-state.json`。

## 研究边界（摘要）

课题为片上磁隔离微变压器的结构设计、仿真优化与工艺制备。当前 Qoder 侧任务是
2026-10-13 确认的新材料路线（PECVD SiO₂ 介质 + 磁控溅射铝绕组）的 HFSS 仿真准备。
设备配方与薄膜实测**尚未取得**，因此所有材料参数按公开标注的假设值 + 敏感性扫描处理；
旧铜/PI 模型结果只作历史对照，不通过改名当作新路线性能；未收敛的求解不写成结果。

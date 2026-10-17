# -*- coding: utf-8 -*-
"""生成 Qoder 侧 GitHub 首次推送清单：按上传范围规则筛文件、算 SHA256、查体积，
并对明显凭据做自检。只读 E 盘本地文件，写 E 盘清单。
范围：记忆文档、日志、方法与规格说明、分析脚本、小型索引 JSON。
排除：原始 GDS、HFSS 工程与缓存、实测原始数据、Word 全文、顶点级网表、Codex 快照、作者标识。
"""
import hashlib
import json
import os
import re

ROOT = r"E:\Qoder_RF11_Sim"
OUT = os.path.join(ROOT, "memory", "remote_push_manifest.json")
MAX_BYTES = 200 * 1024

INCLUDE_DIRS = [r"memory", r"work\hfss_al_sio2", r"work\sysinfo"]
INCLUDE_ROOT_FILES = ["AGENTS.md", "README.md"]
INCLUDE_WORK_FILES = ["build_remote_manifest.py", "build_sync_snapshot.py"]
for name in INCLUDE_WORK_FILES:
    p = os.path.join(ROOT, "work", name)
    if os.path.isfile(p):
        INCLUDE_ROOT_FILES.append(os.path.join("work", name).replace(os.sep, "/"))
EXCLUDE_SUBSTR = [
    "/pylib/",
    "codex_memory_snapshot",
    "/outputs/",
    "/.sync/",
    "memory/remote_push_manifest.json",   # 清单自身，单独随快照推送
    "_model_data.json",          # 顶点级图形数据，留本地
    "v24_layer_analysis.json",   # 全量分析，留本地
    "v24_structure_by_device.json",
    "v24_device_split.json",
    "v24_layer_assignment.json",
    "v24_device_assignment_full.json",
    "smoke",                     # 另一并发会话 19:00 起的 HFSS 试跑，非本档案内容
    "run_aedt_task.ps1",
    "v24_geometry_qa",
]
SECRET_RE = re.compile(
    r"(ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|gho_[A-Za-z0-9]{20,}|"
    r"BEGIN (RSA|OPENSSH|EC) PRIVATE KEY|Authorization:\s*Bearer\s+\S{16,}|"
    r"[A-Za-z0-9+/]{40,}==)", re.I)

files = []
for name in INCLUDE_ROOT_FILES:
    p = os.path.join(ROOT, name)
    if os.path.isfile(p):
        files.append(p)
for d in INCLUDE_DIRS:
    base = os.path.join(ROOT, d)
    for dirpath, _, names in os.walk(base):
        for n in sorted(names):
            files.append(os.path.join(dirpath, n))

entries, flags = [], []
for p in files:
    rel = os.path.relpath(p, ROOT).replace(os.sep, "/")
    if any(x in ("/" + rel) for x in EXCLUDE_SUBSTR):
        continue
    size = os.path.getsize(p)
    with open(p, "rb") as fh:
        raw = fh.read()
    sha = hashlib.sha256(raw).hexdigest()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        flags.append("non-utf8 skipped: " + rel)
        continue
    hits = SECRET_RE.findall(text)
    if hits:
        flags.append("SECRET-LIKE in " + rel)
    if size > MAX_BYTES:
        flags.append("too large skipped: %s (%d B)" % (rel, size))
        continue
    entries.append({"path": rel, "bytes": size, "sha256": sha})

entries.sort(key=lambda e: e["path"])
manifest = {
    "generated_at": "2026-10-17",
    "timezone": "Asia/Shanghai",
    "repository": "yt2088168886-star/Qoder-",
    "remote_url": "https://github.com/yt2088168886-star/Qoder-.git",
    "branch": "main",
    "upload_scope": "Qoder 侧记忆文档、日期日志、方法与规格说明、分析脚本、小型索引",
    "excluded": ["原始 GDS", "HFSS 工程与结果缓存", "实测原始数据", "论文 Word 全文",
                  "顶点级图形/网表 JSON", "Codex 记忆快照", "作者姓名等个人标识", "设备账号与令牌"],
    "preconditions": ["仓库须为 private（用户 2026-10-17 决定）",
                       "推送通道可用（GitHub 连接器工具或本地 git + GCM）"],
    "concurrency_note": "2026-10-17 19:00 起另一会话在同一 E 工作区写入 HFSS 试跑文件"
                        "（smoke_api_test.py、run_aedt_task.ps1、v24_geometry_qa.*、logs/smoke19_*），"
                        "属进行中的他方工作，已从本推送清单排除。",
    "file_count": len(entries),
    "total_bytes": sum(e["bytes"] for e in entries),
    "files": entries,
    "self_check_flags": flags,
}
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(manifest, fh, ensure_ascii=False, indent=1)

print("files: %d, total %d bytes" % (len(entries), manifest["total_bytes"]))
for e in entries:
    print("  %9d  %s  %s" % (e["bytes"], e["sha256"][:12], e["path"]))
print("flags:", flags or "none")
print("manifest:", OUT)

# -*- coding: utf-8 -*-
"""把推送清单里的文件复制成一份带时间戳的远端快照，避免与同工作区的并发会话抢文件。
复制后逐个重算 SHA256 与清单比对；只写 E 盘，不联网、不建 .git、不推送。
"""
import hashlib
import json
import os
import shutil

ROOT = r"E:\Qoder_RF11_Sim"
MANIFEST = os.path.join(ROOT, "memory", "remote_push_manifest.json")
STAMP = "20261017"
DEST = os.path.join(ROOT, ".sync", STAMP)

with open(MANIFEST, encoding="utf-8") as fh:
    manifest = json.load(fh)

if os.path.isdir(DEST):
    shutil.rmtree(DEST)
os.makedirs(DEST, exist_ok=True)

copied, mismatched, missing = [], [], []
for entry in manifest["files"]:
    src = os.path.join(ROOT, entry["path"].replace("/", os.sep))
    if not os.path.isfile(src):
        missing.append(entry["path"])
        continue
    with open(src, "rb") as fh:
        raw = fh.read()
    sha = hashlib.sha256(raw).hexdigest()
    if sha != entry["sha256"]:
        mismatched.append(entry["path"])   # 源文件在清单生成后被改动
        continue
    dst = os.path.join(DEST, entry["path"].replace("/", os.sep))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    copied.append({"path": entry["path"], "bytes": len(raw), "sha256": sha})

# 清单自身随快照一起推送（其 SHA256 无法写进自己，故由 SNAPSHOT.json 记录）
dst_manifest = os.path.join(DEST, "memory", "remote_push_manifest.json")
os.makedirs(os.path.dirname(dst_manifest), exist_ok=True)
shutil.copy2(MANIFEST, dst_manifest)
with open(MANIFEST, "rb") as fh:
    manifest_sha = hashlib.sha256(fh.read()).hexdigest()

out = {"snapshot": ".sync/%s" % STAMP, "source_manifest": "memory/remote_push_manifest.json",
       "source_manifest_sha256": manifest_sha,
       "repository": manifest["repository"], "branch": manifest["branch"],
       "file_count": len(copied) + 1,
       "total_bytes": sum(c["bytes"] for c in copied) + os.path.getsize(dst_manifest),
       "excluded_after_manifest": mismatched, "missing_after_manifest": missing,
       "files": copied, "pushed": False,
       "pending": ["仓库转 private", "推送通道（新会话用 GitHub 连接器 / 或本地 git + GCM）"]}
with open(os.path.join(DEST, "SNAPSHOT.json"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, ensure_ascii=False, indent=1)

print("snapshot files: %d, %d bytes" % (len(copied), out["total_bytes"]))
print("changed after manifest:", mismatched or "none")
print("missing after manifest:", missing or "none")
print("dest:", DEST)

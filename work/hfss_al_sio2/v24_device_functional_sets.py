# -*- coding: utf-8 -*-
"""V24 器件一致性严格检验：把每层图形按尺寸分成"功能图形"与"工艺标记"，
只对功能图形做相对坐标指纹比对，回答"四合一是否为同一设计的四份复制"，
并给出建单器件模型所需的完整功能图形集。只读 D 盘 GDS，输出 E 盘 JSON。
"""
import json
import math
import sys

sys.path.insert(0, r"E:\Qoder_RF11_Sim\work\pylib")
import gdstk

GDS = (r"D:\Codex_RF11_Project\outputs\ASML_100D_OCTAGON_4IN1_7P2_CHROME_V24"
       r"\ASML_100D_OCTAGON_4L_STACKED_EXTERNAL_BAR_ONLY_REVIEW_V24.gds")
OUT = r"E:\Qoder_RF11_Sim\work\hfss_al_sio2\v24_device_functional_sets.json"
SCALE = 5.0
CENTERS = [(-7176.7, -7467.4), (-7176.7, 7532.6), (7823.3, -7467.4), (7823.3, 7532.6)]

lib = gdstk.read_gds(GDS)
cell = lib.top_level()[0]


def diag(w, h):
    return math.hypot(w, h)


rows = []
for p in cell.polygons:
    (x0, y0), (x1, y1) = p.bounding_box()
    w, h = x1 - x0, y1 - y0
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    dev = min(range(4), key=lambda i: (cx - CENTERS[i][0]) ** 2 + (cy - CENTERS[i][1]) ** 2)
    dw, dh = w / SCALE, h / SCALE
    narrow = min(dw, dh)
    if narrow < 2.5:
        cls = "marker_thin"          # 宽 ~1 um 条形标记
    elif p.layer == 2 and abs(dw - dh) < 0.5 and dw < 12:
        cls = "via"                  # 近圆小图形 = Via 开口
    elif max(dw, dh) < 25:
        cls = "marker_small"
    else:
        cls = "functional"
    rows.append({"layer": "L%d/%d" % (p.layer, p.datatype), "dev": dev, "cls": cls,
                 "rel": [round((cx - CENTERS[dev][0]) / SCALE, 2),
                         round((cy - CENTERS[dev][1]) / SCALE, 2)],
                 "size": [round(dw, 3), round(h, 3)], "nverts": len(p.points),
                 "area": round(abs(p.area()) / (SCALE * SCALE), 3),
                 "pts": [[round(x, 3), round(y, 3)] for x, y in p.points]})

summary = {}
for r in rows:
    summary.setdefault(r["dev"], {}).setdefault(r["layer"], {}).setdefault(r["cls"], 0)
    summary[r["dev"]][r["layer"]][r["cls"]] += 1

print("=== per-device / per-layer / class counts (wafer side) ===")
for d in sorted(summary):
    print("DEV%d" % (d + 1))
    for L in sorted(summary[d]):
        print("   ", L, summary[d][L])

# 功能图形指纹：忽略标记类，比较相对中心 + 尺寸 + 顶点数
fps = {}
for d in range(4):
    s = set()
    for r in rows:
        if r["dev"] == d and r["cls"] in ("functional", "via"):
            s.add((r["layer"], tuple(r["rel"]), tuple(r["size"]), r["nverts"]))
    fps[d] = s

print("\n=== functional+via fingerprint overlap ===")
for i in range(4):
    print("DEV%d size %d" % (i + 1, len(fps[i])))
for i in range(4):
    for j in range(i + 1, 4):
        a, b = fps[i], fps[j]
        print("DEV%d vs DEV%d common=%d onlyA=%d onlyB=%d" % (
            i + 1, j + 1, len(a & b), len(a - b), len(b - a)))

print("\n=== DEV1 vs DEV2 symmetric difference detail ===")
for it in sorted(fps[0] ^ fps[1]):
    print("   ", it)

out = {"scale": SCALE, "centers_mask_um": CENTERS, "classification": summary,
       "devices": [{"name": "DEV%d" % (d + 1), "center_mask_um": list(CENTERS[d]),
                    "functional_sets": {L: [r for r in rows if r["dev"] == d and r["layer"] == L
                                            and r["cls"] in ("functional", "via") and r["nverts"] > 0]
                                        for L in sorted({r["layer"] for r in rows if r["dev"] == d})}}
                   for d in range(4)]}
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(out, fh, ensure_ascii=False)
print("\nwritten:", OUT)

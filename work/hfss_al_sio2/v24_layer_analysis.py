# -*- coding: utf-8 -*-
"""V24 GDS 逐层几何分析：确认尺度倍率、区分绕组/跨线/Via/PAD图形。
只读 D 盘，输出 E 盘 JSON + 控制台摘要。
"""
import json
import math
import os
import sys

sys.path.insert(0, r"E:\Qoder_RF11_Sim\work\pylib")
import gdstk

REVIEW = r"D:\Codex_RF11_Project\outputs\ASML_100D_OCTAGON_4IN1_7P2_CHROME_V24\ASML_100D_OCTAGON_4L_STACKED_EXTERNAL_BAR_ONLY_REVIEW_V24.gds"
OUT = r"E:\Qoder_RF11_Sim\work\hfss_al_sio2\v24_layer_analysis.json"

DBU_UM = 1.0  # 假定 1 dbu = 1 um（掩模面），下面用已知图形校验


def poly_metrics(p):
    x0, y0 = p.bounding_box()[0]
    x1, y1 = p.bounding_box()[1]
    w = (x1 - x0) * DBU_UM
    h = (y1 - y0) * DBU_UM
    area = abs(p.area()) * DBU_UM * DBU_UM
    per = p.perimeter() * DBU_UM
    # 圆度：4*pi*A/P^2，正多边形顶点多且接近1视为圆弧近似
    roundness = (4 * math.pi * area / (per * per)) if per > 0 else 0.0
    return {
        "layer": "%d/%d" % (p.layer, p.datatype),
        "x0": round(x0, 3), "y0": round(y0, 3), "x1": round(x1, 3), "y1": round(y1, 3),
        "w_um": round(w, 3), "h_um": round(h, 3),
        "cx": round((x0 + x1) / 2.0, 3), "cy": round((y0 + y1) / 2.0, 3),
        "area_um2": round(area, 1), "perim_um": round(per, 2),
        "nverts": len(p.points), "roundness": round(roundness, 4),
    }


lib = gdstk.read_gds(REVIEW)
cell = lib.top_level()[0]
print("cell", cell.name, "polygons", len(cell.polygons),
      "unit", lib.unit, "precision", lib.precision)

by_layer = {}
for p in cell.polygons:
    m = poly_metrics(p)
    by_layer.setdefault(m["layer"], []).append(m)

report = {"cell": cell.name, "unit": lib.unit, "precision": lib.precision,
          "layers": {}}
for layer, items in sorted(by_layer.items()):
    ws = sorted(set((it["w_um"], it["h_um"]) for it in items))
    print("\n### LAYER %s  count=%d  distinct_bbox_sizes=%d" % (layer, len(items), len(ws)))
    for w, h in ws[:14]:
        n = sum(1 for it in items if it["w_um"] == w and it["h_um"] == h)
        print("   %10.3f x %10.3f um  n=%d" % (w, h, n))
    if len(ws) > 14:
        print("   ...(%d more sizes)" % (len(ws) - 14))
    # 顶点数最多的小图形 = 疑似圆弧 Via
    small = [it for it in items if max(it["w_um"], it["h_um"]) < 200]
    small.sort(key=lambda it: -it["nverts"])
    for it in small[:8]:
        print("   SMALL nverts=%-4d round=%.4f %8.3f x %8.3f um @ (%.3f, %.3f)" % (
            it["nverts"], it["roundness"], it["w_um"], it["h_um"], it["cx"], it["cy"]))
    report["layers"][layer] = {"count": len(items), "sizes": [[w, h] for w, h in ws],
                               "polys": items}

with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(report, fh, ensure_ascii=False, indent=1)
print("\nwritten:", OUT)

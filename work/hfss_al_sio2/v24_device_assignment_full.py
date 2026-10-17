# -*- coding: utf-8 -*-
"""V24 四合一按器件完整分配：把每个多边形按几何中心指派到最近的器件中心，
核对四个子器件是否真的逐位相同，并为 HFSS 建模给出完整、无遗漏的每器件图形集。
只读 D 盘 GDS，写 E 盘 JSON。掩模面 -> 晶圆面 5:1。
"""
import json
import sys

sys.path.insert(0, r"E:\Qoder_RF11_Sim\work\pylib")
import gdstk

GDS = (r"D:\Codex_RF11_Project\outputs\ASML_100D_OCTAGON_4IN1_7P2_CHROME_V24"
       r"\ASML_100D_OCTAGON_4L_STACKED_EXTERNAL_BAR_ONLY_REVIEW_V24.gds")
OUT = r"E:\Qoder_RF11_Sim\work\hfss_al_sio2\v24_device_assignment_full.json"
SCALE = 5.0

# 上一轮由 Via 圆聚类得到的四个器件中心（掩模面 um）
CENTERS = [(-7176.7, -7467.4), (-7176.7, 7532.6), (7823.3, -7467.4), (7823.3, 7532.6)]

lib = gdstk.read_gds(GDS)
cell = lib.top_level()[0]

polys = []
for p in cell.polygons:
    (x0, y0), (x1, y1) = p.bounding_box()
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    d = [((cx - a) ** 2 + (cy - b) ** 2) ** 0.5 for a, b in CENTERS]
    order = sorted(range(4), key=lambda i: d[i])
    polys.append({
        "layer": p.layer, "datatype": p.datatype,
        "cx": cx, "cy": cy, "w": x1 - x0, "h": y1 - y0,
        "area": abs(p.area()), "nverts": len(p.points),
        "dev": order[0], "d0": d[order[0]], "d1": d[order[1]],
        "pts": [[round(x / SCALE, 4), round(y / SCALE, 4)] for x, y in p.points],
    })

result = {"scale": SCALE, "centers_mask_um": CENTERS, "devices": [], "unassigned_far": []}
for i, c in enumerate(CENTERS):
    items = [p for p in polys if p["dev"] == i]
    per_layer = {}
    for p in items:
        key = "L%d/%d" % (p["layer"], p["datatype"])
        rel = [round((p["cx"] - c[0]) / SCALE, 3), round((p["cy"] - c[1]) / SCALE, 3)]
        per_layer.setdefault(key, []).append({
            "rel_center_wafer_um": rel,
            "size_wafer_um": [round(p["w"] / SCALE, 4), round(p["h"] / SCALE, 4)],
            "area_wafer_um2": round(p["area"] / (SCALE * SCALE), 3),
            "nverts": p["nverts"],
            "assign_margin_um": round((p["d1"] - p["d0"]) / SCALE, 2),
            "points_wafer_rel_um": p["pts"],
        })
    counts = {k: len(v) for k, v in sorted(per_layer.items())}
    result["devices"].append({"name": "DEV%d" % (i + 1), "center_mask_um": list(c),
                              "counts": counts, "total": len(items), "layers": per_layer})

# 分配余量过小的图形（中心几乎等距于两个器件）单独列出，避免误判归属
result["unassigned_far"] = [{"layer": "L%d/%d" % (p["layer"], p["datatype"]),
                             "dev": p["dev"], "rel_center_wafer_um":
                             [round((p["cx"] - CENTERS[p["dev"]][0]) / SCALE, 3),
                              round((p["cy"] - CENTERS[p["dev"]][1]) / SCALE, 3)],
                             "size_wafer_um": [round(p["w"] / SCALE, 3), round(p["h"] / SCALE, 3)],
                             "assign_margin_um": round((p["d1"] - p["d0"]) / SCALE, 2)}
                            for p in polys if (p["d1"] - p["d0"]) / SCALE < 60.0]

with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(result, fh, ensure_ascii=False, indent=1)

print("whole-cell polygons:", len(polys))
for dv in result["devices"]:
    print(dv["name"], "total", dv["total"], dv["counts"])
print("tight-assignment polygons (<60 um margin):", len(result["unassigned_far"]))
for e in result["unassigned_far"]:
    print("   ", e["layer"], "dev", "DEV%d" % (e["dev"] + 1), "rel", e["rel_center_wafer_um"],
          "size", e["size_wafer_um"], "margin", e["assign_margin_um"])

# 逐位相同性检验：以 (layer, 取整相对中心, 尺寸, 顶点数) 为指纹比较四个器件
def fp(dv):
    s = set()
    for key, items in dv["layers"].items():
        for it in items:
            s.add((key, tuple(it["rel_center_wafer_um"]), tuple(it["size_wafer_um"]), it["nverts"]))
    return s

fps = [fp(dv) for dv in result["devices"]]
for i in range(4):
    for j in range(i + 1, 4):
        inter = len(fps[i] & fps[j])
        print("DEV%d vs DEV%d: |A|=%d |B|=%d common=%d" % (i + 1, j + 1, len(fps[i]), len(fps[j]), inter))
print("written:", OUT)

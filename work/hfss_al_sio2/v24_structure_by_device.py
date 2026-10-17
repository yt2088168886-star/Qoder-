# -*- coding: utf-8 -*-
"""V24 结构还原：用 16 个 Via 圆聚成 4 个器件，逐器件列出各层图形的晶圆面相对坐标与尺寸，
并计算器件总跨度以判定 2.8 mm 是掩模面还是晶圆面。只读 D 盘。
"""
import json
import math
import sys

sys.path.insert(0, r"E:\Qoder_RF11_Sim\work\pylib")
import gdstk

REVIEW = r"D:\Codex_RF11_Project\outputs\ASML_100D_OCTAGON_4IN1_7P2_CHROME_V24\ASML_100D_OCTAGON_4L_STACKED_EXTERNAL_BAR_ONLY_REVIEW_V24.gds"
OUT = r"E:\Qoder_RF11_Sim\work\hfss_al_sio2\v24_structure_by_device.json"
SCALE = 5.0

lib = gdstk.read_gds(REVIEW)
cell = lib.top_level()[0]

recs = []
for p in cell.polygons:
    (x0, y0), (x1, y1) = p.bounding_box()
    recs.append({"key": "L%d/%d" % (p.layer, p.datatype),
                 "x0": float(x0), "y0": float(y0), "x1": float(x1), "y1": float(y1),
                 "cx": (x0 + x1) / 2.0, "cy": (y0 + y1) / 2.0,
                 "w": float(x1 - x0), "h": float(y1 - y0),
                 "area": abs(p.area()), "nverts": len(p.points)})

circles = [r for r in recs if r["key"] == "L2/0" and r["nverts"] > 20 and r["w"] < 100]
print("via circles:", len(circles))

# 聚类：4 个器件 = 16 个 Via 的四群
centroids = []
for c in circles:
    placed = False
    for g in centroids:
        if math.hypot(g["cx"] / len(g["pts"]) - c["cx"], g["cy"] / len(g["pts"]) - c["cy"]) < 6000:
            g["cx"] += c["cx"]; g["cy"] += c["cy"]; g["pts"].append(c); placed = True
            break
    if not placed:
        centroids.append({"cx": c["cx"], "cy": c["cy"], "pts": [c]})
centers = [(g["cx"] / len(g["pts"]), g["cy"] / len(g["pts"]), len(g["pts"])) for g in centroids]
print("device clusters:", len(centers))
for cx, cy, n in centers:
    print("   mask center (%9.1f, %9.1f) vias=%d  wafer center (%8.2f, %8.2f)" % (cx, cy, n, cx / SCALE, cy / SCALE))

out = {"scale": SCALE, "devices": []}
for i, (cx, cy, nvia) in enumerate(centers):
    dev = {"name": "DEV%d" % (i + 1),
           "center_mask_um": [round(cx, 2), round(cy, 2)],
           "center_wafer_um": [round(cx / SCALE, 3), round(cy / SCALE, 3)],
           "n_vias": nvia, "layers": {}}
    indev = [r for r in recs if math.hypot(r["cx"] - cx, r["cy"] - cy) < 8000]
    for r in indev:
        item = {"size_wafer_um": [round(r["w"] / SCALE, 3), round(r["h"] / SCALE, 3)],
                "rel_center_wafer_um": [round((r["cx"] - cx) / SCALE, 3), round((r["cy"] - cy) / SCALE, 3)],
                "area_wafer_um2": round(r["area"] / (SCALE * SCALE), 1),
                "nverts": r["nverts"]}
        dev["layers"].setdefault(r["key"], []).append(item)
    # 器件跨度
    if indev:
        X0 = min(r["x0"] for r in indev); X1 = max(r["x1"] for r in indev)
        Y0 = min(r["y0"] for r in indev); Y1 = max(r["y1"] for r in indev)
        dev["extent_mask_um"] = [round(X1 - X0, 1), round(Y1 - Y0, 1)]
        dev["extent_wafer_um"] = [round((X1 - X0) / SCALE, 2), round((Y1 - Y0) / SCALE, 2)]
    for k in dev["layers"]:
        dev["layers"][k].sort(key=lambda it: -it["area_wafer_um2"])
    out["devices"].append(dev)
    print("\n=== %s extent mask %s um | wafer %s um | vias=%d" % (
        dev["name"], dev.get("extent_mask_um"), dev.get("extent_wafer_um"), nvia))
    for k, items in sorted(dev["layers"].items()):
        print("  %s n=%d" % (k, len(items)))
        for it in items[:10]:
            print("    size_w=%9.3f x %9.3f  rel=(%9.3f, %9.3f) area=%11.1f nverts=%d" % (
                it["size_wafer_um"][0], it["size_wafer_um"][1],
                it["rel_center_wafer_um"][0], it["rel_center_wafer_um"][1],
                it["area_wafer_um2"], it["nverts"]))

# 器件中心间距
if len(centers) >= 2:
    ds = []
    for i in range(len(centers)):
        for j in range(i + 1, len(centers)):
            ds.append(math.hypot(centers[i][0] - centers[j][0], centers[i][1] - centers[j][1]) / SCALE)
    out["device_pitch_wafer_um"] = [round(d, 2) for d in sorted(ds)]
    print("\ndevice pitch (wafer um):", out["device_pitch_wafer_um"])

with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(out, fh, ensure_ascii=False, indent=1)
print("written:", OUT)

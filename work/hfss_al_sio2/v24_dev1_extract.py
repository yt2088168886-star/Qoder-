# -*- coding: utf-8 -*-
"""V24 DEV1 建模数据提取（晶圆面坐标，器件中心为原点）：
- 每个多边形用 area/perimeter 估计等效导体宽度（细环近似）
- Via 与各层金属的覆盖关系（确定 M2-Via-M3 连接）
- PAD 金属识别（包含 450 um 钝化开口中心的多边形）
- 输出 HFSS 建模可用的顶点表 JSON
只读 D 盘 GDS。
"""
import json
import math
import sys

sys.path.insert(0, r"E:\Qoder_RF11_Sim\work\pylib")
import gdstk

REVIEW = r"D:\Codex_RF11_Project\outputs\ASML_100D_OCTAGON_4IN1_7P2_CHROME_V24\ASML_100D_OCTAGON_4L_STACKED_EXTERNAL_BAR_ONLY_REVIEW_V24.gds"
OUT = r"E:\Qoder_RF11_Sim\work\hfss_al_sio2\v24_dev1_model_data.json"
SCALE = 5.0
DEV = (-7176.7, -7467.4)  # DEV1 掩模面中心（16个Via聚类的质心）

lib = gdstk.read_gds(REVIEW)
cell = lib.top_level()[0]

polys = []
for p in cell.polygons:
    (x0, y0), (x1, y1) = p.bounding_box()
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    if math.hypot(cx - DEV[0], cy - DEV[1]) > 7500:
        continue  # 只取最近邻属于 DEV1 的图形
    per = p.perimeter()
    area = abs(p.area())
    w_est = (2.0 * area / per) if per > 0 else 0.0  # 细环等效宽度
    verts = [[(float(x) - DEV[0]) / SCALE, (float(y) - DEV[1]) / SCALE] for x, y in p.points]
    polys.append({
        "layer": p.layer, "datatype": p.datatype,
        "nverts": len(p.points),
        "size_wafer_um": [round((x1 - x0) / SCALE, 4), round((y1 - y0) / SCALE, 4)],
        "area_wafer_um2": round(area / (SCALE * SCALE), 3),
        "width_est_wafer_um": round(w_est / SCALE, 4),
        "perim_wafer_um": round(per / SCALE, 3),
        "points_wafer_um": [[round(x, 4), round(y, 4)] for x, y in verts],
    })

def is_via_circle(q):
    """Via 圆：小尺寸、近圆（圆度>0.9）、多顶点。"""
    w, h = q["size_wafer_um"]
    if max(w, h) > 50.0 or min(w, h) < 1.0:
        return False
    roundness = 4.0 * math.pi * q["area_wafer_um2"] / (q["perim_wafer_um"] ** 2)
    return q["nverts"] >= 12 and roundness > 0.9


def is_thin_mark(q):
    """工艺标记条：任一方向 < 3 um 的细图形。"""
    return min(q["size_wafer_um"]) < 3.0


vias = [q for q in polys if q["layer"] == 2 and is_via_circle(q)]
pad_openings = [q for q in polys if q["layer"] == 4 and min(q["size_wafer_um"]) > 100]
print("DEV1 polygons: %d | vias: %d | pad openings: %d | L2 total: %d" % (
    len(polys), len(vias), len(pad_openings), len([q for q in polys if q["layer"] == 2])))


def center_of(q):
    xs = [v[0] for v in q["points_wafer_um"]]
    ys = [v[1] for v in q["points_wafer_um"]]
    return (sum(xs) / len(xs), sum(ys) / len(ys))


def covers(q, pt, tol=0.0):
    """点是否在多边形内（用包围盒+射线法近似，tol 为晶圆面 um 容差）。"""
    x, y = pt
    pts = q["points_wafer_um"]
    inside = False
    n = len(pts)
    j = n - 1
    for i in range(n):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


conn = []
for v in vias:
    cv = center_of(v)
    entry = {"via_center_wafer_um": [round(cv[0], 3), round(cv[1], 3)],
             "via_size_wafer_um": v["size_wafer_um"], "links": {}}
    for q in polys:
        if q["layer"] in (2, 4) or is_thin_mark(q):
            continue
        if covers(q, cv):
            entry["links"]["L%d" % q["layer"]] = {
                "size_wafer_um": q["size_wafer_um"],
                "width_est_wafer_um": q["width_est_wafer_um"],
                "nverts": q["nverts"]}
    conn.append(entry)
    print("\nVia @ (%7.3f, %7.3f) size=%s" % (cv[0], cv[1], v["size_wafer_um"]))
    for k, val in sorted(entry["links"].items()):
        print("   %s  size=%s  width_est=%.3f um  nverts=%d" % (
            k, val["size_wafer_um"], val["width_est_wafer_um"], val["nverts"]))

# 各层导体宽度分布
print("\n=== width estimate per layer (wafer um) ===")
widths = {}
for q in polys:
    if q["layer"] == 2 or is_via_circle(q) or is_thin_mark(q):
        continue
    widths.setdefault("L%d" % q["layer"], []).append(q["width_est_wafer_um"])
for k, ws in sorted(widths.items()):
    ws = sorted(ws)
    print("  %s n=%2d  min=%.3f  median=%.3f  max=%.3f" % (
        k, len(ws), ws[0], ws[len(ws) // 2], ws[-1]))

# PAD 金属识别
print("\n=== pad metal candidates (cover a 450um opening center) ===")
pad_meta = []
for po in pad_openings:
    c = center_of(po)
    hits = []
    for q in polys:
        if q["layer"] in (2, 4) or is_via_circle(q) or min(q["size_wafer_um"]) < 50.0:
            continue
        if covers(q, c):
            hits.append("L%d" % q["layer"])
    pad_meta.append({"opening_center_wafer_um": [round(c[0], 3), round(c[1], 3)],
                     "opening_size_wafer_um": po["size_wafer_um"],
                     "metal_layers_under_opening": sorted(set(hits))})
    print("   opening @ (%8.3f, %8.3f) %s -> metal: %s" % (
        c[0], c[1], po["size_wafer_um"], sorted(set(hits)) or "NONE"))

data = {"device": "DEV1", "scale": SCALE, "origin_mask_um": list(DEV),
        "counts": {"polygons": len(polys), "vias": len(vias), "pad_openings": len(pad_openings)},
        "polygons": polys, "via_connectivity": conn, "pad_openings": pad_meta}
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(data, fh, ensure_ascii=False)
print("\nwritten:", OUT)

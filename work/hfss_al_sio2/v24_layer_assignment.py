# -*- coding: utf-8 -*-
"""V24 层归属判定（自含几何原语，不依赖 gdstk 距离函数）。
以 Via 圆心为基准算各层最小金属包围，掩模面 um -> 晶圆面 um (/5)。
判据来自 2026-10-13 记录：M2 最小包围约 3.996 um；M3 最小包围约 8.980/6.333/8.980/7.409 um。
只读 D 盘 GDS，输出 E 盘 JSON。
"""
import json
import math
import sys

sys.path.insert(0, r"E:\Qoder_RF11_Sim\work\pylib")
import gdstk

REVIEW = r"D:\Codex_RF11_Project\outputs\ASML_100D_OCTAGON_4IN1_7P2_CHROME_V24\ASML_100D_OCTAGON_4L_STACKED_EXTERNAL_BAR_ONLY_REVIEW_V24.gds"
OUT = r"E:\Qoder_RF11_Sim\work\hfss_al_sio2\v24_layer_assignment.json"
SCALE = 5.0

lib = gdstk.read_gds(REVIEW)
cell = lib.top_level()[0]


def pts(p):
    return [(float(x), float(y)) for x, y in p.points]


def close_pts_on_edges(q, poly):
    """点 q 到多边形边界的最小距离（遍历各边做点到线段距离）。"""
    n = len(poly)
    best = float("inf")
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        ax, ay = a
        bx, by = b
        vx, vy = bx - ax, by - ay
        wx, wy = q[0] - ax, q[1] - ay
        L = vx * vx + vy * vy
        t = 0.0 if L == 0 else max(0.0, min(1.0, (wx * vx + wy * vy) / L))
        dx, dy = wx - t * vx, wy - t * vy
        d = math.hypot(dx, dy)
        if d < best:
            best = d
    return best


def poly_to_poly_min(pa, pb):
    """两组顶点到对方边界的最小距离；对圆弧与矩形足够精确。"""
    best = float("inf")
    for q in pa:
        best = min(best, close_pts_on_edges(q, pb))
    for q in pb:
        best = min(best, close_pts_on_edges(q, pa))
    return best


def point_in_poly(q, poly):
    x, y = q
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def circle_center_r(v):
    ps = pts(v)
    cx = sum(x for x, y in ps) / len(ps)
    cy = sum(y for x, y in ps) / len(ps)
    r = math.sqrt(abs(v.area()) / math.pi)
    return (cx, cy), r


layers = {}
for p in cell.polygons:
    layers.setdefault((p.layer, p.datatype), []).append(p)

vias = [p for p in cell.polygons if p.layer == 2 and len(p.points) > 20
        and (p.bounding_box()[1][0] - p.bounding_box()[0][0]) < 100]
print("via circles on L2:", len(vias))

result = {"n_vias": len(vias), "scale": SCALE, "vias": []}
for v in vias:
    (cx, cy), r = circle_center_r(v)
    vp = pts(v)
    entry = {"cx_mask_um": round(cx, 3), "cy_mask_um": round(cy, 3),
             "via_radius_mask_um": round(r, 3),
             "via_diameter_wafer_um": round(2 * r / SCALE, 4),
             "layers": {}}
    for (ln, dt), polys in sorted(layers.items()):
        if (ln, dt) == (2, 0):
            continue
        cand = None
        for p in polys:
            (x0, y0), (x1, y1) = p.bounding_box()
            if x1 < cx - 500 or x0 > cx + 500 or y1 < cy - 500 or y0 > cy + 500:
                continue
            d = poly_to_poly_min(vp, pts(p))
            covers = point_in_poly((cx, cy), pts(p))
            key = "cover" if covers else "near"
            cur = entry["layers"].setdefault("L%d/%d" % (ln, dt), {})
            if key not in cur or d < cur[key]["d_um"]:
                cur[key] = {"d_um": round(d, 4),
                            "d_wafer_um": round(d / SCALE, 4),
                            "nverts": len(p.points),
                            "bbox_wafer_um": [round((x1 - x0) / SCALE, 3),
                                              round((y1 - y0) / SCALE, 3)]}
    result["vias"].append(entry)
    lab = []
    for lk, lv in entry["layers"].items():
        if "cover" in lv:
            lab.append("%s cover=%+.4f" % (lk, lv["cover"]["d_wafer_um"]))
        elif "near" in lv:
            lab.append("%s near=-%.4f" % (lk, lv["near"]["d_wafer_um"]))
    print("Via(%.0f,%.0f) Dw=%.4f | %s" % (cx, cy, entry["via_diameter_wafer_um"], "  ".join(lab)))

with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(result, fh, ensure_ascii=False, indent=1)
print("written:", OUT)

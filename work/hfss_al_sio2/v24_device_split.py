# -*- coding: utf-8 -*-
"""V24 四合一子器件拆分：以四个最大 L3 线圈图形为器件窗口，按层清点图形并写出晶圆面坐标。
目的：为新的铝/全氧硅 HFSS 模型提供真实 M2/M3/Via/PAD 多边形，并区分工艺标记图形。
只读 D 盘 GDS，输出 E 盘 JSON。掩模面 -> 晶圆面按 5:1。
"""
import json
import sys

sys.path.insert(0, r"E:\Qoder_RF11_Sim\work\pylib")
import gdstk

REVIEW = r"D:\Codex_RF11_Project\outputs\ASML_100D_OCTAGON_4IN1_7P2_CHROME_V24\ASML_100D_OCTAGON_4L_STACKED_EXTERNAL_BAR_ONLY_REVIEW_V24.gds"
OUT = r"E:\Qoder_RF11_Sim\work\hfss_al_sio2\v24_device_split.json"
SCALE = 5.0

lib = gdstk.read_gds(REVIEW)
cell = lib.top_level()[0]
polys = []
for p in cell.polygons:
    (x0, y0), (x1, y1) = p.bounding_box()
    polys.append({
        "layer": p.layer, "datatype": p.datatype,
        "x0": x0, "y0": y0, "x1": x1, "y1": y1,
        "w_um": x1 - x0, "h_um": y1 - y0,
        "cx": (x0 + x1) / 2.0, "cy": (y0 + y1) / 2.0,
        "area_um2": abs(p.area()), "nverts": len(p.points),
        "obj": p,
    })

# 器件窗口：L3 上面积最大的 4 个图形（各器件的主线圈）
big = sorted([e for e in polys if e["layer"] == 3],
             key=lambda e: -e["area_um2"])[:4]
windows = []
for e in big:
    pad = 1200.0  # 掩模面 um，容纳引线/PAD/Via
    windows.append({"name": "D%d" % (len(windows) + 1),
                    "x0": e["cx"] - pad, "x1": e["cx"] + pad,
                    "y0": e["cy"] - pad, "y1": e["cy"] + pad})

result = {"scale": SCALE, "coil_windows": [], "unassigned": [], "devices": []}
coil_info = []
for e, w in zip(big, windows):
    w["coil"] = e
    coil_info.append({"name": w["name"],
                      "coil_center_mask_um": [round(e["cx"], 1), round(e["cy"], 1)],
                      "coil_size_wafer_um": [round(e["w_um"] / SCALE, 3), round(e["h_um"] / SCALE, 3)],
                      "coil_area_wafer_um2": round(e["area_um2"] / (SCALE * SCALE), 1),
                      "nverts": e["nverts"], "layer": "L%d/%d" % (e["layer"], e["datatype"])})
result["coil_windows"] = coil_info

for w in windows:
    dev = {"name": w["name"], "coil": coil_info[[x["name"] for x in coil_info].index(w["name"])],
           "layers": {}}
    used = set()
    for e in polys:
        if w["x0"] <= e["cx"] <= w["x1"] and w["y0"] <= e["cy"] <= w["y1"]:
            key = "L%d/%d" % (e["layer"], e["datatype"])
            item = {"size_wafer_um": [round(e["w_um"] / SCALE, 4), round(e["h_um"] / SCALE, 4)],
                    "center_wafer_um": [round(e["cx"] / SCALE, 4), round(e["cy"] / SCALE, 4)],
                    "center_rel_coil_wafer_um": [round((e["cx"] - w["coil"]["cx"]) / SCALE, 4),
                                                 round((e["cy"] - w["coil"]["cy"]) / SCALE, 4)],
                    "area_wafer_um2": round(e["area_um2"] / (SCALE * SCALE), 3),
                    "nverts": e["nverts"]}
            dev["layers"].setdefault(key, []).append(item)
            used.add(id(e))
    for key in dev["layers"]:
        dev["layers"][key].sort(key=lambda it: -it["area_wafer_um2"])
    result["devices"].append(dev)

rest = [e for e in polys if id(e) not in used]
result["unassigned"] = [{"layer": "L%d/%d" % (e["layer"], e["datatype"]),
                         "size_wafer_um": [round(e["w_um"] / SCALE, 3), round(e["h_um"] / SCALE, 3)],
                         "center_wafer_um": [round(e["cx"] / SCALE, 2), round(e["cy"] / SCALE, 2)],
                         "nverts": e["nverts"]} for e in rest]

with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(result, fh, ensure_ascii=False, indent=1)

for c in coil_info:
    print("COIL %-3s center_mask=(%.1f,%.1f) size_wafer=%.3f x %.3f um area=%.1f nverts=%d %s" % (
        c["name"], c["coil_center_mask_um"][0], c["coil_center_mask_um"][1],
        c["coil_size_wafer_um"][0], c["coil_size_wafer_um"][1],
        c["coil_area_wafer_um2"], c["nverts"], c["layer"]))
for d in result["devices"]:
    print("\n### device", d["name"])
    for key, items in sorted(d["layers"].items()):
        print("  %s n=%d" % (key, len(items)))
        for it in items[:6]:
            print("     size_wafer=%9.3f x %9.3f  rel=(%9.3f, %9.3f) area=%12.2f nverts=%d" % (
                it["size_wafer_um"][0], it["size_wafer_um"][1],
                it["center_rel_coil_wafer_um"][0], it["center_rel_coil_wafer_um"][1],
                it["area_wafer_um2"], it["nverts"]))
print("\nunassigned polygons:", len(result["unassigned"]))
print("written:", OUT)

# -*- coding: utf-8 -*-
"""V24 GDS 只读盘点：层、单元、多边形数、包围盒、单位倍率。
输出写到 E 盘。只读 D 盘原始文件，不做任何修改。
"""
import json
import os
import sys

sys.path.insert(0, r"E:\Qoder_RF11_Sim\work\pylib")
import gdstk

GDS_DIR = r"D:\Codex_RF11_Project\outputs\ASML_100D_OCTAGON_4IN1_7P2_CHROME_V24"
OUT = r"E:\Qoder_RF11_Sim\work\hfss_al_sio2\v24_gds_inventory.json"

FILES = [
    "ASML_100D_OCTAGON_4L_STACKED_EXTERNAL_BAR_ONLY_REVIEW_V24.gds",
    "ASML_100D_OCTAGON_4IN1_7P2_TONE_D_CLEAR_FEATURES_L1_V24.gds",
]


def summarize(lib, path):
    info = {
        "file": os.path.basename(path),
        "unit": lib.unit,
        "precision": lib.precision,
        "units_per_db_unit": lib.unit / lib.precision if lib.precision else None,
        "cells": [],
    }
    for cell in lib.cells:
        entry = {
            "name": cell.name,
            "polygons": len(cell.polygons),
            "paths": len(cell.paths),
            "labels": len(cell.labels),
            "references": len(cell.references),
            "layers": {},
            "bbox": None,
        }
        if cell.polygons:
            mins = [p.bounding_box()[0] for p in cell.polygons]
            maxs = [p.bounding_box()[1] for p in cell.polygons]
            bbox = (min(x for x, y in mins), min(y for x, y in mins),
                    max(x for x, y in maxs), max(y for x, y in maxs))
            entry["bbox"] = bbox
            entry["bbox_size_db_units"] = [bbox[2] - bbox[0], bbox[3] - bbox[1]]
        for p in cell.polygons:
            key = "%d/%d" % (p.layer, p.datatype)
            d = entry["layers"].setdefault(key, {"count": 0, "areas_db2": 0.0,
                                                 "vertices": 0})
            d["count"] += 1
            d["areas_db2"] += float(abs(p.area()))
            d["vertices"] += len(p.points)
        info["cells"].append(entry)
    tops = [c.name for c in lib.top_level()]
    info["top_level"] = tops
    return info


result = {"files": [], "gdstk_version": getattr(gdstk, "__version__", "unknown")}
for name in FILES:
    path = os.path.join(GDS_DIR, name)
    if not os.path.exists(path):
        result["files"].append({"file": name, "error": "missing"})
        continue
    lib = gdstk.read_gds(path)
    result["files"].append(summarize(lib, path))

with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(result, fh, ensure_ascii=False, indent=2)

for f in result["files"]:
    print("==", f.get("file"), "unit", f.get("unit"), "precision", f.get("precision"))
    print("   top_level:", f.get("top_level"))
    for c in f.get("cells", [])[:40]:
        print("   cell %-46s poly=%-5d ref=%-4d bbox=%s" % (
            c["name"], c["polygons"], c["references"],
            None if not c["bbox"] else ["%.3f" % v for v in c["bbox"]]))
        for lk, lv in sorted(c["layers"].items()):
            print("      L%s count=%d area_db2=%.1f verts=%d" % (
                lk, lv["count"], lv["areas_db2"], lv["vertices"]))
print("written:", OUT)

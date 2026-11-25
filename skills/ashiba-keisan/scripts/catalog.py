"""部材カタログおよび風荷重データテーブルローダー."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class Catalog:
    """JIS・仮設工業会部材カタログおよび風荷重基準テーブル."""

    def __init__(self, data_dir: Path | None = None) -> None:
        base = data_dir or DATA_DIR
        with (base / "wind_tables.json").open("r", encoding="utf-8") as f:
            self.wind_tables: dict[str, Any] = json.load(f)
        with (base / "materials.json").open("r", encoding="utf-8") as f:
            self.materials: dict[str, Any] = json.load(f)

    def get_material(self, category: str, spec: str | dict[str, Any]) -> dict[str, Any]:
        """カタログ名またはカスタム辞書から部材データを取得する."""
        if isinstance(spec, dict):
            base_name = spec.get("base") or spec.get("name")
            if base_name and base_name in self.materials.get(category, {}):
                merged = dict(self.materials[category][base_name])
                merged.update(spec)
                return merged
            return dict(spec)

        table = self.materials.get(category, {})
        if spec in table:
            return dict(table[spec])

        # 全角・半角・空白の揺らぎを吸収して検索
        norm = _normalize_key(spec)
        for k, v in table.items():
            if _normalize_key(k) == norm or _normalize_key(v.get("display_name", "")) == norm:
                return dict(v)

        # ビルトアップH形鋼の動的パース (例: "BH-1000x400x12x19 (SS400)")
        if category == "h_beams":
            parsed = _try_parse_custom_h_beam(spec)
            if parsed is not None:
                return parsed

        raise KeyError(f"カタログ '{category}' に部材 '{spec}' が見つかりません。利用可能: {list(table.keys())}")

    def get_jack_base_allowable(self, jack_spec: str | dict[str, Any], extension_mm: float) -> tuple[float, dict[str, Any]]:
        """ジャッキベースの繰り出し長さ (mm) から許容支持力 (kg) を取得する."""
        jb = self.get_material("jack_bases", jack_spec)
        if "allowable_kg" in jb:
            return float(jb["allowable_kg"]), jb
        curve = jb.get("extension_allowable_kg", [])
        if not curve:
            raise ValueError(f"ジャッキベース '{jack_spec}' に繰り出し長さ別許容荷重表がありません。")
        max_ext = jb.get("max_extension_mm", 350)
        if extension_mm > max_ext:
            raise ValueError(
                f"ジャッキベースの繰り出し長さ {extension_mm} mm は法令上限 ({max_ext} mm) を超過しています。"
            )
        for row in curve:
            if extension_mm <= row["max_mm"]:
                return float(row["allowable_kg"]), jb
        return float(curve[-1]["allowable_kg"]), jb

    def get_region_wind(self, location: str) -> dict[str, Any]:
        """設置場所から基準風速 Vo および台風時割増係数 Ke を取得する."""
        regions = self.wind_tables["regions_v0"]
        if location in regions:
            return dict(regions[location])
        norm = _normalize_key(location)
        for k, v in regions.items():
            if _normalize_key(k) == norm:
                return dict(v)
        # 都道府県名での部分一致フォールバック
        for k, v in regions.items():
            pref = v.get("prefecture", "")
            if pref and pref in location:
                return dict(v)
        return {"v0": self.wind_tables["default_v0_ms"], "ke": 1.00, "prefecture": location}

    def resolve_terrain_code(self, terrain: str) -> tuple[str, str]:
        """地表面粗度区分 (I-V または日本語名) を正規化する."""
        cats = self.wind_tables["terrain_categories"]
        t_norm = _normalize_key(terrain)
        for code, info in cats.items():
            if _normalize_key(code) == t_norm or _normalize_key(info["label"]) == t_norm:
                return code, info["label"]
            for alias in info.get("aliases", []):
                if _normalize_key(alias) == t_norm:
                    return code, info["label"]
        raise ValueError(f"地表面粗度区分 '{terrain}' が不正です。I(海岸・海上)〜V(大都市市街地)を指定してください。")

    def get_gust_factor_S(self, height_z_m: float, terrain: str) -> tuple[float, str, str]:
        """地上高さ Z (m) と地表面粗度区分から瞬間風速分布係数 S を取得する."""
        code, label = self.resolve_terrain_code(terrain)
        rows = self.wind_tables["gust_distribution_S"]
        for row in rows:
            if row["z_min"] <= height_z_m <= row["z_max"]:
                return float(row[code]), row["label"], label
            if height_z_m < row["z_max"]:
                return float(row[code]), row["label"], label
        last = rows[-1]
        return float(last[code]), f"{last['label']}超", label

    def get_position_factor_F(self, position: str, phi: float) -> tuple[float, str, str]:
        """足場設置位置区分 (A/B/C) と充実率 φ から補正係数 F を算出する."""
        pos_key = _normalize_key(position).upper()
        # 全角A/B/C対応
        pos_map = {"A": "A", "B": "B", "C": "C"}
        if pos_key not in pos_map:
            raise ValueError(f"足場設置位置区分 '{position}' は A, B, C のいずれかを指定してください。")
        info = self.wind_tables["position_factor_F"][pos_key]
        f_val = info["constant"] + info["phi_coeff"] * phi
        return f_val, pos_key, info["formula_desc"]


def _normalize_key(s: str) -> str:
    trans = str.maketrans(
        "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ"
        "ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ"
        "０１２３４５６７８９（）　×－",
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "abcdefghijklmnopqrstuvwxyz"
        "0123456789() x-",
    )
    return s.translate(trans).replace(" ", "").lower()


def _try_parse_custom_h_beam(spec: str) -> dict[str, Any] | None:
    """'H-300x300x10x15 (SS400)' 等の文字列から断面性能を自動計算する."""
    import re

    m = re.search(r"(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)", spec)
    if not m:
        return None
    h = float(m.group(1)) / 10.0  # mm -> cm
    b = float(m.group(2)) / 10.0
    tw = float(m.group(3)) / 10.0
    tf = float(m.group(4)) / 10.0
    grade = "SM490" if "SM490" in spec.upper() else "SS400"
    F_val = 3300.0 if grade == "SM490" else 2400.0
    ft_long = 2200.0 if grade == "SM490" else 1600.0
    fs_long = 1270.0 if grade == "SM490" else 900.0

    hw = h - 2.0 * tf
    A = 2.0 * b * tf + hw * tw
    I = (b * h**3 - (b - tw) * hw**3) / 12.0
    Z = I / (h / 2.0)
    # 圧縮フランジ＋ウェブ1/6のT形断面二次半径 i
    A_t = b * tf + (hw / 6.0) * tw
    I_ty = (tf * b**3 + (hw / 6.0) * tw**3) / 12.0
    i_ltb = math.sqrt(I_ty / A_t)
    unit_weight = A * 0.785  # kg/m (鋼材密度 7.85 g/cm3)

    return {
        "display_name": spec,
        "grade": grade,
        "h_cm": round(h, 2),
        "b_cm": round(b, 2),
        "tw_cm": round(tw, 3),
        "tf_cm": round(tf, 3),
        "unit_weight_kg_m": round(unit_weight, 2),
        "A_cm2": round(A, 2),
        "I_cm4": round(I, 1),
        "Z_cm3": round(Z, 1),
        "i_ltb_cm": round(i_ltb, 2),
        "E_kg_cm2": 2100000.0,
        "F_kg_cm2": F_val,
        "ft_long_kg_cm2": ft_long,
        "fb_long_kg_cm2": ft_long,
        "fs_long_kg_cm2": fs_long,
    }

"""風荷重および壁つなぎの検討エンジン (一般社団法人 仮設工業会『改訂 風荷重に対する足場の安全技術指針』 / SUCCES Ver 4.11 準拠)."""

from __future__ import annotations

import math
from typing import Any

from .catalog import Catalog
from .units import kg_m2_to_N_m2, kgf_to_N, round_half_up


def compute_basic_wind_coeff_C0(phi: float) -> float:
    """充実率 φ からシート・ネット等の基本風力係数 C0 を算出する (仮設工業会指針).

    K = 1.2 * φ / (1 - φ)^2
    0 <= K <= 0.73: C0 = K / (1 + K/4)^2
    K > 0.73:       C0 = 2.8 * log10(K + 0.6 - sqrt(1.2K + 0.36)) - 2.8 * log10(K) + 2.0
                       (= 2.8 * log10(φ) + 2.0)
    φ >= 1.0:       C0 = 2.00
    """
    if phi <= 0.0:
        return 0.0
    if phi >= 1.0:
        return 2.00
    K = (1.2 * phi) / ((1.0 - phi) ** 2)
    if K <= 0.73:
        c0 = K / ((1.0 + K / 4.0) ** 2)
    else:
        inner = K + 0.6 - math.sqrt(1.2 * K + 0.36)
        c0 = 2.8 * math.log10(inner) - 2.8 * math.log10(K) + 2.0
    return round_half_up(min(c0, 2.00), 2)


def compute_aspect_ratio_factor_R(height_m: float, width_m: float, elevated: bool = False) -> float:
    """縦横比による形状補正係数 R を算出する (仮設工業会指針).

    地上から建ち上げる場合 (elevated=False): ratio = 2H / B
    地上から離れて設置する場合 (elevated=True): ratio = H / B
    ratio <= 1.5 の場合: R = 0.60
    ratio > 1.5 の場合:  R = 0.5813 + 0.013 * ratio - 0.0001 * ratio^2  (上限 1.00)
    """
    if width_m <= 0:
        raise ValueError("足場の長さ(幅) B は正の値である必要があります。")
    ratio = (height_m / width_m) if elevated else (2.0 * height_m / width_m)
    if ratio <= 1.5:
        return 0.60
    r_val = 0.5813 + 0.013 * ratio - 0.0001 * (ratio**2)
    return round_half_up(min(max(r_val, 0.60), 1.00), 2)


def calculate_wall_tie_wind(
    params: dict[str, Any],
    catalog: Catalog,
    scaffold_planes: int = 2,
) -> dict[str, Any]:
    """壁つなぎの風荷重検討を実行する.

    Args:
        params: 設計条件辞書
            - location: 設置場所 (例: "東京都（23区内）")
            - terrain: 地表面粗度区分 (例: "一般市街地" / "IV")
            - nearby_highrise: 近接高層建築物 ("無し" 等)
            - eval_height_z_m: 検討地上高さ Z (m) (例: 27.5 または Z範囲の代表値)
            - eval_height_label: 任意 (例: "25-30")
            - scaffold_height_m: 足場(シート)高さ H (m)
            - scaffold_length_m: 足場(シート)長さ B (m)
            - tie_horizontal_m: 壁つなぎ水平間隔 (m) (例: 3.600)
            - tie_vertical_m: 壁つなぎ垂直間隔 (m) (例: 3.400)
            - tie_horizontal_desc: 表示用テキスト (例: "2スパンごとに配置")
            - tie_vertical_desc: 表示用テキスト (例: "2段ごとに配置")
            - solidity_phi: 充実率 φ (例: 0.70)
            - sheet_description: 落下物防護材表記 (例: "充実率φ=0.7のメッシュシート")
            - position: 足場設置位置 ("A" / "B" / "C", デフォルト "B")
            - wall_tie_material: 壁つなぎ材料名または辞書 (デフォルト "壁つなぎ専用金具")
            - v0_override / ke_override / s_override / eb_override / c0_override / r_override / f_override: 任意上書き
        catalog: Catalog インスタンス
        scaffold_planes: 構面数 (2 = 枠組足場・本足場, 1 = 単管一側足場)
    """
    location = params.get("location", "東京都（23区内）")
    region = catalog.get_region_wind(location)

    v0 = float(params.get("v0_override", params.get("v0", region["v0"])))
    ke = float(params.get("ke_override", params.get("ke", region["ke"])))

    terrain_in = params.get("terrain", "一般市街地")
    eval_z = float(params.get("eval_height_z_m", params["scaffold_height_m"]))
    s_auto, z_band_auto, terrain_label = catalog.get_gust_factor_S(eval_z, terrain_in)
    s_val = float(params.get("s_override", s_auto))
    z_band_label = params.get("eval_height_label", z_band_auto)

    nearby = params.get("nearby_highrise", "無し")
    eb_table = catalog.wind_tables["nearby_highrise_EB"]
    eb_auto = float(eb_table.get(nearby, 1.00))
    eb = float(params.get("eb_override", eb_auto))

    # (2) 設計用速度圧
    vz = round_half_up(v0 * ke * s_val * eb, 1)
    qz = round_half_up((vz**2) / 16.0, 1)
    qz_N_m2 = kg_m2_to_N_m2(qz)

    # (3) 風力係数
    phi = float(params.get("solidity_phi", 0.70))
    gamma = round_half_up(1.0 - phi, 2) if scaffold_planes == 2 else None
    c0 = float(params.get("c0_override", compute_basic_wind_coeff_C0(phi)))
    H_m = float(params["scaffold_height_m"])
    B_m = float(params["scaffold_length_m"])
    r_val = float(params.get("r_override", compute_aspect_ratio_factor_R(H_m, B_m, elevated=bool(params.get("elevated", False)))))

    pos_in = params.get("position", "B")
    f_raw, pos_code, f_formula_desc = catalog.get_position_factor_F(pos_in, phi)
    f_val = float(params.get("f_override", round_half_up(f_raw, 2)))

    if scaffold_planes == 2:
        c_raw = (0.11 + 0.09 * (gamma or 0.0) + 0.945 * c0 * r_val) * f_val
        c_formula = f"(0.11 + 0.09×{gamma:.2f} + 0.945×{c0:.2f}×{r_val:.2f}) × {f_val:.2f}"
    else:
        c_raw = (0.11 + 0.945 * c0 * r_val) * f_val
        c_formula = f"(0.11 + 0.945×{c0:.2f}×{r_val:.2f}) × {f_val:.2f}"
    c_val = round_half_up(c_raw, 2)

    # (4) 壁つなぎの検討
    tie_h = float(params["tie_horizontal_m"])
    tie_v = float(params["tie_vertical_m"])
    area_A = round_half_up(tie_h * tie_v, 2)

    tie_mat = catalog.get_material("wall_ties", params.get("wall_tie_material", "壁つなぎ専用金具"))
    base_allow = float(tie_mat["base_allowable_kgf"])
    wind_inc = float(tie_mat.get("wind_increase_factor", 1.3))
    f_allow = round_half_up(base_allow * wind_inc, 1)
    f_allow_N = kgf_to_N(f_allow)

    load_R = round_half_up(qz * c_val * area_A, 1)
    load_R_N = kgf_to_N(load_R)
    ratio = round_half_up(load_R / f_allow, 2)
    ok = load_R <= f_allow

    return {
        "scaffold_planes": scaffold_planes,
        "conditions": {
            "location": location,
            "terrain": terrain_label,
            "nearby_highrise": nearby,
            "scaffold_height_m": H_m,
            "scaffold_length_m": B_m,
            "tie_vertical_desc": params.get("tie_vertical_desc", f"{tie_v:.3f}m間隔"),
            "tie_horizontal_desc": params.get("tie_horizontal_desc", f"{tie_h:.3f}m間隔"),
            "sheet_description": params.get("sheet_description", f"充実率φ={phi:g}のメッシュシート"),
            "wall_tie_material": tie_mat.get("display_name", "壁つなぎ専用金具"),
        },
        "velocity_pressure": {
            "V0_ms": v0,
            "Ke": ke,
            "S": s_val,
            "Z_band_m": z_band_label,
            "EB": eb,
            "Vz_ms": vz,
            "qz_kgf_m2": qz,
            "qz_N_m2": qz_N_m2,
        },
        "wind_force_coeff": {
            "phi": phi,
            "gamma": gamma,
            "C0": c0,
            "R": r_val,
            "position": pos_code,
            "F_formula": f_formula_desc,
            "F": f_val,
            "C_formula": c_formula,
            "C": c_val,
        },
        "verification": {
            "tie_horizontal_m": tie_h,
            "tie_vertical_m": tie_v,
            "area_A_m2": area_A,
            "base_allowable_kgf": base_allow,
            "wind_increase_factor": wind_inc,
            "allowable_F_kgf": f_allow,
            "allowable_F_N": f_allow_N,
            "load_R_kgf": load_R,
            "load_R_N": load_R_N,
            "ratio": ratio,
            "ok": ok,
            "verdict": "ＯＫ" if ok else "ＮＧ",
        },
    }

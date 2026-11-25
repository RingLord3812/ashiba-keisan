"""モジュール2: 単管一側ブラケット足場 強度計算エンジン (SUCCES Ver 4.11 準拠, PDF p.7-11)."""

from __future__ import annotations

import math
from typing import Any

from .catalog import Catalog
from .units import cm_to_mm, kg_cm2_to_N_mm2, kg_cm_to_kN_mm, kgf_to_N, round_half_up
from .wind import calculate_wall_tie_wind


def compute_column_allowable_fc(
    E_kg_cm2: float,
    F_kg_cm2: float,
    buckling_length_m: float,
    radius_gyration_cm: float,
    term_factor: float = 1.25,
    strict_aij: bool = False,
) -> dict[str, Any]:
    """AIJ 鋼構造設計規準による許容圧縮応力度 fc を算出する (λ<=Λ / λ>Λ 両対応)."""
    pi_val = math.pi
    lam_raw = (buckling_length_m * 100.0) / radius_gyration_cm
    Lam_raw = pi_val * math.sqrt(E_kg_cm2 / (0.6 * F_kg_cm2))
    lam_disp = lam_raw if strict_aij else int(round_half_up(lam_raw, 0))
    Lam_disp = Lam_raw if strict_aij else int(round_half_up(Lam_raw, 0))

    # SUCCES は内部の未丸め λ, Λ を用いて fc を算出し、表示のみ整数丸めする
    ratio_sq = (lam_raw / Lam_raw) ** 2
    if lam_raw > Lam_raw:
        regime = "elastic_euler"
        fc_long = (0.277 * F_kg_cm2) / ratio_sq
        fc = round_half_up(fc_long * term_factor, 0)
    else:
        regime = "inelastic_parabolic"
        nu = 1.5 + (2.0 / 3.0) * ratio_sq
        fc_long = ((1.0 - 0.4 * ratio_sq) / nu) * F_kg_cm2
        fc = round_half_up(fc_long * term_factor, 0)

    return {
        "lambda": lam_disp,
        "Lambda": Lam_disp,
        "regime": regime,
        "term_factor": term_factor,
        "fc_kg_cm2": fc,
        "fc_N_mm2": kg_cm2_to_N_mm2(fc),
        "pi_used": pi_val,
    }


def calculate_tankan_issoku(
    params: dict[str, Any],
    catalog: Catalog,
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """単管一側ブラケット足場強度計算 (荷重・壁つなぎ・建地・ブラケット上足場板) を実行する."""
    options = options or {}
    strict_aij = bool(options.get("strict_aij", False))
    deflection_limit_div = options.get("deflection_limit")

    building_h = float(params["building_height_m"])
    scaffold_h = float(params["scaffold_height_m"])
    standard_span = float(params.get("standard_span_m", 1.800))
    ledger_spacing = float(params.get("ledger_spacing_m", 1.700))
    bottom_tier_h = float(params.get("bottom_tier_height_m", 2.000))
    tiers = int(params["tiers"])

    std_pipe = catalog.get_material("single_pipes", params.get("standard_pipe", "単管φ48.6x2.4 (STK500)"))
    ledger_pipe = catalog.get_material("single_pipes", params.get("ledger_pipe", "単管φ48.6x2.4 (STK500)"))
    handrail_pipe = catalog.get_material("single_pipes", params.get("handrail_pipe", "単管φ48.6x2.3 (STK400)"))
    brace_pipe = catalog.get_material("single_pipes", params.get("brace_pipe", "単管φ48.6x2.4 (STK400)"))
    plank = catalog.get_material("planks", params.get("plank", "足場板 25x240 (合板)"))
    bracket = catalog.get_material("plank_brackets", params.get("bracket", "SBK (300-500)"))

    projection_mm = float(params.get("bracket_projection_mm", bracket["projection_mm"]))
    eccentricity_mm = float(params.get("plank_eccentricity_mm", bracket["eccentricity_mm"]))
    sheet_name = params.get("sheet_name", "メッシュシート")
    sheet_unit_w = float(params.get("sheet_unit_weight_kg_m2", 0.460))

    plank_tiers = int(params.get("plank_tiers", max(tiers - 1, 0)))
    brace_tiers = int(params.get("brace_tiers", 1))
    brace_length_m = float(params.get("brace_length_m", round_half_up(standard_span * math.sqrt(2.0), 3)))

    # 2. 荷重計算
    dead_items = [
        {
            "label": "建地パイプ",
            "spec": std_pipe["display_name"],
            "expr": f"{std_pipe['unit_weight_kg_m']:.3f} kg/ｍ × {scaffold_h:.3f}ｍ × 1本",
            "weight_kg": round_half_up(std_pipe["unit_weight_kg_m"] * scaffold_h * 1, 1),
        },
        {
            "label": "布パイプ",
            "spec": ledger_pipe["display_name"],
            "expr": f"{ledger_pipe['unit_weight_kg_m']:.3f} kg/ｍ × {standard_span:.3f}ｍ × {tiers}段",
            "weight_kg": round_half_up(ledger_pipe["unit_weight_kg_m"] * standard_span * tiers, 1),
        },
        {
            "label": "足場板",
            "spec": plank["display_name"],
            "expr": f"{plank['unit_weight_kg_m']:.3f} kg/ｍ × {standard_span:.3f}ｍ × {plank_tiers}段",
            "weight_kg": round_half_up(plank["unit_weight_kg_m"] * standard_span * plank_tiers, 1),
        },
        {
            "label": "手摺パイプ",
            "spec": handrail_pipe["display_name"],
            "expr": f"{handrail_pipe['unit_weight_kg_m']:.3f} kg/ｍ × {standard_span:.3f}ｍ × {plank_tiers}段",
            "weight_kg": round_half_up(handrail_pipe["unit_weight_kg_m"] * standard_span * plank_tiers, 1),
        },
        {
            "label": "足場板受ブラケット",
            "spec": bracket["display_name"],
            "expr": f"{bracket['weight_kg']:.3f} kg × {plank_tiers}段",
            "weight_kg": round_half_up(bracket["weight_kg"] * plank_tiers, 1),
        },
        {
            "label": "養生",
            "spec": sheet_name,
            "expr": f"{sheet_unit_w:.3f} kg/㎡ × {standard_span:.3f}ｍ × {scaffold_h:.3f}ｍ",
            "weight_kg": round_half_up(sheet_unit_w * standard_span * scaffold_h, 1),
        },
        {
            "label": "筋かい",
            "spec": brace_pipe["display_name"],
            "expr": f"{brace_pipe['unit_weight_kg_m']:.3f} kg/ｍ × {brace_length_m:.3f}ｍ × {brace_tiers}段",
            "weight_kg": round_half_up(brace_pipe["unit_weight_kg_m"] * brace_length_m * brace_tiers, 1),
        },
    ]
    axial_dead_raw = (
        std_pipe["unit_weight_kg_m"] * scaffold_h
        + ledger_pipe["unit_weight_kg_m"] * standard_span * tiers
        + plank["unit_weight_kg_m"] * standard_span * plank_tiers
        + handrail_pipe["unit_weight_kg_m"] * standard_span * plank_tiers
        + bracket["weight_kg"] * plank_tiers
        + sheet_unit_w * standard_span * scaffold_h
        + brace_pipe["unit_weight_kg_m"] * brace_length_m * brace_tiers
    )
    axial_dead_kg = round_half_up(sum(it["weight_kg"] for it in dead_items), 1)

    brk_w = round_half_up(float(bracket["weight_kg"]), 2)
    brk_plank_w = round_half_up(float(plank["unit_weight_kg_m"]) * standard_span, 2)
    bracket_dead_kg = round_half_up(brk_w + brk_plank_w, 2)
    live_load_kg = float(params.get("live_load_per_standard_kg", 100.0))

    loads_res = {
        "axial_dead_items": dead_items,
        "axial_dead_kg": axial_dead_kg,
        "axial_dead_N": kgf_to_N(axial_dead_raw),
        "bracket_dead_items": [
            {"label": "足場板受ブラケット", "spec": bracket["display_name"], "expr": f"{brk_w:.2f} kg", "weight_kg": brk_w},
            {
                "label": "足場板",
                "spec": plank["display_name"],
                "expr": f"{plank['unit_weight_kg_m']:.3f} kg/ｍ × {standard_span:.3f}ｍ",
                "weight_kg": brk_plank_w,
            },
        ],
        "bracket_dead_kg": bracket_dead_kg,
        "bracket_dead_N": kgf_to_N(bracket_dead_kg),
        "live_load_kg": live_load_kg,
        "live_load_N": kgf_to_N(live_load_kg),
    }

    # 壁つなぎ (1構面)
    tie_cfg = params.get("wall_tie", {})
    tie_h_spans = int(tie_cfg.get("horizontal_spans", 2))
    tie_v_tiers = int(tie_cfg.get("vertical_tiers", 2))
    tie_v_start = int(tie_cfg.get("vertical_start_tier", 1))
    tie_h_m = float(tie_cfg.get("tie_horizontal_m", standard_span * tie_h_spans))
    tie_v_m = float(tie_cfg.get("tie_vertical_m", ledger_spacing * tie_v_tiers))

    wind_in = dict(tie_cfg)
    wind_in.setdefault("scaffold_height_m", float(tie_cfg.get("wind_scaffold_height_m", building_h)))
    wind_in.setdefault("scaffold_length_m", float(tie_cfg.get("scaffold_length_m", 18.500)))
    wind_in.setdefault("tie_horizontal_m", tie_h_m)
    wind_in.setdefault("tie_vertical_m", tie_v_m)
    wind_in.setdefault("tie_horizontal_desc", f"{tie_h_spans}スパンごとに配置")
    wind_in.setdefault("tie_vertical_desc", f"{tie_v_tiers}段ごとに配置")
    wall_tie_res = calculate_wall_tie_wind(wind_in, catalog, scaffold_planes=1)

    # 5. 建地の検討 (圧縮 + 偏心曲げの複合応力検定)
    A_pipe = float(std_pipe["A_cm2"])
    Z_pipe = float(std_pipe["Z_cm3"])
    E_pipe = float(std_pipe["E_kg_cm2"])
    i_pipe = float(std_pipe["i_cm"])
    F_pipe = float(std_pipe["F_kg_cm2"])
    fb_long = float(std_pipe["fb_long_kg_cm2"])
    term_factor = float(params.get("term_factor", 1.25))

    N_axial = round_half_up(axial_dead_kg + live_load_kg, 2)
    P_brk = round_half_up(bracket_dead_kg + live_load_kg, 2)
    L1_m = eccentricity_mm / 1000.0
    M1_kg_m = round_half_up(P_brk * L1_m, 2)
    M_kg_cm = round_half_up(M1_kg_m * 100.0, 0)

    buckling_L_m = float(params.get("buckling_length_m", tie_v_m))
    buckling = compute_column_allowable_fc(
        E_kg_cm2=E_pipe,
        F_kg_cm2=F_pipe,
        buckling_length_m=buckling_L_m,
        radius_gyration_cm=i_pipe,
        term_factor=term_factor,
        strict_aij=strict_aij,
    )
    fc = buckling["fc_kg_cm2"]
    fb = round_half_up(fb_long * term_factor, 0)

    sigma_c = round_half_up(N_axial / A_pipe, 1)
    sigma_b = round_half_up(M_kg_cm / Z_pipe, 1)

    term_c = round_half_up(sigma_c / fc, 3)
    term_b = round_half_up(sigma_b / fb, 3)
    combined_ratio = round_half_up(term_c + term_b, 3)
    std_ok = combined_ratio <= 1.0

    standard_res = {
        "member": std_pipe["display_name"],
        "section": {
            "A_cm2": A_pipe,
            "Z_cm3": Z_pipe,
            "E_kg_cm2": E_pipe,
            "i_cm": i_pipe,
            "F_kg_cm2": F_pipe,
        },
        "N_axial_kg": N_axial,
        "P_bracket_kg": P_brk,
        "L1_m": L1_m,
        "buckling_L_m": buckling_L_m,
        "M_kg_m": M1_kg_m,
        "M_kg_cm": M_kg_cm,
        "M_kN_mm": kg_cm_to_kN_mm(M_kg_cm),
        "buckling": buckling,
        "fc_kg_cm2": fc,
        "fb_long_kg_cm2": fb_long,
        "fb_kg_cm2": fb,
        "sigma_c_kg_cm2": sigma_c,
        "sigma_c_N_mm2": kg_cm2_to_N_mm2(sigma_c),
        "sigma_b_kg_cm2": sigma_b,
        "sigma_b_N_mm2": kg_cm2_to_N_mm2(sigma_b),
        "ratio_c": term_c,
        "ratio_b": term_b,
        "combined_ratio": combined_ratio,
        "summary_ratio": round_half_up(combined_ratio, 2),
        "ok": std_ok,
        "verdict": "ＯＫ" if std_ok else "ＮＧ",
    }

    # 6. ブラケット上の足場板の検討
    plank_L_cm = float(params.get("plank_span_cm", standard_span * 100.0))
    plank_P_kg = float(params.get("plank_live_load_kg", live_load_kg))
    w_plank_raw = float(plank["unit_weight_kg_m"]) / 100.0  # kg/m -> kg/cm
    w_plank = w_plank_raw if strict_aij else round_half_up(w_plank_raw, 2)

    A_pl = float(plank["A_cm2"])
    I_pl = float(plank["I_cm4"])
    Z_pl = float(plank["Z_cm3"])
    E_pl = float(plank["E_kg_cm2"])
    kappa_pl = float(plank["kappa"])
    fb_pl = float(plank["fb_long_kg_cm2"])
    fs_pl = float(plank["fs_long_kg_cm2"])

    M_pl_p = round_half_up(plank_P_kg * plank_L_cm / 4.0, 1)
    M_pl_w = round_half_up(w_plank * (plank_L_cm**2) / 8.0, 1)
    M_pl = round_half_up(M_pl_p + M_pl_w, 1)
    sigma_b_pl = round_half_up(M_pl / Z_pl, 1)
    pl_b_ok = sigma_b_pl <= fb_pl

    Q_pl_p = round_half_up(plank_P_kg / 2.0, 1)
    Q_pl_w = round_half_up(w_plank * plank_L_cm / 2.0, 1)
    Q_pl = round_half_up(Q_pl_p + Q_pl_w, 1)
    tau_pl = round_half_up(kappa_pl * Q_pl / A_pl, 1)
    pl_q_ok = tau_pl <= fs_pl

    d_pl_p = round_half_up(plank_P_kg * (plank_L_cm**3) / (48.0 * E_pl * I_pl), 3)
    d_pl_w = round_half_up(5.0 * w_plank * (plank_L_cm**4) / (384.0 * E_pl * I_pl), 3)
    delta_pl = round_half_up(d_pl_p + d_pl_w, 3)

    deflection_check = _check_deflection(delta_pl, plank_L_cm, deflection_limit_div)

    plank_res = {
        "member": plank["display_name"],
        "L_cm": plank_L_cm,
        "P_kg": plank_P_kg,
        "w_kg_cm": w_plank,
        "section": {
            "A_cm2": A_pl,
            "I_cm4": I_pl,
            "Z_cm3": Z_pl,
            "E_kg_cm2": E_pl,
            "kappa": kappa_pl,
            "fb_kg_cm2": fb_pl,
            "fs_kg_cm2": fs_pl,
        },
        "bending": {
            "M_p_kg_cm": M_pl_p,
            "M_w_kg_cm": M_pl_w,
            "M_kg_cm": M_pl,
            "M_kN_mm": kg_cm_to_kN_mm(M_pl),
            "sigma_b_kg_cm2": sigma_b_pl,
            "sigma_b_N_mm2": kg_cm2_to_N_mm2(sigma_b_pl),
            "fb_kg_cm2": fb_pl,
            "fb_N_mm2": kg_cm2_to_N_mm2(fb_pl),
            "ok": pl_b_ok,
            "verdict": "ＯＫ" if pl_b_ok else "ＮＧ",
        },
        "shear": {
            "Q_p_kg": Q_pl_p,
            "Q_w_kg": Q_pl_w,
            "Q_kg": Q_pl,
            "Q_N": kgf_to_N(Q_pl),
            "tau_kg_cm2": tau_pl,
            "tau_N_mm2": kg_cm2_to_N_mm2(tau_pl),
            "fs_kg_cm2": fs_pl,
            "fs_N_mm2": kg_cm2_to_N_mm2(fs_pl),
            "ok": pl_q_ok,
            "verdict": "ＯＫ" if pl_q_ok else "ＮＧ",
        },
        "deflection": {
            "delta_p_cm": d_pl_p,
            "delta_w_cm": d_pl_w,
            "delta_cm": delta_pl,
            "delta_mm": cm_to_mm(delta_pl),
            "summary_cm": round_half_up(delta_pl, 2),
            "limit_check": deflection_check,
        },
    }

    summary_rows = [
        {
            "section": "単管一側ブラケット足場",
            "part": "壁つなぎ",
            "member": wall_tie_res["conditions"]["wall_tie_material"],
            "verdict": wall_tie_res["verification"]["verdict"],
            "ratio": wall_tie_res["verification"]["ratio"],
            "bending": None,
            "shear": None,
            "deflection_cm": None,
        },
        {
            "section": "単管一側ブラケット足場",
            "part": "建地",
            "member": std_pipe["display_name"],
            "verdict": standard_res["verdict"],
            "ratio": standard_res["summary_ratio"],
            "bending": None,
            "shear": None,
            "deflection_cm": None,
        },
        {
            "section": "単管一側ブラケット足場",
            "part": "ブラケット上足場板",
            "member": plank["display_name"],
            "verdict": None,
            "ratio": None,
            "bending": plank_res["bending"]["verdict"],
            "shear": plank_res["shear"]["verdict"],
            "deflection_cm": plank_res["deflection"]["summary_cm"],
            "deflection_verdict": deflection_check["verdict"] if deflection_check else None,
        },
    ]

    all_ok = (
        wall_tie_res["verification"]["ok"]
        and standard_res["ok"]
        and pl_b_ok
        and pl_q_ok
        and (deflection_check["ok"] if deflection_check else True)
    )

    return {
        "module": "tankan_issoku",
        "title": "単管一側ブラケット 強度計算書",
        "overview": {
            "building_height_m": building_h,
            "scaffold_height_m": scaffold_h,
            "standard_span_m": standard_span,
            "ledger_spacing_m": ledger_spacing,
            "bottom_tier_height_m": bottom_tier_h,
            "tiers": tiers,
            "bracket_projection_mm": projection_mm,
            "plank_eccentricity_mm": eccentricity_mm,
            "design_wind_v0_ms": wall_tie_res["velocity_pressure"]["V0_ms"],
            "reinforcement": params.get("reinforcement", "－"),
            "tie_horizontal_spans": tie_h_spans,
            "tie_vertical_start_tier": tie_v_start,
            "tie_vertical_tiers": tie_v_tiers,
        },
        "loads": loads_res,
        "wall_tie": wall_tie_res,
        "standard_pipe": standard_res,
        "plank": plank_res,
        "summary_rows": summary_rows,
        "all_ok": all_ok,
    }


def _check_deflection(delta_cm: float, span_cm: float, limit_div: int | None) -> dict[str, Any] | None:
    if not limit_div:
        return None
    allow_cm = round_half_up(span_cm / float(limit_div), 3)
    ok = delta_cm <= allow_cm
    return {
        "criterion": f"L/{limit_div}",
        "allowable_cm": allow_cm,
        "allowable_mm": cm_to_mm(allow_cm),
        "actual_ratio": f"L/{int(round(span_cm / delta_cm))}" if delta_cm > 0 else "∞",
        "ok": ok,
        "verdict": "ＯＫ" if ok else "警告(ＮＧ)",
    }

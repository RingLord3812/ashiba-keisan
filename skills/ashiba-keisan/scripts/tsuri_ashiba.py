"""モジュール4: 鉄骨吊り足場 強度計算エンジン (SUCCES Ver 4.11 準拠, PDF p.22-26)."""

from __future__ import annotations

from typing import Any

from .catalog import Catalog
from .units import cm_to_mm, kg_cm2_to_N_mm2, kg_cm_to_kN_mm, kg_cm_to_N_mm, kgf_to_N, round_half_up


def calculate_tsuri_ashiba(
    params: dict[str, Any],
    catalog: Catalog,
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """鉄骨吊り足場強度計算 (荷重・吊りチェーン・足場板・根太・大引・張り出し部) を実行する."""
    options = options or {}
    strict_aij = bool(options.get("strict_aij", False))
    deflection_limit_div = options.get("deflection_limit")

    span_x = float(params["span_x_m"])
    span_y = float(params["span_y_m"])
    girder_spacing = float(params.get("girder_spacing_m", 1.800))
    joist_spacing = float(params.get("joist_spacing_m", 1.500))
    plank_offset_m = float(params.get("support_to_plank_center_m", 0.500))
    cantilever_m = float(params.get("cantilever_length_m", 1.000))

    plank = catalog.get_material("planks", params.get("plank", "足場板 25x240 (合板)"))
    joist = catalog.get_material("square_pipes", params.get("joist", "角パイプ 60x60 (STKR400)"))
    girder = catalog.get_material("square_pipes", params.get("girder", "角パイプ 60x60 (STKR400)"))
    chain = catalog.get_material("suspension_chains", params.get("chain", "ループ吊り"))

    net_name = params.get("net_name", "ラッセルネット")
    net_unit_w = float(params.get("net_unit_weight_kg_m2", 0.320))
    plank_w_per_m = float(params.get("plank_unit_weight_per_m", plank["unit_weight_per_m_width_kg_m"]))
    plank_count = int(params.get("plank_rows", 2))
    joist_count = int(params.get("joist_count_per_girder", 4))

    worker_kg = float(params.get("worker_weight_kg", 80.0))
    worker_count = int(params.get("worker_count", 2))
    bolt_kg = float(params.get("bolt_weight_kg", 40.0))
    bolt_count = int(params.get("bolt_sets", 2))

    # 2. 荷重計算 (中央部・大引1本当り)
    dead_items = [
        {
            "label": "足場板",
            "spec": plank["display_name"],
            "expr": f"{plank_w_per_m:.3f} kg/ｍ × {girder_spacing:.3f}ｍ × 1枚 × {plank_count}",
            "weight_kg": round_half_up(plank_w_per_m * girder_spacing * 1 * plank_count, 1),
        },
        {
            "label": "根太パイプ",
            "spec": joist["display_name"],
            "expr": f"{joist['unit_weight_kg_m']:.3f} kg/ｍ × {girder_spacing:.3f}ｍ × {joist_count}本",
            "weight_kg": round_half_up(joist["unit_weight_kg_m"] * girder_spacing * joist_count, 1),
        },
        {
            "label": "大引パイプ",
            "spec": girder["display_name"],
            "expr": f"{girder['unit_weight_kg_m']:.3f} kg/ｍ × {span_y:.3f}ｍ × 1本",
            "weight_kg": round_half_up(girder["unit_weight_kg_m"] * span_y * 1, 1),
        },
        {
            "label": "水平ネット",
            "spec": net_name,
            "expr": f"{net_unit_w:.3f} kg/㎡ × {span_y:.3f}ｍ × {girder_spacing:.3f}ｍ",
            "weight_kg": round_half_up(net_unit_w * span_y * girder_spacing, 1),
        },
    ]
    dead_total = round_half_up(sum(it["weight_kg"] for it in dead_items), 1)
    live_workers = round_half_up(worker_kg * worker_count, 1)
    live_bolts = round_half_up(bolt_kg * bolt_count, 1)
    live_total = round_half_up(live_workers + live_bolts, 1)

    # 3. 吊チェーンの検討
    chain_allow = float(params.get("chain_allowable_kg", chain["allowable_tension_kg"]))
    chain_T = round_half_up(dead_total + live_total, 1)
    chain_ratio = round_half_up(chain_T / chain_allow, 2)
    chain_ok = chain_T <= chain_allow

    chain_res = {
        "member": chain["display_name"],
        "allowable_f_kg": chain_allow,
        "allowable_f_N": kgf_to_N(chain_allow),
        "tension_T_kg": chain_T,
        "tension_T_N": kgf_to_N(chain_T),
        "ratio": chain_ratio,
        "ok": chain_ok,
        "verdict": "ＯＫ" if chain_ok else "ＮＧ",
    }

    # 4. 足場板の検討 (単純支持, L = 根太間隔)
    L_pl_cm = joist_spacing * 100.0
    P_pl = round_half_up(worker_kg + bolt_kg, 1)
    w_pl = round_half_up(plank_w_per_m / 100.0, 4)
    plank_res = _calc_simply_supported_center_point(
        member=plank,
        L_cm=L_pl_cm,
        P_kg=P_pl,
        w_kg_cm=w_pl,
        z_digits=2,
        deflection_limit_div=deflection_limit_div,
    )

    # 5. 根太の検討 (単純支持, L = 大引間隔)
    L_j_cm = girder_spacing * 100.0
    plank_on_joist_kg = round_half_up(plank_w_per_m * girder_spacing * 1 * plank_count, 1)
    P_j = round_half_up(worker_kg + bolt_kg + plank_on_joist_kg, 1)
    w_j = round_half_up(float(joist["unit_weight_kg_m"]) / 100.0, 5)
    joist_res = _calc_simply_supported_center_point(
        member=joist,
        L_cm=L_j_cm,
        P_kg=P_j,
        w_kg_cm=w_j,
        z_digits=2,
        deflection_limit_div=deflection_limit_div,
    )
    joist_res["plank_load_kg"] = plank_on_joist_kg

    # 6. 大引の検討 (単純支持, 対称2点集中荷重 + 等分布荷重)
    L_g_cm = span_y * 100.0
    a_g_cm = plank_offset_m * 100.0
    b_g_cm = L_g_cm - 2.0 * a_g_cm
    P_g = P_j  # 作業員 + ボルト類 + 足場板

    g_self_kg = round_half_up(float(girder["unit_weight_kg_m"]) * span_y * 1, 1)
    j_self_kg = round_half_up(float(joist["unit_weight_kg_m"]) * girder_spacing * joist_count, 1)
    w_g_total_kg = round_half_up(g_self_kg + j_self_kg, 1)
    w_g = round_half_up(w_g_total_kg / L_g_cm, 4)

    A_g = float(girder["A_cm2"])
    I_g = float(girder["I_cm4"])
    Z_g = round_half_up(float(girder["Z_cm3"]), 2)
    E_g = float(girder["E_kg_cm2"])
    kappa_g = float(girder["kappa"])
    fb_g = float(girder["fb_long_kg_cm2"])
    fs_g = float(girder["fs_long_kg_cm2"])

    M_g = round_half_up(P_g * a_g_cm + (w_g * (L_g_cm**2)) / 8.0, 1)
    sigma_b_g = round_half_up(M_g / Z_g, 1)
    g_b_ok = sigma_b_g <= fb_g

    Q_g = round_half_up(P_g + round_half_up(w_g * L_g_cm / 2.0, 1), 1)
    tau_g = round_half_up(kappa_g * Q_g / A_g, 1)
    g_q_ok = tau_g <= fs_g

    b_over_L = b_g_cm / L_g_cm
    shape_factor = (b_over_L**3) - 3.0 * (b_over_L**2) + 2.0
    d_g_p = round_half_up((P_g * (L_g_cm**3) / (48.0 * E_g * I_g)) * shape_factor, 3)
    d_g_w = round_half_up((5.0 * w_g * (L_g_cm**4)) / (384.0 * E_g * I_g), 3)
    delta_g = round_half_up(d_g_p + d_g_w, 3)
    g_defl_chk = _check_deflection(delta_g, L_g_cm, deflection_limit_div)

    girder_res = {
        "member": girder["display_name"],
        "L_cm": L_g_cm,
        "a_cm": a_g_cm,
        "b_cm": b_g_cm,
        "P_kg": P_g,
        "P_N": kgf_to_N(P_g),
        "girder_self_kg": g_self_kg,
        "joist_self_kg": j_self_kg,
        "w_total_kg": w_g_total_kg,
        "w_total_N": kgf_to_N(w_g_total_kg),
        "w_kg_cm": w_g,
        "w_N_mm": kg_cm_to_N_mm(w_g),
        "section": {
            "A_cm2": A_g,
            "I_cm4": I_g,
            "Z_cm3": float(girder["Z_cm3"]),
            "E_kg_cm2": E_g,
            "kappa": kappa_g,
            "fb_kg_cm2": fb_g,
            "fs_kg_cm2": fs_g,
        },
        "bending": {
            "M_kg_cm": M_g,
            "M_kN_mm": kg_cm_to_kN_mm(M_g),
            "sigma_b_kg_cm2": sigma_b_g,
            "sigma_b_N_mm2": kg_cm2_to_N_mm2(sigma_b_g),
            "fb_kg_cm2": fb_g,
            "fb_N_mm2": kg_cm2_to_N_mm2(fb_g),
            "ok": g_b_ok,
            "verdict": "ＯＫ" if g_b_ok else "ＮＧ",
        },
        "shear": {
            "Q_kg": Q_g,
            "Q_N": kgf_to_N(Q_g),
            "tau_kg_cm2": tau_g,
            "tau_N_mm2": kg_cm2_to_N_mm2(tau_g),
            "fs_kg_cm2": fs_g,
            "fs_N_mm2": kg_cm2_to_N_mm2(fs_g),
            "ok": g_q_ok,
            "verdict": "ＯＫ" if g_q_ok else "ＮＧ",
        },
        "deflection": {
            "delta_p_cm": d_g_p,
            "delta_w_cm": d_g_w,
            "delta_cm": delta_g,
            "delta_mm": cm_to_mm(delta_g),
            "summary_cm": round_half_up(delta_g, 2),
            "limit_check": g_defl_chk,
        },
    }

    # 7. 張り出し部の検討 (片持梁)
    cant_cfg = params.get("cantilever", {})
    L_c_cm = cantilever_m * 100.0
    a_c_cm = float(cant_cfg.get("p2_distance_cm", L_c_cm / 2.0))
    b_c_cm = L_c_cm - a_c_cm
    w_c = round_half_up(float(girder["unit_weight_kg_m"]) / 100.0, 4)

    hr_kg = float(cant_cfg.get("handrail_kg", 2.525))
    hr_post_kg = float(cant_cfg.get("handrail_post_kg", 0.320))
    cant_joist_w_m = float(cant_cfg.get("cantilever_joist_unit_kg_m", 2.730))
    p1_items = [
        {"label": "手摺", "expr": f"{hr_kg:.3f} kg × 1本", "weight_kg": round_half_up(hr_kg, 1)},
        {"label": "手摺柱", "expr": f"{hr_post_kg:.3f} kg × 1本", "weight_kg": round_half_up(hr_post_kg, 1)},
        {
            "label": "根太",
            "expr": f"{cant_joist_w_m:.3f} kg/ｍ × {girder_spacing:.3f}ｍ × 1本",
            "weight_kg": round_half_up(cant_joist_w_m * girder_spacing, 1),
        },
    ]
    P1_c = round_half_up(sum(it["weight_kg"] for it in p1_items), 1)

    p2_items = [
        {"label": "作業員", "expr": f"{worker_kg:.0f} kg", "weight_kg": round_half_up(worker_kg, 1)},
        {"label": "ボルト類", "expr": f"{bolt_kg:.0f} kg", "weight_kg": round_half_up(bolt_kg, 1)},
        {
            "label": "足場板",
            "expr": f"{plank_w_per_m:.3f} kg/ｍ × {girder_spacing:.3f}ｍ × 1枚 × {plank_count}",
            "weight_kg": round_half_up(plank_w_per_m * girder_spacing * plank_count, 1),
        },
        {
            "label": "水平ネット",
            "expr": f"{net_unit_w:.3f} kg/㎡ × {cantilever_m:.3f}ｍ × {girder_spacing:.3f}ｍ",
            "weight_kg": round_half_up(net_unit_w * cantilever_m * girder_spacing, 1),
        },
    ]
    P2_c = round_half_up(sum(it["weight_kg"] for it in p2_items), 1)

    M_c = round_half_up(P1_c * L_c_cm + P2_c * a_c_cm + (w_c * (L_c_cm**2)) / 2.0, 1)
    sigma_b_c = round_half_up(M_c / Z_g, 1)
    c_b_ok = sigma_b_c <= fb_g

    Q_c = round_half_up(P1_c + P2_c + round_half_up(w_c * L_c_cm, 1), 1)
    tau_c = round_half_up(kappa_g * Q_c / A_g, 1)
    c_q_ok = tau_c <= fs_g

    d_c_p1 = round_half_up((P1_c * (L_c_cm**3)) / (3.0 * E_g * I_g), 3)
    d_c_p2 = round_half_up(((P2_c * (a_c_cm**3)) / (3.0 * E_g * I_g)) * (1.0 + (3.0 * b_c_cm) / (2.0 * a_c_cm)), 3)
    d_c_w = round_half_up((w_c * (L_c_cm**4)) / (8.0 * E_g * I_g), 3) if strict_aij else 0.0
    delta_c = round_half_up(d_c_p1 + d_c_p2 + d_c_w, 3)
    c_defl_chk = _check_deflection(delta_c, L_c_cm, deflection_limit_div)

    cantilever_res = {
        "member": girder["display_name"],
        "L_cm": L_c_cm,
        "a_cm": a_c_cm,
        "b_cm": b_c_cm,
        "w_kg_cm": w_c,
        "p1_items": p1_items,
        "P1_kg": P1_c,
        "P1_N": kgf_to_N(P1_c),
        "p2_items": p2_items,
        "P2_kg": P2_c,
        "P2_N": kgf_to_N(P2_c),
        "section": girder_res["section"],
        "bending": {
            "M_kg_cm": M_c,
            "M_kN_mm": kg_cm_to_kN_mm(M_c),
            "sigma_b_kg_cm2": sigma_b_c,
            "sigma_b_N_mm2": kg_cm2_to_N_mm2(sigma_b_c),
            "fb_kg_cm2": fb_g,
            "fb_N_mm2": kg_cm2_to_N_mm2(fb_g),
            "ok": c_b_ok,
            "verdict": "ＯＫ" if c_b_ok else "ＮＧ",
        },
        "shear": {
            "Q_kg": Q_c,
            "Q_N": kgf_to_N(Q_c),
            "tau_kg_cm2": tau_c,
            "tau_N_mm2": kg_cm2_to_N_mm2(tau_c),
            "fs_kg_cm2": fs_g,
            "fs_N_mm2": kg_cm2_to_N_mm2(fs_g),
            "ok": c_q_ok,
            "verdict": "ＯＫ" if c_q_ok else "ＮＧ",
        },
        "deflection": {
            "delta_p1_cm": d_c_p1,
            "delta_p2_cm": d_c_p2,
            "delta_w_cm": d_c_w,
            "delta_cm": delta_c,
            "delta_mm": cm_to_mm(delta_c),
            "summary_cm": round_half_up(delta_c, 2),
            "limit_check": c_defl_chk,
        },
    }

    summary_rows = [
        {
            "section": "鉄骨吊り足場",
            "part": "吊りチェーン",
            "member": chain["display_name"],
            "verdict": chain_res["verdict"],
            "ratio": chain_res["ratio"],
            "bending": None,
            "shear": None,
            "deflection_cm": None,
        },
        {
            "section": "鉄骨吊り足場",
            "part": "足場板",
            "member": plank["display_name"],
            "verdict": None,
            "ratio": None,
            "bending": plank_res["bending"]["verdict"],
            "shear": plank_res["shear"]["verdict"],
            "deflection_cm": plank_res["deflection"]["summary_cm"],
            "deflection_verdict": (
                plank_res["deflection"]["limit_check"]["verdict"]
                if plank_res["deflection"]["limit_check"]
                else None
            ),
        },
        {
            "section": "鉄骨吊り足場",
            "part": "根太",
            "member": joist["display_name"],
            "verdict": None,
            "ratio": None,
            "bending": joist_res["bending"]["verdict"],
            "shear": joist_res["shear"]["verdict"],
            "deflection_cm": joist_res["deflection"]["summary_cm"],
            "deflection_verdict": (
                joist_res["deflection"]["limit_check"]["verdict"]
                if joist_res["deflection"]["limit_check"]
                else None
            ),
        },
        {
            "section": "鉄骨吊り足場",
            "part": "大引",
            "member": girder["display_name"],
            "verdict": None,
            "ratio": None,
            "bending": girder_res["bending"]["verdict"],
            "shear": girder_res["shear"]["verdict"],
            "deflection_cm": girder_res["deflection"]["summary_cm"],
            "deflection_verdict": g_defl_chk["verdict"] if g_defl_chk else None,
        },
        {
            "section": "鉄骨吊り足場",
            "part": "張出部",
            "member": girder["display_name"],
            "verdict": None,
            "ratio": None,
            "bending": cantilever_res["bending"]["verdict"],
            "shear": cantilever_res["shear"]["verdict"],
            "deflection_cm": cantilever_res["deflection"]["summary_cm"],
            "deflection_verdict": c_defl_chk["verdict"] if c_defl_chk else None,
        },
    ]

    defl_checks = [
        plank_res["deflection"]["limit_check"],
        joist_res["deflection"]["limit_check"],
        g_defl_chk,
        c_defl_chk,
    ]
    all_ok = (
        chain_ok
        and plank_res["bending"]["ok"]
        and plank_res["shear"]["ok"]
        and joist_res["bending"]["ok"]
        and joist_res["shear"]["ok"]
        and g_b_ok
        and g_q_ok
        and c_b_ok
        and c_q_ok
        and all((dc["ok"] if dc else True) for dc in defl_checks)
    )

    return {
        "module": "tsuri_ashiba",
        "title": "鉄骨吊り足場 強度計算書",
        "overview": {
            "span_x_m": span_x,
            "span_y_m": span_y,
            "girder_spacing_m": girder_spacing,
            "joist_spacing_m": joist_spacing,
            "support_to_plank_center_m": plank_offset_m,
            "cantilever_length_m": cantilever_m,
        },
        "loads": {
            "dead_items": dead_items,
            "dead_total_kg": dead_total,
            "dead_total_N": kgf_to_N(dead_total),
            "worker_kg": worker_kg,
            "worker_count": worker_count,
            "live_workers_kg": live_workers,
            "bolt_kg": bolt_kg,
            "bolt_count": bolt_count,
            "live_bolts_kg": live_bolts,
            "live_total_kg": live_total,
            "live_total_N": kgf_to_N(live_total),
        },
        "chain": chain_res,
        "plank": plank_res,
        "joist": joist_res,
        "girder": girder_res,
        "cantilever": cantilever_res,
        "summary_rows": summary_rows,
        "all_ok": all_ok,
    }


def _calc_simply_supported_center_point(
    member: dict[str, Any],
    L_cm: float,
    P_kg: float,
    w_kg_cm: float,
    z_digits: int = 2,
    deflection_limit_div: int | None = None,
) -> dict[str, Any]:
    A = float(member["A_cm2"])
    I = float(member["I_cm4"])
    Z_disp = float(member["Z_cm3"])
    Z_calc = round_half_up(Z_disp, z_digits)
    E = float(member["E_kg_cm2"])
    kappa = float(member["kappa"])
    fb = float(member["fb_long_kg_cm2"])
    fs = float(member["fs_long_kg_cm2"])

    M = round_half_up((P_kg * L_cm) / 4.0 + (w_kg_cm * (L_cm**2)) / 8.0, 1)
    sigma_b = round_half_up(M / Z_calc, 1)
    b_ok = sigma_b <= fb

    Q_p = round_half_up(P_kg / 2.0, 1)
    Q_w = round_half_up((w_kg_cm * L_cm) / 2.0, 1)
    Q = round_half_up(Q_p + Q_w, 1)
    tau = round_half_up((kappa * Q) / A, 1)
    q_ok = tau <= fs

    d_p = round_half_up((P_kg * (L_cm**3)) / (48.0 * E * I), 3)
    d_w = round_half_up((5.0 * w_kg_cm * (L_cm**4)) / (384.0 * E * I), 3)
    delta = round_half_up(d_p + d_w, 3)
    defl_chk = _check_deflection(delta, L_cm, deflection_limit_div)

    return {
        "member": member["display_name"],
        "L_cm": L_cm,
        "P_kg": P_kg,
        "P_N": kgf_to_N(P_kg),
        "w_kg_cm": w_kg_cm,
        "w_N_mm": kg_cm_to_N_mm(w_kg_cm),
        "section": {
            "A_cm2": A,
            "I_cm4": I,
            "Z_cm3": Z_disp,
            "E_kg_cm2": E,
            "kappa": kappa,
            "fb_kg_cm2": fb,
            "fs_kg_cm2": fs,
        },
        "bending": {
            "M_kg_cm": M,
            "M_kN_mm": kg_cm_to_kN_mm(M),
            "sigma_b_kg_cm2": sigma_b,
            "sigma_b_N_mm2": kg_cm2_to_N_mm2(sigma_b),
            "fb_kg_cm2": fb,
            "fb_N_mm2": kg_cm2_to_N_mm2(fb),
            "ok": b_ok,
            "verdict": "ＯＫ" if b_ok else "ＮＧ",
        },
        "shear": {
            "Q_kg": Q,
            "Q_N": kgf_to_N(Q),
            "tau_kg_cm2": tau,
            "tau_N_mm2": kg_cm2_to_N_mm2(tau),
            "fs_kg_cm2": fs,
            "fs_N_mm2": kg_cm2_to_N_mm2(fs),
            "ok": q_ok,
            "verdict": "ＯＫ" if q_ok else "ＮＧ",
        },
        "deflection": {
            "delta_p_cm": d_p,
            "delta_w_cm": d_w,
            "delta_cm": delta,
            "delta_mm": cm_to_mm(delta),
            "summary_cm": round_half_up(delta, 2),
            "limit_check": defl_chk,
        },
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

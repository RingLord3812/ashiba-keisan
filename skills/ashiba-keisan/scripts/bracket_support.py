"""モジュール3: 足場受ブラケット 強度計算エンジン (SUCCES Ver 4.11 準拠, PDF p.12-21)."""

from __future__ import annotations

import math
from typing import Any

from .catalog import Catalog
from .units import cm_to_mm, kg_cm2_to_N_mm2, kg_cm_to_kN_mm, kg_cm_to_N_mm, kg_m_to_N_m, kgf_to_N, round_half_up


def compute_aij_ltb_fb(
    E_kg_cm2: float,
    F_kg_cm2: float,
    ft_kg_cm2: float,
    Lb_cm: float,
    i_ltb_cm: float,
    h_cm: float,
    Af_cm2: float,
    C_ltb: float = 1.0,
    strict_aij: bool = False,
) -> dict[str, Any]:
    """AIJ 鋼構造設計規準による横座屈考慮 許容曲げ応力度 fb を算出する."""
    pi_val = math.pi if strict_aij else 3.142
    Lam = round_half_up(math.sqrt((E_kg_cm2 * (pi_val**2)) / (0.6 * F_kg_cm2)), 0)
    ft_t = ft_kg_cm2 / 1000.0  # t/cm2
    Fb1_t = round_half_up((1.0 - 0.4 * ((Lb_cm / i_ltb_cm) ** 2) / (C_ltb * (Lam**2))) * ft_t, 3)
    Fb2_t = round_half_up(900.0 / (Lb_cm * h_cm / Af_cm2), 3) if Lb_cm > 0 else ft_t
    fb_t = min(ft_t, max(Fb1_t, Fb2_t))
    fb_kg = round_half_up(fb_t * 1000.0, 0)
    return {
        "Lambda": int(Lam),
        "Lb_cm": Lb_cm,
        "i_cm": i_ltb_cm,
        "C_ltb": C_ltb,
        "h_cm": h_cm,
        "Af_cm2": Af_cm2,
        "Ft_t_cm2": ft_t,
        "Fb1_t_cm2": Fb1_t,
        "Fb2_t_cm2": Fb2_t,
        "fb_t_cm2": fb_t,
        "fb_kg_cm2": fb_kg,
        "fb_N_mm2": kg_cm2_to_N_mm2(fb_kg),
    }


def calculate_bracket_support(
    params: dict[str, Any],
    catalog: Catalog,
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """足場受ブラケット強度計算 (荷重・大引・ブラケット・溶接・アンカー・コンクリート・BP) を実行する."""
    options = options or {}
    strict_aij = bool(options.get("strict_aij", False))
    deflection_limit_div = options.get("deflection_limit")

    building_h = float(params["building_height_m"])
    scaffold_h = float(params["scaffold_height_m"])
    bracket_elev_m = float(params.get("bracket_elevation_m", 5.800))
    tiers = int(params["tiers"])
    bay_span = float(params.get("bay_span_m", 1.800))
    bracket_span_m = float(params.get("bracket_span_m", 5.400))

    frame = catalog.get_material("frames", params.get("frame", "TC-917"))
    ledger = catalog.get_material("ledgers", params.get("ledger", "SYi-518"))
    brace = catalog.get_material("braces", params.get("brace", "SXB-1618"))
    pin = catalog.get_material("frame_accessories", params.get("joint_pin", "Mジョイント"))
    armlock = catalog.get_material("frame_accessories", params.get("arm_lock", "ALB8"))
    stair = catalog.get_material("frame_accessories", params.get("stair", "KS-1718"))

    jb_mat = catalog.get_material("jack_bases", params.get("jack_base", "BB-35"))
    base_tie = catalog.get_material("single_pipes", params.get("base_tie_pipe", "単管φ48.6x2.3 (STK400)"))
    base_plank = catalog.get_material("planks", params.get("base_plank", "足場板 25x240 (合板)"))
    base_timber = catalog.get_material("timbers", params.get("base_timber", "端太角 90x90 (松・栂Ⅱ類)"))

    girder_mat = catalog.get_material("h_beams", params.get("girder_material", "H形鋼 200x200x8x12 (SS400)"))
    bracket_mat = catalog.get_material("h_beams", params.get("bracket_material", "H形鋼 300x300x10x15 (SS400)"))
    n_girders = int(params.get("num_girders", 2))

    frame_h = float(params.get("frame_height_m", frame["height_m"]))
    frame_w = float(params.get("frame_width_m", frame["width_m"]))
    stair_tiers = int(params.get("stair_tiers", 1))
    sheet_name = params.get("sheet_name", "メッシュシート")
    sheet_unit_w = float(params.get("sheet_unit_weight_kg_m2", 0.460))

    # 2. 荷重計算
    ledger_tiers = int(params.get("ledger_tiers", max(tiers - 1, 0)))
    joint_tiers = int(params.get("joint_tiers", max(tiers - 1, 0)))

    n1_items = [
        {
            "label": "建枠",
            "spec": frame["display_name"],
            "expr": f"{frame['weight_kg']:.3f} kg × {tiers}段 × 1本",
            "weight_kg": round_half_up(frame["weight_kg"] * tiers * 1, 1),
        },
        {
            "label": "布枠",
            "spec": ledger["display_name"],
            "expr": f"{ledger['weight_kg']:.3f} kg × {ledger_tiers}段 × 1枚",
            "weight_kg": round_half_up(ledger["weight_kg"] * ledger_tiers * 1, 1),
        },
        {
            "label": "筋かい",
            "spec": brace["display_name"],
            "expr": f"{brace['weight_kg']:.3f} kg × {tiers}段 × 2本",
            "weight_kg": round_half_up(brace["weight_kg"] * tiers * 2, 1),
        },
        {
            "label": "連結ピン",
            "spec": pin["display_name"],
            "expr": f"{pin['weight_kg']:.3f} kg × {joint_tiers}段 × 2本",
            "weight_kg": round_half_up(pin["weight_kg"] * joint_tiers * 2, 1),
        },
        {
            "label": "アームロック",
            "spec": armlock["display_name"],
            "expr": f"{armlock['weight_kg']:.3f} kg × {joint_tiers}段 × 2枚",
            "weight_kg": round_half_up(armlock["weight_kg"] * joint_tiers * 2, 1),
        },
        {
            "label": "階段",
            "spec": stair["display_name"],
            "expr": f"{stair['weight_kg']:.3f} kg × {stair_tiers}段 × 1本",
            "weight_kg": round_half_up(stair["weight_kg"] * stair_tiers * 1, 1),
        },
        {
            "label": "養生",
            "spec": sheet_name,
            "expr": f"{sheet_unit_w:.3f} kg/㎡ × {scaffold_h:.3f}ｍ × {bay_span:.3f}ｍ",
            "weight_kg": round_half_up(sheet_unit_w * scaffold_h * bay_span, 1),
        },
    ]
    N1 = round_half_up(sum(it["weight_kg"] for it in n1_items), 1)

    n2_items = [
        {
            "label": "ジャッキベース",
            "spec": jb_mat["display_name"],
            "expr": f"{jb_mat['weight_kg']:.3f} kg × 2個",
            "weight_kg": round_half_up(jb_mat["weight_kg"] * 2, 1),
        },
        {
            "label": "根がらみ",
            "spec": base_tie["display_name"],
            "expr": f"{base_tie['unit_weight_kg_m']:.3f} kg/ｍ × {bay_span:.3f}ｍ × 2本",
            "weight_kg": round_half_up(base_tie["unit_weight_kg_m"] * bay_span * 2, 1),
        },
        {
            "label": "足場板",
            "spec": base_plank["display_name"],
            "expr": f"{base_plank['unit_weight_kg_m']:.3f} kg/ｍ × {bay_span:.3f}ｍ × 2枚",
            "weight_kg": round_half_up(base_plank["unit_weight_kg_m"] * bay_span * 2, 1),
        },
        {
            "label": "根太",
            "spec": base_timber["display_name"],
            "expr": f"{base_timber['unit_weight_kg_m']:.3f} kg/ｍ × {bay_span:.3f}ｍ × 2本",
            "weight_kg": round_half_up(base_timber["unit_weight_kg_m"] * bay_span * 2, 1),
        },
    ]
    N2 = round_half_up(sum(it["weight_kg"] for it in n2_items), 1)

    live_per_layer = float(params.get("live_load_per_layer_kg", 400.0))
    live_layers = int(params.get("live_load_layers", 2))
    N3 = round_half_up(live_per_layer * live_layers, 1)
    N4 = float(girder_mat["unit_weight_kg_m"])

    loads_res = {
        "N1_items": n1_items,
        "N1_kg": N1,
        "N1_N": kgf_to_N(N1),
        "N2_items": n2_items,
        "N2_kg": N2,
        "N2_N": kgf_to_N(N2),
        "live_per_layer_kg": live_per_layer,
        "live_layers": live_layers,
        "N3_kg": N3,
        "N3_N": kgf_to_N(N3),
        "N4_kg_m": N4,
        "N4_N_m": kg_m_to_N_m(N4),
    }

    # 3. 大引の検討
    L_g_cm = bracket_span_m * 100.0
    a2_cm = bay_span * 100.0
    n_bays = max(int(round(bracket_span_m / bay_span)), 1)
    n_interior = max(n_bays - 1, 0)

    P_g = round_half_up((N1 + N2 + N3) / n_girders, 1)
    w_g_cm = round_half_up(N4 / 100.0, 3)

    Ra = round_half_up(P_g * n_interior / 2.0, 1)
    Rb = Ra
    # 集中荷重によるスパン中央曲げモーメント (対称等間隔載荷)
    M_g_p = Ra * (L_g_cm / 2.0)
    for j in range(1, n_interior + 1):
        xj = j * a2_cm
        if xj < L_g_cm / 2.0:
            M_g_p -= P_g * (L_g_cm / 2.0 - xj)
    M_g_w = (w_g_cm * (L_g_cm**2)) / 8.0
    M_g = round_half_up(M_g_p + M_g_w, -1) if not strict_aij else round_half_up(M_g_p + M_g_w, 1)

    I_g = float(girder_mat["I_cm4"])
    Z_g = float(girder_mat["Z_cm3"])
    E_g = float(girder_mat["E_kg_cm2"])
    fs_g = float(girder_mat["fs_long_kg_cm2"])
    h_g = float(girder_mat["h_cm"])
    tw_g = float(girder_mat["tw_cm"])
    b_g = float(girder_mat["b_cm"])
    tf_g = float(girder_mat["tf_cm"])
    i_g = float(girder_mat["i_ltb_cm"])
    F_g = float(girder_mat["F_kg_cm2"])
    ft_g = float(girder_mat["ft_long_kg_cm2"])

    sigma_b_g = round_half_up(M_g / Z_g, 1)
    ltb_g = compute_aij_ltb_fb(
        E_kg_cm2=E_g,
        F_kg_cm2=F_g,
        ft_kg_cm2=ft_g,
        Lb_cm=float(params.get("girder_Lb_cm", L_g_cm)),
        i_ltb_cm=i_g,
        h_cm=h_g,
        Af_cm2=b_g * tf_g,
        C_ltb=float(params.get("girder_C_ltb", 1.0)),
        strict_aij=strict_aij,
    )
    fb_g = ltb_g["fb_kg_cm2"]
    g_b_ok = sigma_b_g <= fb_g

    Q_g = round_half_up(Ra + 0.5 * w_g_cm * L_g_cm, 1)
    tau_g = round_half_up(Q_g / (h_g * tw_g), 1)
    g_q_ok = tau_g <= fs_g

    # 大引たわみ: SUCCESデフォルト (多点載荷 63/1000 係数) vs --strict-aij (厳密重ね合わせ)
    if not strict_aij and n_bays >= 3:
        d_g_p = round_half_up((63.0 * P_g * (L_g_cm**3)) / (1000.0 * E_g * I_g), 3)
        deflection_formula_note = "63PL³/(1000EI) + 5wL⁴/(384EI) [SUCCES標準]"
    else:
        d_g_p_raw = 0.0
        for j in range(1, n_interior + 1):
            aj = min(j * a2_cm, L_g_cm - j * a2_cm)
            d_g_p_raw += (P_g * aj * (3.0 * (L_g_cm**2) - 4.0 * (aj**2))) / (48.0 * E_g * I_g)
        d_g_p = round_half_up(d_g_p_raw, 3)
        deflection_formula_note = "Σ[Pa(3L²-4a²)/(48EI)] + 5wL⁴/(384EI) [厳密重ね合わせ]"
    d_g_w = round_half_up((5.0 * w_g_cm * (L_g_cm**4)) / (384.0 * E_g * I_g), 3)
    delta_g = round_half_up(d_g_p + d_g_w, 3)
    g_defl_chk = _check_deflection(delta_g, L_g_cm, deflection_limit_div)

    girder_res = {
        "member": girder_mat["display_name"],
        "num_girders": n_girders,
        "L_m": bracket_span_m,
        "L_cm": L_g_cm,
        "a2_cm": a2_cm,
        "n_bays": n_bays,
        "section": {
            "I_cm4": I_g,
            "Z_cm3": Z_g,
            "E_kg_cm2": E_g,
            "fs_kg_cm2": fs_g,
            "i_ltb_cm": i_g,
            "h_cm": h_g,
            "b_cm": b_g,
            "tw_cm": tw_g,
            "tf_cm": tf_g,
        },
        "P_kg": P_g,
        "P_N": kgf_to_N(P_g),
        "w_kg_m": N4,
        "w_kg_cm": w_g_cm,
        "w_N_mm": kg_cm_to_N_mm(w_g_cm),
        "Ra_kg": Ra,
        "Rb_kg": Rb,
        "bending": {
            "M_kg_cm": M_g,
            "M_kN_mm": kg_cm_to_kN_mm(M_g),
            "sigma_b_kg_cm2": sigma_b_g,
            "sigma_b_N_mm2": kg_cm2_to_N_mm2(sigma_b_g),
            "ltb": ltb_g,
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
            "formula_note": deflection_formula_note,
            "delta_p_cm": d_g_p,
            "delta_w_cm": d_g_w,
            "delta_cm": delta_g,
            "delta_mm": cm_to_mm(delta_g),
            "summary_cm": round_half_up(delta_g, 2),
            "limit_check": g_defl_chk,
        },
    }

    # 4. 足場受ブラケットの検討 (片持梁)
    brk_cfg = params.get("bracket_geometry", {})
    L_brk_cm = float(brk_cfg.get("length_cm", 150.0))
    a_brk_cm = float(brk_cfg.get("frame_width_a_cm", frame_w * 100.0))
    b_brk_cm = float(brk_cfg.get("wall_clearance_b_cm", 30.0))
    Pn = int(brk_cfg.get("frames_per_span", n_bays))
    Po = int(brk_cfg.get("girders_on_bracket", n_girders))
    frame_legs = int(brk_cfg.get("frame_legs", 2))

    P_brk = round_half_up(((N1 + N2 + N3) * Pn + N4 * bracket_span_m * Po) / frame_legs, 1)
    w_brk_m = float(bracket_mat["unit_weight_kg_m"])
    w_brk_cm = round_half_up(w_brk_m / 100.0, 3)

    M_brk = round_half_up(
        (a_brk_cm + b_brk_cm) * P_brk + b_brk_cm * P_brk + 0.5 * w_brk_cm * (L_brk_cm**2),
        0,
    )
    I_b = float(bracket_mat["I_cm4"])
    Z_b = float(bracket_mat["Z_cm3"])
    E_b = float(bracket_mat["E_kg_cm2"])
    fs_b = float(bracket_mat["fs_long_kg_cm2"])
    h_b = float(bracket_mat["h_cm"])
    tw_b = float(bracket_mat["tw_cm"])
    b_b = float(bracket_mat["b_cm"])
    tf_b = float(bracket_mat["tf_cm"])
    i_b = float(bracket_mat["i_ltb_cm"])
    F_b = float(bracket_mat["F_kg_cm2"])
    ft_b = float(bracket_mat["ft_long_kg_cm2"])

    sigma_b_brk = round_half_up(M_brk / Z_b, 1)
    Lb_brk_cm = float(brk_cfg.get("Lb_cm", round_half_up(1.6 * L_brk_cm, 1)))
    ltb_b = compute_aij_ltb_fb(
        E_kg_cm2=E_b,
        F_kg_cm2=F_b,
        ft_kg_cm2=ft_b,
        Lb_cm=Lb_brk_cm,
        i_ltb_cm=i_b,
        h_cm=h_b,
        Af_cm2=b_b * tf_b,
        C_ltb=float(brk_cfg.get("C_ltb", 1.75)),
        strict_aij=strict_aij,
    )
    fb_brk = ltb_b["fb_kg_cm2"]
    b_b_ok = sigma_b_brk <= fb_brk

    Q_brk = round_half_up(2.0 * P_brk + w_brk_cm * L_brk_cm, 1)
    tau_brk = round_half_up(Q_brk / (h_b * tw_b), 1)
    b_q_ok = tau_brk <= fs_b

    d_brk_w = round_half_up((w_brk_cm * (L_brk_cm**4)) / (8.0 * E_b * I_b), 4)
    d_brk_p = round_half_up(
        (P_brk / (6.0 * E_b * I_b))
        * (
            ((a_brk_cm + b_brk_cm) ** 2) * (3.0 * L_brk_cm - a_brk_cm - b_brk_cm)
            + (b_brk_cm**2) * (3.0 * L_brk_cm - b_brk_cm)
        ),
        3,
    )
    delta_brk_raw = d_brk_w + d_brk_p
    delta_brk = round_half_up(delta_brk_raw, 3)
    b_defl_chk = _check_deflection(delta_brk, L_brk_cm, deflection_limit_div)

    bracket_res = {
        "member": bracket_mat["display_name"],
        "L_cm": L_brk_cm,
        "a_cm": a_brk_cm,
        "b_cm": b_brk_cm,
        "Pn": Pn,
        "Po": Po,
        "section": {
            "I_cm4": I_b,
            "Z_cm3": Z_b,
            "E_kg_cm2": E_b,
            "fs_kg_cm2": fs_b,
            "i_ltb_cm": i_b,
            "h_cm": h_b,
            "b_cm": b_b,
            "tw_cm": tw_b,
            "tf_cm": tf_b,
        },
        "P_kg": P_brk,
        "P_N": kgf_to_N(P_brk),
        "w_kg_m": w_brk_m,
        "w_kg_cm": w_brk_cm,
        "w_N_mm": kg_cm_to_N_mm(w_brk_cm),
        "bending": {
            "M_kg_cm": M_brk,
            "M_kN_mm": kg_cm_to_kN_mm(M_brk),
            "sigma_b_kg_cm2": sigma_b_brk,
            "sigma_b_N_mm2": kg_cm2_to_N_mm2(sigma_b_brk),
            "ltb": ltb_b,
            "fb_kg_cm2": fb_brk,
            "fb_N_mm2": kg_cm2_to_N_mm2(fb_brk),
            "ok": b_b_ok,
            "verdict": "ＯＫ" if b_b_ok else "ＮＧ",
        },
        "shear": {
            "Q_kg": Q_brk,
            "Q_N": kgf_to_N(Q_brk),
            "tau_kg_cm2": tau_brk,
            "tau_N_mm2": kg_cm2_to_N_mm2(tau_brk),
            "fs_kg_cm2": fs_b,
            "fs_N_mm2": kg_cm2_to_N_mm2(fs_b),
            "ok": b_q_ok,
            "verdict": "ＯＫ" if b_q_ok else "ＮＧ",
        },
        "deflection": {
            "delta_w_cm": d_brk_w,
            "delta_p_cm": d_brk_p,
            "delta_cm": delta_brk,
            "delta_mm": cm_to_mm(delta_brk),
            "summary_cm": round_half_up(delta_brk, 2),
            "limit_check": b_defl_chk,
        },
    }

    # 5〜8. ベースプレート溶接・アンカーボルト・コンクリート支圧・ベースプレートの検討
    conn = calculate_bracket_connection(
        M_kg_cm=M_brk,
        Q_kg=Q_brk,
        bracket_mat=bracket_mat,
        weld_cfg=params.get("weld", {}),
        anc_cfg=params.get("anchor_bolt", {}),
        conc_cfg=params.get("concrete", {}),
        bp_cfg=params.get("base_plate", {}),
        catalog=catalog,
    )
    weld_res = conn["weld"]
    anchor_res = conn["anchor_bolt"]
    concrete_res = conn["concrete"]
    base_plate_res = conn["base_plate"]
    conc_ok = concrete_res["ok"]

    summary_rows = [
        {
            "section": "足場受ブラケット",
            "part": "大引",
            "member": girder_mat["display_name"],
            "verdict": None,
            "ratio": None,
            "bending": girder_res["bending"]["verdict"],
            "shear": girder_res["shear"]["verdict"],
            "deflection_cm": girder_res["deflection"]["summary_cm"],
            "deflection_verdict": g_defl_chk["verdict"] if g_defl_chk else None,
        },
        {
            "section": "足場受ブラケット",
            "part": "ブラケット",
            "member": bracket_mat["display_name"],
            "verdict": None,
            "ratio": None,
            "bending": bracket_res["bending"]["verdict"],
            "shear": bracket_res["shear"]["verdict"],
            "deflection_cm": bracket_res["deflection"]["summary_cm"],
            "deflection_verdict": b_defl_chk["verdict"] if b_defl_chk else None,
        },
    ]

    all_ok = (
        g_b_ok
        and g_q_ok
        and b_b_ok
        and b_q_ok
        and weld_res["ok"]
        and anchor_res["ok"]
        and conc_ok
        and base_plate_res["ok"]
        and (g_defl_chk["ok"] if g_defl_chk else True)
        and (b_defl_chk["ok"] if b_defl_chk else True)
    )

    return {
        "module": "bracket_support",
        "title": "足場受ブラケット 強度計算書",
        "overview": {
            "building_height_m": building_h,
            "scaffold_height_m": scaffold_h,
            "bracket_elevation_m": bracket_elev_m,
            "tiers": tiers,
            "bay_span_m": bay_span,
            "frame_height_m": frame_h,
            "frame_width_m": frame_w,
            "bracket_span_m": bracket_span_m,
            "num_girders": n_girders,
            "girder_material": girder_mat["display_name"],
            "bracket_material": bracket_mat["display_name"],
        },
        "loads": loads_res,
        "girder": girder_res,
        "bracket": bracket_res,
        "weld": weld_res,
        "anchor_bolt": anchor_res,
        "concrete": concrete_res,
        "base_plate": base_plate_res,
        "summary_rows": summary_rows,
        "all_ok": all_ok,
    }


def calculate_bracket_connection(
    M_kg_cm: float,
    Q_kg: float,
    bracket_mat: dict[str, Any],
    weld_cfg: dict[str, Any],
    anc_cfg: dict[str, Any],
    conc_cfg: dict[str, Any],
    bp_cfg: dict[str, Any],
    catalog: Catalog,
) -> dict[str, Any]:
    """ブラケット接合部 (溶接・アンカーボルト・コンクリート支圧・ベースプレート) の単体/共通検討."""
    h_b = float(bracket_mat["h_cm"])
    b_b = float(bracket_mat["b_cm"])

    # 5. ベースプレート溶接部の検討
    weld_grade = weld_cfg.get("grade", bracket_mat.get("grade", "SS400"))
    weld_allow = catalog.materials["weld_allowables"].get(weld_grade, catalog.materials["weld_allowables"]["SS400"])

    L1_w = float(weld_cfg.get("flange_length_cm", round_half_up(b_b - 2.0, 1)))
    a1_w = float(weld_cfg.get("flange_throat_cm", 1.0))
    L2_w = float(weld_cfg.get("web_length_cm", round_half_up(h_b - 6.0, 1)))
    a2_w = float(weld_cfg.get("web_throat_cm", 1.0))
    fs_butt = float(weld_cfg.get("butt_fs_kg_cm2", weld_allow["butt_weld_fs_kg_cm2"]))
    fs_pen = float(weld_cfg.get("penetration_fs_kg_cm2", weld_allow["full_penetration_shear_fs_kg_cm2"]))

    Z_w = round_half_up((L1_w / (6.0 * (h_b + 2.0 * a1_w))) * (((h_b + 2.0 * a1_w) ** 3) - (h_b**3)), 1)
    sigma_b_w = round_half_up(M_kg_cm / Z_w, 1)
    w_b_ok = sigma_b_w <= fs_butt

    A_w = round_half_up(2.0 * a2_w * L2_w, 1)
    tau_w = round_half_up(Q_kg / A_w, 1)
    w_q_ok = tau_w <= fs_pen

    sigma_MQ = round_half_up(math.sqrt(sigma_b_w**2 + tau_w**2), 1)
    w_comb_ok = sigma_MQ <= fs_pen

    weld_res = {
        "L1_cm": L1_w,
        "a1_cm": a1_w,
        "L2_cm": L2_w,
        "a2_cm": a2_w,
        "h_cm": h_b,
        "b_cm": b_b,
        "fs_butt_kg_cm2": fs_butt,
        "fs_pen_kg_cm2": fs_pen,
        "Z_w_cm3": Z_w,
        "sigma_b_kg_cm2": sigma_b_w,
        "sigma_b_N_mm2": kg_cm2_to_N_mm2(sigma_b_w),
        "fs_butt_N_mm2": kg_cm2_to_N_mm2(fs_butt),
        "bending_ok": w_b_ok,
        "bending_verdict": "ＯＫ" if w_b_ok else "ＮＧ",
        "A_w_cm2": A_w,
        "tau_kg_cm2": tau_w,
        "tau_N_mm2": kg_cm2_to_N_mm2(tau_w),
        "fs_pen_N_mm2": kg_cm2_to_N_mm2(fs_pen),
        "shear_ok": w_q_ok,
        "shear_verdict": "ＯＫ" if w_q_ok else "ＮＧ",
        "sigma_MQ_kg_cm2": sigma_MQ,
        "sigma_MQ_N_mm2": kg_cm2_to_N_mm2(sigma_MQ),
        "combined_ok": w_comb_ok,
        "combined_verdict": "ＯＫ" if w_comb_ok else "ＮＧ",
        "ok": w_b_ok and w_q_ok and w_comb_ok,
    }

    # 6. アンカーボルトの検討
    bp_h_cm = float(bp_cfg.get("height_cm", 60.0))
    bp_b_cm = float(bp_cfg.get("width_cm", 50.0))
    bp_t_mm = float(bp_cfg.get("thickness_mm", 25.0))
    bp_t_cm = bp_t_mm / 10.0

    bolt = catalog.get_material("anchor_bolts", anc_cfg.get("size", "M20"))
    n_t = int(anc_cfg.get("tension_count", 4))
    n_c = int(anc_cfg.get("compression_count", 2))
    A_bolt = float(bolt["A_cm2"])
    psi_bolt = float(bolt["perimeter_cm"])
    fs_bolt = float(anc_cfg.get("fs_kg_cm2", bolt["fs_kg_cm2"]))
    ft_bolt = float(anc_cfg.get("ft_kg_cm2", bolt["ft_kg_cm2"]))

    Q1_bolt = round_half_up(Q_kg / (n_t + n_c), 1)
    tau_bolt = round_half_up(Q1_bolt / A_bolt, 1)
    anc_q_ok = tau_bolt <= fs_bolt

    dt_center_cm = float(anc_cfg.get("tension_bolt_to_center_cm", round_half_up((bp_h_cm / 2.0) - 7.5, 1)))
    comp_half_cm = round_half_up(bp_h_cm / 2.0, 1)
    j_cm = round_half_up(dt_center_cm + comp_half_cm * (2.0 / 3.0), 2)

    T1_bolt = round_half_up(M_kg_cm / (j_cm * n_t), 1)
    fts_raw = round_half_up(1.4 * ft_bolt - 1.6 * tau_bolt, 1)
    fts_allow = min(ft_bolt, fts_raw)
    sigma_ts = round_half_up(T1_bolt / A_bolt, 1)
    anc_t_ok = sigma_ts <= fts_allow

    conc_grade = conc_cfg.get("grade", "Fc27")
    conc_mat = catalog.materials["concrete_grades"].get(conc_grade, catalog.materials["concrete_grades"]["Fc27"])
    Fc_kg = float(conc_cfg.get("Fc_kg_cm2", conc_mat["Fc_kg_cm2"]))
    fa_bond = float(anc_cfg.get("fa_bond_kg_cm2", conc_mat["fa_bond_kg_cm2"]))

    L_embed = round_half_up(T1_bolt / (fa_bond * psi_bolt), 1)
    L_embed_hook = round_half_up((2.0 / 3.0) * L_embed, 1)
    L_adopted = float(anc_cfg.get("adopted_length_cm", math.ceil(L_embed / 5.0) * 5.0))

    anchor_res = {
        "size": bolt["display_name"],
        "tension_count": n_t,
        "compression_count": n_c,
        "A_cm2": A_bolt,
        "perimeter_cm": psi_bolt,
        "fs_kg_cm2": fs_bolt,
        "ft_kg_cm2": ft_bolt,
        "Q1_kg": Q1_bolt,
        "Q1_N": kgf_to_N(Q1_bolt),
        "tau_kg_cm2": tau_bolt,
        "tau_N_mm2": kg_cm2_to_N_mm2(tau_bolt),
        "fs_N_mm2": kg_cm2_to_N_mm2(fs_bolt),
        "shear_ok": anc_q_ok,
        "shear_verdict": "ＯＫ" if anc_q_ok else "ＮＧ",
        "dt_center_cm": dt_center_cm,
        "comp_half_cm": comp_half_cm,
        "j_cm": j_cm,
        "T1_kg": T1_bolt,
        "T1_N": kgf_to_N(T1_bolt),
        "fts_calc_kg_cm2": fts_raw,
        "fts_allow_kg_cm2": fts_allow,
        "fts_allow_N_mm2": kg_cm2_to_N_mm2(fts_allow),
        "sigma_ts_kg_cm2": sigma_ts,
        "sigma_ts_N_mm2": kg_cm2_to_N_mm2(sigma_ts),
        "tension_ok": anc_t_ok,
        "tension_verdict": "ＯＫ" if anc_t_ok else "ＮＧ",
        "fa_bond_kg_cm2": fa_bond,
        "embedment_straight_cm": L_embed,
        "embedment_hook_cm": L_embed_hook,
        "adopted_length_cm": L_adopted,
        "ok": anc_q_ok and anc_t_ok,
    }

    # 7. コンクリートの圧縮応力度の検討
    fc_conc = round_half_up((1.0 / 3.0) * Fc_kg * 1.5, 1)
    sigma_conc = round_half_up((4.0 * M_kg_cm) / (bp_b_cm * bp_h_cm * j_cm), 1)
    conc_ok = sigma_conc <= fc_conc

    concrete_res = {
        "Fc_kg_cm2": Fc_kg,
        "Fc_N_mm2": round_half_up(Fc_kg / 10.0, 1),
        "fc_allow_kg_cm2": fc_conc,
        "fc_allow_N_mm2": kg_cm2_to_N_mm2(fc_conc),
        "bp_width_cm": bp_b_cm,
        "bp_height_cm": bp_h_cm,
        "j_cm": j_cm,
        "sigma_kg_cm2": sigma_conc,
        "sigma_N_mm2": kg_cm2_to_N_mm2(sigma_conc),
        "ok": conc_ok,
        "verdict": "ＯＫ" if conc_ok else "ＮＧ",
    }

    # 8. ベースプレートの検討
    bp_F_steel = float(bp_cfg.get("F_kg_cm2", 2400.0))
    bp_term_factor = float(bp_cfg.get("term_factor", 1.25))
    fb_bp = round_half_up((1.0 / 1.3) * bp_F_steel * bp_term_factor, 0)

    bp_t_cant_L = float(bp_cfg.get("tension_cantilever_cm", 7.5))
    bp_t_pitch = float(bp_cfg.get("tension_bolt_pitch_cm", 10.0))
    M_bp_t = round_half_up(T1_bolt * bp_t_cant_L, 1)
    Z_bp_t = round_half_up((bp_t_pitch * (bp_t_cm**2)) / 6.0, 2)
    sigma_bp_t = round_half_up(M_bp_t / Z_bp_t, 1)
    bp_t_ok = sigma_bp_t <= fb_bp

    bp_c_cant_L = float(bp_cfg.get("compression_cantilever_cm", round_half_up((bp_h_cm - h_b) / 2.0, 1)))
    sigma2_c = sigma_conc
    sigma1_c = round_half_up(sigma2_c * ((bp_h_cm / 2.0 - bp_c_cant_L) / (bp_h_cm / 2.0)), 2)
    M_bp_c = round_half_up(
        0.5 * sigma1_c * (bp_c_cant_L**2) + (1.0 / 3.0) * (sigma2_c - sigma1_c) * (bp_c_cant_L**2),
        1,
    )
    Z_bp_c = round_half_up((1.0 * (bp_t_cm**2)) / 6.0, 2)
    sigma_bp_c = round_half_up(M_bp_c / Z_bp_c, 1)
    bp_c_ok = sigma_bp_c <= fb_bp

    base_plate_res = {
        "thickness_mm": bp_t_mm,
        "thickness_cm": bp_t_cm,
        "F_kg_cm2": bp_F_steel,
        "term_factor": bp_term_factor,
        "fb_kg_cm2": fb_bp,
        "fb_N_mm2": kg_cm2_to_N_mm2(fb_bp),
        "tension_side": {
            "T1_kg": T1_bolt,
            "L_cm": bp_t_cant_L,
            "bolt_pitch_cm": bp_t_pitch,
            "M_kg_cm": M_bp_t,
            "M_kN_mm": kg_cm_to_kN_mm(M_bp_t),
            "Z_cm3": Z_bp_t,
            "sigma_kg_cm2": sigma_bp_t,
            "sigma_N_mm2": kg_cm2_to_N_mm2(sigma_bp_t),
            "ok": bp_t_ok,
            "verdict": "ＯＫ" if bp_t_ok else "ＮＧ",
        },
        "compression_side": {
            "L_cm": bp_c_cant_L,
            "sigma2_kg_cm2": sigma2_c,
            "sigma1_kg_cm2": sigma1_c,
            "M_kg_cm": M_bp_c,
            "M_kN_mm": kg_cm_to_kN_mm(M_bp_c),
            "Z_cm3": Z_bp_c,
            "sigma_kg_cm2": sigma_bp_c,
            "sigma_N_mm2": kg_cm2_to_N_mm2(sigma_bp_c),
            "ok": bp_c_ok,
            "verdict": "ＯＫ" if bp_c_ok else "ＮＧ",
        },
        "ok": bp_t_ok and bp_c_ok,
    }

    return {
        "weld": weld_res,
        "anchor_bolt": anchor_res,
        "concrete": concrete_res,
        "base_plate": base_plate_res,
        "all_ok": weld_res["ok"] and anchor_res["ok"] and conc_ok and base_plate_res["ok"],
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

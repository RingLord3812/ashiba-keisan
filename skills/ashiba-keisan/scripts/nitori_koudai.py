"""モジュール5: 荷取り構台 強度計算エンジン (SUCCES Ver 4.11 準拠, PDF p.27-31)."""

from __future__ import annotations

from typing import Any

from .catalog import Catalog
from .units import (
    cm_to_mm,
    kg_cm2_to_N_mm2,
    kg_cm_to_kN_mm,
    kg_cm_to_N_mm,
    kg_m2_to_N_m2,
    kg_m_to_kN_mm,
    kg_m_to_N_m,
    kgf_to_N,
    round_half_up,
)


def calculate_nitori_koudai(
    params: dict[str, Any],
    catalog: Catalog,
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """荷取り構台強度計算 (床板・根太・大引・本設梁) を実行する."""
    options = options or {}
    strict_aij = bool(options.get("strict_aij", False))
    deflection_limit_div = options.get("deflection_limit")

    beam_span_m = float(params["permanent_beam_span_m"])
    girder_span_m = float(params["girder_span_m"])
    girder_spacing_m = float(params.get("girder_spacing_m", 1.800))
    joist_spacing_m = float(params.get("joist_spacing_m", 0.900))
    platform_area_m2 = float(params["platform_area_m2"])

    live_load_t = float(params.get("live_load_t", 5.00))
    live_load_kg = live_load_t * 1000.0
    impact_factor = float(params.get("impact_factor", 1.10))

    deck = catalog.get_material("planks", params.get("deck_plank", "足場板 28x240 (合板)"))
    joist = catalog.get_material("square_pipes", params.get("joist", "角パイプ 60x60 (STKR400)"))
    girder = catalog.get_material("h_beams", params.get("girder", "H形鋼 250x250x9x14 (SS400)"))
    perm_beam = catalog.get_material("h_beams", params.get("permanent_beam", "ビルトH 1200x800x15x12 (SS400)"))

    deck_self_kg_m2 = float(params.get("deck_self_weight_kg_m2", deck["unit_weight_kg_m2"]))
    joist_self_kg_m = float(joist["unit_weight_kg_m"])
    girder_self_kg_m = float(girder["unit_weight_kg_m"])
    beam_self_kg_m = float(perm_beam["unit_weight_kg_m"])

    # 3. 床板の検討 (単純支持等分布荷重, 1m幅当り)
    w_deck_m2_raw = (live_load_kg * impact_factor) / platform_area_m2 + deck_self_kg_m2
    w_deck_m2 = round_half_up(w_deck_m2_raw, 1)
    w_deck_cm = round_half_up(w_deck_m2 / 100.0, 2)
    L_deck_cm = joist_spacing_m * 100.0

    A_d = float(deck["A_cm2"])
    I_d = float(deck["I_cm4"])
    Z_d = float(deck["Z_cm3"])
    E_d = float(deck["E_kg_cm2"])
    kappa_d = float(deck["kappa"])
    fb_d = float(deck["fb_long_kg_cm2"])
    fs_d = float(deck["fs_long_kg_cm2"])

    M_d = round_half_up((w_deck_cm * (L_deck_cm**2)) / 8.0, 1)
    sigma_b_d = round_half_up(M_d / Z_d, 1)
    d_b_ok = sigma_b_d <= fb_d

    Q_d = round_half_up((w_deck_cm * L_deck_cm) / 2.0, 1)
    tau_d = round_half_up((kappa_d * Q_d) / A_d, 1)
    d_q_ok = tau_d <= fs_d

    delta_d = round_half_up((5.0 * (w_deck_m2_raw / 100.0) * (L_deck_cm**4)) / (384.0 * E_d * I_d), 3)
    d_defl_chk = _check_deflection(delta_d, L_deck_cm, deflection_limit_div)

    deck_res = {
        "member": deck["display_name"],
        "L_cm": L_deck_cm,
        "w_kg_m2": w_deck_m2,
        "w_kg_cm": w_deck_cm,
        "w_N_mm": kg_cm_to_N_mm(w_deck_cm),
        "section": {
            "A_cm2": A_d,
            "I_cm4": I_d,
            "Z_cm3": Z_d,
            "E_kg_cm2": E_d,
            "kappa": kappa_d,
            "fb_kg_cm2": fb_d,
            "fs_kg_cm2": fs_d,
        },
        "bending": {
            "M_kg_cm": M_d,
            "M_kN_mm": kg_cm_to_kN_mm(M_d),
            "sigma_b_kg_cm2": sigma_b_d,
            "sigma_b_N_mm2": kg_cm2_to_N_mm2(sigma_b_d),
            "fb_kg_cm2": fb_d,
            "fb_N_mm2": kg_cm2_to_N_mm2(fb_d),
            "ok": d_b_ok,
            "verdict": "ＯＫ" if d_b_ok else "ＮＧ",
        },
        "shear": {
            "Q_kg": Q_d,
            "Q_N": kgf_to_N(Q_d),
            "tau_kg_cm2": tau_d,
            "tau_N_mm2": kg_cm2_to_N_mm2(tau_d),
            "fs_kg_cm2": fs_d,
            "fs_N_mm2": kg_cm2_to_N_mm2(fs_d),
            "ok": d_q_ok,
            "verdict": "ＯＫ" if d_q_ok else "ＮＧ",
        },
        "deflection": {
            "delta_cm": delta_d,
            "delta_mm": cm_to_mm(delta_d),
            "summary_cm": round_half_up(delta_d, 2),
            "limit_check": d_defl_chk,
        },
    }

    # 4. 根太の検討 (単純支持等分布荷重, L = 大引間隔)
    # SUCCES標準では安全側に単位幅 1.0m 分担 (strict_aij では 根太間隔 joist_spacing_m を乗じる)
    joist_trib_w = float(params.get("joist_tributary_width_m", joist_spacing_m if strict_aij else 1.0))
    w_j_m = round_half_up(w_deck_m2 * joist_trib_w + joist_self_kg_m, 1)
    w_j_cm = round_half_up(w_j_m / 100.0, 2)
    L_j_cm = girder_spacing_m * 100.0

    A_j = float(joist["A_cm2"])
    I_j = float(joist["I_cm4"])
    Z_j = float(joist["Z_cm3"])
    E_j = float(joist["E_kg_cm2"])
    kappa_j = float(joist["kappa"])
    fb_j = float(joist["fb_long_kg_cm2"])
    fs_j = float(joist["fs_long_kg_cm2"])

    M_j = round_half_up((w_j_cm * (L_j_cm**2)) / 8.0, 1)
    sigma_b_j = round_half_up(M_j / Z_j, 1)
    j_b_ok = sigma_b_j <= fb_j

    Q_j = round_half_up((w_j_cm * L_j_cm) / 2.0, 1)
    tau_j = round_half_up((kappa_j * Q_j) / A_j, 1)
    j_q_ok = tau_j <= fs_j

    delta_j = round_half_up((5.0 * w_j_cm * (L_j_cm**4)) / (384.0 * E_j * I_j), 3)
    j_defl_chk = _check_deflection(delta_j, L_j_cm, deflection_limit_div)

    joist_res = {
        "member": joist["display_name"],
        "spacing_m": joist_spacing_m,
        "tributary_width_m": joist_trib_w,
        "L_cm": L_j_cm,
        "w_kg_m": w_j_m,
        "w_kg_cm": w_j_cm,
        "w_N_mm": kg_cm_to_N_mm(w_j_cm),
        "section": {
            "A_cm2": A_j,
            "I_cm4": I_j,
            "Z_cm3": Z_j,
            "E_kg_cm2": E_j,
            "kappa": kappa_j,
            "fb_kg_cm2": fb_j,
            "fs_kg_cm2": fs_j,
        },
        "bending": {
            "M_kg_cm": M_j,
            "M_kN_mm": kg_cm_to_kN_mm(M_j),
            "sigma_b_kg_cm2": sigma_b_j,
            "sigma_b_N_mm2": kg_cm2_to_N_mm2(sigma_b_j),
            "fb_kg_cm2": fb_j,
            "fb_N_mm2": kg_cm2_to_N_mm2(fb_j),
            "ok": j_b_ok,
            "verdict": "ＯＫ" if j_b_ok else "ＮＧ",
        },
        "shear": {
            "Q_kg": Q_j,
            "Q_N": kgf_to_N(Q_j),
            "tau_kg_cm2": tau_j,
            "tau_N_mm2": kg_cm2_to_N_mm2(tau_j),
            "fs_kg_cm2": fs_j,
            "fs_N_mm2": kg_cm2_to_N_mm2(fs_j),
            "ok": j_q_ok,
            "verdict": "ＯＫ" if j_q_ok else "ＮＧ",
        },
        "deflection": {
            "delta_cm": delta_j,
            "delta_mm": cm_to_mm(delta_j),
            "summary_cm": round_half_up(delta_j, 2),
            "limit_check": j_defl_chk,
        },
    }

    # 5. 大引の検討 (単純支持 + 部分等分布荷重 a)
    girder_loaded_a_m = float(params.get("girder_loaded_length_m", 4.500))
    joist_count_on_girder = int(params.get("joist_count_on_girder", int(round(girder_loaded_a_m / joist_spacing_m)) + 1))

    W1_g = girder_self_kg_m
    W2_g = round_half_up(
        w_deck_m2 * girder_spacing_m * girder_loaded_a_m + joist_self_kg_m * girder_spacing_m * joist_count_on_girder,
        1,
    )
    girder_res = _calc_partial_uniform_h_beam(
        member=girder,
        L_m=girder_span_m,
        a_m=girder_loaded_a_m,
        W1_kg_m=W1_g,
        W2_kg=W2_g,
        fb_override=params.get("girder_fb_kg_cm2"),
        deflection_limit_div=deflection_limit_div,
    )
    girder_res["spacing_m"] = girder_spacing_m
    girder_res["joist_count_on_girder"] = joist_count_on_girder

    # 6. 本設梁の検討 (単純支持 + 部分等分布荷重 a)
    beam_loaded_a_m = float(params.get("beam_loaded_length_m", 3.600))
    num_girders_on_beam = int(params.get("num_girders_on_beam", int(round(beam_loaded_a_m / girder_spacing_m)) + 1))

    W1_b = beam_self_kg_m
    W2_b = round_half_up(girder_res["shear"]["Q_kg"] * num_girders_on_beam, 1)
    beam_res = _calc_partial_uniform_h_beam(
        member=perm_beam,
        L_m=beam_span_m,
        a_m=beam_loaded_a_m,
        W1_kg_m=W1_b,
        W2_kg=W2_b,
        fb_override=params.get("permanent_beam_fb_kg_cm2"),
        deflection_limit_div=deflection_limit_div,
    )
    beam_res["num_girders_on_beam"] = num_girders_on_beam
    beam_res["girder_max_Q_kg"] = girder_res["shear"]["Q_kg"]

    summary_rows = [
        {
            "section": "荷取り構台",
            "part": "床板",
            "member": deck["display_name"],
            "verdict": None,
            "ratio": None,
            "bending": deck_res["bending"]["verdict"],
            "shear": deck_res["shear"]["verdict"],
            "deflection_cm": deck_res["deflection"]["summary_cm"],
            "deflection_verdict": d_defl_chk["verdict"] if d_defl_chk else None,
        },
        {
            "section": "荷取り構台",
            "part": "根太",
            "member": joist["display_name"],
            "verdict": None,
            "ratio": None,
            "bending": joist_res["bending"]["verdict"],
            "shear": joist_res["shear"]["verdict"],
            "deflection_cm": joist_res["deflection"]["summary_cm"],
            "deflection_verdict": j_defl_chk["verdict"] if j_defl_chk else None,
        },
        {
            "section": "荷取り構台",
            "part": "大引",
            "member": girder["display_name"],
            "verdict": None,
            "ratio": None,
            "bending": girder_res["bending"]["verdict"],
            "shear": girder_res["shear"]["verdict"],
            "deflection_cm": girder_res["deflection"]["summary_cm"],
            "deflection_verdict": (
                girder_res["deflection"]["limit_check"]["verdict"]
                if girder_res["deflection"]["limit_check"]
                else None
            ),
        },
        {
            "section": "荷取り構台",
            "part": "本設梁",
            "member": perm_beam["display_name"],
            "verdict": None,
            "ratio": None,
            "bending": beam_res["bending"]["verdict"],
            "shear": beam_res["shear"]["verdict"],
            "deflection_cm": beam_res["deflection"]["summary_cm"],
            "deflection_verdict": (
                beam_res["deflection"]["limit_check"]["verdict"]
                if beam_res["deflection"]["limit_check"]
                else None
            ),
        },
    ]

    defl_checks = [
        d_defl_chk,
        j_defl_chk,
        girder_res["deflection"]["limit_check"],
        beam_res["deflection"]["limit_check"],
    ]
    all_ok = (
        d_b_ok
        and d_q_ok
        and j_b_ok
        and j_q_ok
        and girder_res["bending"]["ok"]
        and girder_res["shear"]["ok"]
        and beam_res["bending"]["ok"]
        and beam_res["shear"]["ok"]
        and all((dc["ok"] if dc else True) for dc in defl_checks)
    )

    return {
        "module": "nitori_koudai",
        "title": "荷取り構台 強度計算書",
        "overview": {
            "permanent_beam_span_m": beam_span_m,
            "girder_span_m": girder_span_m,
            "girder_spacing_m": girder_spacing_m,
            "joist_spacing_m": joist_spacing_m,
            "platform_area_m2": platform_area_m2,
            "live_load_t": live_load_t,
            "live_load_kN": round_half_up(live_load_t * 9.81, 1),
            "impact_factor": impact_factor,
            "deck_self_kg_m2": deck_self_kg_m2,
            "deck_self_N_m2": kg_m2_to_N_m2(deck_self_kg_m2),
            "joist_self_kg_m": joist_self_kg_m,
            "joist_self_N_m": kg_m_to_N_m(joist_self_kg_m),
            "girder_self_kg_m": girder_self_kg_m,
            "girder_self_N_m": kg_m_to_N_m(girder_self_kg_m),
            "beam_self_kg_m": beam_self_kg_m,
            "beam_self_N_m": kg_m_to_N_m(beam_self_kg_m),
        },
        "deck": deck_res,
        "joist": joist_res,
        "girder": girder_res,
        "permanent_beam": beam_res,
        "summary_rows": summary_rows,
        "all_ok": all_ok,
    }


def _calc_partial_uniform_h_beam(
    member: dict[str, Any],
    L_m: float,
    a_m: float,
    W1_kg_m: float,
    W2_kg: float,
    fb_override: float | None = None,
    deflection_limit_div: int | None = None,
) -> dict[str, Any]:
    """H形鋼の単純支持 + 部分等分布荷重 (載荷範囲 a) 検討."""
    I = float(member["I_cm4"])
    Z = float(member["Z_cm3"])
    E = float(member["E_kg_cm2"])
    h_cm = float(member["h_cm"])
    tw_cm = float(member["tw_cm"])
    fb = float(fb_override) if fb_override is not None else float(member["fb_long_kg_cm2"])
    fs = float(member["fs_long_kg_cm2"])

    w2_dist_kg_m = round_half_up(W2_kg / a_m, 1) if a_m > 0 else 0.0

    # (1) 曲げモーメント (中央対称載荷で最大)
    M1_kg_m = round_half_up((W1_kg_m * (L_m**2)) / 8.0, 1)
    M2_kg_m = round_half_up((W2_kg * (2.0 * L_m - a_m)) / 8.0, 1)
    M_kg_m = round_half_up(M1_kg_m + M2_kg_m, 1)
    sigma_b = round_half_up((M_kg_m * 100.0) / Z, 1)
    b_ok = sigma_b <= fb

    # (2) せん断力 (片側支点寄せ載荷で最大)
    Q1_kg = round_half_up((W1_kg_m * L_m) / 2.0, 1)
    Q2_kg = round_half_up((W2_kg * (L_m - a_m / 2.0)) / L_m, 1)
    Q_kg = round_half_up(Q1_kg + Q2_kg, 1)
    tau = round_half_up(Q_kg / (tw_cm * h_cm), 1)
    q_ok = tau <= fs

    # (3) たわみ (全スパン等分布荷重換算; 内部計算は未丸め値を使用)
    L_cm = L_m * 100.0
    w1_cm_raw = W1_kg_m / 100.0
    w2_cm_raw = W2_kg / L_cm
    w1_cm = round_half_up(w1_cm_raw, 2)
    w2_cm = round_half_up(w2_cm_raw, 2)
    delta_raw = (5.0 * (w1_cm_raw + w2_cm_raw) * (L_cm**4)) / (384.0 * E * I)
    delta_cm = round_half_up(delta_raw, 3)
    defl_chk = _check_deflection(delta_cm, L_cm, deflection_limit_div)

    summary_defl = round_half_up(delta_raw, 2)

    return {
        "member": member["display_name"],
        "L_m": L_m,
        "L_cm": L_cm,
        "a_m": a_m,
        "W1_kg_m": W1_kg_m,
        "W1_N_m": kg_m_to_N_m(W1_kg_m),
        "W2_kg": W2_kg,
        "W2_N": kgf_to_N(W2_kg),
        "w2_dist_kg_m": w2_dist_kg_m,
        "section": {
            "I_cm4": I,
            "Z_cm3": Z,
            "E_kg_cm2": E,
            "h_cm": h_cm,
            "tw_cm": tw_cm,
            "fb_kg_cm2": fb,
            "fs_kg_cm2": fs,
        },
        "bending": {
            "M1_kg_m": M1_kg_m,
            "M2_kg_m": M2_kg_m,
            "M_kg_m": M_kg_m,
            "M_kN_mm": kg_m_to_kN_mm(M_kg_m),
            "sigma_b_kg_cm2": sigma_b,
            "sigma_b_N_mm2": kg_cm2_to_N_mm2(sigma_b),
            "fb_kg_cm2": fb,
            "fb_N_mm2": kg_cm2_to_N_mm2(fb),
            "ok": b_ok,
            "verdict": "ＯＫ" if b_ok else "ＮＧ",
        },
        "shear": {
            "Q1_kg": Q1_kg,
            "Q2_kg": Q2_kg,
            "Q_kg": Q_kg,
            "Q_N": kgf_to_N(Q_kg),
            "tau_kg_cm2": tau,
            "tau_N_mm2": kg_cm2_to_N_mm2(tau),
            "fs_kg_cm2": fs,
            "fs_N_mm2": kg_cm2_to_N_mm2(fs),
            "ok": q_ok,
            "verdict": "ＯＫ" if q_ok else "ＮＧ",
        },
        "deflection": {
            "w1_kg_cm": w1_cm,
            "w1_N_mm": kg_cm_to_N_mm(w1_cm),
            "w2_kg_cm": w2_cm,
            "w2_N_mm": kg_cm_to_N_mm(w2_cm),
            "delta_cm": delta_cm,
            "delta_mm": cm_to_mm(delta_cm),
            "summary_cm": summary_defl,
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

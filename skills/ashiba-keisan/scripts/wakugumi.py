"""モジュール1: 枠組足場 強度計算エンジン (SUCCES Ver 4.11 準拠, PDF p.3-6)."""

from __future__ import annotations

from typing import Any

from .catalog import Catalog
from .units import kgf_to_N, round_half_up
from .wind import calculate_wall_tie_wind


def calculate_wakugumi(
    params: dict[str, Any],
    catalog: Catalog,
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """枠組足場強度計算 (壁つなぎ・建枠・梁枠開口部・ジャッキベース) を実行する."""
    options = options or {}

    building_h = float(params["building_height_m"])
    scaffold_h = float(params["scaffold_height_m"])
    bottom_tier_h = float(params.get("bottom_tier_height_m", 2.000))
    tiers = int(params["tiers"])
    bay_span = float(params.get("bay_span_m", 1.800))

    frame = catalog.get_material("frames", params.get("frame", "TC-917"))
    ledger = catalog.get_material("ledgers", params.get("ledger", "SYi-518"))
    brace = catalog.get_material("braces", params.get("brace", "SXB-1618"))
    pin = catalog.get_material("frame_accessories", params.get("joint_pin", "Mジョイント"))
    armlock = catalog.get_material("frame_accessories", params.get("arm_lock", "ALB8"))
    stair = catalog.get_material("frame_accessories", params.get("stair", "KS-1718"))

    frame_h = float(params.get("frame_height_m", frame["height_m"]))
    frame_w = float(params.get("frame_width_m", frame["width_m"]))
    stair_tiers = int(params.get("stair_tiers", 3))
    sheet_name = params.get("sheet_name", "メッシュシート")
    sheet_unit_w = float(params.get("sheet_unit_weight_kg_m2", 0.460))

    # 壁つなぎ配置条件
    tie_cfg = params.get("wall_tie", {})
    tie_h_spans = int(tie_cfg.get("horizontal_spans", 2))
    tie_v_tiers = int(tie_cfg.get("vertical_tiers", 2))
    tie_v_start = int(tie_cfg.get("vertical_start_tier", 2))
    tie_h_m = float(tie_cfg.get("tie_horizontal_m", bay_span * tie_h_spans))
    tie_v_m = float(tie_cfg.get("tie_vertical_m", frame_h * tie_v_tiers))

    wind_in = dict(tie_cfg)
    wind_in.setdefault("scaffold_height_m", float(tie_cfg.get("wind_scaffold_height_m", scaffold_h)))
    wind_in.setdefault("scaffold_length_m", float(tie_cfg.get("scaffold_length_m", 25.0)))
    wind_in.setdefault("tie_horizontal_m", tie_h_m)
    wind_in.setdefault("tie_vertical_m", tie_v_m)
    wind_in.setdefault("tie_horizontal_desc", f"{tie_h_spans}スパンごとに配置")
    wind_in.setdefault("tie_vertical_desc", f"{tie_v_tiers}段ごとに配置")
    wall_tie_res = calculate_wall_tie_wind(wind_in, catalog, scaffold_planes=2)

    # 3. 建枠の検討
    allow_frame = float(params.get("frame_allowable_kg", frame["allowable_compression_kg"]))
    ledger_tiers = int(params.get("ledger_tiers", max(tiers - 1, 0)))
    joint_tiers = int(params.get("joint_tiers", max(tiers - 1, 0)))

    dead_items = [
        {
            "label": "建枠",
            "spec": frame["display_name"],
            "unit_weight": float(frame["weight_kg"]),
            "unit_label": "kg",
            "expr": f"{frame['weight_kg']:.3f} kg × {tiers}段 × 1本",
            "weight_kg": round_half_up(frame["weight_kg"] * tiers * 1, 1),
        },
        {
            "label": "布枠",
            "spec": ledger["display_name"],
            "unit_weight": float(ledger["weight_kg"]),
            "unit_label": "kg",
            "expr": f"{ledger['weight_kg']:.3f} kg × {ledger_tiers}段 × 1本",
            "weight_kg": round_half_up(ledger["weight_kg"] * ledger_tiers * 1, 1),
        },
        {
            "label": "筋かい",
            "spec": brace["display_name"],
            "unit_weight": float(brace["weight_kg"]),
            "unit_label": "kg",
            "expr": f"{brace['weight_kg']:.3f} kg × {tiers}段 × 2本",
            "weight_kg": round_half_up(brace["weight_kg"] * tiers * 2, 1),
        },
        {
            "label": "連結ピン",
            "spec": pin["display_name"],
            "unit_weight": float(pin["weight_kg"]),
            "unit_label": "kg",
            "expr": f"{pin['weight_kg']:.3f} kg × {joint_tiers}段 × 2本",
            "weight_kg": round_half_up(pin["weight_kg"] * joint_tiers * 2, 1),
        },
        {
            "label": "アームロック",
            "spec": armlock["display_name"],
            "unit_weight": float(armlock["weight_kg"]),
            "unit_label": "kg",
            "expr": f"{armlock['weight_kg']:.3f} kg × {joint_tiers}段 × 2本",
            "weight_kg": round_half_up(armlock["weight_kg"] * joint_tiers * 2, 1),
        },
        {
            "label": "階段",
            "spec": stair["display_name"],
            "unit_weight": float(stair["weight_kg"]),
            "unit_label": "kg",
            "expr": f"{stair['weight_kg']:.3f} kg × {stair_tiers}段 × 1本",
            "weight_kg": round_half_up(stair["weight_kg"] * stair_tiers * 1, 1),
        },
        {
            "label": "養生",
            "spec": sheet_name,
            "unit_weight": sheet_unit_w,
            "unit_label": "kg/㎡",
            "expr": f"{sheet_unit_w:.3f} kg/㎡ × {bay_span:.3f}ｍ × {scaffold_h:.3f}ｍ",
            "weight_kg": round_half_up(sheet_unit_w * bay_span * scaffold_h, 1),
        },
    ]

    dead_total = round_half_up(sum(it["weight_kg"] for it in dead_items), 1)
    live_per_layer = float(params.get("live_load_per_layer_kg", 400.0))
    live_layers = int(params.get("live_load_layers", 2))
    live_total = round_half_up(live_per_layer * live_layers, 1)

    frame_load_W = round_half_up(dead_total + live_total, 1)
    frame_ratio = round_half_up(frame_load_W / allow_frame, 2)
    frame_ok = frame_load_W <= allow_frame

    standard_frame_res = {
        "tiers": tiers,
        "allowable_f_kg": allow_frame,
        "allowable_f_N": kgf_to_N(allow_frame),
        "dead_items": dead_items,
        "dead_total_kg": dead_total,
        "dead_total_N": kgf_to_N(dead_total),
        "live_per_layer_kg": live_per_layer,
        "live_layers": live_layers,
        "live_total_kg": live_total,
        "live_total_N": kgf_to_N(live_total),
        "total_W_kg": frame_load_W,
        "total_W_N": kgf_to_N(frame_load_W),
        "ratio": frame_ratio,
        "ok": frame_ok,
        "verdict": "ＯＫ" if frame_ok else "ＮＧ",
    }

    # 4. 梁枠を支える建枠の検討 (開口部ありの場合)
    opening_cfg = params.get("opening")
    opening_res: dict[str, Any] | None = None
    governing_frame_load = frame_load_W

    if opening_cfg:
        beam_mat = catalog.get_material("beam_frames", opening_cfg.get("beam_frame", "SPL-54"))
        open_spans = int(opening_cfg.get("open_spans", beam_mat.get("open_spans", 3)))
        open_span_m = float(opening_cfg.get("open_span_m", round_half_up(open_spans * bay_span, 3)))
        beam_tier = int(opening_cfg.get("install_tier", 3))
        beam_height_m = float(
            opening_cfg.get(
                "install_height_m",
                round_half_up(bottom_tier_h + (beam_tier - 1) * frame_h, 3),
            )
        )
        tiers_above = int(opening_cfg.get("tiers_above", tiers - beam_tier))
        beam_live_kg = float(opening_cfg.get("live_load_kg", beam_mat.get("allowable_load_kg", 1000.0)))

        # 梁枠上のシート高さ: SUCCES では 足場高さ - 設置段数 * 建枠高さ (例: 32.60 - 3*1.70 = 27.50m)
        sheet_h_above = float(
            opening_cfg.get("sheet_height_above_m", round_half_up(scaffold_h - beam_tier * frame_h, 2))
        )
        mid_cols = max(open_spans - 1, 1)
        half_spans = open_spans / 2.0
        ledgers_above = max(tiers_above - 1, 0)
        joints_above = max(tiers_above - 1, 0)

        w1_items = [
            {
                "label": "建枠",
                "spec": frame["display_name"],
                "expr": f"{frame['weight_kg']:.3f} kg × {tiers_above}段 × 1本 × {mid_cols}列／2",
                "weight_kg": round_half_up(frame["weight_kg"] * tiers_above * 1 * mid_cols / 2.0, 1),
            },
            {
                "label": "布枠",
                "spec": ledger["display_name"],
                "expr": f"{ledger['weight_kg']:.3f} kg × {ledgers_above}段 × 1本 × {half_spans:g}スパン",
                "weight_kg": round_half_up(ledger["weight_kg"] * ledgers_above * 1 * half_spans, 1),
            },
            {
                "label": "筋かい",
                "spec": brace["display_name"],
                "expr": f"{brace['weight_kg']:.3f} kg × {tiers_above}段 × 2本 × {half_spans:g}スパン",
                "weight_kg": round_half_up(brace["weight_kg"] * tiers_above * 2 * half_spans, 1),
            },
            {
                "label": "連結ピン",
                "spec": pin["display_name"],
                "expr": f"{pin['weight_kg']:.3f} kg × {joints_above}段 × 2本 × {mid_cols}列／2",
                "weight_kg": round_half_up(pin["weight_kg"] * joints_above * 2 * mid_cols / 2.0, 1),
            },
            {
                "label": "アームロック",
                "spec": armlock["display_name"],
                "expr": f"{armlock['weight_kg']:.3f} kg × {joints_above}段 × 2本 × {mid_cols}列／2",
                "weight_kg": round_half_up(armlock["weight_kg"] * joints_above * 2 * mid_cols / 2.0, 1),
            },
            {
                "label": "階段",
                "spec": stair["display_name"],
                "expr": f"{stair['weight_kg']:.3f} kg × {stair_tiers}本 × {half_spans:g}スパン",
                "weight_kg": round_half_up(stair["weight_kg"] * stair_tiers * half_spans, 1),
            },
            {
                "label": "養生",
                "spec": sheet_name,
                "expr": f"{sheet_unit_w:.3f} kg/㎡ × {bay_span:.2f}ｍ × {sheet_h_above:.2f}ｍ × {half_spans:g}スパン",
                "weight_kg": round_half_up(sheet_unit_w * bay_span * sheet_h_above * half_spans, 1),
            },
        ]
        w1_dead = round_half_up(sum(it["weight_kg"] for it in w1_items), 1)
        w1_live = round_half_up(beam_live_kg / 2.0, 1)
        w1_total = round_half_up(w1_dead + w1_live, 1)

        # (3) 梁枠を支える建枠自身の荷重 (片側1/2スパン分担)
        w2_items = [
            {
                "label": "建枠",
                "spec": frame["display_name"],
                "expr": f"{frame['weight_kg']:.3f} kg × {tiers}段 × 1本",
                "weight_kg": round_half_up(frame["weight_kg"] * tiers * 1, 1),
            },
            {
                "label": "布枠",
                "spec": ledger["display_name"],
                "expr": f"{ledger['weight_kg']:.3f} kg × {ledger_tiers}段 × 1本／2",
                "weight_kg": round_half_up(ledger["weight_kg"] * ledger_tiers * 1 / 2.0, 1),
            },
            {
                "label": "筋かい",
                "spec": brace["display_name"],
                "expr": f"{brace['weight_kg']:.3f} kg × {tiers}段 × 2本／2",
                "weight_kg": round_half_up(brace["weight_kg"] * tiers * 2 / 2.0, 1),
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
                "expr": f"{armlock['weight_kg']:.3f} kg × {joint_tiers}段 × 2本",
                "weight_kg": round_half_up(armlock["weight_kg"] * joint_tiers * 2, 1),
            },
            {
                "label": "階段",
                "spec": stair["display_name"],
                "expr": f"{stair['weight_kg']:.3f} kg × {stair_tiers}段 × 1本／2",
                "weight_kg": round_half_up(stair["weight_kg"] * stair_tiers * 1 / 2.0, 1),
            },
            {
                "label": "養生",
                "spec": sheet_name,
                "expr": f"{sheet_unit_w:.3f} kg/㎡ × {bay_span:.3f}ｍ × {scaffold_h:.3f}ｍ／2",
                "weight_kg": round_half_up(sheet_unit_w * bay_span * scaffold_h / 2.0, 1),
            },
        ]
        w2_dead = round_half_up(sum(it["weight_kg"] for it in w2_items), 1)
        w2_live = round_half_up(live_total / 2.0, 1)
        w2_total = round_half_up(w2_dead + w2_live, 1)

        total_support = round_half_up(w1_total + w2_total, 1)
        sup_ratio = round_half_up(total_support / allow_frame, 2)
        sup_ok = total_support <= allow_frame
        governing_frame_load = max(governing_frame_load, total_support)

        opening_res = {
            "beam_frame_name": beam_mat["display_name"],
            "open_spans": open_spans,
            "open_span_m": open_span_m,
            "install_tier": beam_tier,
            "install_height_m": beam_height_m,
            "beam_live_load_kg": beam_live_kg,
            "tiers_above": tiers_above,
            "sheet_height_above_m": sheet_h_above,
            "w1_items": w1_items,
            "w1_dead_kg": w1_dead,
            "w1_live_kg": w1_live,
            "w1_total_kg": w1_total,
            "w1_total_N": kgf_to_N(w1_total),
            "w2_items": w2_items,
            "w2_dead_kg": w2_dead,
            "w2_live_kg": w2_live,
            "w2_total_kg": w2_total,
            "w2_total_N": kgf_to_N(w2_total),
            "total_W_kg": total_support,
            "total_W_N": kgf_to_N(total_support),
            "allowable_f_kg": allow_frame,
            "allowable_f_N": kgf_to_N(allow_frame),
            "ratio": sup_ratio,
            "ok": sup_ok,
            "verdict": "ＯＫ" if sup_ok else "ＮＧ",
        }

    # 5. ジャッキベースの検討
    jb_cfg = params.get("jack_base", {})
    jb_spec = jb_cfg.get("material", "BB-35")
    jb_ext_mm = float(jb_cfg.get("extension_mm", 100.0))
    jb_allow_auto, jb_mat = catalog.get_jack_base_allowable(jb_spec, jb_ext_mm)
    jb_allow = float(jb_cfg.get("allowable_kg", jb_allow_auto))
    jb_load_N = round_half_up(governing_frame_load / 2.0, 1)
    jb_ratio = round_half_up(jb_load_N / jb_allow, 2)
    jb_ok = jb_load_N <= jb_allow

    jack_base_res = {
        "material": jb_mat.get("display_name", str(jb_spec)),
        "extension_mm": jb_ext_mm,
        "allowable_f_kg": jb_allow,
        "allowable_f_N": kgf_to_N(jb_allow),
        "governing_frame_load_kg": governing_frame_load,
        "load_per_jack_kg": jb_load_N,
        "load_per_jack_N": kgf_to_N(jb_load_N),
        "ratio": jb_ratio,
        "ok": jb_ok,
        "verdict": "ＯＫ" if jb_ok else "ＮＧ",
    }

    # 検討結果概要テーブル用サマリー行
    summary_rows = [
        {
            "section": "枠組足場",
            "part": "壁つなぎ",
            "member": wall_tie_res["conditions"]["wall_tie_material"],
            "verdict": wall_tie_res["verification"]["verdict"],
            "ratio": wall_tie_res["verification"]["ratio"],
            "bending": None,
            "shear": None,
            "deflection_cm": None,
        },
        {
            "section": "枠組足場",
            "part": "建枠",
            "member": frame["display_name"],
            "verdict": standard_frame_res["verdict"],
            "ratio": standard_frame_res["ratio"],
            "bending": None,
            "shear": None,
            "deflection_cm": None,
        },
    ]
    if opening_res:
        summary_rows.append(
            {
                "section": "枠組足場",
                "part": "梁枠",
                "member": opening_res["beam_frame_name"],
                "verdict": opening_res["verdict"],
                "ratio": opening_res["ratio"],
                "bending": None,
                "shear": None,
                "deflection_cm": None,
            }
        )

    all_ok = (
        wall_tie_res["verification"]["ok"]
        and standard_frame_res["ok"]
        and (opening_res["ok"] if opening_res else True)
        and jack_base_res["ok"]
    )

    return {
        "module": "wakugumi",
        "title": "枠組足場 強度計算書",
        "overview": {
            "building_height_m": building_h,
            "scaffold_height_m": scaffold_h,
            "bottom_tier_height_m": bottom_tier_h,
            "tiers": tiers,
            "bay_span_m": bay_span,
            "frame_height_m": frame_h,
            "frame_width_m": frame_w,
            "design_wind_v0_ms": wall_tie_res["velocity_pressure"]["V0_ms"],
            "tie_horizontal_spans": tie_h_spans,
            "tie_vertical_start_tier": tie_v_start,
            "tie_vertical_tiers": tie_v_tiers,
        },
        "wall_tie": wall_tie_res,
        "standard_frame": standard_frame_res,
        "opening": opening_res,
        "jack_base": jack_base_res,
        "summary_rows": summary_rows,
        "all_ok": all_ok,
    }

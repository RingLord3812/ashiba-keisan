"""足場計算書ジェネレーター (SUCCES Ver 4.11 準拠 Markdown / A4印刷対応HTML+SVG)."""

from __future__ import annotations

import html
from typing import Any

from .svg_diagrams import (
    svg_cantilever_bracket,
    svg_girder_multipoint_and_moment,
    svg_nitori_plan,
    svg_opening_load_diagram,
    svg_partial_uniform_beam,
    svg_simple_beam,
    svg_tankan_bracket_detail,
    svg_tsuri_cantilever,
    svg_tsuri_girder_2pt,
    svg_tsuri_plan,
    svg_wakugumi_elevation,
    svg_weld_detail,
)
from .units import fmt_N, fmt_N_m, fmt_N_m2, fmt_N_mm, fmt_N_mm2, fmt_kN_mm, fmt_sig


def _v_badge(verdict: str | None) -> str:
    if not verdict:
        return ""
    if "ＮＧ" in verdict or "NG" in verdict or "警告" in verdict:
        return f'<span class="ng">{html.escape(verdict)}</span>'
    return f'<span class="ok">{html.escape(verdict)}</span>'


def _defl_badge(defl: dict[str, Any]) -> str:
    chk = defl.get("limit_check")
    if not chk:
        return ""
    cls = "ok-tag" if chk["ok"] else "ng-tag"
    return (
        f' <span class="{cls}">[{chk["criterion"]} 許容 {chk["allowable_cm"]:.3f}cm ({chk["allowable_mm"]:.2f}mm) '
        f'実測 {chk["actual_ratio"]} → {chk["verdict"]}]</span>'
    )


def _defl_md(defl: dict[str, Any]) -> str:
    chk = defl.get("limit_check")
    if not chk:
        return ""
    return f"  `[{chk['criterion']} 許容 {chk['allowable_cm']:.3f}cm ({chk['allowable_mm']:.2f}mm) / 実測 {chk['actual_ratio']} → {chk['verdict']}]`"


def render_markdown(report: dict[str, Any]) -> str:
    """構造計算結果辞書から日本語の足場計算書 (Markdown) を生成する."""
    meta = report["project"]
    modules = report["modules"]
    out: list[str] = []

    out.append(f"# 足場計算書 — {meta.get('name', '仮設足場工事')}")
    out.append("")
    out.append(f"- **現場名**: {meta.get('name', '')}")
    if meta.get("locations"):
        out.append("- **検討場所**:")
        for loc in meta["locations"]:
            out.append(f"  - {loc}")
    out.append(f"- **作成・施工**: {meta.get('company', '')}")
    out.append(f"- **計算モード**: {'厳密AIJモード (--strict-aij)' if report['options'].get('strict_aij') else 'SUCCES Ver 4.11 準拠モード'}")
    if report["options"].get("deflection_limit"):
        out.append(f"- **たわみ制限照査**: L/{report['options']['deflection_limit']}")
    out.append(f"- **総合判定**: **{'ＯＫ（全項目適合）' if report['all_ok'] else 'ＮＧ（要再検討項目あり）'}**")
    out.append("")

    # 検討結果概要テーブル
    out.append("## 検討結果概要")
    out.append("")
    out.append("| 種別 | 部位 | 使用部材 | 判定 | 計算値／許容値 | 曲げ(M) | せん断(Q) | たわみ(δ cm) |")
    out.append("| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |")
    for row in report["summary_rows"]:
        ratio_s = f"{row['ratio']:.2f}" if row["ratio"] is not None else ""
        if row["deflection_cm"] is not None:
            dv = row.get("deflection_verdict")
            defl_s = f"{row['deflection_cm']:.2f} ({dv})" if dv else f"{row['deflection_cm']:.2f}"
        else:
            defl_s = ""
        out.append(
            f"| {row['section']} | {row['part']} | {row['member']} | {row['verdict'] or ''} | "
            f"{ratio_s} | {row['bending'] or ''} | {row['shear'] or ''} | {defl_s} |"
        )
    out.append("")

    for mod in modules:
        mtype = mod["module"]
        out.append("---")
        out.append(f"## {mod['title']}")
        out.append("")
        if mtype == "wakugumi":
            out.extend(_md_wakugumi(mod))
        elif mtype == "tankan_issoku":
            out.extend(_md_tankan_issoku(mod))
        elif mtype == "bracket_support":
            out.extend(_md_bracket_support(mod))
        elif mtype == "tsuri_ashiba":
            out.extend(_md_tsuri_ashiba(mod))
        elif mtype == "nitori_koudai":
            out.extend(_md_nitori_koudai(mod))
        out.append("")

    return "\n".join(out)


def _md_wind_section(wt: dict[str, Any], title: str = "### ２．壁つなぎの検討") -> list[str]:
    c = wt["conditions"]
    vp = wt["velocity_pressure"]
    wf = wt["wind_force_coeff"]
    v = wt["verification"]
    lines = [
        title,
        "",
        "#### (1) 設計条件",
        f"- 場所：{c['location']} ／ 地表面粗度区分：{c['terrain']} ／ 近接高層建築物：{c['nearby_highrise']}",
        f"- 足場の高さ：{c['scaffold_height_m']:.3f} m ／ 足場の長さ：{c['scaffold_length_m']:.3f} m",
        f"- 壁つなぎ設置間隔：縦 {c['tie_vertical_desc']}、横 {c['tie_horizontal_desc']}",
        f"- 落下物防護材：{c['sheet_description']} ／ 壁つなぎ材料：{c['wall_tie_material']}",
        "",
        "#### (2) 設計用速度圧",
        f"- $V_0 = {vp['V0_ms']:g}$ m/s, $K_e = {vp['Ke']:.2f}$, $S = {vp['S']:.2f}$ (Z={vp['Z_band_m']}m, {c['terrain']}), $E_B = {vp['EB']:.2f}$",
        f"- $V_z = V_0 \\times K_e \\times S \\times E_B = {vp['V0_ms']:g} \\times {vp['Ke']:.2f} \\times {vp['S']:.2f} \\times {vp['EB']:.2f} = {vp['Vz_ms']:.1f}$ m/s",
        f"- $q_z = \\frac{{1}}{{16}} V_z^2 = \\frac{{1}}{{16}} \\times {vp['Vz_ms']:.1f}^2 = {vp['qz_kgf_m2']:.1f}$ kgf/㎡ ({fmt_N_m2(vp['qz_kgf_m2'])})",
        "",
        "#### (3) 風力係数",
        f"- 充実率 $\\phi = {wf['phi']:.2f}$" + (f", 第2構面風力低減係数 $\\gamma = 1 - \\phi = {wf['gamma']:.2f}$" if wf["gamma"] is not None else " (単管一側：1構面)"),
        f"- 基本風力係数 $C_0 = {wf['C0']:.2f}$, 形状補正係数 $R = {wf['R']:.2f}$, 設置位置補正係数 $F = {wf['F']:.2f}$ (位置 {wf['position']}, {wf['F_formula']})",
        f"- $C = {wf['C_formula']} = {wf['C']:.2f}$",
        "",
        "#### (4) 壁つなぎの検討",
        f"- 作用面積 $A = {v['tie_horizontal_m']:.3f} \\times {v['tie_vertical_m']:.3f} = {v['area_A_m2']:.2f}$ ㎡",
        f"- 許容耐力 $F = {v['base_allowable_kgf']:.0f} \\times {v['wind_increase_factor']:.1f} = {v['allowable_F_kgf']:.0f}$ kgf ({fmt_N(v['allowable_F_kgf'])})",
        f"- 作用荷重 $R = q_z \\cdot C \\cdot A = {vp['qz_kgf_m2']:.1f} \\times {wf['C']:.2f} \\times {v['area_A_m2']:.2f} = {v['load_R_kgf']:.1f}$ kgf ({fmt_N(v['load_R_kgf'])}) {'＜' if v['ok'] else '＞'} $F = {v['allowable_F_kgf']:.0f}$ kgf → **{v['verdict']}** (検定比 {v['ratio']:.2f})",
        "",
    ]
    return lines


def _md_wakugumi(m: dict[str, Any]) -> list[str]:
    ov = m["overview"]
    sf = m["standard_frame"]
    jb = m["jack_base"]
    lines = [
        "### １．設計条件",
        f"- 建物高さ：{ov['building_height_m']:.3f} m ／ 足場高さ：{ov['scaffold_height_m']:.3f} m ／ 最下段高さ：{ov['bottom_tier_height_m']:.3f} m ／ 段数：{ov['tiers']} 段",
        f"- 建枠設置間隔：{ov['bay_span_m']:.3f} m ／ 建枠高さ：{ov['frame_height_m']:.3f} m ／ 建枠巾：{ov['frame_width_m']:.3f} m",
        "",
    ]
    lines.extend(_md_wind_section(m["wall_tie"]))
    lines.extend(
        [
            "### ３．建枠の検討",
            f"- 建枠段数：{sf['tiers']} 段 ／ 建枠許容圧縮力 $f = {sf['allowable_f_kg']:.0f}$ kg/枠 ({fmt_N(sf['allowable_f_kg'])})",
            "",
            "| 部材 | 規格 | 計算式 | 質量 (kg) |",
            "| :--- | :--- | :--- | ---: |",
        ]
    )
    for it in sf["dead_items"]:
        lines.append(f"| {it['label']} | {it['spec']} | {it['expr']} | {it['weight_kg']:.1f} |")
    lines.extend(
        [
            f"| **固定荷重 合計** | | | **{sf['dead_total_kg']:.1f}** ({fmt_N(sf['dead_total_kg'])}) |",
            "",
            f"- 積載荷重 = {sf['live_per_layer_kg']:.0f} kg × {sf['live_layers']} 層 = **{sf['live_total_kg']:.0f} kg** ({fmt_N(sf['live_total_kg'])})",
            f"- 最下段建枠作用荷重 $W = {sf['dead_total_kg']:.1f} + {sf['live_total_kg']:.0f} = {sf['total_W_kg']:.1f}$ kg ({fmt_N(sf['total_W_kg'])}) {'＜' if sf['ok'] else '＞'} $f = {sf['allowable_f_kg']:.0f}$ kg → **{sf['verdict']}** (検定比 {sf['ratio']:.2f})",
            "",
        ]
    )
    if m["opening"]:
        op = m["opening"]
        lines.extend(
            [
                "### ４．梁枠を支える建枠の検討",
                f"- 梁枠：{op['beam_frame_name']} ／ 開口スパン：{op['open_spans']}スパン ({op['open_span_m']:.3f} m) ／ 設置高さ：{op['install_tier']}段 ({op['install_height_m']:.3f} m) ／ 上部段数：{op['tiers_above']}段",
                f"- 梁枠上の固定荷重 = {op['w1_dead_kg']:.1f} kg ＋ 積載荷重 {op['beam_live_load_kg']:.0f}/2 = **$W_1 = {op['w1_total_kg']:.1f}$ kg** ({fmt_N(op['w1_total_kg'])})",
                f"- 梁枠を支える建枠の固定荷重 = {op['w2_dead_kg']:.1f} kg ＋ 積載荷重 {sf['live_total_kg']:.0f}/2 = **$W_2 = {op['w2_total_kg']:.1f}$ kg** ({fmt_N(op['w2_total_kg'])})",
                f"- 荷重合計 $W = W_1 + W_2 = {op['w1_total_kg']:.1f} + {op['w2_total_kg']:.1f} = {op['total_W_kg']:.1f}$ kg ({fmt_N(op['total_W_kg'])}) {'＜' if op['ok'] else '＞'} $f = {op['allowable_f_kg']:.0f}$ kg → **{op['verdict']}** (検定比 {op['ratio']:.2f})",
                "",
            ]
        )
    jb_sec_num = "５" if m["opening"] else "４"
    lines.extend(
        [
            f"### {jb_sec_num}．ジャッキベースの検討",
            f"- ジャッキベース：{jb['material']} (繰り出し長さ {jb['extension_mm']:.0f} mm) ／ 許容支持力 $f = {jb['allowable_f_kg']:.0f}$ kg ({fmt_N(jb['allowable_f_kg'])})",
            f"- 1本あたり鉛直力 $N = {jb['governing_frame_load_kg']:.1f} / 2 = {jb['load_per_jack_kg']:.1f}$ kg ({fmt_N(jb['load_per_jack_kg'])}) {'＜' if jb['ok'] else '＞'} $f = {jb['allowable_f_kg']:.0f}$ kg → **{jb['verdict']}**",
        ]
    )
    return lines


def _md_tankan_issoku(m: dict[str, Any]) -> list[str]:
    ov = m["overview"]
    ld = m["loads"]
    st = m["standard_pipe"]
    pl = m["plank"]
    lines = [
        "### １．設計条件",
        f"- 建物高さ：{ov['building_height_m']:.3f} m ／ 足場高さ：{ov['scaffold_height_m']:.3f} m ／ 段数：{ov['tiers']} 段",
        f"- 建地間隔：{ov['standard_span_m']:.3f} m ／ 布間隔：{ov['ledger_spacing_m']:.3f} m ／ 最下段高さ：{ov['bottom_tier_height_m']:.3f} m",
        f"- ブラケット張出し量：{ov['bracket_projection_mm']:.0f} mm ／ 建地中心〜足場板中心離れ $L_1 = {ov['plank_eccentricity_mm']:.0f}$ mm",
        "",
        "### ２．荷重",
        f"- 建地最下段の固定荷重合計 = **{ld['axial_dead_kg']:.1f} kg** ({fmt_sig(ld['axial_dead_N'], 3)} N)",
        f"- 足場板受ブラケット固定荷重 = **{ld['bracket_dead_kg']:.2f} kg** ({fmt_N(ld['bracket_dead_kg'])})",
        f"- 積載荷重（建地1本あたり） = **{ld['live_load_kg']:.0f} kg** ({fmt_N(ld['live_load_kg'])})",
        "",
    ]
    lines.extend(_md_wind_section(m["wall_tie"], "### ３．壁つなぎの検討"))
    bk = st["buckling"]
    lines.extend(
        [
            "### ５．建地の検討",
            f"- 使用部材：{st['member']} ($A={st['section']['A_cm2']:.3f}$ cm², $Z={st['section']['Z_cm3']:.3f}$ cm³, $i={st['section']['i_cm']:.2f}$ cm, $E={st['section']['E_kg_cm2']:.0f}$ kg/cm²)",
            f"- 最下段軸力 $N = {st['N_axial_kg']:.2f}$ kg ／ ブラケット荷重 $P = {st['P_bracket_kg']:.2f}$ kg ／ 偏心距離 $L_1 = {st['L1_m']:.3f}$ m",
            f"- 曲げモーメント $M = P \\times L_1 = {st['M_kg_m']:.2f}$ kg・m = {st['M_kg_cm']:.0f} kg・cm ({fmt_kN_mm(st['M_kg_cm'])})",
            f"- 細長比 $\\lambda = {bk['lambda']}$, 限界細長比 $\\Lambda = {bk['Lambda']}$ ({'λ > Λ 弾性座屈域' if bk['regime']=='elastic_euler' else 'λ ≦ Λ 非弾性座屈域'})",
            f"- 許容応力度 (係数 {bk['term_factor']:.2f} 中期)：$f_c = {st['fc_kg_cm2']:.0f}$ kg/cm², $f_b = {st['fb_kg_cm2']:.0f}$ kg/cm²",
            f"- 発生応力度：$\\sigma_c = {st['sigma_c_kg_cm2']:.1f}$ kg/cm² ({fmt_N_mm2(st['sigma_c_kg_cm2'])}), $\\sigma_b = {st['sigma_b_kg_cm2']:.1f}$ kg/cm² ({fmt_N_mm2(st['sigma_b_kg_cm2'])})",
            f"- 複合応力検定：$\\frac{{\\sigma_c}}{{f_c}} + \\frac{{\\sigma_b}}{{f_b}} = {st['ratio_c']:.3f} + {st['ratio_b']:.3f} = {st['combined_ratio']:.3f}$ {'＜' if st['ok'] else '＞'} 1.0 → **{st['verdict']}**",
            "",
            "### ６．ブラケット上の足場板の検討",
            f"- 使用部材：{pl['member']} ($L={pl['L_cm']:.1f}$ cm, $P={pl['P_kg']:.0f}$ kg, $w={pl['w_kg_cm']:.2f}$ kg/cm)",
            f"- 曲げ：$M = {pl['bending']['M_kg_cm']:.1f}$ kg・cm ({fmt_kN_mm(pl['bending']['M_kg_cm'])}), $\\sigma_b = {pl['bending']['sigma_b_kg_cm2']:.1f}$ kg/cm² ＜ $f_b = {pl['bending']['fb_kg_cm2']:.0f}$ kg/cm² → **{pl['bending']['verdict']}**",
            f"- せん断：$Q = {pl['shear']['Q_kg']:.1f}$ kg ({fmt_N(pl['shear']['Q_kg'])}), $\\tau = {pl['shear']['tau_kg_cm2']:.1f}$ kg/cm² ＜ $f_s = {pl['shear']['fs_kg_cm2']:.1f}$ kg/cm² → **{pl['shear']['verdict']}**",
            f"- たわみ：$\\delta = {pl['deflection']['delta_cm']:.3f}$ cm ({pl['deflection']['delta_mm']:.2f} mm){_defl_md(pl['deflection'])}",
        ]
    )
    return lines


def _md_bracket_support(m: dict[str, Any]) -> list[str]:
    ov = m["overview"]
    ld = m["loads"]
    g = m["girder"]
    b = m["bracket"]
    w = m["weld"]
    a = m["anchor_bolt"]
    c = m["concrete"]
    bp = m["base_plate"]
    return [
        "### １．設計条件・２．荷重",
        f"- 建物高さ：{ov['building_height_m']:.3f} m ／ 足場高さ：{ov['scaffold_height_m']:.3f} m ({ov['tiers']}段) ／ ブラケット設置高さ：{ov['bracket_elevation_m']:.3f} m ／ スパン：{ov['bracket_span_m']:.3f} m",
        f"- 荷重：$N_1 = {ld['N1_kg']:.1f}$ kg, $N_2 = {ld['N2_kg']:.1f}$ kg, $N_3 = {ld['N3_kg']:.0f}$ kg, 大引自重 $N_4 = {ld['N4_kg_m']:.1f}$ kg/m",
        "",
        f"### ３．大引の検討 ({g['member']} × {g['num_girders']}本)",
        f"- 集中荷重 $P = {g['P_kg']:.1f}$ kg ({fmt_N(g['P_kg'])}), 自重 $w = {g['w_kg_cm']:.3f}$ kg/cm",
        f"- 曲げ：$M = {g['bending']['M_kg_cm']:.0f}$ kg・cm ({fmt_kN_mm(g['bending']['M_kg_cm'])}), $\\sigma_b = {g['bending']['sigma_b_kg_cm2']:.1f}$ kg/cm² ＜ $f_b = {g['bending']['fb_kg_cm2']:.0f}$ kg/cm² (横座屈考慮: $F_{{b1}}={g['bending']['ltb']['Fb1_t_cm2']:.3f}$, $F_{{b2}}={g['bending']['ltb']['Fb2_t_cm2']:.3f}$ t/cm²) → **{g['bending']['verdict']}**",
        f"- せん断：$Q = {g['shear']['Q_kg']:.1f}$ kg ({fmt_N(g['shear']['Q_kg'])}), $\\tau = {g['shear']['tau_kg_cm2']:.1f}$ kg/cm² ＜ $f_s = {g['shear']['fs_kg_cm2']:.0f}$ kg/cm² → **{g['shear']['verdict']}**",
        f"- たわみ：$\\delta = {g['deflection']['delta_cm']:.3f}$ cm ({g['deflection']['delta_mm']:.2f} mm) [{g['deflection']['formula_note']}]{_defl_md(g['deflection'])}",
        "",
        f"### ４．足場受ブラケットの検討 ({b['member']}, 片持 L={b['L_cm']:.0f}cm)",
        f"- 集中荷重 $P = {b['P_kg']:.1f}$ kg ({fmt_N(b['P_kg'])}), 自重 $w = {b['w_kg_cm']:.3f}$ kg/cm",
        f"- 曲げ：$M = {b['bending']['M_kg_cm']:.0f}$ kg・cm ({fmt_kN_mm(b['bending']['M_kg_cm'])}), $\\sigma_b = {b['bending']['sigma_b_kg_cm2']:.1f}$ kg/cm² ＜ $f_b = {b['bending']['fb_kg_cm2']:.0f}$ kg/cm² (横座屈 $L_b={b['bending']['ltb']['Lb_cm']:.1f}$cm, $C={b['bending']['ltb']['C_ltb']:.2f}$) → **{b['bending']['verdict']}**",
        f"- せん断：$Q = {b['shear']['Q_kg']:.1f}$ kg ({fmt_N(b['shear']['Q_kg'])}), $\\tau = {b['shear']['tau_kg_cm2']:.1f}$ kg/cm² ＜ $f_s = {b['shear']['fs_kg_cm2']:.0f}$ kg/cm² → **{b['shear']['verdict']}**",
        f"- たわみ：$\\delta = {b['deflection']['delta_cm']:.3f}$ cm ({b['deflection']['delta_mm']:.2f} mm){_defl_md(b['deflection'])}",
        "",
        "### ５．ベースプレート溶接部の検討",
        f"- フランジ突合せ溶接：$Z = {w['Z_w_cm3']:.1f}$ cm³, $\\sigma_b = {w['sigma_b_kg_cm2']:.1f}$ kg/cm² ＜ {w['fs_butt_kg_cm2']:.0f} kg/cm² → **{w['bending_verdict']}**",
        f"- ウェブ完全溶込み溶接：$A = {w['A_w_cm2']:.1f}$ cm², $\\tau = {w['tau_kg_cm2']:.1f}$ kg/cm² ＜ {w['fs_pen_kg_cm2']:.0f} kg/cm² → **{w['shear_verdict']}**",
        f"- 複合応力：$\\sigma_{{MQ}} = \\sqrt{{\\sigma_b^2 + \\tau^2}} = {w['sigma_MQ_kg_cm2']:.1f}$ kg/cm² ＜ {w['fs_pen_kg_cm2']:.0f} kg/cm² → **{w['combined_verdict']}**",
        "",
        f"### ６．アンカーボルトの検討 ({a['size']} 引張{a['tension_count']}本・圧縮{a['compression_count']}本)",
        f"- せん断：$Q_1 = {a['Q1_kg']:.1f}$ kg, $\\tau = {a['tau_kg_cm2']:.1f}$ kg/cm² ＜ $f_s = {a['fs_kg_cm2']:.0f}$ kg/cm² → **{a['shear_verdict']}**",
        f"- 引張＋せん断複合：$j = {a['j_cm']:.2f}$ cm, $T_1 = {a['T1_kg']:.1f}$ kg, $\\sigma_{{ts}} = {a['sigma_ts_kg_cm2']:.1f}$ kg/cm² ＜ $f_{{ts}} = {a['fts_allow_kg_cm2']:.0f}$ kg/cm² → **{a['tension_verdict']}**",
        f"- 必要埋め込み長さ：直線 $L = {a['embedment_straight_cm']:.1f}$ cm (フック付き {a['embedment_hook_cm']:.1f} cm) → 採用長さ **{a['adopted_length_cm']:.1f} cm**",
        "",
        f"### ７．コンクリートの圧縮応力度の検討 ($F_c = {c['Fc_kg_cm2']:.0f}$ kgf/cm²)",
        f"- $\\sigma = \\frac{{4M}}{{bhj}} = {c['sigma_kg_cm2']:.1f}$ kg/cm² ({fmt_N_mm2(c['sigma_kg_cm2'])}) ＜ $f_c = {c['fc_allow_kg_cm2']:.0f}$ kgf/cm² ({fmt_N_mm2(c['fc_allow_kg_cm2'])}) → **{c['verdict']}**",
        "",
        f"### ８．ベースプレートの検討 (板厚 t = {bp['thickness_mm']:.0f} mm, $f_b = {bp['fb_kg_cm2']:.0f}$ kg/cm²)",
        f"- 引張側：$M = {bp['tension_side']['M_kg_cm']:.1f}$ kg・cm, $Z = {bp['tension_side']['Z_cm3']:.2f}$ cm³, $\\sigma = {bp['tension_side']['sigma_kg_cm2']:.1f}$ kg/cm² ＜ $f_b$ → **{bp['tension_side']['verdict']}**",
        f"- 圧縮側：$M = {bp['compression_side']['M_kg_cm']:.1f}$ kg・cm, $Z = {bp['compression_side']['Z_cm3']:.2f}$ cm³, $\\sigma = {bp['compression_side']['sigma_kg_cm2']:.1f}$ kg/cm² ＜ $f_b$ → **{bp['compression_side']['verdict']}**",
    ]


def _md_tsuri_ashiba(m: dict[str, Any]) -> list[str]:
    ov = m["overview"]
    ch = m["chain"]
    pl = m["plank"]
    j = m["joist"]
    g = m["girder"]
    c = m["cantilever"]
    return [
        "### １．設計条件・２．荷重・３．吊チェーンの検討",
        f"- 躯体スパン：X={ov['span_x_m']:.3f} m × Y={ov['span_y_m']:.3f} m ／ 大引間隔 {ov['girder_spacing_m']:.3f} m ／ 根太間隔 {ov['joist_spacing_m']:.3f} m ／ 張出 {ov['cantilever_length_m']:.3f} m",
        f"- 固定荷重 {m['loads']['dead_total_kg']:.1f} kg ＋ 積載荷重 {m['loads']['live_total_kg']:.0f} kg = 引張力 $T = {ch['tension_T_kg']:.1f}$ kg ({fmt_N(ch['tension_T_kg'])}) ＜ $f = {ch['allowable_f_kg']:.0f}$ kg ({ch['member']}) → **{ch['verdict']}** (検定比 {ch['ratio']:.2f})",
        "",
        f"### ４．足場板 ({pl['member']}, L={pl['L_cm']:.0f}cm)",
        f"- 曲げ $\\sigma_b = {pl['bending']['sigma_b_kg_cm2']:.1f} < {pl['bending']['fb_kg_cm2']:.0f}$ **{pl['bending']['verdict']}** ／ せん断 $\\tau = {pl['shear']['tau_kg_cm2']:.1f} < {pl['shear']['fs_kg_cm2']:.1f}$ **{pl['shear']['verdict']}** ／ たわみ $\\delta = {pl['deflection']['delta_cm']:.3f}$ cm ({pl['deflection']['delta_mm']:.2f} mm){_defl_md(pl['deflection'])}",
        "",
        f"### ５．根太 ({j['member']}, L={j['L_cm']:.0f}cm)",
        f"- 曲げ $\\sigma_b = {j['bending']['sigma_b_kg_cm2']:.1f} < {j['bending']['fb_kg_cm2']:.0f}$ **{j['bending']['verdict']}** ／ せん断 $\\tau = {j['shear']['tau_kg_cm2']:.1f} < {j['shear']['fs_kg_cm2']:.0f}$ **{j['shear']['verdict']}** ／ たわみ $\\delta = {j['deflection']['delta_cm']:.3f}$ cm ({j['deflection']['delta_mm']:.2f} mm){_defl_md(j['deflection'])}",
        "",
        f"### ６．大引 ({g['member']}, L={g['L_cm']:.0f}cm, a={g['a_cm']:.0f}cm, b={g['b_cm']:.0f}cm)",
        f"- 曲げ $M = {g['bending']['M_kg_cm']:.1f}$ kg・cm, $\\sigma_b = {g['bending']['sigma_b_kg_cm2']:.1f} < {g['bending']['fb_kg_cm2']:.0f}$ **{g['bending']['verdict']}** ／ せん断 $Q = {g['shear']['Q_kg']:.1f}$ kg, $\\tau = {g['shear']['tau_kg_cm2']:.1f} < {g['shear']['fs_kg_cm2']:.0f}$ **{g['shear']['verdict']}** ／ たわみ $\\delta = {g['deflection']['delta_cm']:.3f}$ cm ({g['deflection']['delta_mm']:.2f} mm){_defl_md(g['deflection'])}",
        "",
        f"### ７．張り出し部 ({c['member']}, 片持 L={c['L_cm']:.0f}cm, P1={c['P1_kg']:.1f}kg, P2={c['P2_kg']:.1f}kg)",
        f"- 曲げ $M = {c['bending']['M_kg_cm']:.1f}$ kg・cm, $\\sigma_b = {c['bending']['sigma_b_kg_cm2']:.1f} < {c['bending']['fb_kg_cm2']:.0f}$ **{c['bending']['verdict']}** ／ せん断 $Q = {c['shear']['Q_kg']:.1f}$ kg, $\\tau = {c['shear']['tau_kg_cm2']:.1f} < {c['shear']['fs_kg_cm2']:.0f}$ **{c['shear']['verdict']}** ／ たわみ $\\delta = {c['deflection']['delta_cm']:.3f}$ cm ({c['deflection']['delta_mm']:.2f} mm){_defl_md(c['deflection'])}",
    ]


def _md_nitori_koudai(m: dict[str, Any]) -> list[str]:
    ov = m["overview"]
    d = m["deck"]
    j = m["joist"]
    g = m["girder"]
    b = m["permanent_beam"]
    return [
        "### １．設計条件・２．設計荷重",
        f"- 本設梁スパン {ov['permanent_beam_span_m']:.3f} m ／ 大引スパン {ov['girder_span_m']:.3f} m ／ 構台面積 {ov['platform_area_m2']:.1f} ㎡ ／ 積載荷重 {ov['live_load_t']:.2f} t × 衝撃割増 {ov['impact_factor']:.2f}",
        "",
        f"### ３．床板 ({d['member']}, L={d['L_cm']:.0f}cm, w={d['w_kg_cm']:.2f}kg/cm)",
        f"- 曲げ $M={d['bending']['M_kg_cm']:.1f}$ kg・cm, $\\sigma_b={d['bending']['sigma_b_kg_cm2']:.1f} < {d['bending']['fb_kg_cm2']:.0f}$ **{d['bending']['verdict']}** ／ せん断 $\\tau={d['shear']['tau_kg_cm2']:.1f} < {d['shear']['fs_kg_cm2']:.1f}$ **{d['shear']['verdict']}** ／ たわみ $\\delta={d['deflection']['delta_cm']:.3f}$ cm ({d['deflection']['delta_mm']:.2f} mm){_defl_md(d['deflection'])}",
        "",
        f"### ４．根太 ({j['member']}, L={j['L_cm']:.0f}cm, w={j['w_kg_cm']:.2f}kg/cm)",
        f"- 曲げ $M={j['bending']['M_kg_cm']:.1f}$ kg・cm, $\\sigma_b={j['bending']['sigma_b_kg_cm2']:.1f} < {j['bending']['fb_kg_cm2']:.0f}$ **{j['bending']['verdict']}** ／ せん断 $\\tau={j['shear']['tau_kg_cm2']:.1f} < {j['shear']['fs_kg_cm2']:.0f}$ **{j['shear']['verdict']}** ／ たわみ $\\delta={j['deflection']['delta_cm']:.3f}$ cm ({j['deflection']['delta_mm']:.2f} mm){_defl_md(j['deflection'])}",
        "",
        f"### ５．大引 ({g['member']}, L={g['L_m']:.3f}m, 載荷範囲 a={g['a_m']:.3f}m, W2={g['W2_kg']:.1f}kg)",
        f"- 曲げ $M={g['bending']['M_kg_m']:.1f}$ kg・m, $\\sigma_b={g['bending']['sigma_b_kg_cm2']:.1f} < {g['bending']['fb_kg_cm2']:.0f}$ **{g['bending']['verdict']}** ／ せん断 $Q={g['shear']['Q_kg']:.1f}$ kg, $\\tau={g['shear']['tau_kg_cm2']:.1f} < {g['shear']['fs_kg_cm2']:.0f}$ **{g['shear']['verdict']}** ／ たわみ $\\delta={g['deflection']['delta_cm']:.3f}$ cm ({g['deflection']['delta_mm']:.2f} mm){_defl_md(g['deflection'])}",
        "",
        f"### ６．本設梁 ({b['member']}, L={b['L_m']:.3f}m, 載荷範囲 a={b['a_m']:.3f}m, W2={b['W2_kg']:.1f}kg)",
        f"- 曲げ $M={b['bending']['M_kg_m']:.1f}$ kg・m, $\\sigma_b={b['bending']['sigma_b_kg_cm2']:.1f} < {b['bending']['fb_kg_cm2']:.0f}$ **{b['bending']['verdict']}** ／ せん断 $Q={b['shear']['Q_kg']:.1f}$ kg, $\\tau={b['shear']['tau_kg_cm2']:.1f} < {b['shear']['fs_kg_cm2']:.0f}$ **{b['shear']['verdict']}** ／ たわみ $\\delta={b['deflection']['delta_cm']:.3f}$ cm ({b['deflection']['delta_mm']:.2f} mm){_defl_md(b['deflection'])}",
    ]


def render_html(report: dict[str, Any]) -> str:
    """A4印刷対応・SVG図面付き 足場計算書 HTML (SUCCES Ver 4.11 様式) を生成する."""
    meta = report["project"]
    pages: list[str] = []

    # ページ配列を組み立て (表紙はノンブル外、本文 1..N)
    # まずモジュール別詳細ページを生成してページ番号を割り当てる
    detail_pages: list[tuple[str, str]] = []  # (key, inner_html)
    page_map: dict[str, int] = {}
    cur_p = 3  # Page 1=検討概要書, Page 2=検討結果概要

    for mod in report["modules"]:
        mt = mod["module"]
        if mt == "wakugumi":
            m_pages = _html_wakugumi_pages(mod)
        elif mt == "tankan_issoku":
            m_pages = _html_tankan_pages(mod)
        elif mt == "bracket_support":
            m_pages = _html_bracket_pages(mod)
        elif mt == "tsuri_ashiba":
            m_pages = _html_tsuri_pages(mod)
        elif mt == "nitori_koudai":
            m_pages = _html_nitori_pages(mod)
        else:
            m_pages = []
        for tag, body in m_pages:
            page_map[tag] = cur_p
            detail_pages.append((tag, body))
            cur_p += 1

    total_pages = cur_p - 1

    # 表紙
    locs_html = "".join(f"<div>{html.escape(loc)}</div>" for loc in meta.get("locations", []))
    cover_html = f"""
    <section class="page cover-page">
      <div class="cover-title">足　場　計　算　書</div>
      <div class="cover-locs">{locs_html}</div>
      <div class="cover-project">{html.escape(meta.get('name', '（仮称）新築工事'))}</div>
      <div class="cover-company">{html.escape(meta.get('company', ''))}</div>
      <table class="stamp-box">
        <tr><th>課長</th><th>工事長</th></tr>
        <tr><td class="stamp-cell"></td><td class="stamp-cell"></td></tr>
      </table>
    </section>
    """
    pages.append(cover_html)

    # Page 1: 検討概要書
    ov_rows = [
        f"<tr><th class='ov-k'>現場名</th><td>{html.escape(meta.get('name', ''))}</td></tr>",
        f"<tr><th class='ov-k'>検討場所</th><td>{'<br>'.join(html.escape(x) for x in meta.get('locations', []))}</td></tr>",
    ]
    for mod in report["modules"]:
        ov = mod["overview"]
        mt = mod["module"]
        if mt == "wakugumi":
            ov_rows.append("<tr><th colspan='2' class='ov-sec'>枠組足場</th></tr>")
            ov_rows.append(f"<tr><td>建物高さ / 足場高さ</td><td>{ov['building_height_m']:.3f} m / {ov['scaffold_height_m']:.3f} m ({ov['tiers']} 段)</td></tr>")
            ov_rows.append(f"<tr><td>建枠寸法 / 基準風速</td><td>建地間隔 = {ov['bay_span_m']:.3f} m, 布間隔 = {ov['frame_height_m']:.3f} m / Vo = {ov['design_wind_v0_ms']:g} m/s</td></tr>")
        elif mt == "tankan_issoku":
            ov_rows.append("<tr><th colspan='2' class='ov-sec'>単管一側ブラケット足場</th></tr>")
            ov_rows.append(f"<tr><td>建物高さ / 足場高さ</td><td>{ov['building_height_m']:.3f} m / {ov['scaffold_height_m']:.3f} m ({ov['tiers']} 段)</td></tr>")
            ov_rows.append(f"<tr><td>足場寸法 / 基準風速</td><td>建地間隔 = {ov['standard_span_m']:.3f} m, 布間隔 = {ov['ledger_spacing_m']:.3f} m / Vo = {ov['design_wind_v0_ms']:g} m/s</td></tr>")
        elif mt == "bracket_support":
            ov_rows.append("<tr><th colspan='2' class='ov-sec'>足場受ブラケット</th></tr>")
            ov_rows.append(f"<tr><td>建物高さ / 足場高さ</td><td>{ov['building_height_m']:.3f} m / {ov['scaffold_height_m']:.3f} m ({ov['tiers']} 段)</td></tr>")
            ov_rows.append(f"<tr><td>ブラケットスパン / 部材</td><td>{ov['bracket_span_m']:.3f} m / 大引 {html.escape(ov['girder_material'])} / ブラケット {html.escape(ov['bracket_material'])}</td></tr>")
        elif mt == "tsuri_ashiba":
            ov_rows.append("<tr><th colspan='2' class='ov-sec'>鉄骨吊り足場</th></tr>")
            ov_rows.append(f"<tr><td>躯体スパン</td><td>X方向 = {ov['span_x_m']:.3f} m, Y方向 = {ov['span_y_m']:.3f} m (張出 {ov['cantilever_length_m']:.3f} m)</td></tr>")
        elif mt == "nitori_koudai":
            ov_rows.append("<tr><th colspan='2' class='ov-sec'>荷取り構台</th></tr>")
            ov_rows.append(f"<tr><td>躯体スパン / 積載荷重</td><td>本設梁 {ov['permanent_beam_span_m']:.3f} m × 大引 {ov['girder_span_m']:.3f} m / {ov['live_load_t']:.2f} t (衝撃 {ov['impact_factor']:.2f}倍)</td></tr>")

    pages.append(_wrap_page(1, total_pages, f"<h1>検討概要書</h1><table class='grid-tbl'>{''.join(ov_rows)}</table>"))

    # Page 2: 検討結果概要
    sum_rows_html: list[str] = []
    last_sec = None
    for row in report["summary_rows"]:
        if row["section"] != last_sec:
            sum_rows_html.append(f"<tr class='sec-row'><td colspan='8'>{html.escape(row['section'])}</td></tr>")
            last_sec = row["section"]
        pno = page_map.get(f"{row['section']}:{row['part']}", "")
        ratio_s = f"{row['ratio']:.2f}" if row["ratio"] is not None else ""
        if row["deflection_cm"] is not None:
            dv = row.get("deflection_verdict")
            defl_s = f"{row['deflection_cm']:.2f} {_v_badge(dv)}" if dv else f"{row['deflection_cm']:.2f}"
        else:
            defl_s = ""
        sum_rows_html.append(
            f"<tr><td>{html.escape(row['part'])}</td>"
            f"<td>{html.escape(row['member'])}</td>"
            f"<td class='c'>{_v_badge(row['verdict'])}</td>"
            f"<td class='r'>{ratio_s}</td>"
            f"<td class='c'>{_v_badge(row['bending'])}</td>"
            f"<td class='c'>{_v_badge(row['shear'])}</td>"
            f"<td class='r'>{defl_s}</td>"
            f"<td class='c'>{pno}</td></tr>"
        )

    summary_page = f"""
    <h1>検討結果概要</h1>
    <table class="grid-tbl summary-tbl">
      <thead>
        <tr>
          <th>部位</th><th>使用部材</th><th>判定</th><th>計算値／許容値</th>
          <th>曲げ(M)</th><th>せん断(Q)</th><th>たわみ(δ cm)</th><th>ページ</th>
        </tr>
      </thead>
      <tbody>{''.join(sum_rows_html)}</tbody>
    </table>
    """
    pages.append(_wrap_page(2, total_pages, summary_page))

    for idx, (_tag, body) in enumerate(detail_pages, start=3):
        pages.append(_wrap_page(idx, total_pages, body))

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>足場計算書 - {html.escape(meta.get('name', ''))}</title>
<style>
  @page {{ size: A4; margin: 14mm; }}
  body {{ font-family: "Yu Mincho", "MS PMincho", "Hiragino Mincho ProN", "Noto Serif JP", serif; color: #111; margin: 0; background: #f3f4f6; font-size: 11pt; line-height: 1.55; }}
  .page {{ width: 210mm; min-height: 297mm; box-sizing: border-box; margin: 10mm auto; padding: 15mm 16mm 18mm; background: #fff; box-shadow: 0 2px 10px rgba(0,0,0,0.08); position: relative; page-break-after: always; }}
  .page-num {{ position: absolute; bottom: 10mm; left: 0; right: 0; text-align: center; font-size: 9.5pt; color: #333; }}
  .cover-page {{ display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; }}
  .cover-title {{ font-size: 24pt; letter-spacing: 0.35em; border-bottom: 2px solid #111; padding: 0 24mm 6mm; margin-bottom: 14mm; }}
  .cover-locs {{ font-size: 12pt; margin-bottom: 18mm; line-height: 1.9; }}
  .cover-project {{ font-size: 15pt; font-weight: bold; margin-bottom: 14mm; }}
  .cover-company {{ font-size: 12pt; margin-bottom: 28mm; }}
  .stamp-box {{ border-collapse: collapse; width: 76mm; margin-top: 10mm; }}
  .stamp-box th, .stamp-box td {{ border: 1px solid #111; text-align: center; }}
  .stamp-box th {{ height: 8mm; font-weight: normal; }}
  .stamp-cell {{ height: 22mm; }}
  h1 {{ font-size: 14pt; border-bottom: 1.5px solid #111; padding-bottom: 2mm; margin: 0 0 5mm; }}
  h2 {{ font-size: 12pt; margin: 5mm 0 2.5mm; }}
  h3 {{ font-size: 10.5pt; margin: 3.5mm 0 1.5mm; }}
  table.grid-tbl {{ width: 100%; border-collapse: collapse; margin: 3mm 0 5mm; font-size: 9.5pt; }}
  table.grid-tbl th, table.grid-tbl td {{ border: 1px solid #333; padding: 1.6mm 2.5mm; }}
  table.grid-tbl th {{ background: #f8fafc; font-weight: bold; }}
  .ov-k {{ width: 32%; text-align: left; }}
  .ov-sec, .sec-row td {{ background: #eef2f7; font-weight: bold; }}
  .c {{ text-align: center; }}
  .r {{ text-align: right; font-variant-numeric: tabular-nums; }}
  .eq {{ margin: 1.5mm 0 1.5mm 4mm; font-family: "Cambria Math", "Yu Mincho", serif; }}
  .si {{ color: #374151; font-size: 9.5pt; margin-left: 6px; }}
  .ok {{ font-weight: bold; border-bottom: 3px double #111; padding: 0 3px; }}
  .ng {{ font-weight: bold; color: #b91c1c; border-bottom: 3px double #b91c1c; padding: 0 3px; }}
  .ok-tag {{ font-size: 8.5pt; color: #166534; background: #dcfce7; padding: 1px 5px; border-radius: 3px; }}
  .ng-tag {{ font-size: 8.5pt; color: #991b1b; background: #fee2e2; padding: 1px 5px; border-radius: 3px; font-weight: bold; }}
  .flex-row {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 6mm; }}
  .eng-svg {{ display: block; margin: 2mm auto; max-width: 100%; }}
  @media print {{ body {{ background: #fff; }} .page {{ margin: 0; box-shadow: none; width: auto; min-height: auto; }} }}
</style>
</head>
<body>
{''.join(pages)}
</body>
</html>
"""


def _wrap_page(pno: int, total: int, inner: str) -> str:
    return f'<section class="page">{inner}<div class="page-num">{pno} / {total}</div></section>'


def _html_wind_body(wt: dict[str, Any], header: str) -> str:
    c = wt["conditions"]
    vp = wt["velocity_pressure"]
    wf = wt["wind_force_coeff"]
    v = wt["verification"]
    gamma_line = (
        f'<div class="eq">第2構面風力低減係数 γ ＝ {wf["gamma"]:.2f} （γ＝1－充実率φ）</div>'
        if wf["gamma"] is not None
        else ""
    )
    return f"""
    <h2>{header}</h2>
    <h3>(1) 設計条件</h3>
    <table class="grid-tbl">
      <tr><th>場所</th><td>{html.escape(c['location'])}</td><th>地表面粗度区分</th><td>{html.escape(c['terrain'])}</td></tr>
      <tr><th>近接高層建築物</th><td>{html.escape(c['nearby_highrise'])}</td><th>落下物防護材</th><td>{html.escape(c['sheet_description'])}</td></tr>
      <tr><th>足場の高さ / 長さ</th><td>{c['scaffold_height_m']:.3f} m / {c['scaffold_length_m']:.3f} m</td><th>壁つなぎ材料</th><td>{html.escape(c['wall_tie_material'])}</td></tr>
      <tr><th>壁つなぎ設置間隔</th><td colspan="3">縦：{html.escape(c['tie_vertical_desc'])} ／ 横：{html.escape(c['tie_horizontal_desc'])}</td></tr>
    </table>
    <h3>(2) 設計用速度圧</h3>
    <div class="eq">基準風速 V<sub>o</sub> ＝ {vp['V0_ms']:g} m/s，台風時割増係数 K<sub>e</sub> ＝ {vp['Ke']:.2f}，瞬間風速分布係数 S ＝ {vp['S']:.2f}（Z={vp['Z_band_m']}m，{html.escape(c['terrain'])}），E<sub>B</sub> ＝ {vp['EB']:.2f}</div>
    <div class="eq">設計風速 V<sub>z</sub> ＝ V<sub>o</sub> × K<sub>e</sub> × S × E<sub>B</sub> ＝ {vp['V0_ms']:g} × {vp['Ke']:.2f} × {vp['S']:.2f} × {vp['EB']:.2f} ＝ <b>{vp['Vz_ms']:.1f} m/s</b></div>
    <div class="eq">設計用速度圧 q<sub>z</sub> ＝ (1/16) V<sub>z</sub><sup>2</sup> ＝ (1/16) × {vp['Vz_ms']:.1f}<sup>2</sup> ＝ <b>{vp['qz_kgf_m2']:.1f} kgf/㎡</b> <span class="si">({fmt_N_m2(vp['qz_kgf_m2'])})</span></div>
    <h3>(3) 風力係数</h3>
    <div class="eq">充実率 φ ＝ {wf['phi']:.2f}，基本風力係数 C<sub>o</sub> ＝ {wf['C0']:.2f}，形状補正係数 R ＝ {wf['R']:.2f}，設置位置補正係数 F ＝ {wf['F']:.2f}（設置位置={wf['position']}，{wf['F_formula']}）</div>
    {gamma_line}
    <div class="eq">風力係数 C ＝ {wf['C_formula']} ＝ <b>{wf['C']:.2f}</b></div>
    <h3>(4) 壁つなぎの検討</h3>
    <div class="eq">壁つなぎ作用面積 A ＝ {v['tie_horizontal_m']:.3f} m × {v['tie_vertical_m']:.3f} m ＝ <b>{v['area_A_m2']:.2f} ㎡</b></div>
    <div class="eq">壁つなぎ許容耐力 F ＝ {v['base_allowable_kgf']:.0f} × {v['wind_increase_factor']:.1f} ＝ <b>{v['allowable_F_kgf']:.0f} kgf</b> <span class="si">({fmt_N(v['allowable_F_kgf'])})</span>（風荷重負担のため30％割増考慮）</div>
    <div class="eq">壁つなぎ1本にかかる荷重 R ＝ q<sub>z</sub>・C・A ＝ {vp['qz_kgf_m2']:.1f} × {wf['C']:.2f} × {v['area_A_m2']:.2f} ＝ <b>{v['load_R_kgf']:.1f} kgf</b> <span class="si">({fmt_N(v['load_R_kgf'])})</span> {'＜' if v['ok'] else '＞'} F ＝ {v['allowable_F_kgf']:.0f} kgf {_v_badge(v['verdict'])}</div>
    """


def _html_load_table(items: list[dict[str, Any]], total_kg: float, total_N: float | None = None) -> str:
    rows = "".join(
        f"<tr><td>{html.escape(it['label'])}</td><td>{html.escape(it.get('spec', ''))}</td>"
        f"<td>{html.escape(it['expr'])}</td><td class='r'>{it['weight_kg']:.1f} kg</td></tr>"
        for it in items
    )
    n_txt = f"{fmt_sig(total_N, 3)} N" if total_N is not None else fmt_N(total_kg)
    return (
        f'<table class="grid-tbl"><thead><tr><th>部材</th><th>規格</th><th>算定式</th><th>質量</th></tr></thead>'
        f'<tbody>{rows}<tr><th colspan="3" class="r">小計</th>'
        f'<th class="r">{total_kg:.1f} kg <span class="si">({n_txt})</span></th></tr></tbody></table>'
    )


def _html_wakugumi_pages(m: dict[str, Any]) -> list[tuple[str, str]]:
    ov = m["overview"]
    sf = m["standard_frame"]
    jb = m["jack_base"]
    p1 = f"""
    <h1>{html.escape(m['title'])}</h1>
    <h2>１．設計条件</h2>
    {svg_wakugumi_elevation(ov, m['opening'])}
    <table class="grid-tbl">
      <tr><th>建物高さ</th><td>{ov['building_height_m']:.3f} m</td><th>足場高さ</th><td>{ov['scaffold_height_m']:.3f} m ({ov['tiers']} 段)</td></tr>
      <tr><th>最下段高さ</th><td>{ov['bottom_tier_height_m']:.3f} m</td><th>建枠寸法</th><td>間隔 {ov['bay_span_m']:.3f} m × 高さ {ov['frame_height_m']:.3f} m × 巾 {ov['frame_width_m']:.3f} m</td></tr>
      <tr><th>壁つなぎ配置</th><td colspan="3">水平 {ov['tie_horizontal_spans']}スパンごと ／ 垂直 {ov['tie_vertical_start_tier']}段目から {ov['tie_vertical_tiers']}段ごと</td></tr>
    </table>
    """
    p2 = _html_wind_body(m["wall_tie"], "２．壁つなぎの検討")
    p3 = f"""
    <h2>３．建枠の検討</h2>
    <div class="eq">建枠段数：{sf['tiers']} 段 ／ 建枠の許容圧縮力 f ＝ {sf['allowable_f_kg']:.0f} kg/枠 <span class="si">({fmt_N(sf['allowable_f_kg'])})</span></div>
    {_html_load_table(sf['dead_items'], sf['dead_total_kg'])}
    <div class="eq">積載荷重 ＝ {sf['live_per_layer_kg']:.0f} kg × {sf['live_layers']} 層 ＝ <b>{sf['live_total_kg']:.0f} kg</b> <span class="si">({fmt_N(sf['live_total_kg'])})</span></div>
    <div class="eq">最下段建枠作用荷重 W ＝ {sf['dead_total_kg']:.1f} ＋ {sf['live_total_kg']:.0f} ＝ <b>{sf['total_W_kg']:.1f} kg</b> <span class="si">({fmt_N(sf['total_W_kg'])})</span> {'＜' if sf['ok'] else '＞'} f ＝ {sf['allowable_f_kg']:.0f} kg {_v_badge(sf['verdict'])}</div>
    """
    out = [("枠組足場:設計条件", p1), ("枠組足場:壁つなぎ", p2), ("枠組足場:建枠", p3)]
    if m["opening"]:
        op = m["opening"]
        p4 = f"""
        <h2>４．梁枠を支える建枠の検討</h2>
        <div class="flex-row">
          <div>
            <div class="eq">梁枠材料：{html.escape(op['beam_frame_name'])} ／ 開口スパン：{op['open_spans']}スパン ({op['open_span_m']:.3f} m)</div>
            <div class="eq">設置高さ：{op['install_tier']}段 ({op['install_height_m']:.3f} m) ／ 梁枠上段数：{op['tiers_above']}段 ／ 梁枠上積載荷重：{op['beam_live_load_kg']:.0f} kg</div>
          </div>
          {svg_opening_load_diagram()}
        </div>
        <h3>(2) 梁枠上の荷重計算 (W<sub>1</sub>)</h3>
        {_html_load_table(op['w1_items'], op['w1_dead_kg'])}
        <div class="eq">W<sub>1</sub> ＝ {op['w1_dead_kg']:.1f} ＋ {op['beam_live_load_kg']:.0f}/2 ＝ <b>{op['w1_total_kg']:.1f} kg</b> <span class="si">({fmt_N(op['w1_total_kg'])})</span></div>
        <h3>(3) 梁枠を支える建枠の荷重計算 (W<sub>2</sub>)</h3>
        {_html_load_table(op['w2_items'], op['w2_dead_kg'])}
        <div class="eq">W<sub>2</sub> ＝ {op['w2_dead_kg']:.1f} ＋ {sf['live_total_kg']:.0f}/2 ＝ <b>{op['w2_total_kg']:.1f} kg</b> <span class="si">({fmt_N(op['w2_total_kg'])})</span></div>
        <h3>(4) 梁枠を支える建枠の検討</h3>
        <div class="eq">荷重合計 W ＝ W<sub>1</sub> ＋ W<sub>2</sub> ＝ {op['w1_total_kg']:.1f} ＋ {op['w2_total_kg']:.1f} ＝ <b>{op['total_W_kg']:.1f} kg</b> <span class="si">({fmt_N(op['total_W_kg'])})</span> {'＜' if op['ok'] else '＞'} f ＝ {op['allowable_f_kg']:.0f} kg {_v_badge(op['verdict'])}</div>
        <h2>５．ジャッキベースの検討</h2>
        <div class="eq">ジャッキベース許容支持力 f ＝ {jb['allowable_f_kg']:.0f} kg（繰り出し長さ {jb['extension_mm']:.0f} mm）</div>
        <div class="eq">鉛直力 N ＝ {jb['governing_frame_load_kg']:.1f} / 2 ＝ <b>{jb['load_per_jack_kg']:.1f} kg</b> <span class="si">({fmt_N(jb['load_per_jack_kg'])})</span> {'＜' if jb['ok'] else '＞'} f ＝ {jb['allowable_f_kg']:.0f} kg {_v_badge(jb['verdict'])}</div>
        """
        out.append(("枠組足場:梁枠", p4))
    else:
        p3_extra = f"""
        <h2>４．ジャッキベースの検討</h2>
        <div class="eq">ジャッキベース許容支持力 f ＝ {jb['allowable_f_kg']:.0f} kg（繰り出し長さ {jb['extension_mm']:.0f} mm）</div>
        <div class="eq">鉛直力 N ＝ {jb['governing_frame_load_kg']:.1f} / 2 ＝ <b>{jb['load_per_jack_kg']:.1f} kg</b> <span class="si">({fmt_N(jb['load_per_jack_kg'])})</span> {'＜' if jb['ok'] else '＞'} f ＝ {jb['allowable_f_kg']:.0f} kg {_v_badge(jb['verdict'])}</div>
        """
        out[-1] = ("枠組足場:建枠", p3 + p3_extra)
    return out


def _html_tankan_pages(m: dict[str, Any]) -> list[tuple[str, str]]:
    ov = m["overview"]
    ld = m["loads"]
    st = m["standard_pipe"]
    pl = m["plank"]
    bk = st["buckling"]
    p1 = f"""
    <h1>{html.escape(m['title'])}</h1>
    <h2>１．設計条件</h2>
    <table class="grid-tbl">
      <tr><th>建物高さ / 足場高さ</th><td>{ov['building_height_m']:.3f} m / {ov['scaffold_height_m']:.3f} m ({ov['tiers']} 段)</td></tr>
      <tr><th>建地間隔 / 布間隔 / 最下段</th><td>{ov['standard_span_m']:.3f} m / {ov['ledger_spacing_m']:.3f} m / {ov['bottom_tier_height_m']:.3f} m</td></tr>
      <tr><th>ブラケット張出 / 離れ L1</th><td>{ov['bracket_projection_mm']:.0f} mm / {ov['plank_eccentricity_mm']:.0f} mm</td></tr>
    </table>
    <h2>２．荷重</h2>
    {_html_load_table(ld['axial_dead_items'], ld['axial_dead_kg'], ld['axial_dead_N'])}
    <div class="eq">足場板受ブラケット固定荷重 ＝ <b>{ld['bracket_dead_kg']:.2f} kg</b> <span class="si">({fmt_N(ld['bracket_dead_kg'])})</span> ／ 積載荷重（建地1本あたり）＝ <b>{ld['live_load_kg']:.0f} kg</b> <span class="si">({fmt_N(ld['live_load_kg'])})</span></div>
    """
    p2 = _html_wind_body(m["wall_tie"], "３．壁つなぎの検討")
    p3 = f"""
    <h2>５．建地の検討</h2>
    <div class="flex-row">
      <div>
        <div class="eq">使用部材：{html.escape(st['member'])}（A={st['section']['A_cm2']:.3f} cm², Z={st['section']['Z_cm3']:.3f} cm³, i={st['section']['i_cm']:.2f} cm, E={st['section']['E_kg_cm2']:.0f} kg/cm²）</div>
        <div class="eq">最下段軸力 N ＝ {st['N_axial_kg']:.2f} kg ／ ブラケット荷重 P ＝ {st['P_bracket_kg']:.2f} kg ／ L<sub>1</sub> ＝ {st['L1_m']:.3f} m</div>
        <div class="eq">曲げモーメント M ＝ P × L<sub>1</sub> ＝ {st['M_kg_m']:.2f} kg・m ＝ <b>{st['M_kg_cm']:.0f} kg・cm</b> <span class="si">({fmt_kN_mm(st['M_kg_cm'])})</span></div>
      </div>
      {svg_tankan_bracket_detail(st['L1_m'], st['buckling_L_m'])}
    </div>
    <div class="eq">細長比 λ ＝ {bk['lambda']}，限界細長比 Λ ＝ {bk['Lambda']}（{'λ ＞ Λ' if bk['regime']=='elastic_euler' else 'λ ≦ Λ'}）</div>
    <div class="eq">許容圧縮応力度 f<sub>c</sub> ＝ <b>{st['fc_kg_cm2']:.0f} kg/cm²</b>（中期 {bk['term_factor']:.2f}倍），許容曲げ応力度 f<sub>b</sub> ＝ <b>{st['fb_kg_cm2']:.0f} kg/cm²</b>（中期）</div>
    <div class="eq">圧縮応力度 σ<sub>c</sub> ＝ {st['N_axial_kg']:.2f} / {st['section']['A_cm2']:.3f} ＝ <b>{st['sigma_c_kg_cm2']:.1f} kg/cm²</b> <span class="si">({fmt_N_mm2(st['sigma_c_kg_cm2'])})</span></div>
    <div class="eq">曲げ応力度 σ<sub>b</sub> ＝ {st['M_kg_cm']:.0f} / {st['section']['Z_cm3']:.3f} ＝ <b>{st['sigma_b_kg_cm2']:.1f} kg/cm²</b> <span class="si">({fmt_N_mm2(st['sigma_b_kg_cm2'])})</span></div>
    <div class="eq">複合応力検定：σ<sub>c</sub>/f<sub>c</sub> ＋ σ<sub>b</sub>/f<sub>b</sub> ＝ {st['ratio_c']:.3f} ＋ {st['ratio_b']:.3f} ＝ <b>{st['combined_ratio']:.3f}</b> {'＜' if st['ok'] else '＞'} 1.0 {_v_badge(st['verdict'])}</div>
    """
    p4 = f"""
    <h2>６．ブラケット上の足場板の検討</h2>
    <div class="flex-row">
      <div>
        <div class="eq">使用部材：{html.escape(pl['member'])}（A={pl['section']['A_cm2']:.3f} cm², I={pl['section']['I_cm4']:.3f} cm⁴, Z={pl['section']['Z_cm3']:.3f} cm³, E={pl['section']['E_kg_cm2']:.0f} kg/cm²）</div>
        <div class="eq">P ＝ {pl['P_kg']:.0f} kg，自重 w ＝ {pl['w_kg_cm']:.2f} kg/cm，スパン L ＝ {pl['L_cm']:.1f} cm</div>
      </div>
      {svg_simple_beam(f"L = {pl['L_cm']:.1f} cm", True, f"w={pl['w_kg_cm']:.2f}", f"P={pl['P_kg']:.0f}kg")}
    </div>
    <div class="eq">(1) 曲げ：M ＝ {pl['bending']['M_kg_cm']:.1f} kg・cm <span class="si">({fmt_kN_mm(pl['bending']['M_kg_cm'])})</span>，σ<sub>b</sub> ＝ <b>{pl['bending']['sigma_b_kg_cm2']:.1f} kg/cm²</b> ＜ f<sub>b</sub> ＝ {pl['bending']['fb_kg_cm2']:.0f} kg/cm² {_v_badge(pl['bending']['verdict'])}</div>
    <div class="eq">(2) せん断：Q ＝ {pl['shear']['Q_kg']:.1f} kg <span class="si">({fmt_N(pl['shear']['Q_kg'])})</span>，τ ＝ <b>{pl['shear']['tau_kg_cm2']:.1f} kg/cm²</b> ＜ f<sub>s</sub> ＝ {pl['shear']['fs_kg_cm2']:.1f} kg/cm² {_v_badge(pl['shear']['verdict'])}</div>
    <div class="eq">(3) たわみ：δ ＝ {pl['deflection']['delta_p_cm']:.3f} ＋ {pl['deflection']['delta_w_cm']:.3f} ＝ <b>{pl['deflection']['delta_cm']:.3f} cm</b> ({pl['deflection']['delta_mm']:.2f} mm){_defl_badge(pl['deflection'])}</div>
    """
    return [
        ("単管一側ブラケット足場:荷重", p1),
        ("単管一側ブラケット足場:壁つなぎ", p2),
        ("単管一側ブラケット足場:建地", p3),
        ("単管一側ブラケット足場:ブラケット上足場板", p4),
    ]


def _html_bracket_pages(m: dict[str, Any]) -> list[tuple[str, str]]:
    ov = m["overview"]
    ld = m["loads"]
    g = m["girder"]
    b = m["bracket"]
    w = m["weld"]
    a = m["anchor_bolt"]
    c = m["concrete"]
    bp = m["base_plate"]

    p1 = f"""
    <h1>{html.escape(m['title'])}</h1>
    <h2>１．設計条件・２．荷重</h2>
    <table class="grid-tbl">
      <tr><th>建物高さ / 足場高さ</th><td>{ov['building_height_m']:.3f} m / {ov['scaffold_height_m']:.3f} m ({ov['tiers']} 段)</td><th>設置高さ / スパン</th><td>{ov['bracket_elevation_m']:.3f} m / {ov['bracket_span_m']:.3f} m</td></tr>
      <tr><th>大引材料 ({ov['num_girders']}本)</th><td>{html.escape(ov['girder_material'])}</td><th>ブラケット材料</th><td>{html.escape(ov['bracket_material'])}</td></tr>
    </table>
    <h3>(1) 建枠1スパンあたり荷重 (N<sub>1</sub>)</h3>
    {_html_load_table(ld['N1_items'], ld['N1_kg'])}
    <h3>(2) 最下部荷重 (N<sub>2</sub>) ・ (3) 積載荷重 (N<sub>3</sub>) ・ (4) 大引自重 (N<sub>4</sub>)</h3>
    {_html_load_table(ld['N2_items'], ld['N2_kg'])}
    <div class="eq">N<sub>3</sub> ＝ {ld['live_per_layer_kg']:.0f} × {ld['live_layers']} ＝ <b>{ld['N3_kg']:.0f} kg</b> <span class="si">({fmt_N(ld['N3_kg'])})</span> ／ N<sub>4</sub> ＝ <b>{ld['N4_kg_m']:.1f} kg/m</b> <span class="si">({fmt_N_m(ld['N4_kg_m'])})</span></div>
    """
    p2 = f"""
    <h2>３．大引の検討 ({html.escape(g['member'])} × {g['num_girders']}本)</h2>
    <div class="flex-row">
      <div>
        <div class="eq">I = {g['section']['I_cm4']:.1f} cm⁴, Z = {g['section']['Z_cm3']:.1f} cm³, i = {g['section']['i_ltb_cm']:.2f} cm, f<sub>s</sub> = {g['section']['fs_kg_cm2']:.0f} kg/cm²</div>
        <div class="eq">P ＝ (N<sub>1</sub>+N<sub>2</sub>+N<sub>3</sub>)/{g['num_girders']} ＝ <b>{g['P_kg']:.1f} kg</b> <span class="si">({fmt_N(g['P_kg'])})</span>，自重 w ＝ {g['w_kg_cm']:.3f} kg/cm</div>
        <div class="eq">(2) 曲げ：M ＝ <b>{g['bending']['M_kg_cm']:.0f} kg・cm</b> <span class="si">({fmt_kN_mm(g['bending']['M_kg_cm'])})</span></div>
        <div class="eq">σ<sub>b</sub> ＝ {g['bending']['sigma_b_kg_cm2']:.1f} kg/cm² ＜ f<sub>b</sub> ＝ {g['bending']['fb_kg_cm2']:.0f} kg/cm² {_v_badge(g['bending']['verdict'])}</div>
        <div class="eq">横座屈照査：Λ={g['bending']['ltb']['Lambda']}, F<sub>b1</sub>={g['bending']['ltb']['Fb1_t_cm2']:.3f} t/cm², F<sub>b2</sub>={g['bending']['ltb']['Fb2_t_cm2']:.3f} t/cm²</div>
      </div>
      {svg_girder_multipoint_and_moment(g['L_m'], g['a2_cm'], g['n_bays'])}
    </div>
    <div class="eq">(3) せん断：Q ＝ <b>{g['shear']['Q_kg']:.1f} kg</b> <span class="si">({fmt_N(g['shear']['Q_kg'])})</span>，τ ＝ <b>{g['shear']['tau_kg_cm2']:.1f} kg/cm²</b> ＜ f<sub>s</sub> ＝ {g['shear']['fs_kg_cm2']:.0f} kg/cm² {_v_badge(g['shear']['verdict'])}</div>
    <div class="eq">(4) たわみ：δ ＝ {g['deflection']['delta_p_cm']:.3f} ＋ {g['deflection']['delta_w_cm']:.3f} ＝ <b>{g['deflection']['delta_cm']:.3f} cm</b> ({g['deflection']['delta_mm']:.2f} mm){_defl_badge(g['deflection'])}</div>
    """
    p3 = f"""
    <h2>４．足場受ブラケットの検討 ({html.escape(b['member'])})</h2>
    <div class="flex-row">
      <div>
        <div class="eq">I = {b['section']['I_cm4']:.1f} cm⁴, Z = {b['section']['Z_cm3']:.1f} cm³, i = {b['section']['i_ltb_cm']:.2f} cm, L = {b['L_cm']:.0f} cm (a={b['a_cm']:.0f}, b={b['b_cm']:.0f})</div>
        <div class="eq">集中荷重 P ＝ <b>{b['P_kg']:.1f} kg</b> <span class="si">({fmt_N(b['P_kg'])})</span>，自重 w ＝ {b['w_kg_cm']:.3f} kg/cm</div>
        <div class="eq">(2) 曲げ：M ＝ <b>{b['bending']['M_kg_cm']:.0f} kg・cm</b> <span class="si">({fmt_kN_mm(b['bending']['M_kg_cm'])})</span></div>
        <div class="eq">σ<sub>b</sub> ＝ <b>{b['bending']['sigma_b_kg_cm2']:.1f} kg/cm²</b> ＜ f<sub>b</sub> ＝ {b['bending']['fb_kg_cm2']:.0f} kg/cm² (L<sub>b</sub>={b['bending']['ltb']['Lb_cm']:.1f}cm, C={b['bending']['ltb']['C_ltb']:.2f}) {_v_badge(b['bending']['verdict'])}</div>
      </div>
      {svg_cantilever_bracket(b['L_cm'], b['a_cm'], b['b_cm'])}
    </div>
    <div class="eq">(3) せん断：Q ＝ <b>{b['shear']['Q_kg']:.1f} kg</b> <span class="si">({fmt_N(b['shear']['Q_kg'])})</span>，τ ＝ <b>{b['shear']['tau_kg_cm2']:.1f} kg/cm²</b> ＜ f<sub>s</sub> ＝ {b['shear']['fs_kg_cm2']:.0f} kg/cm² {_v_badge(b['shear']['verdict'])}</div>
    <div class="eq">(4) たわみ：δ ＝ {b['deflection']['delta_w_cm']:.4f} ＋ {b['deflection']['delta_p_cm']:.3f} ＝ <b>{b['deflection']['delta_cm']:.3f} cm</b> ({b['deflection']['delta_mm']:.2f} mm){_defl_badge(b['deflection'])}</div>
    """
    p4 = f"""
    <h2>５．ベースプレート溶接部の検討</h2>
    <div class="flex-row">
      <div>
        <div class="eq">(1) 曲げ（突合せ溶接）：Z ＝ <b>{w['Z_w_cm3']:.1f} cm³</b>，σ<sub>b</sub> ＝ <b>{w['sigma_b_kg_cm2']:.1f} kg/cm²</b> ＜ f<sub>s</sub> ＝ {w['fs_butt_kg_cm2']:.0f} kg/cm² {_v_badge(w['bending_verdict'])}</div>
        <div class="eq">(2) せん断（完全溶込み）：A ＝ 2×{w['L2_cm']:.1f}×{w['a2_cm']:.1f} ＝ {w['A_w_cm2']:.1f} cm²，τ ＝ <b>{w['tau_kg_cm2']:.1f} kg/cm²</b> ＜ f<sub>s</sub> ＝ {w['fs_pen_kg_cm2']:.0f} kg/cm² {_v_badge(w['shear_verdict'])}</div>
        <div class="eq">(3) 複合応力：σ<sub>MQ</sub> ＝ √({w['sigma_b_kg_cm2']:.1f}²＋{w['tau_kg_cm2']:.1f}²) ＝ <b>{w['sigma_MQ_kg_cm2']:.1f} kg/cm²</b> ＜ f<sub>s</sub> ＝ {w['fs_pen_kg_cm2']:.0f} kg/cm² {_v_badge(w['combined_verdict'])}</div>
      </div>
      {svg_weld_detail(w['L1_cm'], w['a1_cm'], w['L2_cm'], w['a2_cm'], w['h_cm'], w['b_cm'])}
    </div>
    <h2>６．アンカーボルトの検討 ({html.escape(a['size'])} 引張{a['tension_count']}本・圧縮{a['compression_count']}本)</h2>
    <div class="eq">(1) せん断：Q<sub>1</sub> ＝ {a['Q1_kg']:.1f} kg，τ ＝ <b>{a['tau_kg_cm2']:.1f} kg/cm²</b> ＜ f<sub>s</sub> ＝ {a['fs_kg_cm2']:.0f} kg/cm² {_v_badge(a['shear_verdict'])}</div>
    <div class="eq">(2) せん断同時引張：j ＝ {a['j_cm']:.2f} cm，T<sub>1</sub> ＝ {a['T1_kg']:.1f} kg，f<sub>ts</sub> ＝ min({a['ft_kg_cm2']:.0f}, {a['fts_calc_kg_cm2']:.1f}) ＝ {a['fts_allow_kg_cm2']:.0f} kg/cm²</div>
    <div class="eq">σ<sub>ts</sub> ＝ <b>{a['sigma_ts_kg_cm2']:.1f} kg/cm²</b> ＜ f<sub>ts</sub> ＝ {a['fts_allow_kg_cm2']:.0f} kg/cm² {_v_badge(a['tension_verdict'])}</div>
    <div class="eq">(3) 必要埋め込み長さ：L ＝ {a['embedment_straight_cm']:.1f} cm（フック付 {a['embedment_hook_cm']:.1f} cm）→ 採用長さ <b>{a['adopted_length_cm']:.1f} cm</b></div>
    """
    p5 = f"""
    <h2>７．コンクリートの圧縮応力度の検討</h2>
    <div class="eq">躯体コンクリート F<sub>c</sub> ＝ {c['Fc_kg_cm2']:.0f} kgf/cm² ({c['Fc_N_mm2']:.0f} N/mm²) ／ 許容圧縮応力度 f<sub>c</sub> ＝ (1/3)F<sub>c</sub>×1.5 ＝ <b>{c['fc_allow_kg_cm2']:.0f} kgf/cm²</b></div>
    <div class="eq">最大圧縮応力度 σ ＝ 4M / (b・h・j) ＝ 4×{b['bending']['M_kg_cm']:.0f} / ({c['bp_width_cm']:.1f}×{c['bp_height_cm']:.1f}×{c['j_cm']:.2f}) ＝ <b>{c['sigma_kg_cm2']:.1f} kg/cm²</b> ＜ f<sub>c</sub> ＝ {c['fc_allow_kg_cm2']:.0f} kg/cm² {_v_badge(c['verdict'])}</div>
    <h2>８．ベースプレートの検討（板厚 t ＝ {bp['thickness_mm']:.0f} mm）</h2>
    <div class="eq">許容曲げ応力度 f<sub>b</sub> ＝ (1/1.3) × {bp['F_kg_cm2']:.0f} × {bp['term_factor']:.2f} ＝ <b>{bp['fb_kg_cm2']:.0f} kg/cm²</b>（中期）</div>
    <h3>(1) 引張側ベースプレート</h3>
    <div class="eq">M ＝ {bp['tension_side']['T1_kg']:.1f} × {bp['tension_side']['L_cm']:.1f} ＝ {bp['tension_side']['M_kg_cm']:.1f} kg・cm，Z ＝ {bp['tension_side']['Z_cm3']:.2f} cm³，σ ＝ <b>{bp['tension_side']['sigma_kg_cm2']:.1f} kg/cm²</b> ＜ f<sub>b</sub> ＝ {bp['fb_kg_cm2']:.0f} kg/cm² {_v_badge(bp['tension_side']['verdict'])}</div>
    <h3>(2) 圧縮側ベースプレート（単位幅 b=1cm）</h3>
    <div class="eq">L ＝ {bp['compression_side']['L_cm']:.1f} cm，σ<sub>2</sub> ＝ {bp['compression_side']['sigma2_kg_cm2']:.1f}，σ<sub>1</sub> ＝ {bp['compression_side']['sigma1_kg_cm2']:.2f} kg/cm²，M ＝ {bp['compression_side']['M_kg_cm']:.1f} kg・cm，Z ＝ {bp['compression_side']['Z_cm3']:.2f} cm³</div>
    <div class="eq">σ ＝ <b>{bp['compression_side']['sigma_kg_cm2']:.1f} kg/cm²</b> ＜ f<sub>b</sub> ＝ {bp['fb_kg_cm2']:.0f} kg/cm² {_v_badge(bp['compression_side']['verdict'])}</div>
    """
    return [
        ("足場受ブラケット:荷重", p1),
        ("足場受ブラケット:大引", p2),
        ("足場受ブラケット:ブラケット", p3),
        ("足場受ブラケット:溶接・アンカー", p4),
        ("足場受ブラケット:コンクリート・BP", p5),
    ]


def _html_tsuri_pages(m: dict[str, Any]) -> list[tuple[str, str]]:
    ov = m["overview"]
    ch = m["chain"]
    pl = m["plank"]
    j = m["joist"]
    g = m["girder"]
    c = m["cantilever"]
    p1 = f"""
    <h1>{html.escape(m['title'])}</h1>
    <div class="flex-row">
      <div>
        <h2>１．設計条件</h2>
        <div class="eq">X方向スパン：{ov['span_x_m']:.3f} m ／ Y方向スパン：{ov['span_y_m']:.3f} m</div>
        <div class="eq">大引間隔：{ov['girder_spacing_m']:.3f} m ／ 根太間隔：{ov['joist_spacing_m']:.3f} m ／ 張出し長さ：{ov['cantilever_length_m']:.3f} m</div>
      </div>
      {svg_tsuri_plan(ov['span_x_m'], ov['span_y_m'], ov['cantilever_length_m'])}
    </div>
    <h2>２．荷重計算・３．吊チェーンの検討</h2>
    {_html_load_table(m['loads']['dead_items'], m['loads']['dead_total_kg'])}
    <div class="eq">積載荷重 ＝ {m['loads']['live_workers_kg']:.0f} ＋ {m['loads']['live_bolts_kg']:.0f} ＝ <b>{m['loads']['live_total_kg']:.0f} kg</b></div>
    <div class="eq">引張力 T ＝ {m['loads']['dead_total_kg']:.1f} ＋ {m['loads']['live_total_kg']:.0f} ＝ <b>{ch['tension_T_kg']:.1f} kg</b> <span class="si">({fmt_N(ch['tension_T_kg'])})</span> ＜ f ＝ {ch['allowable_f_kg']:.0f} kg ({html.escape(ch['member'])}) {_v_badge(ch['verdict'])}</div>
    """
    p2 = f"""
    <h2>４．足場板の検討 ({html.escape(pl['member'])})</h2>
    {svg_simple_beam(f"L = {pl['L_cm']:.0f} cm", True, f"w={pl['w_kg_cm']:.4f}", f"P={pl['P_kg']:.0f}kg")}
    <div class="eq">(1) 曲げ：M ＝ {pl['bending']['M_kg_cm']:.1f} kg・cm，σ<sub>b</sub> ＝ <b>{pl['bending']['sigma_b_kg_cm2']:.1f} kg/cm²</b> ＜ f<sub>b</sub> ＝ {pl['bending']['fb_kg_cm2']:.0f} {_v_badge(pl['bending']['verdict'])}</div>
    <div class="eq">(2) せん断：Q ＝ {pl['shear']['Q_kg']:.1f} kg，τ ＝ <b>{pl['shear']['tau_kg_cm2']:.1f} kg/cm²</b> ＜ f<sub>s</sub> ＝ {pl['shear']['fs_kg_cm2']:.1f} {_v_badge(pl['shear']['verdict'])}</div>
    <div class="eq">(3) たわみ：δ ＝ <b>{pl['deflection']['delta_cm']:.3f} cm</b> ({pl['deflection']['delta_mm']:.2f} mm){_defl_badge(pl['deflection'])}</div>
    <h2>５．根太の検討 ({html.escape(j['member'])})</h2>
    {svg_simple_beam(f"L = {j['L_cm']:.0f} cm", True, f"w={j['w_kg_cm']:.5f}", f"P={j['P_kg']:.1f}kg")}
    <div class="eq">(1) 曲げ：M ＝ {j['bending']['M_kg_cm']:.1f} kg・cm，σ<sub>b</sub> ＝ <b>{j['bending']['sigma_b_kg_cm2']:.1f} kg/cm²</b> ＜ f<sub>b</sub> ＝ {j['bending']['fb_kg_cm2']:.0f} {_v_badge(j['bending']['verdict'])}</div>
    <div class="eq">(2) せん断：Q ＝ {j['shear']['Q_kg']:.1f} kg，τ ＝ <b>{j['shear']['tau_kg_cm2']:.1f} kg/cm²</b> ＜ f<sub>s</sub> ＝ {j['shear']['fs_kg_cm2']:.0f} {_v_badge(j['shear']['verdict'])}</div>
    <div class="eq">(3) たわみ：δ ＝ <b>{j['deflection']['delta_cm']:.3f} cm</b> ({j['deflection']['delta_mm']:.2f} mm){_defl_badge(j['deflection'])}</div>
    """
    p3 = f"""
    <h2>６．大引の検討 ({html.escape(g['member'])})</h2>
    {svg_tsuri_girder_2pt(g['L_cm'], g['a_cm'], g['b_cm'])}
    <div class="eq">P ＝ {g['P_kg']:.1f} kg，w ＝ {g['w_kg_cm']:.4f} kg/cm（大引 {g['girder_self_kg']:.1f} + 根太 {g['joist_self_kg']:.1f} ＝ {g['w_total_kg']:.1f} kg）</div>
    <div class="eq">(1) 曲げ：M ＝ {g['bending']['M_kg_cm']:.1f} kg・cm，σ<sub>b</sub> ＝ <b>{g['bending']['sigma_b_kg_cm2']:.1f} kg/cm²</b> ＜ f<sub>b</sub> ＝ {g['bending']['fb_kg_cm2']:.0f} {_v_badge(g['bending']['verdict'])}</div>
    <div class="eq">(2) せん断：Q ＝ {g['shear']['Q_kg']:.1f} kg，τ ＝ <b>{g['shear']['tau_kg_cm2']:.1f} kg/cm²</b> ＜ f<sub>s</sub> ＝ {g['shear']['fs_kg_cm2']:.0f} {_v_badge(g['shear']['verdict'])}</div>
    <div class="eq">(3) たわみ：δ ＝ {g['deflection']['delta_p_cm']:.3f} ＋ {g['deflection']['delta_w_cm']:.3f} ＝ <b>{g['deflection']['delta_cm']:.3f} cm</b> ({g['deflection']['delta_mm']:.2f} mm){_defl_badge(g['deflection'])}</div>
    <h2>７．張り出し部の検討 ({html.escape(c['member'])})</h2>
    {svg_tsuri_cantilever(c['L_cm'], c['a_cm'])}
    <div class="eq">P<sub>1</sub> ＝ {c['P1_kg']:.1f} kg，P<sub>2</sub> ＝ {c['P2_kg']:.1f} kg，w ＝ {c['w_kg_cm']:.4f} kg/cm</div>
    <div class="eq">(1) 曲げ：M ＝ {c['bending']['M_kg_cm']:.1f} kg・cm，σ<sub>b</sub> ＝ <b>{c['bending']['sigma_b_kg_cm2']:.1f} kg/cm²</b> ＜ f<sub>b</sub> ＝ {c['bending']['fb_kg_cm2']:.0f} {_v_badge(c['bending']['verdict'])}</div>
    <div class="eq">(2) せん断：Q ＝ {c['shear']['Q_kg']:.1f} kg，τ ＝ <b>{c['shear']['tau_kg_cm2']:.1f} kg/cm²</b> ＜ f<sub>s</sub> ＝ {c['shear']['fs_kg_cm2']:.0f} {_v_badge(c['shear']['verdict'])}</div>
    <div class="eq">(3) たわみ：δ ＝ <b>{c['deflection']['delta_cm']:.3f} cm</b> ({c['deflection']['delta_mm']:.2f} mm){_defl_badge(c['deflection'])}</div>
    """
    return [
        ("鉄骨吊り足場:吊りチェーン", p1),
        ("鉄骨吊り足場:足場板", p2.split("<h2>５．")[0]),
        ("鉄骨吊り足場:根太", "<h2>５．" + p2.split("<h2>５．")[1]),
        ("鉄骨吊り足場:大引", p3.split("<h2>７．")[0]),
        ("鉄骨吊り足場:張出部", "<h2>７．" + p3.split("<h2>７．")[1]),
    ]


def _html_nitori_pages(m: dict[str, Any]) -> list[tuple[str, str]]:
    ov = m["overview"]
    d = m["deck"]
    j = m["joist"]
    g = m["girder"]
    b = m["permanent_beam"]
    p1 = f"""
    <h1>{html.escape(m['title'])}</h1>
    <div class="flex-row">
      <div>
        <h2>１．設計条件・２．設計荷重</h2>
        <div class="eq">本設梁方向：{ov['permanent_beam_span_m']:.3f} m ／ 大引方向：{ov['girder_span_m']:.3f} m</div>
        <div class="eq">大引間隔：{ov['girder_spacing_m']:.3f} m ／ 根太間隔：{ov['joist_spacing_m']:.3f} m ／ 構台面積：{ov['platform_area_m2']:.1f} ㎡</div>
        <div class="eq">積載荷重：{ov['live_load_t']:.2f} t ({ov['live_load_kN']:.1f} kN) × 衝撃割増 {ov['impact_factor']:.2f}倍</div>
      </div>
      {svg_nitori_plan(ov['permanent_beam_span_m'], ov['girder_span_m'], ov['platform_area_m2'])}
    </div>
    <h2>３．床板の検討 ({html.escape(d['member'])})</h2>
    {svg_simple_beam(f"L = {d['L_cm']:.0f} cm", False, f"w={d['w_kg_cm']:.2f}kg/cm")}
    <div class="eq">(1) 曲げ：M ＝ {d['bending']['M_kg_cm']:.1f} kg・cm，σ<sub>b</sub> ＝ <b>{d['bending']['sigma_b_kg_cm2']:.1f} kg/cm²</b> ＜ f<sub>b</sub> ＝ {d['bending']['fb_kg_cm2']:.0f} {_v_badge(d['bending']['verdict'])}</div>
    <div class="eq">(2) せん断：Q ＝ {d['shear']['Q_kg']:.1f} kg，τ ＝ <b>{d['shear']['tau_kg_cm2']:.1f} kg/cm²</b> ＜ f<sub>s</sub> ＝ {d['shear']['fs_kg_cm2']:.1f} {_v_badge(d['shear']['verdict'])}</div>
    <div class="eq">(3) たわみ：δ ＝ <b>{d['deflection']['delta_cm']:.3f} cm</b> ({d['deflection']['delta_mm']:.2f} mm){_defl_badge(d['deflection'])}</div>
    """
    p2 = f"""
    <h2>４．根太の検討 ({html.escape(j['member'])})</h2>
    {svg_simple_beam(f"L = {j['L_cm']:.0f} cm", False, f"w={j['w_kg_cm']:.2f}kg/cm")}
    <div class="eq">荷重 w ＝ {j['w_kg_m']:.1f} kg/m ＝ {j['w_kg_cm']:.2f} kg/cm（分担幅 {j['tributary_width_m']:.2f} m）</div>
    <div class="eq">(1) 曲げ：M ＝ {j['bending']['M_kg_cm']:.1f} kg・cm，σ<sub>b</sub> ＝ <b>{j['bending']['sigma_b_kg_cm2']:.1f} kg/cm²</b> ＜ f<sub>b</sub> ＝ {j['bending']['fb_kg_cm2']:.0f} {_v_badge(j['bending']['verdict'])}</div>
    <div class="eq">(2) せん断：Q ＝ {j['shear']['Q_kg']:.1f} kg，τ ＝ <b>{j['shear']['tau_kg_cm2']:.1f} kg/cm²</b> ＜ f<sub>s</sub> ＝ {j['shear']['fs_kg_cm2']:.0f} {_v_badge(j['shear']['verdict'])}</div>
    <div class="eq">(3) たわみ：δ ＝ <b>{j['deflection']['delta_cm']:.3f} cm</b> ({j['deflection']['delta_mm']:.2f} mm){_defl_badge(j['deflection'])}</div>
    """
    p3 = f"""
    <h2>５．大引の検討 ({html.escape(g['member'])})</h2>
    {svg_partial_uniform_beam(g['L_m'], g['a_m'], f"W2={g['W2_kg']:.1f}kg")}
    <div class="eq">W<sub>1</sub> ＝ {g['W1_kg_m']:.2f} kg/m，W<sub>2</sub> ＝ {g['W2_kg']:.1f} kg（載荷範囲 a = {g['a_m']:.3f} m）</div>
    <div class="eq">(1) 曲げ：M ＝ {g['bending']['M1_kg_m']:.1f} ＋ {g['bending']['M2_kg_m']:.1f} ＝ <b>{g['bending']['M_kg_m']:.1f} kg・m</b>，σ<sub>b</sub> ＝ <b>{g['bending']['sigma_b_kg_cm2']:.1f} kg/cm²</b> ＜ f<sub>b</sub> ＝ {g['bending']['fb_kg_cm2']:.0f} {_v_badge(g['bending']['verdict'])}</div>
    <div class="eq">(2) せん断：Q ＝ {g['shear']['Q1_kg']:.1f} ＋ {g['shear']['Q2_kg']:.1f} ＝ <b>{g['shear']['Q_kg']:.1f} kg</b>，τ ＝ <b>{g['shear']['tau_kg_cm2']:.1f} kg/cm²</b> ＜ f<sub>s</sub> ＝ {g['shear']['fs_kg_cm2']:.0f} {_v_badge(g['shear']['verdict'])}</div>
    <div class="eq">(3) たわみ：δ ＝ <b>{g['deflection']['delta_cm']:.3f} cm</b> ({g['deflection']['delta_mm']:.2f} mm){_defl_badge(g['deflection'])}</div>
    """
    p4 = f"""
    <h2>６．本設梁の検討 ({html.escape(b['member'])})</h2>
    {svg_partial_uniform_beam(b['L_m'], b['a_m'], f"W2={b['W2_kg']:.1f}kg")}
    <div class="eq">W<sub>1</sub> ＝ {b['W1_kg_m']:.2f} kg/m，W<sub>2</sub> ＝ {b['girder_max_Q_kg']:.1f} × {b['num_girders_on_beam']}本 ＝ <b>{b['W2_kg']:.1f} kg</b>（載荷範囲 a = {b['a_m']:.3f} m）</div>
    <div class="eq">(1) 曲げ：M ＝ {b['bending']['M1_kg_m']:.1f} ＋ {b['bending']['M2_kg_m']:.1f} ＝ <b>{b['bending']['M_kg_m']:.1f} kg・m</b>，σ<sub>b</sub> ＝ <b>{b['bending']['sigma_b_kg_cm2']:.1f} kg/cm²</b> ＜ f<sub>b</sub> ＝ {b['bending']['fb_kg_cm2']:.0f} {_v_badge(b['bending']['verdict'])}</div>
    <div class="eq">(2) せん断：Q ＝ {b['shear']['Q1_kg']:.1f} ＋ {b['shear']['Q2_kg']:.1f} ＝ <b>{b['shear']['Q_kg']:.1f} kg</b>，τ ＝ <b>{b['shear']['tau_kg_cm2']:.1f} kg/cm²</b> ＜ f<sub>s</sub> ＝ {b['shear']['fs_kg_cm2']:.0f} {_v_badge(b['shear']['verdict'])}</div>
    <div class="eq">(3) たわみ：δ ＝ <b>{b['deflection']['delta_cm']:.3f} cm</b> ({b['deflection']['delta_mm']:.2f} mm){_defl_badge(b['deflection'])}</div>
    """
    return [
        ("荷取り構台:床板", p1),
        ("荷取り構台:根太", p2),
        ("荷取り構台:大引", p3),
        ("荷取り構台:本設梁", p4),
    ]

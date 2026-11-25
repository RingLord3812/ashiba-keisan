"""SUCCES 準拠 工学図面・荷重図 SVG ジェネレーター."""

from __future__ import annotations

from typing import Any


def svg_wakugumi_elevation(ov: dict[str, Any], opening: dict[str, Any] | None) -> str:
    """枠組足場 立面図・壁つなぎ配置・断面図."""
    tiers = min(int(ov["tiers"]), 22)
    bays = 6
    x0, y0 = 95, 22
    bw, bh = 28, max(8, int(190 / max(tiers, 1)))
    total_h = tiers * bh
    total_w = bays * bw
    y_bot = y0 + total_h

    lines: list[str] = []
    # 外枠・建地・布材・筋かい
    open_spans = int(opening["open_spans"]) if opening else 0
    open_tier = int(opening["install_tier"]) if opening else 0
    open_start = 2
    open_end = min(open_start + open_spans, bays - 1) if opening else -1

    for col in range(bays + 1):
        cx = x0 + col * bw
        in_open_col = opening and (open_start < col < open_end)
        col_y_bot = y_bot - open_tier * bh if in_open_col else y_bot
        lines.append(f'<line x1="{cx}" y1="{y0}" x2="{cx}" y2="{col_y_bot}" stroke="#111" stroke-width="1"/>')

    for t in range(tiers + 1):
        ty = y_bot - t * bh
        for b in range(bays):
            bx1 = x0 + b * bw
            bx2 = bx1 + bw
            is_open_cell = opening and (open_start <= b < open_end) and (0 <= t < open_tier)
            if is_open_cell and t > 0:
                continue
            lines.append(f'<line x1="{bx1}" y1="{ty}" x2="{bx2}" y2="{ty}" stroke="#111" stroke-width="0.7"/>')
            if t < tiers and not is_open_cell:
                ty_top = ty - bh
                lines.append(
                    f'<line x1="{bx1}" y1="{ty}" x2="{bx2}" y2="{ty_top}" stroke="#444" stroke-width="0.45"/>'
                    f'<line x1="{bx2}" y1="{ty}" x2="{bx1}" y2="{ty_top}" stroke="#444" stroke-width="0.45"/>'
                )

    # 開口部 梁枠
    if opening:
        oy = y_bot - open_tier * bh
        ox1 = x0 + open_start * bw
        ox2 = x0 + open_end * bw
        lines.append(
            f'<rect x="{ox1}" y="{oy - 4}" width="{ox2 - ox1}" height="8" fill="#d9e2ec" stroke="#111" stroke-width="1.2"/>'
        )

    # 壁つなぎ黒丸
    h_sp = max(int(ov.get("tie_horizontal_spans", 2)), 1)
    v_start = int(ov.get("tie_vertical_start_tier", 2))
    v_step = max(int(ov.get("tie_vertical_tiers", 2)), 1)
    for t in range(v_start, tiers + 1, v_step):
        ty = y_bot - t * bh
        for col in range(0, bays + 1, h_sp):
            if opening and (open_start < col < open_end) and t < open_tier:
                continue
            cx = x0 + col * bw
            lines.append(f'<circle cx="{cx}" cy="{ty}" r="2.6" fill="#111"/>')

    # 右側断面図 (建物躯体 + 足場 + 壁つなぎ)
    sx = x0 + total_w + 55
    lines.append(f'<rect x="{sx + 26}" y="{y0 + 10}" width="55" height="{total_h - 10}" fill="#e5e7eb" stroke="#111" stroke-width="0.9"/>')
    lines.append(f'<rect x="{sx}" y="{y0}" width="14" height="{total_h}" fill="none" stroke="#111" stroke-width="0.9"/>')
    for t in range(v_start, tiers + 1, v_step):
        ty = y_bot - t * bh
        lines.append(f'<line x1="{sx + 14}" y1="{ty}" x2="{sx + 26}" y2="{ty}" stroke="#111" stroke-width="1.2"/>')

    # 寸法線
    dim_x = 42
    lines.append(f'<line x1="{dim_x}" y1="{y0}" x2="{dim_x}" y2="{y_bot}" stroke="#111" stroke-width="0.8"/>')
    lines.append(f'<line x1="{dim_x - 5}" y1="{y0}" x2="{x0 - 8}" y2="{y0}" stroke="#111" stroke-width="0.5"/>')
    lines.append(f'<line x1="{dim_x - 5}" y1="{y_bot}" x2="{sx + 85}" y2="{y_bot}" stroke="#111" stroke-width="0.8"/>')
    lines.append(f'<text x="{dim_x - 4}" y="{(y0 + y_bot) / 2}" text-anchor="end" font-size="10">{ov["scaffold_height_m"]*1000:,.0f}</text>')
    lines.append(f'<text x="{x0 + bw/2}" y="{y_bot + 16}" text-anchor="middle" font-size="9">{ov["bay_span_m"]*1000:.0f}</text>')
    lines.append(f'<text x="{x0 + total_w/2}" y="{y0 - 7}" text-anchor="middle" font-size="9">壁つなぎ ● ({h_sp}スパン×{v_step}段)</text>')

    return (
        f'<svg viewBox="0 0 430 {y_bot + 28}" width="430" height="{y_bot + 28}" '
        f'xmlns="http://www.w3.org/2000/svg" class="eng-svg">'
        + "".join(lines)
        + "</svg>"
    )


def svg_opening_load_diagram() -> str:
    """梁枠開口部の荷重分担図 (W1・W2)."""
    return (
        '<svg viewBox="0 0 180 140" width="180" height="140" xmlns="http://www.w3.org/2000/svg" class="eng-svg">'
        '<rect x="38" y="22" width="16" height="98" fill="#fca5a5" opacity="0.6"/>'
        '<rect x="54" y="22" width="46" height="58" fill="#bfdbfe" opacity="0.55"/>'
        '<line x1="20" y1="120" x2="160" y2="120" stroke="#111" stroke-width="2.5"/>'
        '<rect x="38" y="22" width="16" height="98" fill="none" stroke="#111" stroke-width="1"/>'
        '<rect x="54" y="22" width="90" height="58" fill="none" stroke="#111" stroke-width="1"/>'
        '<rect x="128" y="80" width="16" height="40" fill="none" stroke="#111" stroke-width="1"/>'
        '<rect x="54" y="76" width="74" height="7" fill="#cbd5e1" stroke="#111" stroke-width="1.2"/>'
        '<text x="46" y="15" text-anchor="middle" font-size="10" font-weight="bold">W2</text>'
        '<text x="77" y="15" text-anchor="middle" font-size="10" font-weight="bold">W1</text>'
        '<text x="91" y="106" text-anchor="middle" font-size="9">開口部</text>'
        "</svg>"
    )


def svg_tankan_bracket_detail(L1_m: float, tie_v_m: float) -> str:
    """単管一側ブラケット偏心荷重詳細図."""
    return (
        '<svg viewBox="0 0 210 120" width="210" height="120" xmlns="http://www.w3.org/2000/svg" class="eng-svg">'
        '<line x1="125" y1="10" x2="125" y2="110" stroke="#111" stroke-width="3"/>'
        '<line x1="130" y1="10" x2="130" y2="110" stroke="#111" stroke-width="1"/>'
        '<line x1="35" y1="45" x2="125" y2="45" stroke="#111" stroke-width="2"/>'
        '<line x1="45" y1="45" x2="125" y2="82" stroke="#111" stroke-width="1.4"/>'
        '<line x1="80" y1="16" x2="80" y2="42" stroke="#111" stroke-width="1.3"/>'
        '<polygon points="80,45 76,37 84,37" fill="#111"/>'
        '<text x="80" y="13" text-anchor="middle" font-size="10">P</text>'
        '<line x1="80" y1="95" x2="125" y2="95" stroke="#111" stroke-width="0.8"/>'
        f'<text x="102" y="108" text-anchor="middle" font-size="9">L1={L1_m:.3f}m</text>'
        f'<text x="142" y="56" font-size="9">壁つなぎ間隔</text>'
        f'<text x="142" y="70" font-size="9">L = {tie_v_m:.2f} m</text>'
        "</svg>"
    )


def svg_simple_beam(L_label: str, has_point: bool = True, w_label: str = "w", P_label: str = "P") -> str:
    """単純支持梁 荷重図 (等分布荷重 + 任意中央集中荷重)."""
    point_svg = ""
    if has_point:
        point_svg = (
            '<line x1="120" y1="10" x2="120" y2="46" stroke="#111" stroke-width="1.4"/>'
            '<polygon points="120,48 116,40 124,40" fill="#111"/>'
            f'<text x="128" y="20" font-size="10">{P_label}</text>'
        )
    arrows = "".join(
        f'<line x1="{x}" y1="32" x2="{x}" y2="47" stroke="#333" stroke-width="0.8"/>'
        f'<polygon points="{x},48 {x-2.5},43 {x+2.5},43" fill="#333"/>'
        for x in range(42, 200, 14)
    )
    return (
        '<svg viewBox="0 0 240 92" width="240" height="92" xmlns="http://www.w3.org/2000/svg" class="eng-svg">'
        f'<rect x="35" y="32" width="170" height="16" fill="none" stroke="#333" stroke-width="0.7"/>'
        + arrows
        + point_svg
        + '<line x1="35" y1="48" x2="205" y2="48" stroke="#111" stroke-width="2.2"/>'
        '<polygon points="35,48 29,58 41,58" fill="none" stroke="#111" stroke-width="1.1"/>'
        '<polygon points="205,48 199,58 211,58" fill="none" stroke="#111" stroke-width="1.1"/>'
        '<line x1="35" y1="74" x2="205" y2="74" stroke="#111" stroke-width="0.8"/>'
        f'<text x="120" y="87" text-anchor="middle" font-size="10">{L_label}</text>'
        f'<text x="40" y="26" font-size="9">{w_label}</text>'
        "</svg>"
    )


def svg_girder_multipoint_and_moment(L_m: float, a2_cm: float, n_bays: int = 3) -> str:
    """足場受ブラケット大引の多点集中荷重図と曲げモーメント図."""
    x1, x2 = 30, 210
    span_px = x2 - x1
    step = span_px / max(n_bays, 1)
    pts = [x1 + i * step for i in range(n_bays + 1)]
    p_arrows = "".join(
        f'<line x1="{px:.1f}" y1="12" x2="{px:.1f}" y2="44" stroke="#111" stroke-width="1.3"/>'
        f'<polygon points="{px:.1f},46 {px-3:.1f},39 {px+3:.1f},39" fill="#111"/>'
        for px in pts
    )
    w_arrows = "".join(
        f'<line x1="{x}" y1="30" x2="{x}" y2="45" stroke="#555" stroke-width="0.7"/>'
        for x in range(36, 206, 12)
    )
    m_pts = f"{x1},100 {x1 + step:.1f},134 {x2 - step:.1f},134 {x2},100"
    return (
        '<svg viewBox="0 0 240 155" width="240" height="155" xmlns="http://www.w3.org/2000/svg" class="eng-svg">'
        + w_arrows
        + p_arrows
        + f'<line x1="{x1}" y1="46" x2="{x2}" y2="46" stroke="#111" stroke-width="2.2"/>'
        f'<polygon points="{x1},46 {x1-5},55 {x1+5},55" fill="none" stroke="#111" stroke-width="1"/>'
        f'<polygon points="{x2},46 {x2-5},55 {x2+5},55" fill="none" stroke="#111" stroke-width="1"/>'
        f'<line x1="{x1}" y1="72" x2="{x2}" y2="72" stroke="#111" stroke-width="0.8"/>'
        f'<text x="120" y="84" text-anchor="middle" font-size="9.5">L = {L_m:.3f}m (a2={a2_cm:.0f}cm×{n_bays})</text>'
        f'<polygon points="{m_pts}" fill="#dbeafe" stroke="#111" stroke-width="1.1"/>'
        '<text x="120" y="148" text-anchor="middle" font-size="9">曲げモーメント図 (Ra / Rb)</text>'
        "</svg>"
    )


def svg_cantilever_bracket(L_cm: float, a_cm: float, b_cm: float) -> str:
    """片持ブラケット荷重図 (壁面右固定)."""
    wall_x = 195
    tip_x = 35
    scale = (wall_x - tip_x) / max(L_cm, 1.0)
    x_p2 = wall_x - b_cm * scale
    x_p1 = wall_x - (a_cm + b_cm) * scale
    return (
        '<svg viewBox="0 0 235 108" width="235" height="108" xmlns="http://www.w3.org/2000/svg" class="eng-svg">'
        f'<rect x="{wall_x}" y="12" width="26" height="82" fill="#e5e7eb" stroke="#111" stroke-width="1"/>'
        f'<rect x="{tip_x}" y="44" width="{wall_x - tip_x}" height="12" fill="#f8fafc" stroke="#111" stroke-width="1.5"/>'
        f'<line x1="{x_p1:.1f}" y1="14" x2="{x_p1:.1f}" y2="42" stroke="#111" stroke-width="1.4"/>'
        f'<polygon points="{x_p1:.1f},44 {x_p1-3.5:.1f},36 {x_p1+3.5:.1f},36" fill="#111"/>'
        f'<text x="{x_p1:.1f}" y="11" text-anchor="middle" font-size="9.5">P</text>'
        f'<line x1="{x_p2:.1f}" y1="14" x2="{x_p2:.1f}" y2="42" stroke="#111" stroke-width="1.4"/>'
        f'<polygon points="{x_p2:.1f},44 {x_p2-3.5:.1f},36 {x_p2+3.5:.1f},36" fill="#111"/>'
        f'<text x="{x_p2:.1f}" y="11" text-anchor="middle" font-size="9.5">P</text>'
        f'<line x1="{tip_x}" y1="78" x2="{wall_x}" y2="78" stroke="#111" stroke-width="0.8"/>'
        f'<text x="{(tip_x + wall_x)/2:.1f}" y="91" text-anchor="middle" font-size="9.5">L={L_cm:.0f}cm (a={a_cm:.0f}, b={b_cm:.0f})</text>'
        "</svg>"
    )


def svg_weld_detail(L1: float, a1: float, L2: float, a2: float, h: float, b: float) -> str:
    """H形鋼-ベースプレート溶接部詳細図."""
    return (
        '<svg viewBox="0 0 215 130" width="215" height="130" xmlns="http://www.w3.org/2000/svg" class="eng-svg">'
        '<rect x="55" y="25" width="90" height="8" fill="#cbd5e1" stroke="#111" stroke-width="1.2"/>'
        '<rect x="55" y="95" width="90" height="8" fill="#cbd5e1" stroke="#111" stroke-width="1.2"/>'
        '<rect x="96" y="33" width="8" height="62" fill="#cbd5e1" stroke="#111" stroke-width="1.2"/>'
        '<rect x="62" y="19" width="76" height="6" fill="#93c5fd" stroke="#1d4ed8" stroke-width="0.8"/>'
        '<rect x="62" y="103" width="76" height="6" fill="#93c5fd" stroke="#1d4ed8" stroke-width="0.8"/>'
        '<rect x="91" y="40" width="5" height="48" fill="#93c5fd" stroke="#1d4ed8" stroke-width="0.8"/>'
        '<rect x="104" y="40" width="5" height="48" fill="#93c5fd" stroke="#1d4ed8" stroke-width="0.8"/>'
        f'<text x="100" y="13" text-anchor="middle" font-size="9">L1={L1:.1f} / a1={a1:.1f}</text>'
        f'<text x="155" y="65" font-size="9">L2={L2:.1f}</text>'
        f'<text x="155" y="78" font-size="9">a2={a2:.1f}</text>'
        f'<text x="155" y="52" font-size="9">h={h:.1f}</text>'
        f'<text x="100" y="123" text-anchor="middle" font-size="9">b={b:.1f} cm</text>'
        "</svg>"
    )


def svg_tsuri_plan(span_x: float, span_y: float, cant: float) -> str:
    """鉄骨吊り足場 平面配置図."""
    return (
        '<svg viewBox="0 0 250 165" width="250" height="165" xmlns="http://www.w3.org/2000/svg" class="eng-svg">'
        '<rect x="30" y="25" width="150" height="105" fill="#f8fafc" stroke="#111" stroke-width="1.6"/>'
        '<rect x="180" y="25" width="32" height="105" fill="#fef3c7" stroke="#111" stroke-width="1" stroke-dasharray="3,2"/>'
        '<line x1="65" y1="20" x2="65" y2="135" stroke="#111" stroke-width="1.1"/>'
        '<line x1="105" y1="20" x2="105" y2="135" stroke="#111" stroke-width="1.1"/>'
        '<line x1="145" y1="20" x2="145" y2="135" stroke="#111" stroke-width="1.1"/>'
        '<line x1="25" y1="55" x2="215" y2="55" stroke="#334155" stroke-width="0.9"/>'
        '<line x1="25" y1="78" x2="215" y2="78" stroke="#334155" stroke-width="0.9"/>'
        '<line x1="25" y1="101" x2="215" y2="101" stroke="#334155" stroke-width="0.9"/>'
        f'<text x="105" y="152" text-anchor="middle" font-size="9.5">X = {span_x*1000:.0f} mm</text>'
        f'<text x="196" y="152" text-anchor="middle" font-size="8.5">張出{cant*1000:.0f}</text>'
        f'<text x="234" y="80" text-anchor="middle" font-size="9.5" transform="rotate(-90 234 80)">Y = {span_y*1000:.0f} mm</text>'
        "</svg>"
    )


def svg_tsuri_girder_2pt(L_cm: float, a_cm: float, b_cm: float) -> str:
    """鉄骨吊り足場 大引 2点集中荷重図."""
    return (
        '<svg viewBox="0 0 240 92" width="240" height="92" xmlns="http://www.w3.org/2000/svg" class="eng-svg">'
        '<line x1="35" y1="48" x2="205" y2="48" stroke="#111" stroke-width="2.2"/>'
        '<line x1="58" y1="14" x2="58" y2="45" stroke="#111" stroke-width="1.3"/>'
        '<polygon points="58,47 54,40 62,40" fill="#111"/>'
        '<line x1="182" y1="14" x2="182" y2="45" stroke="#111" stroke-width="1.3"/>'
        '<polygon points="182,47 178,40 186,40" fill="#111"/>'
        '<rect x="35" y="34" width="170" height="14" fill="none" stroke="#555" stroke-width="0.7"/>'
        '<polygon points="35,48 29,58 41,58" fill="none" stroke="#111" stroke-width="1"/>'
        '<polygon points="205,48 199,58 211,58" fill="none" stroke="#111" stroke-width="1"/>'
        f'<text x="120" y="72" text-anchor="middle" font-size="8.5">a={a_cm:.0f} | b={b_cm:.0f} | a={a_cm:.0f}</text>'
        f'<text x="120" y="86" text-anchor="middle" font-size="9.5">L = {L_cm:.0f} cm</text>'
        "</svg>"
    )


def svg_tsuri_cantilever(L_cm: float, a_cm: float) -> str:
    """鉄骨吊り足場 張り出し部 片持梁図."""
    return (
        '<svg viewBox="0 0 220 92" width="220" height="92" xmlns="http://www.w3.org/2000/svg" class="eng-svg">'
        '<line x1="35" y1="18" x2="35" y2="75" stroke="#111" stroke-width="2.2"/>'
        '<line x1="35" y1="46" x2="185" y2="46" stroke="#111" stroke-width="2.2"/>'
        '<line x1="110" y1="14" x2="110" y2="43" stroke="#111" stroke-width="1.4"/>'
        '<polygon points="110,45 106,38 114,38" fill="#111"/>'
        '<text x="110" y="11" text-anchor="middle" font-size="9.5">P2</text>'
        '<line x1="185" y1="14" x2="185" y2="43" stroke="#111" stroke-width="1.4"/>'
        '<polygon points="185,45 181,38 189,38" fill="#111"/>'
        '<text x="185" y="11" text-anchor="middle" font-size="9.5">P1</text>'
        f'<text x="72" y="64" text-anchor="middle" font-size="9">a={a_cm:.0f}cm</text>'
        f'<text x="110" y="84" text-anchor="middle" font-size="9.5">L = {L_cm:.0f} cm</text>'
        "</svg>"
    )


def svg_nitori_plan(beam_span_m: float, girder_span_m: float, area_m2: float) -> str:
    """荷取り構台 平面配置図."""
    return (
        '<svg viewBox="0 0 250 165" width="250" height="165" xmlns="http://www.w3.org/2000/svg" class="eng-svg">'
        '<rect x="30" y="20" width="165" height="110" fill="none" stroke="#111" stroke-width="1.8"/>'
        '<rect x="42" y="34" width="90" height="82" fill="#e0f2fe" stroke="#0369a1" stroke-width="1.2"/>'
        '<line x1="72" y1="20" x2="72" y2="130" stroke="#111" stroke-width="1.2"/>'
        '<line x1="102" y1="20" x2="102" y2="130" stroke="#111" stroke-width="1.2"/>'
        '<line x1="132" y1="20" x2="132" y2="130" stroke="#111" stroke-width="1.2"/>'
        + "".join(
            f'<line x1="42" y1="{y}" x2="132" y2="{y}" stroke="#334155" stroke-width="0.8"/>'
            for y in (50, 66, 82, 98)
        )
        + f'<text x="112" y="150" text-anchor="middle" font-size="9.5">本設梁方向 {beam_span_m*1000:.0f} mm (構台 {area_m2:.1f}㎡)</text>'
        f'<text x="225" y="75" text-anchor="middle" font-size="9.5" transform="rotate(-90 225 75)">大引方向 {girder_span_m*1000:.0f} mm</text>'
        "</svg>"
    )


def svg_partial_uniform_beam(L_m: float, a_m: float, w_label: str) -> str:
    """部分等分布荷重 (長さ a) を受ける単純梁."""
    x1, x2 = 30, 210
    span_px = x2 - x1
    a_px = span_px * min(max(a_m / max(L_m, 0.01), 0.1), 1.0)
    ax1 = x1 + (span_px - a_px) / 2.0
    ax2 = ax1 + a_px
    arrows = "".join(
        f'<line x1="{x:.1f}" y1="26" x2="{x:.1f}" y2="45" stroke="#1d4ed8" stroke-width="0.9"/>'
        f'<polygon points="{x:.1f},47 {x-2.2:.1f},42 {x+2.2:.1f},42" fill="#1d4ed8"/>'
        for x in [ax1 + i * (a_px / 6.0) for i in range(7)]
    )
    return (
        '<svg viewBox="0 0 240 90" width="240" height="90" xmlns="http://www.w3.org/2000/svg" class="eng-svg">'
        f'<rect x="{ax1:.1f}" y="26" width="{a_px:.1f}" height="20" fill="#dbeafe" stroke="#1d4ed8" stroke-width="0.8"/>'
        + arrows
        + f'<line x1="{x1}" y1="47" x2="{x2}" y2="47" stroke="#111" stroke-width="2.2"/>'
        f'<polygon points="{x1},47 {x1-5},56 {x1+5},56" fill="none" stroke="#111" stroke-width="1"/>'
        f'<polygon points="{x2},47 {x2-5},56 {x2+5},56" fill="none" stroke="#111" stroke-width="1"/>'
        f'<text x="120" y="18" text-anchor="middle" font-size="9">{w_label} (a={a_m:.3f}m)</text>'
        f'<text x="120" y="79" text-anchor="middle" font-size="9.5">L = {L_m:.3f} m</text>'
        "</svg>"
    )

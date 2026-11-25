"""足場強度計算 統合CLIエントリーポイント (ashiba-keisan).

Usage:
    python scripts/calculate.py run <input.json> [--out-dir <dir>] [--format all|html|md|json]
                                [--strict-aij] [--deflection-limit <N>]
    python scripts/calculate.py catalog [--category <name>]
    python scripts/calculate.py lookup-wind --location "東京都（23区内）" --terrain 一般市街地
                                --z 27.5 --height 31.0 --length 25.0 --phi 0.7 --position B
                                --tie-h 3.6 --tie-v 3.4 [--planes 2]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# 直接スクリプト実行時 (python scripts/calculate.py) のパッケージ解決
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from scripts.bracket_support import calculate_bracket_connection, calculate_bracket_support
    from scripts.catalog import Catalog
    from scripts.nitori_koudai import calculate_nitori_koudai
    from scripts.report_generator import render_html, render_markdown
    from scripts.tankan_issoku import calculate_tankan_issoku
    from scripts.tsuri_ashiba import calculate_tsuri_ashiba
    from scripts.wakugumi import calculate_wakugumi
    from scripts.wind import calculate_wall_tie_wind
else:
    from .bracket_support import calculate_bracket_connection, calculate_bracket_support
    from .catalog import Catalog
    from .nitori_koudai import calculate_nitori_koudai
    from .report_generator import render_html, render_markdown
    from .tankan_issoku import calculate_tankan_issoku
    from .tsuri_ashiba import calculate_tsuri_ashiba
    from .wakugumi import calculate_wakugumi
    from .wind import calculate_wall_tie_wind


MODULE_DISPATCH = {
    "wakugumi": calculate_wakugumi,
    "tankan_issoku": calculate_tankan_issoku,
    "bracket_support": calculate_bracket_support,
    "tsuri_ashiba": calculate_tsuri_ashiba,
    "nitori_koudai": calculate_nitori_koudai,
}


def run_project(config: dict[str, Any], options: dict[str, Any] | None = None) -> dict[str, Any]:
    """プロジェクト設定辞書に含まれる全モジュールを計算し統合結果を返す."""
    catalog = Catalog()
    opts = dict(config.get("options", {}))
    if options:
        opts.update({k: v for k, v in options.items() if v is not None})

    results: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []

    for mod_cfg in config.get("modules", []):
        mtype = mod_cfg["type"]
        if mtype not in MODULE_DISPATCH:
            raise ValueError(f"未対応のモジュール種別 '{mtype}'。利用可能: {list(MODULE_DISPATCH.keys())}")
        res = MODULE_DISPATCH[mtype](mod_cfg["params"], catalog, opts)
        results.append(res)
        summary_rows.extend(res["summary_rows"])

    return {
        "project": config.get("project", {}),
        "options": opts,
        "modules": results,
        "summary_rows": summary_rows,
        "all_ok": all(r["all_ok"] for r in results),
    }


def _cmd_run(args: argparse.Namespace) -> int:
    in_path = Path(args.input)
    with in_path.open("r", encoding="utf-8") as f:
        cfg = json.load(f)

    opts = {
        "strict_aij": args.strict_aij,
        "deflection_limit": args.deflection_limit,
    }
    report = run_project(cfg, opts)

    out_dir = Path(args.out_dir) if args.out_dir else in_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = args.stem or in_path.stem

    written: list[Path] = []
    fmt = args.format
    if fmt in ("all", "json"):
        p = out_dir / f"{stem}_result.json"
        p.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        written.append(p)
    if fmt in ("all", "md"):
        p = out_dir / f"{stem}_report.md"
        p.write_text(render_markdown(report), encoding="utf-8")
        written.append(p)
    if fmt in ("all", "html"):
        p = out_dir / f"{stem}_report.html"
        p.write_text(render_html(report), encoding="utf-8")
        written.append(p)

    # コンソール要約表示
    print(f"=== 足場計算完了: {report['project'].get('name', stem)} ===")
    print(f"総合判定: {'ＯＫ' if report['all_ok'] else 'ＮＧ'}")
    for row in report["summary_rows"]:
        if row["verdict"]:
            v_txt = row["verdict"]
        else:
            dv = row.get("deflection_verdict")
            dv_txt = f" [{dv}]" if dv else ""
            v_txt = f"M:{row['bending']} Q:{row['shear']} δ:{row['deflection_cm']}cm{dv_txt}"
        r_txt = f" (比 {row['ratio']:.2f})" if row["ratio"] is not None else ""
        print(f"  - [{row['section']}] {row['part']} ({row['member']}): {v_txt}{r_txt}")
    for p in written:
        print(f"出力: {p}")
    return 0 if report["all_ok"] else 2


def _cmd_catalog(args: argparse.Namespace) -> int:
    cat = Catalog()
    if not args.category:
        print("部材カテゴリ (materials.json):", ", ".join(k for k in cat.materials if k != "_meta"))
        print("風荷重テーブル (wind_tables.json):", ", ".join(k for k in cat.wind_tables if k != "_meta"))
        return 0
    if args.category in cat.materials:
        print(json.dumps(cat.materials[args.category], ensure_ascii=False, indent=2))
        return 0
    if args.category in cat.wind_tables:
        print(json.dumps(cat.wind_tables[args.category], ensure_ascii=False, indent=2))
        return 0
    print(f"カテゴリ '{args.category}' が見つかりません。", file=sys.stderr)
    return 1


def _cmd_lookup_wind(args: argparse.Namespace) -> int:
    cat = Catalog()
    res = calculate_wall_tie_wind(
        {
            "location": args.location,
            "terrain": args.terrain,
            "nearby_highrise": args.nearby,
            "eval_height_z_m": args.z,
            "scaffold_height_m": args.height,
            "scaffold_length_m": args.length,
            "solidity_phi": args.phi,
            "position": args.position,
            "tie_horizontal_m": args.tie_h,
            "tie_vertical_m": args.tie_v,
            "wall_tie_material": args.tie_material,
        },
        cat,
        scaffold_planes=args.planes,
    )
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0 if res["verification"]["ok"] else 2


def _cmd_check_connection(args: argparse.Namespace) -> int:
    cat = Catalog()
    brk_mat = cat.get_material("h_beams", args.bracket)
    res = calculate_bracket_connection(
        M_kg_cm=args.moment,
        Q_kg=args.shear,
        bracket_mat=brk_mat,
        weld_cfg={
            "flange_length_cm": args.l1,
            "flange_throat_cm": args.a1,
            "web_length_cm": args.l2,
            "web_throat_cm": args.a2,
        },
        anc_cfg={
            "size": args.bolt,
            "tension_count": args.nt,
            "compression_count": args.nc,
            "tension_bolt_to_center_cm": args.dt,
        },
        conc_cfg={"grade": args.concrete},
        bp_cfg={
            "width_cm": args.bp_w,
            "height_cm": args.bp_h,
            "thickness_mm": args.bp_t,
            "tension_cantilever_cm": args.lt,
            "tension_bolt_pitch_cm": args.pitch,
        },
        catalog=cat,
    )
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0 if res["all_ok"] else 2


def main(argv: list[str] | None = None) -> int:
    # Windows の非UTF-8コンソール (cp1252/cp932等) での日本語出力文字化け・例外を防止
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass

    parser = argparse.ArgumentParser(description="足場強度計算システム CLI (SUCCES Ver 4.11 / 仮設工業会 / AIJ 準拠)")
    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", help="JSON設計条件ファイルから足場強度計算を実行し計算書を出力する")
    p_run.add_argument("input", help="入力JSONファイルパス")
    p_run.add_argument("--out-dir", help="出力ディレクトリ (既定: 入力ファイルと同じフォルダ)")
    p_run.add_argument("--stem", help="出力ファイル名プレフィックス")
    p_run.add_argument("--format", choices=["all", "html", "md", "json"], default="all")
    p_run.add_argument("--strict-aij", action="store_true", help="厳密力学・AIJ理論モードで照査")
    p_run.add_argument("--deflection-limit", type=int, default=None, help="たわみ制限 L/N を追加照査 (例: 200, 300)")
    p_run.set_defaults(func=_cmd_run)

    p_cat = sub.add_parser("catalog", help="登録済みJIS部材・風荷重基準テーブルを照会する")
    p_cat.add_argument("--category", help="表示するカテゴリ名")
    p_cat.set_defaults(func=_cmd_catalog)

    p_wind = sub.add_parser("lookup-wind", help="仮設工業会指針による風荷重・壁つなぎ単体照査を実行する")
    p_wind.add_argument("--location", default="東京都（23区内）")
    p_wind.add_argument("--terrain", default="一般市街地")
    p_wind.add_argument("--nearby", default="無し")
    p_wind.add_argument("--z", type=float, required=True, help="検討地上高さ Z (m)")
    p_wind.add_argument("--height", type=float, required=True, help="足場高さ H (m)")
    p_wind.add_argument("--length", type=float, required=True, help="足場長さ B (m)")
    p_wind.add_argument("--phi", type=float, default=0.70, help="シート充実率 φ")
    p_wind.add_argument("--position", default="B", choices=["A", "B", "C"])
    p_wind.add_argument("--tie-h", type=float, default=3.6, help="壁つなぎ水平間隔 (m)")
    p_wind.add_argument("--tie-v", type=float, default=3.4, help="壁つなぎ垂直間隔 (m)")
    p_wind.add_argument("--planes", type=int, default=2, choices=[1, 2], help="構面数 (2:枠組, 1:単管一側)")
    p_wind.add_argument("--tie-material", default="壁つなぎ専用金具")
    p_wind.set_defaults(func=_cmd_lookup_wind)

    p_conn = sub.add_parser("check-connection", help="作用M・Qからブラケット溶接・アンカー・コンクリート・BPを単体照査する")
    p_conn.add_argument("--bracket", default="H形鋼 300x300x10x15 (SS400)")
    p_conn.add_argument("--moment", type=float, required=True, help="作用曲げモーメント M (kg・cm)")
    p_conn.add_argument("--shear", type=float, required=True, help="作用せん断力 Q (kg)")
    p_conn.add_argument("--l1", type=float, default=28.0, help="フランジ溶接長さ L1 (cm)")
    p_conn.add_argument("--a1", type=float, default=1.0, help="フランジのど厚 a1 (cm)")
    p_conn.add_argument("--l2", type=float, default=24.0, help="ウェブ溶接長さ L2 (cm)")
    p_conn.add_argument("--a2", type=float, default=1.0, help="ウェブのど厚 a2 (cm)")
    p_conn.add_argument("--bolt", default="M20", help="アンカーボルト呼び径")
    p_conn.add_argument("--nt", type=int, default=4, help="引張側ボルト本数")
    p_conn.add_argument("--nc", type=int, default=2, help="圧縮側ボルト本数")
    p_conn.add_argument("--dt", type=float, default=22.5, help="引張ボルト中心〜BP中心距離 (cm)")
    p_conn.add_argument("--concrete", default="Fc27", help="コンクリート設計基準強度区分")
    p_conn.add_argument("--bp-w", type=float, default=50.0, help="ベースプレート幅 b (cm)")
    p_conn.add_argument("--bp-h", type=float, default=60.0, help="ベースプレート高さ h (cm)")
    p_conn.add_argument("--bp-t", type=float, default=25.0, help="ベースプレート板厚 t (mm)")
    p_conn.add_argument("--lt", type=float, default=7.5, help="引張側片持長 L (cm)")
    p_conn.add_argument("--pitch", type=float, default=10.0, help="引張側ボルト間隔 (cm)")
    p_conn.set_defaults(func=_cmd_check_connection)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

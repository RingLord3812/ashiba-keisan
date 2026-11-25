"""エッジケース・非弾性座屈(λ≦Λ)・NG判定・strict-aij・たわみ制限照査テスト."""

from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.calculate import run_project
from scripts.catalog import Catalog
from scripts.tankan_issoku import compute_column_allowable_fc
from scripts.wind import calculate_wall_tie_wind, compute_aspect_ratio_factor_R, compute_basic_wind_coeff_C0


class TestEdgeCasesAndExtensions(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = Catalog()

    def test_wind_c0_and_r_formulas_across_range(self) -> None:
        self.assertEqual(compute_basic_wind_coeff_C0(0.0), 0.0)
        self.assertEqual(compute_basic_wind_coeff_C0(0.70), 1.57)
        self.assertEqual(compute_basic_wind_coeff_C0(0.80), 1.73)
        self.assertEqual(compute_basic_wind_coeff_C0(0.90), 1.87)
        self.assertEqual(compute_basic_wind_coeff_C0(1.00), 2.00)
        # ratio <= 1.5 -> R = 0.60
        self.assertEqual(compute_aspect_ratio_factor_R(10.0, 20.0), 0.60)
        self.assertEqual(compute_aspect_ratio_factor_R(31.0, 25.0), 0.61)
        self.assertEqual(compute_aspect_ratio_factor_R(25.0, 18.5), 0.62)

    def test_typhoon_region_ng_wall_tie(self) -> None:
        """沖縄県・防音シート(φ=1.0)・海岸(I) で壁つなぎ NG を正しく検出する."""
        res = calculate_wall_tie_wind(
            {
                "location": "沖縄県（本島）",
                "terrain": "海岸・海上",
                "eval_height_z_m": 25.0,
                "scaffold_height_m": 30.0,
                "scaffold_length_m": 20.0,
                "solidity_phi": 1.0,
                "position": "B",
                "tie_horizontal_m": 3.6,
                "tie_vertical_m": 3.4,
            },
            self.catalog,
            scaffold_planes=2,
        )
        self.assertEqual(res["velocity_pressure"]["V0_ms"], 22.0)
        self.assertEqual(res["velocity_pressure"]["Ke"], 1.20)
        self.assertFalse(res["verification"]["ok"])
        self.assertEqual(res["verification"]["verdict"], "ＮＧ")

    def test_inelastic_buckling_lambda_le_Lambda(self) -> None:
        """壁つなぎ間隔が短い (L=1.2m) 場合に λ <= Λ 非弾性座屈式が正しく適用される."""
        res = compute_column_allowable_fc(
            E_kg_cm2=2100000.0,
            F_kg_cm2=3300.0,
            buckling_length_m=1.20,
            radius_gyration_cm=1.64,
            term_factor=1.25,
        )
        self.assertEqual(res["regime"], "inelastic_parabolic")
        self.assertLessEqual(res["lambda"], res["Lambda"])
        # λ = 73, Λ = 102 -> (λ/Λ)^2 = 0.5122 -> ν = 1.8415 -> fc_long = 1424.9 -> *1.25 = 1781
        self.assertGreater(res["fc_kg_cm2"], 1500.0)
        self.assertLess(res["fc_kg_cm2"], 2200.0)

    def test_strict_aij_vs_succes_girder_deflection(self) -> None:
        """--strict-aij モードで大引たわみが厳密重ね合わせ (23/648 相当) に切り替わる."""
        cfg_path = ROOT / "examples" / "kts_building_full.json"
        with cfg_path.open("r", encoding="utf-8") as f:
            cfg = json.load(f)
        res_succes = run_project(cfg, {"strict_aij": False})
        res_strict = run_project(cfg, {"strict_aij": True})

        g_succes = [m for m in res_succes["modules"] if m["module"] == "bracket_support"][0]["girder"]
        g_strict = [m for m in res_strict["modules"] if m["module"] == "bracket_support"][0]["girder"]
        # SUCCES 63/1000 -> 0.872cm vs 厳密 23/648 -> 約 0.516cm
        self.assertEqual(g_succes["deflection"]["delta_cm"], 0.872)
        self.assertLess(g_strict["deflection"]["delta_cm"], 0.55)
        self.assertGreater(g_strict["deflection"]["delta_cm"], 0.45)

    def test_deflection_limit_catches_tsuri_girder_87mm(self) -> None:
        """--deflection-limit 300 指定時、PDF p.25 の 87.51mm たわみを自動警告(NG)する."""
        cfg_path = ROOT / "examples" / "kts_building_full.json"
        with cfg_path.open("r", encoding="utf-8") as f:
            cfg = json.load(f)
        res = run_project(cfg, {"deflection_limit": 300})
        self.assertFalse(res["all_ok"])
        tsuri = [m for m in res["modules"] if m["module"] == "tsuri_ashiba"][0]
        chk = tsuri["girder"]["deflection"]["limit_check"]
        self.assertFalse(chk["ok"])
        self.assertEqual(chk["criterion"], "L/300")

    def test_jack_base_extension_limit_enforced(self) -> None:
        """ジャッキベース繰り出し長さ 350mm 超過で法令違反エラーを送出する."""
        with self.assertRaises(ValueError):
            self.catalog.get_jack_base_allowable("BB-35", 400.0)

    def test_custom_h_beam_dynamic_parsing(self) -> None:
        """カタログ外のビルトアップH形鋼文字列を動的に断面計算できる."""
        h = self.catalog.get_material("h_beams", "BH-600x300x12x19 (SM490)")
        self.assertEqual(h["grade"], "SM490")
        self.assertEqual(h["F_kg_cm2"], 3300.0)
        self.assertGreater(h["I_cm4"], 100000.0)

    def test_wakugumi_without_opening(self) -> None:
        """開口部なしの単独枠組足場サンプルが正常完了し全判定 OK・章番号連続."""
        from scripts.report_generator import render_markdown

        with (ROOT / "examples" / "wakugumi_only.json").open("r", encoding="utf-8") as f:
            cfg = json.load(f)
        res = run_project(cfg)
        self.assertTrue(res["all_ok"])
        self.assertIsNone(res["modules"][0]["opening"])
        md = render_markdown(res)
        self.assertIn("### ４．ジャッキベースの検討", md)
        self.assertNotIn("### ５．ジャッキベースの検討", md)

    def test_summary_rows_surface_deflection_warnings_and_clean_si_floats(self) -> None:
        """たわみ制限NGが概要表に表示され、JSON内のSI数値に浮動小数点ノイズが出ない."""
        from scripts.units import kg_cm2_to_N_mm2

        self.assertEqual(str(kg_cm2_to_N_mm2(496.8)), "48.8")
        self.assertEqual(str(kg_cm2_to_N_mm2(900.0)), "88.3")

        with (ROOT / "examples" / "kts_building_full.json").open("r", encoding="utf-8") as f:
            cfg = json.load(f)
        res = run_project(cfg, {"deflection_limit": 300})
        ng_rows = [r for r in res["summary_rows"] if r.get("deflection_verdict") == "警告(ＮＧ)"]
        self.assertEqual(len(ng_rows), 5)

    def test_standalone_bracket_connection_helper(self) -> None:
        """作用M・Qからのブラケット接合部単体照査が PDF p.18-21 と一致する."""
        from scripts.bracket_support import calculate_bracket_connection

        brk = self.catalog.get_material("h_beams", "H形鋼 300x300x10x15 (SS400)")
        conn = calculate_bracket_connection(
            M_kg_cm=417930.0,
            Q_kg=5572.4,
            bracket_mat=brk,
            weld_cfg={"flange_length_cm": 28.0, "flange_throat_cm": 1.0, "web_length_cm": 24.0, "web_throat_cm": 1.0},
            anc_cfg={"size": "M20", "tension_count": 4, "compression_count": 2, "tension_bolt_to_center_cm": 22.5},
            conc_cfg={"grade": "Fc27"},
            bp_cfg={"width_cm": 50.0, "height_cm": 60.0, "thickness_mm": 25.0, "tension_cantilever_cm": 7.5, "tension_bolt_pitch_cm": 10.0},
            catalog=self.catalog,
        )
        self.assertTrue(conn["all_ok"])
        self.assertEqual(conn["weld"]["sigma_MQ_kg_cm2"], 510.2)
        self.assertEqual(conn["anchor_bolt"]["embedment_straight_cm"], 42.4)
        self.assertEqual(conn["concrete"]["sigma_kg_cm2"], 13.1)
        self.assertEqual(conn["base_plate"]["compression_side"]["sigma_kg_cm2"], 1180.9)


if __name__ == "__main__":
    unittest.main()

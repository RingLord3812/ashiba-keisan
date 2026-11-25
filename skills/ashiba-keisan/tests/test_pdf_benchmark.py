"""SUCCES Ver 4.11 出力例 PDF (全31ページ: (仮称)KTSビル新築工事) 完全照合テスト."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.calculate import run_project
from scripts.report_generator import render_html, render_markdown


class TestSUCCESPDFBenchmark(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cfg_path = ROOT / "examples" / "kts_building_full.json"
        with cfg_path.open("r", encoding="utf-8") as f:
            cls.cfg = json.load(f)
        cls.report = run_project(cls.cfg)
        cls.mods = {m["module"]: m for m in cls.report["modules"]}

    def test_overall_ok_and_summary_table_page2(self) -> None:
        """PDF p.2 検討結果概要テーブル 全17行の判定・検定比・たわみ完全一致."""
        self.assertTrue(self.report["all_ok"])
        rows = self.report["summary_rows"]
        self.assertEqual(len(rows), 17)

        expected = [
            ("枠組足場", "壁つなぎ", "ＯＫ", 1.00, None, None, None),
            ("枠組足場", "建枠", "ＯＫ", 0.37, None, None, None),
            ("枠組足場", "梁枠", "ＯＫ", 0.56, None, None, None),
            ("単管一側ブラケット足場", "壁つなぎ", "ＯＫ", 0.83, None, None, None),
            ("単管一側ブラケット足場", "建地", "ＯＫ", 0.75, None, None, None),
            ("単管一側ブラケット足場", "ブラケット上足場板", None, None, "ＯＫ", "ＯＫ", 1.08),
            ("足場受ブラケット", "大引", None, None, "ＯＫ", "ＯＫ", 0.87),
            ("足場受ブラケット", "ブラケット", None, None, "ＯＫ", "ＯＫ", 0.05),
            ("鉄骨吊り足場", "吊りチェーン", "ＯＫ", 0.83, None, None, None),
            ("鉄骨吊り足場", "足場板", None, None, "ＯＫ", "ＯＫ", 0.81),
            ("鉄骨吊り足場", "根太", None, None, "ＯＫ", "ＯＫ", 0.38),
            ("鉄骨吊り足場", "大引", None, None, "ＯＫ", "ＯＫ", 8.75),
            ("鉄骨吊り足場", "張出部", None, None, "ＯＫ", "ＯＫ", 0.36),
            ("荷取り構台", "床板", None, None, "ＯＫ", "ＯＫ", 0.18),
            ("荷取り構台", "根太", None, None, "ＯＫ", "ＯＫ", 0.80),
            ("荷取り構台", "大引", None, None, "ＯＫ", "ＯＫ", 0.38),
            ("荷取り構台", "本設梁", None, None, "ＯＫ", "ＯＫ", 0.01),
        ]
        for row, exp in zip(rows, expected):
            sec, part, verd, ratio, mb, mq, defl = exp
            self.assertEqual(row["section"], sec)
            self.assertEqual(row["part"], part)
            self.assertEqual(row["verdict"], verd)
            self.assertEqual(row["ratio"], ratio)
            self.assertEqual(row["bending"], mb)
            self.assertEqual(row["shear"], mq)
            if defl is None:
                self.assertIsNone(row["deflection_cm"])
            else:
                self.assertAlmostEqual(row["deflection_cm"], defl, delta=0.011)

    def test_module1_wakugumi_pages_3_to_6(self) -> None:
        m = self.mods["wakugumi"]
        # p.4 壁つなぎ
        vp = m["wall_tie"]["velocity_pressure"]
        wf = m["wall_tie"]["wind_force_coeff"]
        wv = m["wall_tie"]["verification"]
        self.assertEqual(vp["V0_ms"], 18.0)
        self.assertEqual(vp["S"], 1.36)
        self.assertEqual(vp["Vz_ms"], 24.5)
        self.assertEqual(vp["qz_kgf_m2"], 37.5)
        self.assertEqual(vp["qz_N_m2"], 368.0)
        self.assertEqual(wf["gamma"], 0.30)
        self.assertEqual(wf["C0"], 1.57)
        self.assertEqual(wf["R"], 0.61)
        self.assertEqual(wf["F"], 1.22)
        self.assertEqual(wf["C"], 1.27)
        self.assertEqual(wv["area_A_m2"], 12.24)
        self.assertEqual(wv["allowable_F_kgf"], 585.0)
        self.assertEqual(wv["load_R_kgf"], 582.9)
        self.assertEqual(wv["load_R_N"], 5720.0)
        self.assertEqual(wv["allowable_F_N"], 5740.0)

        # p.5 建枠
        sf = m["standard_frame"]
        self.assertEqual(sf["dead_total_kg"], 1048.4)
        self.assertEqual(sf["dead_total_N"], 10300.0)
        self.assertEqual(sf["live_total_kg"], 800.0)
        self.assertEqual(sf["total_W_kg"], 1848.4)
        self.assertEqual(sf["total_W_N"], 18200.0)

        # p.6 梁枠を支える建枠 & ジャッキベース
        op = m["opening"]
        self.assertEqual(op["w1_dead_kg"], 1196.5)
        self.assertEqual(op["w1_total_kg"], 1696.5)
        self.assertEqual(op["w1_total_N"], 16700.0)
        self.assertEqual(op["w2_dead_kg"], 698.7)
        self.assertEqual(op["w2_total_kg"], 1098.7)
        self.assertEqual(op["w2_total_N"], 10800.0)
        self.assertEqual(op["total_W_kg"], 2795.2)
        self.assertEqual(op["total_W_N"], 27500.0)

        jb = m["jack_base"]
        self.assertEqual(jb["load_per_jack_kg"], 1397.6)
        self.assertEqual(jb["load_per_jack_N"], 13800.0)
        self.assertEqual(jb["allowable_f_kg"], 2800.0)

    def test_module2_tankan_issoku_pages_7_to_11(self) -> None:
        m = self.mods["tankan_issoku"]
        # p.8 荷重
        self.assertEqual(m["loads"]["axial_dead_kg"], 394.5)
        self.assertEqual(m["loads"]["axial_dead_N"], 3870.0)
        self.assertEqual(m["loads"]["bracket_dead_kg"], 11.12)
        self.assertEqual(m["loads"]["live_load_kg"], 100.0)

        # p.9 壁つなぎ (1構面)
        vp = m["wall_tie"]["velocity_pressure"]
        wf = m["wall_tie"]["wind_force_coeff"]
        wv = m["wall_tie"]["verification"]
        self.assertEqual(vp["S"], 1.25)
        self.assertEqual(vp["Vz_ms"], 22.5)
        self.assertEqual(vp["qz_kgf_m2"], 31.6)
        self.assertEqual(wf["gamma"], None)
        self.assertEqual(wf["R"], 0.62)
        self.assertEqual(wf["C"], 1.26)
        self.assertEqual(wv["load_R_kgf"], 487.3)
        self.assertEqual(wv["load_R_N"], 4790.0)

        # p.10 建地
        st = m["standard_pipe"]
        self.assertEqual(st["N_axial_kg"], 494.50)
        self.assertEqual(st["P_bracket_kg"], 111.12)
        self.assertEqual(st["M_kg_cm"], 2778.0)
        self.assertEqual(st["buckling"]["lambda"], 207)
        self.assertEqual(st["buckling"]["Lambda"], 102)
        self.assertEqual(st["fc_kg_cm2"], 278.0)
        self.assertEqual(st["fb_kg_cm2"], 3000.0)
        self.assertEqual(st["sigma_c_kg_cm2"], 142.0)
        self.assertEqual(st["sigma_b_kg_cm2"], 725.3)
        self.assertEqual(st["ratio_c"], 0.511)
        self.assertEqual(st["ratio_b"], 0.242)
        self.assertEqual(st["combined_ratio"], 0.753)

        # p.11 ブラケット上足場板
        pl = m["plank"]
        self.assertEqual(pl["bending"]["M_kg_cm"], 4662.0)
        self.assertEqual(pl["bending"]["sigma_b_kg_cm2"], 44.8)
        self.assertEqual(pl["shear"]["Q_kg"], 53.6)
        self.assertEqual(pl["shear"]["tau_kg_cm2"], 0.3)
        self.assertEqual(pl["deflection"]["delta_cm"], 1.084)

    def test_module3_bracket_support_pages_12_to_21(self) -> None:
        m = self.mods["bracket_support"]
        # p.13 荷重
        self.assertEqual(m["loads"]["N1_kg"], 774.2)
        self.assertEqual(m["loads"]["N2_kg"], 56.6)
        self.assertEqual(m["loads"]["N3_kg"], 800.0)
        self.assertEqual(m["loads"]["N4_kg_m"], 49.9)

        # p.14-15 大引
        g = m["girder"]
        self.assertEqual(g["P_kg"], 815.4)
        self.assertEqual(g["bending"]["M_kg_cm"], 164960.0)
        self.assertEqual(g["bending"]["sigma_b_kg_cm2"], 349.5)
        self.assertEqual(g["bending"]["ltb"]["Lambda"], 120)
        self.assertEqual(g["bending"]["ltb"]["Fb1_t_cm2"], 1.172)
        self.assertEqual(g["bending"]["ltb"]["Fb2_t_cm2"], 2.000)
        self.assertEqual(g["bending"]["fb_kg_cm2"], 1600.0)
        self.assertEqual(g["shear"]["Q_kg"], 950.1)
        self.assertEqual(g["shear"]["tau_kg_cm2"], 59.4)
        self.assertEqual(g["deflection"]["delta_cm"], 0.872)

        # p.16-17 ブラケット
        b = m["bracket"]
        self.assertEqual(b["P_kg"], 2715.7)
        self.assertEqual(b["bending"]["M_kg_cm"], 417930.0)
        self.assertEqual(b["bending"]["sigma_b_kg_cm2"], 307.3)
        self.assertEqual(b["bending"]["ltb"]["Fb1_t_cm2"], 1.578)
        self.assertEqual(b["bending"]["ltb"]["Fb2_t_cm2"], 5.625)
        self.assertEqual(b["shear"]["Q_kg"], 5572.4)
        self.assertEqual(b["shear"]["tau_kg_cm2"], 185.7)
        self.assertEqual(b["deflection"]["delta_cm"], 0.055)

        # p.18 溶接部
        w = m["weld"]
        self.assertEqual(w["Z_w_cm3"], 841.2)
        self.assertEqual(w["sigma_b_kg_cm2"], 496.8)
        self.assertEqual(w["A_w_cm2"], 48.0)
        self.assertEqual(w["tau_kg_cm2"], 116.1)
        self.assertEqual(w["sigma_MQ_kg_cm2"], 510.2)

        # p.19 アンカーボルト
        a = m["anchor_bolt"]
        self.assertEqual(a["Q1_kg"], 928.7)
        self.assertEqual(a["tau_kg_cm2"], 295.8)
        self.assertEqual(a["j_cm"], 42.5)
        self.assertEqual(a["T1_kg"], 2458.4)
        self.assertEqual(a["fts_calc_kg_cm2"], 1206.7)
        self.assertEqual(a["fts_allow_kg_cm2"], 1200.0)
        self.assertEqual(a["sigma_ts_kg_cm2"], 782.9)
        self.assertEqual(a["embedment_straight_cm"], 42.4)
        self.assertEqual(a["embedment_hook_cm"], 28.3)
        self.assertEqual(a["adopted_length_cm"], 45.0)

        # p.20 コンクリート
        c = m["concrete"]
        self.assertEqual(c["fc_allow_kg_cm2"], 135.0)
        self.assertEqual(c["sigma_kg_cm2"], 13.1)

        # p.21 ベースプレート
        bp = m["base_plate"]
        self.assertEqual(bp["fb_kg_cm2"], 2308.0)
        self.assertEqual(bp["tension_side"]["M_kg_cm"], 18438.0)
        self.assertEqual(bp["tension_side"]["Z_cm3"], 10.42)
        self.assertEqual(bp["tension_side"]["sigma_kg_cm2"], 1769.5)
        self.assertEqual(bp["compression_side"]["sigma1_kg_cm2"], 6.55)
        self.assertEqual(bp["compression_side"]["M_kg_cm"], 1228.1)
        self.assertEqual(bp["compression_side"]["Z_cm3"], 1.04)
        self.assertEqual(bp["compression_side"]["sigma_kg_cm2"], 1180.9)

    def test_module4_tsuri_ashiba_pages_22_to_26(self) -> None:
        m = self.mods["tsuri_ashiba"]
        # p.22 荷重 & 吊チェーン
        self.assertEqual(m["loads"]["dead_total_kg"], 116.7)
        self.assertEqual(m["loads"]["live_total_kg"], 240.0)
        self.assertEqual(m["chain"]["tension_T_kg"], 356.7)
        self.assertEqual(m["chain"]["ratio"], 0.83)

        # p.23 足場板
        pl = m["plank"]
        self.assertEqual(pl["bending"]["M_kg_cm"], 4970.8)
        self.assertEqual(pl["bending"]["sigma_b_kg_cm2"], 47.7)
        self.assertEqual(pl["shear"]["Q_kg"], 72.6)
        self.assertEqual(pl["shear"]["tau_kg_cm2"], 0.4)
        self.assertEqual(pl["deflection"]["delta_cm"], 0.814)

        # p.24 根太
        j = m["joist"]
        self.assertEqual(j["P_kg"], 180.3)
        self.assertEqual(j["bending"]["M_kg_cm"], 8277.9)
        self.assertEqual(j["bending"]["sigma_b_kg_cm2"], 876.9)
        self.assertEqual(j["shear"]["Q_kg"], 93.9)
        self.assertEqual(j["shear"]["tau_kg_cm2"], 34.0)
        self.assertEqual(j["deflection"]["delta_cm"], 0.378)

        # p.25 大引
        g = m["girder"]
        self.assertEqual(g["w_kg_cm"], 0.0906)
        self.assertEqual(g["bending"]["M_kg_cm"], 12890.7)
        self.assertEqual(g["bending"]["sigma_b_kg_cm2"], 1365.5)
        self.assertEqual(g["shear"]["Q_kg"], 206.8)
        self.assertEqual(g["shear"]["tau_kg_cm2"], 74.9)
        self.assertAlmostEqual(g["deflection"]["delta_cm"], 8.751, delta=0.005)
        self.assertEqual(g["deflection"]["summary_cm"], 8.75)

        # p.26 張り出し部
        c = m["cantilever"]
        self.assertEqual(c["P1_kg"], 7.7)
        self.assertEqual(c["P2_kg"], 180.9)
        self.assertEqual(c["bending"]["M_kg_cm"], 10018.0)
        self.assertEqual(c["bending"]["sigma_b_kg_cm2"], 1061.2)
        self.assertEqual(c["shear"]["Q_kg"], 192.7)
        self.assertEqual(c["shear"]["tau_kg_cm2"], 69.8)
        self.assertEqual(c["deflection"]["delta_cm"], 0.360)

    def test_module5_nitori_koudai_pages_27_to_31(self) -> None:
        m = self.mods["nitori_koudai"]
        # p.28 床板
        d = m["deck"]
        self.assertEqual(d["w_kg_m2"], 344.2)
        self.assertEqual(d["w_kg_cm"], 3.44)
        self.assertEqual(d["bending"]["M_kg_cm"], 3483.0)
        self.assertEqual(d["bending"]["sigma_b_kg_cm2"], 26.7)
        self.assertEqual(d["shear"]["Q_kg"], 154.8)
        self.assertEqual(d["shear"]["tau_kg_cm2"], 0.8)
        self.assertEqual(d["deflection"]["delta_cm"], 0.179)

        # p.29 根太
        j = m["joist"]
        self.assertEqual(j["w_kg_m"], 348.3)
        self.assertEqual(j["w_kg_cm"], 3.48)
        self.assertEqual(j["bending"]["M_kg_cm"], 14094.0)
        self.assertEqual(j["bending"]["sigma_b_kg_cm2"], 1493.0)
        self.assertEqual(j["shear"]["Q_kg"], 313.2)
        self.assertEqual(j["shear"]["tau_kg_cm2"], 113.5)
        self.assertEqual(j["deflection"]["delta_cm"], 0.800)

        # p.30 大引
        g = m["girder"]
        self.assertEqual(g["W2_kg"], 2831.9)
        self.assertEqual(g["bending"]["M1_kg_m"], 309.7)
        self.assertEqual(g["bending"]["M2_kg_m"], 2548.7)
        self.assertEqual(g["bending"]["M_kg_m"], 2858.4)
        self.assertEqual(g["bending"]["sigma_b_kg_cm2"], 329.7)
        self.assertEqual(g["shear"]["Q1_kg"], 211.8)
        self.assertEqual(g["shear"]["Q2_kg"], 1742.7)
        self.assertEqual(g["shear"]["Q_kg"], 1954.5)
        self.assertEqual(g["shear"]["tau_kg_cm2"], 86.9)
        self.assertAlmostEqual(g["deflection"]["delta_cm"], 0.375, delta=0.002)

        # p.31 本設梁
        b = m["permanent_beam"]
        self.assertEqual(b["W2_kg"], 5863.5)
        self.assertEqual(b["bending"]["M1_kg_m"], 1528.4)
        self.assertEqual(b["bending"]["M2_kg_m"], 6889.6)
        self.assertEqual(b["bending"]["M_kg_m"], 8418.0)
        self.assertEqual(b["bending"]["sigma_b_kg_cm2"], 57.3)
        self.assertEqual(b["shear"]["Q1_kg"], 940.6)
        self.assertEqual(b["shear"]["Q2_kg"], 4239.8)
        self.assertEqual(b["shear"]["Q_kg"], 5180.4)
        self.assertEqual(b["shear"]["tau_kg_cm2"], 28.8)
        self.assertEqual(b["deflection"]["delta_cm"], 0.015)

    def test_report_rendering_md_and_html(self) -> None:
        md = render_markdown(self.report)
        html_out = render_html(self.report)
        self.assertIn("（仮称）ＫＴＳビル新築工事", md)
        self.assertIn("検討結果概要", md)
        self.assertIn("足　場　計　算　書", html_out)
        self.assertIn("<svg ", html_out)
        self.assertIn("課長", html_out)
        self.assertIn("工事長", html_out)


if __name__ == "__main__":
    unittest.main()

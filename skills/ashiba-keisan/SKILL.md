---
name: ashiba-keisan
description: >-
  Use when performing Japanese scaffolding or temporary structure strength calculations
  (足場計算書, 枠組足場, 単管一側ブラケット足場, 足場受ブラケット, 鉄骨吊り足場, 荷取り構台),
  checking wall ties under wind load (壁つなぎ, 仮設工業会), anchor bolts, welds, or base plates,
  or scaffolding structural design (tính toán giàn giáo, scaffolding calculation, SUCCES, AIJ).
---

# 足場強度計算スキル (ashiba-keisan)

## 概要

日本の建築仮設基準（一般社団法人 仮設工業会『改訂 風荷重に対する足場の安全技術指針』、日本建築学会『鋼構造設計規準』、および **SUCCES for Windows Ver 4.11** 様式）に完全準拠した足場・仮設構台の構造強度計算および「足場計算書」（Markdown / A4印刷対応HTML＋SVG図面 / JSON）の自動生成を行う。すべての計算結果は `kgf/cm²`（併記 `N/mm²`・`N`・`kN・mm`、$g = 9.81$・有効数字3桁切上げ）で出力する。

## 対応モジュールとリファレンス

必要なモジュールのリファレンスのみを参照し、数値計算は必ず同梱の Python エンジンを実行する（暗算・概算は禁止）。

| モジュール種別 (`type`) | 対象構造 | 主な検討項目 | 詳細マニュアル |
| :--- | :--- | :--- | :--- |
| `wakugumi` | 枠組足場 | 壁つなぎ(2構面風荷重)・建枠・梁枠開口部($W_1+W_2$)・ジャッキベース | [wakugumi_ashiba.md](./references/wakugumi_ashiba.md) |
| `tankan_issoku` | 単管一側ブラケット足場 | 荷重・壁つなぎ(1構面風荷重)・建地(座屈＋偏心曲げ中期1.25倍)・足場板 | [tankan_issoku.md](./references/tankan_issoku.md) |
| `bracket_support` | 足場受ブラケット | 荷重・大引(横座屈)・片持ブラケット・溶接部・アンカーボルト(埋込長)・コンクリート支圧・ベースプレート | [ashiba_uke_bracket.md](./references/ashiba_uke_bracket.md) |
| `tsuri_ashiba` | 鉄骨吊り足場 | 荷重・ループ吊りチェーン・足場板・根太・大引(2点集中)・張り出し部 | [tekkotsu_tsuri.md](./references/tekkotsu_tsuri.md) |
| `nitori_koudai` | 荷取り構台 | 衝撃割増(1.1倍)・床板・根太・大引(部分等分布)・本設梁(部分等分布) | [nitori_koudai.md](./references/nitori_koudai.md) |
| 共通風荷重 | 壁つなぎ・風荷重 | 地域別 $V_0$・台風 $K_e$・粗度区分Ⅰ〜Ⅴ $S$・$E_B$・$C_0(\phi)$・$R$・$F$ | [wind_load.md](./references/wind_load.md) |

## 標準実行手順

1. **設計条件の収集とJSON作成**: 現場名・検討場所・各モジュール条件を [kts_building_full.json](./examples/kts_building_full.json) または [wakugumi_only.json](./examples/wakugumi_only.json) の形式で記述する。
2. **部材・風荷重・接合部の単体照査（任意）**:
   ```bash
   python scripts/calculate.py catalog --category h_beams
   python scripts/calculate.py lookup-wind --location "東京都（23区内）" --terrain 一般市街地 --z 27.5 --height 31 --length 25 --phi 0.7 --position B --tie-h 3.6 --tie-v 3.4 --planes 2
   python scripts/calculate.py check-connection --moment 417930 --shear 5572.4 --bolt M20 --nt 4 --nc 2
   ```
3. **構造計算および計算書出力**:
   ```bash
   python scripts/calculate.py run <input.json> --out-dir <out_dir> --format all
   ```
   - 厳密力学・AIJ理論との比較照査が必要な場合: `--strict-aij` を付与する。
   - たわみ制限（例: $L/300$ や $L/200$）を追加照査する場合: `--deflection-limit 300` を付与する。
4. **検証**: 終了コード `0`（全項目ＯＫ）または `2`（ＮＧあり）を確認し、出力された `*_report.html`（ブラウザからA4 PDF印刷可）および `*_report.md` の全数値を依頼者へ提示する。ＮＧまたは過大なたわみ（例: $L/200$ 超）がある場合は部材サイズアップ・スパン短縮・壁つなぎ増設の具体案を併記する。

## 厳守事項・よくある誤り（禁止パターン）

手計算や記憶頼みの計算で以下の誤りが頻発するため、**必ず `python scripts/calculate.py` と `data/*.json` を使用すること**。

| よくある誤り | 正しい基準（SUCCES / 仮設工業会 / AIJ） |
| :--- | :--- |
| 建築基準法の50年再現風速 ($V_0=34\text{m/s}$, $q=0.6EV_0^2$) を流用する | 仮設工業会指針の12ヶ月再現基準風速（東京23区 $V_0=18\text{m/s}$ 等）、$V_z=V_0 K_e S E_B$、$q_z=\frac{1}{16}V_z^2$ を使用する |
| 風力係数を $C = 0.8\phi$ 等と簡略化する | 枠組(2構面)は $C=(0.11+0.09\gamma+0.945C_0 R)F$、単管一側(1構面)は $0.09\gamma$ を除いた $C=(0.11+0.945C_0 R)F$ とする |
| 単管一側建地で中期割増を忘れる、または偏心曲げを $M/2$ とする | STK500 ($F=3300\text{ kg/cm}^2$) に中期係数 **1.25倍** を適用し、偏心曲げは $M=P \cdot L_1$ を全量採用する |
| 溶接部ウェブ面積を片面計算、またはアンカー埋め込み長さを省略する | ウェブ両面 $A=2 a_2 L_2$、複合 $\sigma_{MQ}=\sqrt{\sigma_b^2+\tau^2}\le 800$、アンカー直線埋込長 $L=T_1/(f_a\psi)$（フック付 $\frac{2}{3}L$）を必ず照査する |
| コンクリート支圧・ベースプレートの割増係数を落とす | 支圧は $f_c=\frac{1}{3}F_c\times 1.5$、ベースプレートは中期 $f_b=\frac{1}{1.3}F\times 1.25$ とする |
| 鉄骨吊り足場大引等の過大なたわみ（例: 87.5mm）を見逃す | 曲げ・せん断がＯＫでも、スパンに対してたわみが過大な場合は `--deflection-limit 300` で警告照査し大引補強を提案する |

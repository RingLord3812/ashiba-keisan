# 足場強度計算スキル (ashiba-keisan) — Web Chat AI 用スタンドアロン指示書

> ChatGPT (Custom GPT / Projects)、Claude.ai (Projects)、Gemini Gems、NotebookLM 等の Web AI にそのまま貼り付け、またはナレッジファイルとしてアップロードして使用できます。
> Python 実行環境（Code Interpreter 等）がある場合は、下記数式とカタログデータを用いて高精度に自動計算し、なければ各ステップを検算付きで `kgf/cm² (N/mm²)` 併記（$g=9.81$・有効数字3桁切上げ）で出力してください。

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

---

# 風荷重・壁つなぎ算定リファレンス

準拠基準：一般社団法人 仮設工業会『改訂 風荷重に対する足場の安全技術指針』／ SUCCES Ver 4.11（PDF p.4, p.9）
データソース：[wind_tables.json](../data/wind_tables.json) ／ 計算エンジン：[wind.py](../scripts/wind.py)

---

## １．設計用風速および設計用速度圧

$$V_z = V_0 \times K_e \times S \times E_B \quad [\text{m/s}]$$

$$q_z = \frac{1}{16} V_z^2 \quad [\text{kgf/m}^2] \qquad \left(\text{SI併記: } q_z \times 9.81 \text{ を有効数字3桁切上げ [N/m}^2\text{]}\right)$$

### 1.1 基準風速 $V_0$（再現期間12ヶ月・代表地域）

原則として特記のない地域は **$14\text{ m/s}$** とする。主要地域の基準値（全47都道府県は [wind_tables.json](../data/wind_tables.json) に収録）：

| 地域区分 | $V_0$ (m/s) | 台風時割増係数 $K_e$ |
| :--- | :---: | :---: |
| 東京都（23区内）・横浜/川崎沿岸・千葉県沿岸・渥美半島・淡路島 | 18 | 1.00 |
| 東京都（23区外）・埼玉県・大阪府・愛知県(一般)・静岡県(一般)・兵庫県(一般) | 16 | 1.00 |
| 北海道(一般)・宮城県・長野県・京都府・岡山県・広島県・香川県 | 14 | 1.00 |
| 東京都（島しょ部）・潮岬・室戸/足摺沿岸 | 20 | 1.00 |
| 山口県・福岡県・佐賀県・熊本県・大分県 | 16 | 1.10 |
| 長崎県・宮崎県 | 18 | 1.10 |
| 鹿児島県（本土） | 18 | 1.20 |
| 沖縄県（本島）／ 鹿児島県（離島） | 22 | 1.20 |
| 沖縄県（先島・大東諸島） | 24 | 1.20 |

### 1.2 瞬間風速分布係数 $S$（地表面粗度区分 × 地上高さ $Z$）

| 地上高さ $Z$ (m) | Ⅰ（海岸・海上） | Ⅱ（草原・田園） | Ⅲ（郊外・森） | Ⅳ（一般市街地） | Ⅴ（大都市市街地） |
| :---: | :---: | :---: | :---: | :---: | :---: |
| 0 – 5 | 1.65 | 1.50 | 1.35 | 1.19 | 1.07 |
| 5 – 10 | 1.65 | 1.50 | 1.35 | 1.19 | 1.07 |
| 10 – 15 | 1.74 | 1.62 | 1.47 | 1.25 | 1.07 |
| 15 – 20 | 1.74 | 1.62 | 1.47 | 1.25 | 1.07 |
| 20 – 25 | 1.84 | 1.74 | 1.59 | 1.36 | 1.13 |
| 25 – 30 | 1.84 | 1.74 | 1.59 | 1.36 | 1.13 |
| 30 – 35 | 1.84 | 1.74 | 1.59 | 1.36 | 1.13 |
| 35 – 40 | 1.84 | 1.74 | 1.68 | 1.46 | 1.22 |
| 40 – 50 | 1.92 | 1.85 | 1.68 | 1.46 | 1.22 |
| 50 – 55 | 1.92 | 1.85 | 1.68 | 1.55 | 1.31 |
| 55 – 65 | 1.92 | 1.85 | 1.77 | 1.55 | 1.31 |
| 65 – 70 | 1.99 | 1.92 | 1.77 | 1.55 | 1.31 |
| 70 – 80 | 1.99 | 1.92 | 1.85 | 1.64 | 1.41 |
| 80 – 90 | 2.04 | 1.98 | 1.85 | 1.64 | 1.41 |
| 90 – 100 | 2.04 | 1.98 | 1.92 | 1.72 | 1.49 |

### 1.3 近接高層建築物による影響係数 $E_B$

高さ 50m 以上の高層建築物が近接しない場合は $E_B = 1.00$。近接距離 $L$ に応じて $1.10 \sim 1.30$ を適用する。

---

## ２．風力係数 $C$ の算定

### 2.1 構面数による算定式の違い（重要）

- **枠組足場・本足場（2構面）**:
  $$C = (0.11 + 0.09\gamma + 0.945 C_0 R) \times F \qquad (\gamma = 1 - \phi)$$
- **単管一側ブラケット足場（1構面）**:
  $$C = (0.11 + 0.945 C_0 R) \times F$$

### 2.2 基本風力係数 $C_0$（充実率 $\phi$ より算出）

抵抗係数 $K = \dfrac{1.2\phi}{(1-\phi)^2}$ とし：
- $0 \le K \le 0.73$: $C_0 = \dfrac{K}{(1 + K/4)^2}$
- $K > 0.73$: $C_0 = 2.8\log_{10}\left(K + 0.6 - \sqrt{1.2K+0.36}\right) - 2.8\log_{10}K + 2.0 = 2.8\log_{10}\phi + 2.0$
- $\phi = 1.0$: $C_0 = 2.00$

| 落下物防護材 | 充実率 $\phi$ | 基本風力係数 $C_0$ | 標準単位質量 (kg/m²) |
| :--- | :---: | :---: | :---: |
| メッシュシート（標準） | 0.70 | 1.57 | 0.460 |
| メッシュシート（密目） | 0.80 | 1.73 | 0.500 |
| 防炎メッシュシート | 0.90 | 1.87 | 0.550 |
| 防音シート | 1.00 | 2.00 | 1.100 |
| 防音パネル | 1.00 | 2.00 | 11.000 |

### 2.3 縦横比による形状補正係数 $R$

足場高さ $H$、足場長さ $B$ に対し、地上立上げ時は $\alpha = 2H/B$（地上離隔設置時は $H/B$）：
- $\alpha \le 1.5 \implies R = 0.60$
- $\alpha > 1.5 \implies R = 0.5813 + 0.013\alpha - 0.0001\alpha^2$（上限 1.00）

### 2.4 足場設置位置による補正係数 $F$

| 設置位置区分 | 適用箇所 | 算定式 | $\phi=0.70$ 時 |
| :---: | :--- | :--- | :---: |
| **A** | 独立足場・最上層2層部 | $F = 1.00$ | 1.00 |
| **B** | 建物併設一般部（正圧・標準） | $F = 1.00 + 0.31\phi$ | 1.22 |
| **C** | 建物隅角部（負圧考慮） | $F = 1.00 + 0.38\phi$ | 1.27 |

---

## ３．壁つなぎの強度照査

$$A = L_{\text{水平}} \times L_{\text{垂直}} \quad [\text{m}^2]$$
$$F_{\text{許容}} = F_0 \times 1.3 \quad [\text{kgf}] \quad (\text{風荷重負担のため30％割増し、標準金具 } 450 \times 1.3 = 585\text{ kgf})$$
$$R = q_z \cdot C \cdot A \le F_{\text{許容}} \implies \text{ＯＫ}$$

---

# 枠組足場 強度計算マニュアル

準拠：SUCCES Ver 4.11（PDF p.3–6）／ 労働安全衛生規則・仮設工業会認定基準
計算エンジン：[wakugumi.py](../scripts/wakugumi.py)

---

## １．検討項目一覧

1. **設計条件の整理**: 建物高さ・足場高さ・最下段高さ・段数・建枠寸法（間隔×高さ×巾）・壁つなぎ間隔・開口部梁枠条件。
2. **壁つなぎの検討**: [wind_load.md](./wind_load.md) の 2構面算定式で照査。
3. **建枠の検討（一般部）**: 最下段建枠1枠に作用する固定荷重＋積載荷重が建枠許容圧縮力 $f$ 以下であることを確認。
4. **梁枠を支える建枠の検討（開口部ありの場合）**: 開口部上部からの伝達荷重 $W_1$ と支持建枠自身の分担荷重 $W_2$ の合算を照査。
5. **ジャッキベースの検討**: 支配荷重（一般部と梁枠支持部の大きい方）の 1/2（脚柱1本あたり）が繰り出し長さに応じた許容支持力以下であることを確認。

---

## ２．一般部 建枠の荷重算定

建枠段数を $n$ 段としたとき、最下段建枠1枠あたり（1スパン分担）の固定荷重：
- **建枠**: $w_{\text{枠}} \times n \times 1$
- **布枠**: $w_{\text{布}} \times (n - 1) \times 1$（最下段地上レベルは布枠なし）
- **筋かい**: $w_{\text{筋}} \times n \times 2$（表裏2本）
- **連結ピン**: $w_{\text{ピン}} \times (n - 1) \times 2$
- **アームロック**: $w_{\text{ロック}} \times (n - 1) \times 2$
- **階段**: $w_{\text{階段}} \times n_{\text{階段段数}} \times 1$
- **養生シート**: $w_{\text{シート}} \times L_{\text{スパン}} \times H_{\text{足場}}$

積載荷重は作業床2層同時載荷を標準とする（400 kg × 2層 = 800 kg）。

$$W = W_{\text{固定}} + W_{\text{積載}} \le f_{\text{建枠}} \quad (\text{例: TC-917 は } 5000\text{ kg/枠})$$

---

## ３．開口部（梁枠）を支える建枠の荷重算定

開口スパン数 $m$（例: 3スパン = 5.400m、SPL-54）、梁枠設置段数 $k$ 段、上部段数 $n_{\text{上}} = n - k$ 段のとき：

### 3.1 梁枠上の荷重 $W_1$（片側支持建枠への伝達分）
- 梁枠上の中間建枠列数 = $m - 1$ 列 → 片側支持建枠の負担比 = $(m - 1)/2$
- 布枠・筋かい・階段・養生シートの負担スパン数 = $m / 2$ スパン
- 梁枠上シート高さ（SUCCES規約）: $H_{\text{上}} = H_{\text{足場}} - k \times H_{\text{建枠}}$
- 梁枠上積載荷重（例: 1000 kg）の 1/2 を加算：
  $$W_1 = W_{1,\text{固定}} + \frac{W_{\text{梁枠積載}}}{2}$$

### 3.2 支持建枠自身の荷重 $W_2$
- 建枠・連結ピン・アームロックは全量（1列分）
- 布枠・筋かい・階段・養生シートおよび一般部積載荷重は隣接側 1/2 スパン分を加算：
  $$W_2 = W_{2,\text{固定}} + \frac{W_{\text{一般積載}}}{2}$$

### 3.3 照査
$$W_{\text{合計}} = W_1 + W_2 \le f_{\text{建枠}}$$

---

## ４．ジャッキベースの検討

建枠は2本の脚柱で支持されるため、ジャッキベース1本あたりの鉛直力：
$$N = \frac{\max(W_{\text{一般}}, W_{\text{合計}})}{2} \le f_{\text{ジャッキ}}$$

### ジャッキベース（BB-35）繰り出し長さ別許容支持力
- 法令上限：**350 mm 以下**（200 mm 超の場合は水平つなぎ等の座屈防止措置が必要）
- 100 mm 以下: **2,800 kg** (27,500 N) ／ 150 mm: 2,500 kg ／ 200 mm: 2,175 kg ／ 250 mm: 2,075 kg ／ 300 mm: 1,975 kg ／ 350 mm: 1,900 kg

---

# 単管一側ブラケット足場 強度計算マニュアル

準拠：SUCCES Ver 4.11（PDF p.7–11）／ 日本建築学会『鋼構造設計規準』
計算エンジン：[tankan_issoku.py](../scripts/tankan_issoku.py)

---

## １．荷重算定（建地1本あたり）

段数を $n$ 段、足場板・手摺・ブラケット段数を $n_{\text{床}} = n - 1$ 段としたとき：
1. **建地最下段の固定荷重**:
   - 建地パイプ（全長 $H_{\text{足場}}$ × 1本）
   - 布パイプ（建地間隔 $L_s$ × $n$ 段）
   - 足場板・手摺パイプ・足場板受ブラケット（各 $n_{\text{床}}$ 段）
   - 養生シート（$L_s \times H_{\text{足場}}$）
   - 筋かいパイプ（斜長 $\sqrt{2} L_s$ × 所定段数）
2. **ブラケット1組の固定荷重**: ブラケット自重 ＋ 足場板1スパン自重。
3. **積載荷重**: 建地1本あたり 100 kg（標準）。

---

## ２．壁つなぎの検討（1構面）

一側足場は単一構面であるため、第2構面低減項 $0.09\gamma$ を含まない式を用いる（[wind_load.md](./wind_load.md) 参照）：
$$C = (0.11 + 0.945 C_0 R) \times F$$

---

## ３．建地パイプの検討（圧縮＋偏心曲げ 複合応力検定）

標準材：単管 $\phi 48.6 \times 2.4$（STK500）：$A = 3.483\text{ cm}^2$, $Z = 3.830\text{ cm}^3$, $i = 1.64\text{ cm}$, $E = 2.1 \times 10^6\text{ kg/cm}^2$, $F = 3300\text{ kg/cm}^2$, 長期 $f_b = 2400\text{ kg/cm}^2$。

### 3.1 作用応力
- 軸圧縮力：$N = W_{\text{建地固定}} + W_{\text{積載}}$，$\sigma_c = \dfrac{N}{A}$
- ブラケット偏心曲げモーメント（偏心距離 $L_1$ [m]）：
  $$P = W_{\text{ブラケット固定}} + W_{\text{積載}}, \qquad M = P \cdot L_1 \times 100 \quad [\text{kg}\cdot\text{cm}], \qquad \sigma_b = \frac{M}{Z}$$
  （※SUCCES準拠では $M$ を上下分配せず安全側に全量作用させる。）

### 3.2 許容応力度（仮設中期割増 1.25倍）
座屈長さ $L$ = 壁つなぎ垂直間隔 [m] とし、細長比 $\lambda = \dfrac{100 L}{i}$、限界細長比 $\Lambda = \pi\sqrt{\dfrac{E}{0.6 F}}$：
- **弾性座屈域（$\lambda > \Lambda$）**:
  $$f_c = \frac{0.277 F}{(\lambda / \Lambda)^2} \times 1.25$$
- **非弾性座屈域（$\lambda \le \Lambda$）**（壁つなぎ間隔が短い場合）:
  $$\nu = \frac{3}{2} + \frac{2}{3}\left(\frac{\lambda}{\Lambda}\right)^2, \qquad f_c = \frac{1 - 0.4(\lambda/\Lambda)^2}{\nu} F \times 1.25$$
- **許容曲げ応力度**: $f_b = f_{b,\text{長期}} \times 1.25$（STK500では $2400 \times 1.25 = 3000\text{ kg/cm}^2$）

### 3.3 複合応力検定
$$\frac{\sigma_c}{f_c} + \frac{\sigma_b}{f_b} \le 1.0 \implies \text{ＯＫ}$$

---

## ４．ブラケット上の足場板の検討

単純支持梁（スパン $L$ = 建地間隔 [cm]、中央集中荷重 $P$ + 自重等分布荷重 $w$）として照査（断面性能は1m幅あたり）：
- 曲げ：$M = \dfrac{PL}{4} + \dfrac{wL^2}{8}$，$\sigma_b = \dfrac{M}{Z} \le f_b$（合板長期 $165\text{ kg/cm}^2$）
- せん断：$Q = \dfrac{P}{2} + \dfrac{wL}{2}$，$\tau = \dfrac{\kappa Q}{A} \le f_s$（矩形 $\kappa = 1.5$、合板長期 $10.5\text{ kg/cm}^2$）
- たわみ：$\delta = \dfrac{PL^3}{48EI} + \dfrac{5wL^4}{384EI}$

---

# 足場受ブラケット 強度計算マニュアル

準拠：SUCCES Ver 4.11（PDF p.12–21）／ 日本建築学会『鋼構造設計規準』
計算エンジン：[bracket_support.py](../scripts/bracket_support.py)

---

## １．荷重区分

1. **$N_1$（建枠1スパンあたり荷重）**: 建枠・布枠・筋かい・連結ピン・アームロック・階段・養生シートの合計。
2. **$N_2$（最下部荷重）**: ジャッキベース2個・根がらみ2本・足場板2枚・根太（端太角）2本の合計。
3. **$N_3$（積載荷重）**: 標準 400 kg × 2層 = 800 kg。
4. **$N_4$（大引自重）**: 使用H形鋼の単位質量 [kg/m]。

---

## ２．大引の検討（単純支持H形鋼・横座屈考慮）

ブラケット直上の建枠荷重は応力算出上除外し、大引本数 $n_g$（通常2本）で分担する：
$$P = \frac{1}{n_g}(N_1 + N_2 + N_3), \qquad w = \frac{N_4}{100} \quad [\text{kg/cm}]$$

### 2.1 曲げ・横座屈照査（AIJ鋼構造設計規準）
- 3スパン載荷（中間建枠2点、間隔 $a_2 = L/3$）のとき $R_a = R_b = P$、$M = a_2 R_b + \dfrac{1}{8}wL^2$、$\sigma_b = M/Z$。
- 限界細長比 $\Lambda = \sqrt{\dfrac{E\pi^2}{0.6F}}$（SS400では $\Lambda = 120$）：
  $$F_{b1} = \left(1 - 0.4\frac{(L_b / i)^2}{C\Lambda^2}\right) f_t, \qquad F_{b2} = \frac{900}{L_b \cdot h / A_f} \quad [\text{t/cm}^2]$$
  $$f_b = \min\bigl(f_t,\; \max(F_{b1}, F_{b2})\bigr) \times 1000 \quad [\text{kg/cm}^2]$$
  （単純支持大引では $L_b = L$, $C = 1.0$、SS400長期 $f_t = 1.6\text{ t/cm}^2 = 1600\text{ kg/cm}^2$）

### 2.2 せん断・たわみ
- $Q = R_a + \dfrac{1}{2}wL$，$\tau = \dfrac{Q}{h \cdot t_w} \le f_s$（SS400長期 $900\text{ kg/cm}^2$）
- たわみ：
  - **SUCCES標準モード**: $\delta = \dfrac{63 P L^3}{1000 E I} + \dfrac{5 w L^4}{384 E I}$（安全側多点載荷係数）
  - **厳密AIJモード (`--strict-aij`)**: $\delta = \sum \dfrac{P a_j (3L^2 - 4a_j^2)}{48 E I} + \dfrac{5 w L^4}{384 E I}$

---

## ３．足場受ブラケットの検討（片持梁H形鋼）

壁面から内側大引まで $b$、建枠幅 $a$、片持全長 $L$、1スパンあたり建枠数 $P_n$、大引本数 $P_o$：
$$P = \frac{1}{2}\left\{(N_1 + N_2 + N_3) P_n + N_4 L_{\text{span}} P_o\right\}$$
- **曲げ**: $M = (a+b)P + bP + \dfrac{1}{2}wL^2$，$\sigma_b = M/Z \le f_b$（片持横座屈 $L_b = 1.6L$, $C = 1.75$）
- **せん断**: $Q = 2P + wL$，$\tau = \dfrac{Q}{h \cdot t_w} \le f_s$
- **先端たわみ**: $\delta = \dfrac{wL^4}{8EI} + \dfrac{P}{6EI}\left\{(a+b)^2(3L-a-b) + b^2(3L-b)\right\}$

---

## ４．ベースプレート溶接部の検討

- **フランジ突合せ溶接**（溶接長 $L_1$, のど厚 $a_1$, 許容応力度 $f_s = 1400\text{ kg/cm}^2$）:
  $$Z_w = \frac{L_1}{6(h + 2a_1)}\left\{(h + 2a_1)^3 - h^3\right\}, \qquad \sigma_b = \frac{M}{Z_w} \le 1400$$
- **ウェブ完全溶込み溶接（両面）**（溶接長 $L_2$, のど厚 $a_2$, 許容応力度 $f_s = 800\text{ kg/cm}^2$）:
  $$A_w = 2 a_2 L_2, \qquad \tau = \frac{Q}{A_w} \le 800$$
- **複合応力**:
  $$\sigma_{MQ} = \sqrt{\sigma_b^2 + \tau^2} \le 800\text{ kg/cm}^2$$

---

## ５．アンカーボルトの検討

引張側 $n_t$ 本、圧縮側 $n_c$ 本、断面積 $A$、周長 $\psi$（M20: $A=3.14\text{ cm}^2, \psi=6.44\text{ cm}$、長期 $f_s=900, f_t=1200\text{ kg/cm}^2$）：
1. **せん断**: $Q_1 = \dfrac{Q}{n_t + n_c}$，$\tau = \dfrac{Q_1}{A} \le f_s$
2. **せん断同時引張**: 応力中心間距離 $j = d_t + \dfrac{h_{\text{BP}}}{2}\times\dfrac{2}{3}$（下半分三角形圧縮分布仮定）：
   $$T_1 = \frac{M}{j \cdot n_t}, \qquad f_{ts} = \min\bigl(f_t,\; 1.4 f_t - 1.6\tau\bigr), \qquad \sigma_{ts} = \frac{T_1}{A} \le f_{ts}$$
3. **必要埋め込み長さ**: 許容付着応力度 $f_a$（$F_c=270$ で $9.0\text{ kg/cm}^2$）：
   $$L_{\text{直線}} = \frac{T_1}{f_a \cdot \psi}, \qquad L_{\text{フック付}} = \frac{2}{3} L_{\text{直線}}$$
   余裕を見て 5cm 刻みで切り上げた長さを採用する（例: 42.4cm → 45.0cm）。

---

## ６．コンクリートの圧縮応力度の検討

$$f_c = \frac{1}{3} F_c \times 1.5 \quad (\text{支圧割増1.5倍、}F_c=270 \implies 135\text{ kgf/cm}^2)$$
$$\sigma = \frac{4M}{b_{\text{BP}} \cdot h_{\text{BP}} \cdot j} \le f_c$$

---

## ７．ベースプレートの検討（板厚 $t$）

許容曲げ応力度（中期）：$f_b = \dfrac{1}{1.3} F \times 1.25$（SS400 $F=2400 \implies 2308\text{ kg/cm}^2$）。
1. **引張側片持梁**（ボルト間隔 $b_{\text{pitch}}$, フランジ面〜ボルト距離 $L_t$）:
   $$M = T_1 \cdot L_t, \qquad Z = \frac{b_{\text{pitch}} t^2}{6}, \qquad \sigma = \frac{M}{Z} \le f_b$$
2. **圧縮側片持梁（単位幅 $b = 1\text{ cm}$、台形支圧分布）**（張出長 $L_c$, 最大応力 $\sigma_2=\sigma$, フランジ面応力 $\sigma_1$）:
   $$M = \frac{1}{2}\sigma_1 L_c^2 + \frac{1}{3}(\sigma_2 - \sigma_1) L_c^2, \qquad Z = \frac{1 \cdot t^2}{6}, \qquad \sigma = \frac{M}{Z} \le f_b$$

---

# 鉄骨吊り足場 強度計算マニュアル

準拠：SUCCES Ver 4.11（PDF p.22–26）
計算エンジン：[tsuri_ashiba.py](../scripts/tsuri_ashiba.py)

---

## １．構造モデルと荷重

鉄骨本設梁（スパン $X \times Y$）から吊りチェーンで大引を吊り、その上に根太・足場板・水平養生ネットを敷設する構造。張り出し部より中央部の荷重が大きいため、吊りチェーンは中央部で照査する。

- **固定荷重（大引1本当り）**: 足場板 ＋ 根太パイプ ＋ 大引パイプ ＋ 水平ネット（ラッセルネット 0.320 kg/m²）
- **積載荷重（1スパン当り）**: 作業員 80 kg × 2人 ＋ ボルト類 40 kg × 2 = 240 kg

---

## ２．吊りチェーンの検討

$$T = W_{\text{固定}} + W_{\text{積載}} \le f_{\text{吊り}} \quad (\text{ループ吊り標準 } f = 430\text{ kg})$$

---

## ３．足場板・根太の検討（単純支持：中央集中荷重＋等分布自重）

| 部位 | スパン $L$ | 集中荷重 $P$ | 自重 $w$ | 代表部材 |
| :--- | :--- | :--- | :--- | :--- |
| **足場板** | 根太間隔 | 作業員 80 + ボルト 40 = 120 kg | 足場板自重 (1m幅) | 足場板 25×240 合板 ($\kappa=1.5$) |
| **根太** | 大引間隔 | 作業員 80 + ボルト 40 + 足場板質量 | 根太単体自重 | 角パイプ 60×60 STKR400 ($\kappa=1.0$) |

$$M = \frac{PL}{4} + \frac{wL^2}{8}, \qquad Q = \frac{P}{2} + \frac{wL}{2}, \qquad \delta = \frac{PL^3}{48EI} + \frac{5wL^4}{384EI}$$
（※角パイプ 60×60×2.3 のせん断有効断面積は両ウェブ分 $A = 2 \times 6.0 \times 0.23 = 2.760\text{ cm}^2$、$\kappa = 1.0$ を採用する。）

---

## ４．大引の検討（単純支持：対称2点集中荷重＋等分布荷重）

支点から足場板中心（荷重作用点）までの離れを $a$、中央区間長を $b = L - 2a$ とする：
- 等分布荷重 $w$ = (大引自重 + 根太総自重) / $L$
- **曲げ**: $M = P a + \dfrac{wL^2}{8}$，$\sigma_b = M/Z \le f_b$
- **せん断**: $Q = P + \dfrac{wL}{2}$，$\tau = \kappa Q / A \le f_s$
- **たわみ**:
  $$\delta = \frac{PL^3}{48EI}\left\{\left(\frac{b}{L}\right)^3 - 3\left(\frac{b}{L}\right)^2 + 2\right\} + \frac{5wL^4}{384EI}$$

> **実務上の重要注意（たわみ管理）**: SUCCES サンプル（PDF p.25）のように 60×60 角パイプを $L = 5.85\text{ m}$ 無中間吊りで用いると、曲げ・せん断はＯＫでもたわみが **8.75 cm（$L/67$）** と過大になる。実設計では必ず `--deflection-limit 300`（または `200`）を併用し、超過時は中間吊りチェーン追加または大引断面アップ（75×75 / 100×100 / H形鋼）を検討すること。

---

## ５．張り出し部の検討（片持梁）

片持長 $L$、先端集中荷重 $P_1$（手摺＋手摺柱＋端部根太）、中間点 $a$（先端まで $b = L - a$）の集中荷重 $P_2$（作業員＋ボルト＋足場板＋ネット）、自重 $w$：
- **曲げ**: $M = P_1 L + P_2 a + \dfrac{wL^2}{2}$
- **せん断**: $Q = P_1 + P_2 + wL$
- **先端たわみ**:
  - SUCCES標準: $\delta = \dfrac{P_1 L^3}{3EI} + \dfrac{P_2 a^3}{3EI}\left(1 + \dfrac{3b}{2a}\right)$
  - 厳密AIJ (`--strict-aij`): 上式に自重項 $+\dfrac{wL^4}{8EI}$ を加算。

---

# 荷取り構台 強度計算マニュアル

準拠：SUCCES Ver 4.11（PDF p.27–31）
計算エンジン：[nitori_koudai.py](../scripts/nitori_koudai.py)

---

## １．設計荷重（衝撃割増し考慮）

積載荷重 $W_{\text{積載}}$ [kg]（例: 5.00 t = 5000 kg）、構台面積 $A_{\text{構台}}$ [m²]、衝撃割増係数 $\alpha_{\text{imp}} = 1.10$（標準）、床板自重 $w_{\text{床}}$ [kg/m²] に対し、床板単位面積あたり設計荷重：

$$w_{\text{面}} = \frac{W_{\text{積載}} \times \alpha_{\text{imp}}}{A_{\text{構台}}} + w_{\text{床}} \quad [\text{kg/m}^2]$$

---

## ２．床板・根太の検討（単純支持・等分布荷重）

### 2.1 床板（スパン $L$ = 根太間隔 [cm]、1m幅あたり）
$$w = \frac{w_{\text{面}}}{100} \quad [\text{kg/cm}]$$
$$M = \frac{wL^2}{8}, \qquad Q = \frac{wL}{2}, \qquad \tau = \frac{\kappa Q}{A}, \qquad \delta = \frac{5wL^4}{384EI}$$

### 2.2 根太（スパン $L$ = 大引間隔 [cm]）
- **SUCCES標準モード**: 安全側として分担幅 **1.0 m** を採用し $w_{\text{根太}} = w_{\text{面}} \times 1.0 + w_{\text{根太自重}}$。
- **厳密AIJモード (`--strict-aij`)**: 実配置間隔（根太間隔 $s_j$）を乗じて $w_{\text{根太}} = w_{\text{面}} \cdot s_j + w_{\text{根太自重}}$。

---

## ３．大引・本設梁の検討（単純支持・部分等分布荷重）

全スパン $L$ [m] に自重 $W_1$ [kg/m] が等分布し、載荷範囲 $a$ [m] に上部からの伝達総荷重 $W_2$ [kg] が部分等分布するモデル：

- **大引の $W_2$**: $W_2 = w_{\text{面}} \times s_{\text{大引}} \times a_{\text{大引}} + w_{\text{根太自重}} \times s_{\text{大引}} \times n_{\text{根太本数}}$
- **本設梁の $W_2$**: $W_2 = Q_{\text{大引最大}} \times n_{\text{大引本数}}$

### 3.1 曲げモーメント（中央対称載荷で最大）
$$M_1 = \frac{W_1 L^2}{8}, \qquad M_2 = \frac{W_2 (2L - a)}{8}, \qquad M = M_1 + M_2 \quad [\text{kg}\cdot\text{m}]$$
$$\sigma_b = \frac{M \times 100}{Z} \le f_b$$

### 3.2 せん断力（支点片寄せ載荷で最大）
$$Q_1 = \frac{W_1 L}{2}, \qquad Q_2 = \frac{W_2 (L - a/2)}{L}, \qquad Q = Q_1 + Q_2 \quad [\text{kg}]$$
$$\tau = \frac{Q}{t_w \cdot h} \le f_s$$

### 3.3 たわみ（全スパン等分布換算）
$$w_1 = \frac{W_1}{100}, \qquad w_2 = \frac{W_2}{100 L} \quad [\text{kg/cm}], \qquad \delta = \frac{5(w_1 + w_2)(100 L)^4}{384 E I}$$

---

# 付録：標準部材・地域風速データ抜粋（JSON 原本準拠）

## 建枠・布枠・筋かい・梁枠・ジャッキベース
```json
{
  "frames": {
    "TC-917": {
      "display_name": "TC-917 ( 900-1700)",
      "width_m": 0.9,
      "height_m": 1.7,
      "weight_kg": 15.9,
      "allowable_compression_kg": 5000.0
    },
    "TC-617": {
      "display_name": "TC-617 ( 600-1700)",
      "width_m": 0.6,
      "height_m": 1.7,
      "weight_kg": 14.3,
      "allowable_compression_kg": 5000.0
    },
    "TC-1217": {
      "display_name": "TC-1217 (1200-1700)",
      "width_m": 1.2,
      "height_m": 1.7,
      "weight_kg": 17.5,
      "allowable_compression_kg": 5000.0
    },
    "FT-917": {
      "display_name": "FT-917 ( 900-1700)",
      "width_m": 0.9,
      "height_m": 1.7,
      "weight_kg": 16.5,
      "allowable_compression_kg": 4350.0
    },
    "FT-617": {
      "display_name": "FT-617 ( 600-1700)",
      "width_m": 0.6,
      "height_m": 1.7,
      "weight_kg": 14.8,
      "allowable_compression_kg": 4350.0
    },
    "FT-1217": {
      "display_name": "FT-1217 (1200-1700)",
      "width_m": 1.2,
      "height_m": 1.7,
      "weight_kg": 18.2,
      "allowable_compression_kg": 4350.0
    }
  },
  "ledgers": {
    "SYi-518": {
      "display_name": "SYi-518",
      "span_m": 1.8,
      "width_m": 0.5,
      "weight_kg": 23.0
    },
    "SYi-515": {
      "display_name": "SYi-515",
      "span_m": 1.5,
      "width_m": 0.5,
      "weight_kg": 19.5
    },
    "SYi-512": {
      "display_name": "SYi-512",
      "span_m": 1.2,
      "width_m": 0.5,
      "weight_kg": 16.0
    },
    "SYi-418": {
      "display_name": "SYi-418",
      "span_m": 1.8,
      "width_m": 0.4,
      "weight_kg": 18.5
    },
    "SYi-2418": {
      "display_name": "SYi-2418",
      "span_m": 1.8,
      "width_m": 0.24,
      "weight_kg": 12.5
    }
  },
  "braces": {
    "SXB-1618": {
      "display_name": "SXB-1618",
      "span_m": 1.8,
      "height_m": 1.7,
      "weight_kg": 4.04
    },
    "SXB-1615": {
      "display_name": "SXB-1615",
      "span_m": 1.5,
      "height_m": 1.7,
      "weight_kg": 3.65
    },
    "SXB-1612": {
      "display_name": "SXB-1612",
      "span_m": 1.2,
      "height_m": 1.7,
      "weight_kg": 3.3
    }
  },
  "beam_frames": {
    "SPL-36": {
      "display_name": "SPL-36",
      "span_m": 3.6,
      "open_spans": 2,
      "weight_kg": 36.0,
      "allowable_load_kg": 1000.0
    },
    "SPL-54": {
      "display_name": "SPL-54",
      "span_m": 5.4,
      "open_spans": 3,
      "weight_kg": 54.0,
      "allowable_load_kg": 1000.0
    },
    "SPL-72": {
      "display_name": "SPL-72",
      "span_m": 7.2,
      "open_spans": 4,
      "weight_kg": 76.0,
      "allowable_load_kg": 1000.0
    }
  },
  "jack_bases": {
    "BB-35": {
      "display_name": "BB-35 (55-350)",
      "weight_kg": 4.4,
      "max_extension_mm": 350,
      "extension_allowable_kg": [
        {
          "max_mm": 100,
          "allowable_kg": 2800.0
        },
        {
          "max_mm": 150,
          "allowable_kg": 2500.0
        },
        {
          "max_mm": 200,
          "allowable_kg": 2175.0
        },
        {
          "max_mm": 250,
          "allowable_kg": 2075.0
        },
        {
          "max_mm": 300,
          "allowable_kg": 1975.0
        },
        {
          "max_mm": 350,
          "allowable_kg": 1900.0
        }
      ]
    }
  },
  "wall_ties": {
    "壁つなぎ専用金具": {
      "display_name": "壁つなぎ専用金具",
      "base_allowable_kgf": 450.0,
      "wind_increase_factor": 1.3
    },
    "強力壁つなぎ": {
      "display_name": "強力壁つなぎ",
      "base_allowable_kgf": 650.0,
      "wind_increase_factor": 1.3
    }
  },
  "suspension_chains": {
    "ループ吊り": {
      "display_name": "ループ吊り",
      "allowable_tension_kg": 430.0
    },
    "1本吊り（φ6）": {
      "display_name": "1本吊り（φ6）",
      "allowable_tension_kg": 250.0
    },
    "強力ループ吊り": {
      "display_name": "強力ループ吊り",
      "allowable_tension_kg": 600.0
    }
  }
}
```

## 単管・角パイプ・足場板・H形鋼・アンカー・コンクリート・溶接許容値
```json
{
  "single_pipes": {
    "単管φ48.6x2.4 (STK500)": {
      "display_name": "単管φ48.6x2.4 (STK500)",
      "grade": "STK500",
      "D_mm": 48.6,
      "t_mm": 2.4,
      "unit_weight_kg_m": 2.73,
      "A_cm2": 3.483,
      "I_cm4": 9.319,
      "Z_cm3": 3.83,
      "i_cm": 1.64,
      "E_kg_cm2": 2100000.0,
      "F_kg_cm2": 3300.0,
      "fb_long_kg_cm2": 2400.0,
      "fs_long_kg_cm2": 1270.0
    },
    "単管φ48.6x2.3 (STK400)": {
      "display_name": "単管φ48.6x2.3 (STK400)",
      "grade": "STK400",
      "D_mm": 48.6,
      "t_mm": 2.3,
      "unit_weight_kg_m": 2.63,
      "A_cm2": 3.345,
      "I_cm4": 8.987,
      "Z_cm3": 3.7,
      "i_cm": 1.64,
      "E_kg_cm2": 2100000.0,
      "F_kg_cm2": 2400.0,
      "fb_long_kg_cm2": 1600.0,
      "fs_long_kg_cm2": 900.0
    },
    "単管φ48.6x2.4 (STK400)": {
      "display_name": "単管φ48.6x2.4 (STK400)",
      "grade": "STK400",
      "D_mm": 48.6,
      "t_mm": 2.4,
      "unit_weight_kg_m": 2.73,
      "A_cm2": 3.483,
      "I_cm4": 9.319,
      "Z_cm3": 3.83,
      "i_cm": 1.64,
      "E_kg_cm2": 2100000.0,
      "F_kg_cm2": 2400.0,
      "fb_long_kg_cm2": 1600.0,
      "fs_long_kg_cm2": 900.0
    }
  },
  "plank_brackets": {
    "SBK (300-500)": {
      "display_name": "SBK (300-500)",
      "projection_mm": 500.0,
      "eccentricity_mm": 250.0,
      "weight_kg": 3.6
    },
    "SBK-250": {
      "display_name": "SBK-250",
      "projection_mm": 250.0,
      "eccentricity_mm": 125.0,
      "weight_kg": 2.2
    },
    "SBK-400": {
      "display_name": "SBK-400",
      "projection_mm": 400.0,
      "eccentricity_mm": 200.0,
      "weight_kg": 3.1
    },
    "SBK-600": {
      "display_name": "SBK-600",
      "projection_mm": 600.0,
      "eccentricity_mm": 300.0,
      "weight_kg": 4.2
    }
  },
  "square_pipes": {
    "角パイプ 60x60 (STKR400)": {
      "display_name": "角パイプ 60x60 (STKR400)",
      "grade": "STKR400",
      "h_cm": 6.0,
      "b_cm": 6.0,
      "t_cm": 0.23,
      "unit_weight_kg_m": 4.06,
      "A_cm2": 2.76,
      "A_gross_cm2": 5.174,
      "I_cm4": 28.3,
      "Z_cm3": 9.44,
      "E_kg_cm2": 2100000.0,
      "kappa": 1.0,
      "F_kg_cm2": 2400.0,
      "fb_long_kg_cm2": 1600.0,
      "fs_long_kg_cm2": 900.0
    },
    "角パイプ 50x50 (STKR400)": {
      "display_name": "角パイプ 50x50 (STKR400)",
      "grade": "STKR400",
      "h_cm": 5.0,
      "b_cm": 5.0,
      "t_cm": 0.23,
      "unit_weight_kg_m": 3.34,
      "A_cm2": 2.3,
      "A_gross_cm2": 4.254,
      "I_cm4": 15.9,
      "Z_cm3": 6.34,
      "E_kg_cm2": 2100000.0,
      "kappa": 1.0,
      "F_kg_cm2": 2400.0,
      "fb_long_kg_cm2": 1600.0,
      "fs_long_kg_cm2": 900.0
    },
    "角パイプ 75x75x2.3 (STKR400)": {
      "display_name": "角パイプ 75x75x2.3 (STKR400)",
      "grade": "STKR400",
      "h_cm": 7.5,
      "b_cm": 7.5,
      "t_cm": 0.23,
      "unit_weight_kg_m": 5.14,
      "A_cm2": 3.45,
      "A_gross_cm2": 6.554,
      "I_cm4": 57.1,
      "Z_cm3": 15.2,
      "E_kg_cm2": 2100000.0,
      "kappa": 1.0,
      "F_kg_cm2": 2400.0,
      "fb_long_kg_cm2": 1600.0,
      "fs_long_kg_cm2": 900.0
    },
    "角パイプ 75x75x3.2 (STKR400)": {
      "display_name": "角パイプ 75x75x3.2 (STKR400)",
      "grade": "STKR400",
      "h_cm": 7.5,
      "b_cm": 7.5,
      "t_cm": 0.32,
      "unit_weight_kg_m": 7.01,
      "A_cm2": 4.8,
      "A_gross_cm2": 8.932,
      "I_cm4": 75.5,
      "Z_cm3": 20.1,
      "E_kg_cm2": 2100000.0,
      "kappa": 1.0,
      "F_kg_cm2": 2400.0,
      "fb_long_kg_cm2": 1600.0,
      "fs_long_kg_cm2": 900.0
    },
    "角パイプ 100x100x3.2 (STKR400)": {
      "display_name": "角パイプ 100x100x3.2 (STKR400)",
      "grade": "STKR400",
      "h_cm": 10.0,
      "b_cm": 10.0,
      "t_cm": 0.32,
      "unit_weight_kg_m": 9.52,
      "A_cm2": 6.4,
      "A_gross_cm2": 12.13,
      "I_cm4": 187.0,
      "Z_cm3": 37.5,
      "E_kg_cm2": 2100000.0,
      "kappa": 1.0,
      "F_kg_cm2": 2400.0,
      "fb_long_kg_cm2": 1600.0,
      "fs_long_kg_cm2": 900.0
    }
  },
  "planks": {
    "足場板 25x240 (合板)": {
      "display_name": "足場板 25x240 (合板)",
      "thickness_mm": 25.0,
      "width_mm": 240.0,
      "unit_weight_kg_m": 4.18,
      "unit_weight_per_m_width_kg_m": 16.741,
      "unit_weight_kg_m2": 16.741,
      "A_cm2": 250.0,
      "I_cm4": 130.208,
      "Z_cm3": 104.167,
      "E_kg_cm2": 90000.0,
      "kappa": 1.5,
      "fb_long_kg_cm2": 165.0,
      "fs_long_kg_cm2": 10.5
    },
    "足場板 28x240 (合板)": {
      "display_name": "足場板 28x240 (合板)",
      "thickness_mm": 28.0,
      "width_mm": 240.0,
      "unit_weight_kg_m": 4.68,
      "unit_weight_per_m_width_kg_m": 18.75,
      "unit_weight_kg_m2": 4.68,
      "A_cm2": 280.0,
      "I_cm4": 182.933,
      "Z_cm3": 130.667,
      "E_kg_cm2": 90000.0,
      "kappa": 1.5,
      "fb_long_kg_cm2": 165.0,
      "fs_long_kg_cm2": 10.5
    },
    "足場板 36x240 (杉・松)": {
      "display_name": "足場板 36x240 (杉・松)",
      "thickness_mm": 36.0,
      "width_mm": 240.0,
      "unit_weight_kg_m": 5.18,
      "unit_weight_per_m_width_kg_m": 21.6,
      "unit_weight_kg_m2": 21.6,
      "A_cm2": 360.0,
      "I_cm4": 388.8,
      "Z_cm3": 216.0,
      "E_kg_cm2": 75000.0,
      "kappa": 1.5,
      "fb_long_kg_cm2": 90.0,
      "fs_long_kg_cm2": 7.0
    }
  },
  "timbers": {
    "端太角 90x90 (松・栂Ⅱ類)": {
      "display_name": "端太角 90x90 (松・栂Ⅱ類)",
      "b_cm": 9.0,
      "h_cm": 9.0,
      "unit_weight_kg_m": 6.48
    },
    "端太角 100x100 (松・栂Ⅱ類)": {
      "display_name": "端太角 100x100 (松・栂Ⅱ類)",
      "b_cm": 10.0,
      "h_cm": 10.0,
      "unit_weight_kg_m": 8.0
    }
  },
  "h_beams": {
    "H形鋼 150x150x7x10 (SS400)": {
      "display_name": "Ｈ形鋼 150x150x7x10 (SS400)",
      "grade": "SS400",
      "h_cm": 15.0,
      "b_cm": 15.0,
      "tw_cm": 0.7,
      "tf_cm": 1.0,
      "unit_weight_kg_m": 31.5,
      "A_cm2": 40.14,
      "I_cm4": 1640.0,
      "Z_cm3": 219.0,
      "i_ltb_cm": 4.13,
      "E_kg_cm2": 2100000.0,
      "F_kg_cm2": 2400.0,
      "ft_long_kg_cm2": 1600.0,
      "fb_long_kg_cm2": 1600.0,
      "fs_long_kg_cm2": 900.0
    },
    "H形鋼 200x200x8x12 (SS400)": {
      "display_name": "Ｈ形鋼 200x200x8x12 (SS400)",
      "grade": "SS400",
      "h_cm": 20.0,
      "b_cm": 20.0,
      "tw_cm": 0.8,
      "tf_cm": 1.2,
      "unit_weight_kg_m": 49.9,
      "A_cm2": 63.53,
      "I_cm4": 4720.0,
      "Z_cm3": 472.0,
      "i_ltb_cm": 5.5,
      "E_kg_cm2": 2100000.0,
      "F_kg_cm2": 2400.0,
      "ft_long_kg_cm2": 1600.0,
      "fb_long_kg_cm2": 1600.0,
      "fs_long_kg_cm2": 900.0
    },
    "H形鋼 250x250x9x14 (SS400)": {
      "display_name": "Ｈ形鋼 250x250x9x14 (SS400)",
      "grade": "SS400",
      "h_cm": 25.0,
      "b_cm": 25.0,
      "tw_cm": 0.9,
      "tf_cm": 1.4,
      "unit_weight_kg_m": 72.4,
      "A_cm2": 92.18,
      "I_cm4": 10800.0,
      "Z_cm3": 867.0,
      "i_ltb_cm": 6.87,
      "E_kg_cm2": 2100000.0,
      "F_kg_cm2": 2400.0,
      "ft_long_kg_cm2": 1600.0,
      "fb_long_kg_cm2": 1600.0,
      "fs_long_kg_cm2": 900.0
    },
    "H形鋼 300x300x10x15 (SS400)": {
      "display_name": "Ｈ形鋼 300x300x10x15 (SS400)",
      "grade": "SS400",
      "h_cm": 30.0,
      "b_cm": 30.0,
      "tw_cm": 1.0,
      "tf_cm": 1.5,
      "unit_weight_kg_m": 94.0,
      "A_cm2": 119.8,
      "I_cm4": 20400.0,
      "Z_cm3": 1360.0,
      "i_ltb_cm": 8.23,
      "E_kg_cm2": 2100000.0,
      "F_kg_cm2": 2400.0,
      "ft_long_kg_cm2": 1600.0,
      "fb_long_kg_cm2": 1600.0,
      "fs_long_kg_cm2": 900.0
    },
    "H形鋼 350x350x12x19 (SS400)": {
      "display_name": "Ｈ形鋼 350x350x12x19 (SS400)",
      "grade": "SS400",
      "h_cm": 35.0,
      "b_cm": 35.0,
      "tw_cm": 1.2,
      "tf_cm": 1.9,
      "unit_weight_kg_m": 137.0,
      "A_cm2": 173.9,
      "I_cm4": 40300.0,
      "Z_cm3": 2300.0,
      "i_ltb_cm": 9.61,
      "E_kg_cm2": 2100000.0,
      "F_kg_cm2": 2400.0,
      "ft_long_kg_cm2": 1600.0,
      "fb_long_kg_cm2": 1600.0,
      "fs_long_kg_cm2": 900.0
    },
    "H形鋼 200x100x5.5x8 (SS400)": {
      "display_name": "Ｈ形鋼 200x100x5.5x8 (SS400)",
      "grade": "SS400",
      "h_cm": 20.0,
      "b_cm": 10.0,
      "tw_cm": 0.55,
      "tf_cm": 0.8,
      "unit_weight_kg_m": 21.3,
      "A_cm2": 27.16,
      "I_cm4": 1840.0,
      "Z_cm3": 184.0,
      "i_ltb_cm": 2.66,
      "E_kg_cm2": 2100000.0,
      "F_kg_cm2": 2400.0,
      "ft_long_kg_cm2": 1600.0,
      "fb_long_kg_cm2": 1600.0,
      "fs_long_kg_cm2": 900.0
    },
    "H形鋼 300x150x6.5x9 (SS400)": {
      "display_name": "Ｈ形鋼 300x150x6.5x9 (SS400)",
      "grade": "SS400",
      "h_cm": 30.0,
      "b_cm": 15.0,
      "tw_cm": 0.65,
      "tf_cm": 0.9,
      "unit_weight_kg_m": 36.7,
      "A_cm2": 46.78,
      "I_cm4": 7210.0,
      "Z_cm3": 481.0,
      "i_ltb_cm": 3.92,
      "E_kg_cm2": 2100000.0,
      "F_kg_cm2": 2400.0,
      "ft_long_kg_cm2": 1600.0,
      "fb_long_kg_cm2": 1600.0,
      "fs_long_kg_cm2": 900.0
    },
    "H形鋼 400x200x8x13 (SS400)": {
      "display_name": "Ｈ形鋼 400x200x8x13 (SS400)",
      "grade": "SS400",
      "h_cm": 40.0,
      "b_cm": 20.0,
      "tw_cm": 0.8,
      "tf_cm": 1.3,
      "unit_weight_kg_m": 66.0,
      "A_cm2": 84.12,
      "I_cm4": 23700.0,
      "Z_cm3": 1190.0,
      "i_ltb_cm": 5.31,
      "E_kg_cm2": 2100000.0,
      "F_kg_cm2": 2400.0,
      "ft_long_kg_cm2": 1600.0,
      "fb_long_kg_cm2": 1600.0,
      "fs_long_kg_cm2": 900.0
    },
    "ビルトH 1200x800x15x12 (SS400)": {
      "display_name": "ﾋﾞﾙﾄH 1200x800x15x12 (SS400)",
      "grade": "SS400",
      "h_cm": 120.0,
      "b_cm": 80.0,
      "tw_cm": 1.5,
      "tf_cm": 1.2,
      "unit_weight_kg_m": 289.4,
      "A_cm2": 368.4,
      "I_cm4": 880766.0,
      "Z_cm3": 14679.4,
      "i_ltb_cm": 25.8,
      "E_kg_cm2": 2100000.0,
      "F_kg_cm2": 2400.0,
      "ft_long_kg_cm2": 1600.0,
      "fb_long_kg_cm2": 1571.0,
      "fs_long_kg_cm2": 900.0
    }
  },
  "anchor_bolts": {
    "M16": {
      "display_name": "Ｍ１６",
      "d_mm": 16,
      "A_cm2": 2.01,
      "perimeter_cm": 5.03,
      "fs_kg_cm2": 900.0,
      "ft_kg_cm2": 1200.0
    },
    "M20": {
      "display_name": "Ｍ２０",
      "d_mm": 20,
      "A_cm2": 3.14,
      "perimeter_cm": 6.44,
      "fs_kg_cm2": 900.0,
      "ft_kg_cm2": 1200.0
    },
    "M22": {
      "display_name": "Ｍ２２",
      "d_mm": 22,
      "A_cm2": 3.8,
      "perimeter_cm": 6.91,
      "fs_kg_cm2": 900.0,
      "ft_kg_cm2": 1200.0
    },
    "M24": {
      "display_name": "Ｍ２４",
      "d_mm": 24,
      "A_cm2": 4.52,
      "perimeter_cm": 7.54,
      "fs_kg_cm2": 900.0,
      "ft_kg_cm2": 1200.0
    },
    "M27": {
      "display_name": "Ｍ２７",
      "d_mm": 27,
      "A_cm2": 5.73,
      "perimeter_cm": 8.48,
      "fs_kg_cm2": 900.0,
      "ft_kg_cm2": 1200.0
    },
    "M30": {
      "display_name": "Ｍ３０",
      "d_mm": 30,
      "A_cm2": 7.07,
      "perimeter_cm": 9.42,
      "fs_kg_cm2": 900.0,
      "ft_kg_cm2": 1200.0
    }
  },
  "concrete_grades": {
    "Fc18": {
      "Fc_kg_cm2": 180.0,
      "Fc_N_mm2": 18.0,
      "fa_bond_kg_cm2": 7.0
    },
    "Fc21": {
      "Fc_kg_cm2": 210.0,
      "Fc_N_mm2": 21.0,
      "fa_bond_kg_cm2": 8.0
    },
    "Fc24": {
      "Fc_kg_cm2": 240.0,
      "Fc_N_mm2": 24.0,
      "fa_bond_kg_cm2": 8.5
    },
    "Fc27": {
      "Fc_kg_cm2": 270.0,
      "Fc_N_mm2": 27.0,
      "fa_bond_kg_cm2": 9.0
    },
    "Fc30": {
      "Fc_kg_cm2": 300.0,
      "Fc_N_mm2": 30.0,
      "fa_bond_kg_cm2": 9.5
    },
    "Fc36": {
      "Fc_kg_cm2": 360.0,
      "Fc_N_mm2": 36.0,
      "fa_bond_kg_cm2": 10.5
    }
  },
  "weld_allowables": {
    "SS400": {
      "butt_weld_fs_kg_cm2": 1400.0,
      "full_penetration_shear_fs_kg_cm2": 800.0,
      "fillet_weld_fs_kg_cm2": 800.0
    },
    "SM490": {
      "butt_weld_fs_kg_cm2": 1900.0,
      "full_penetration_shear_fs_kg_cm2": 1100.0,
      "fillet_weld_fs_kg_cm2": 1100.0
    }
  }
}
```

## 47都道府県・地域別 基準風速 Vo / 台風時割増係数 Ke
```json
{
  "東京都（23区内）": {
    "v0": 18,
    "ke": 1.0,
    "prefecture": "東京都"
  },
  "東京都（23区外・多摩）": {
    "v0": 16,
    "ke": 1.0,
    "prefecture": "東京都"
  },
  "東京都（島しょ部）": {
    "v0": 20,
    "ke": 1.0,
    "prefecture": "東京都"
  },
  "北海道（札幌・一般）": {
    "v0": 14,
    "ke": 1.0,
    "prefecture": "北海道"
  },
  "北海道（室蘭・襟裳・沿岸強風域）": {
    "v0": 18,
    "ke": 1.0,
    "prefecture": "北海道"
  },
  "青森県": {
    "v0": 16,
    "ke": 1.0,
    "prefecture": "青森県"
  },
  "岩手県": {
    "v0": 14,
    "ke": 1.0,
    "prefecture": "岩手県"
  },
  "宮城県": {
    "v0": 14,
    "ke": 1.0,
    "prefecture": "宮城県"
  },
  "秋田県": {
    "v0": 16,
    "ke": 1.0,
    "prefecture": "秋田県"
  },
  "山形県": {
    "v0": 14,
    "ke": 1.0,
    "prefecture": "山形県"
  },
  "福島県": {
    "v0": 14,
    "ke": 1.0,
    "prefecture": "福島県"
  },
  "茨城県": {
    "v0": 16,
    "ke": 1.0,
    "prefecture": "茨城県"
  },
  "栃木県": {
    "v0": 14,
    "ke": 1.0,
    "prefecture": "栃木県"
  },
  "群馬県": {
    "v0": 14,
    "ke": 1.0,
    "prefecture": "群馬県"
  },
  "埼玉県": {
    "v0": 16,
    "ke": 1.0,
    "prefecture": "埼玉県"
  },
  "千葉県（一般）": {
    "v0": 16,
    "ke": 1.0,
    "prefecture": "千葉県"
  },
  "千葉県（東京湾・房総沿岸）": {
    "v0": 18,
    "ke": 1.0,
    "prefecture": "千葉県"
  },
  "神奈川県（横浜・川崎・沿岸）": {
    "v0": 18,
    "ke": 1.0,
    "prefecture": "神奈川県"
  },
  "神奈川県（内陸）": {
    "v0": 16,
    "ke": 1.0,
    "prefecture": "神奈川県"
  },
  "新潟県": {
    "v0": 16,
    "ke": 1.0,
    "prefecture": "新潟県"
  },
  "富山県": {
    "v0": 14,
    "ke": 1.0,
    "prefecture": "富山県"
  },
  "石川県": {
    "v0": 16,
    "ke": 1.0,
    "prefecture": "石川県"
  },
  "福井県": {
    "v0": 14,
    "ke": 1.0,
    "prefecture": "福井県"
  },
  "山梨県": {
    "v0": 14,
    "ke": 1.0,
    "prefecture": "山梨県"
  },
  "長野県": {
    "v0": 14,
    "ke": 1.0,
    "prefecture": "長野県"
  },
  "岐阜県": {
    "v0": 14,
    "ke": 1.0,
    "prefecture": "岐阜県"
  },
  "静岡県（一般）": {
    "v0": 16,
    "ke": 1.0,
    "prefecture": "静岡県"
  },
  "静岡県（御前崎・伊豆沿岸）": {
    "v0": 18,
    "ke": 1.0,
    "prefecture": "静岡県"
  },
  "愛知県（一般・名古屋）": {
    "v0": 16,
    "ke": 1.0,
    "prefecture": "愛知県"
  },
  "愛知県（渥美半島）": {
    "v0": 18,
    "ke": 1.0,
    "prefecture": "愛知県"
  },
  "三重県（一般）": {
    "v0": 16,
    "ke": 1.0,
    "prefecture": "三重県"
  },
  "三重県（志摩・尾鷲）": {
    "v0": 18,
    "ke": 1.0,
    "prefecture": "三重県"
  },
  "滋賀県": {
    "v0": 14,
    "ke": 1.0,
    "prefecture": "滋賀県"
  },
  "京都府": {
    "v0": 14,
    "ke": 1.0,
    "prefecture": "京都府"
  },
  "大阪府": {
    "v0": 16,
    "ke": 1.0,
    "prefecture": "大阪府"
  },
  "兵庫県（神戸・阪神）": {
    "v0": 16,
    "ke": 1.0,
    "prefecture": "兵庫県"
  },
  "兵庫県（淡路島・沿岸）": {
    "v0": 18,
    "ke": 1.0,
    "prefecture": "兵庫県"
  },
  "奈良県": {
    "v0": 14,
    "ke": 1.0,
    "prefecture": "奈良県"
  },
  "和歌山県（一般）": {
    "v0": 16,
    "ke": 1.0,
    "prefecture": "和歌山県"
  },
  "和歌山県（潮岬・南部沿岸）": {
    "v0": 20,
    "ke": 1.0,
    "prefecture": "和歌山県"
  },
  "鳥取県": {
    "v0": 16,
    "ke": 1.0,
    "prefecture": "鳥取県"
  },
  "島根県": {
    "v0": 16,
    "ke": 1.0,
    "prefecture": "島根県"
  },
  "岡山県": {
    "v0": 14,
    "ke": 1.0,
    "prefecture": "岡山県"
  },
  "広島県": {
    "v0": 14,
    "ke": 1.0,
    "prefecture": "広島県"
  },
  "山口県": {
    "v0": 16,
    "ke": 1.1,
    "prefecture": "山口県"
  },
  "徳島県": {
    "v0": 16,
    "ke": 1.0,
    "prefecture": "徳島県"
  },
  "香川県": {
    "v0": 14,
    "ke": 1.0,
    "prefecture": "香川県"
  },
  "愛媛県": {
    "v0": 16,
    "ke": 1.0,
    "prefecture": "愛媛県"
  },
  "高知県（一般）": {
    "v0": 16,
    "ke": 1.0,
    "prefecture": "高知県"
  },
  "高知県（室戸・足摺沿岸）": {
    "v0": 20,
    "ke": 1.0,
    "prefecture": "高知県"
  },
  "福岡県": {
    "v0": 16,
    "ke": 1.1,
    "prefecture": "福岡県"
  },
  "佐賀県": {
    "v0": 16,
    "ke": 1.1,
    "prefecture": "佐賀県"
  },
  "長崎県": {
    "v0": 18,
    "ke": 1.1,
    "prefecture": "長崎県"
  },
  "熊本県": {
    "v0": 16,
    "ke": 1.1,
    "prefecture": "熊本県"
  },
  "大分県": {
    "v0": 16,
    "ke": 1.1,
    "prefecture": "大分県"
  },
  "宮崎県": {
    "v0": 18,
    "ke": 1.1,
    "prefecture": "宮崎県"
  },
  "鹿児島県（本土）": {
    "v0": 18,
    "ke": 1.2,
    "prefecture": "鹿児島県"
  },
  "鹿児島県（離島）": {
    "v0": 22,
    "ke": 1.2,
    "prefecture": "鹿児島県"
  },
  "沖縄県（本島）": {
    "v0": 22,
    "ke": 1.2,
    "prefecture": "沖縄県"
  },
  "沖縄県（先島・大東諸島）": {
    "v0": 24,
    "ke": 1.2,
    "prefecture": "沖縄県"
  }
}
```

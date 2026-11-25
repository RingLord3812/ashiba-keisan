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

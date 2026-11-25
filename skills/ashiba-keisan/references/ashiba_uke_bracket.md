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

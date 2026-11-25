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

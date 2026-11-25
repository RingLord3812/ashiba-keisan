"""単位換算および丸め処理ユーティリティ (SUCCES Ver 4.11 準拠)."""

from __future__ import annotations

import math
from decimal import Decimal, ROUND_HALF_UP

G_SUCCES = 9.81  # SUCCES Ver 4.11 の重力加速度換算定数 (1 kgf = 9.81 N)


def round_half_up(value: float, ndigits: int = 1) -> float:
    """四捨五入 (ROUND_HALF_UP)."""
    if not math.isfinite(value):
        return value
    q = Decimal("1") if ndigits <= 0 else Decimal("1." + "0" * ndigits)
    if ndigits < 0:
        factor = Decimal(10) ** (-ndigits)
        res = (Decimal(str(value)) / factor).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * factor
        return float(res)
    return float(Decimal(str(value)).quantize(q, rounding=ROUND_HALF_UP))


def ceil_sig(value: float, sig: int = 3) -> float:
    """有効数字 sig 桁で切り上げ (SUCCES の SI 併記換算規則)."""
    if value == 0 or not math.isfinite(value):
        return 0.0
    sign = 1.0 if value > 0 else -1.0
    v = abs(value)
    exp = math.floor(math.log10(v))
    scale = 10.0 ** (exp - sig + 1)
    # 浮動小数点誤差 (例: 981.0000000000001) による不要な切り上げを防止
    scaled = v / scale
    if abs(scaled - round(scaled)) < 1e-9:
        ceiled = round(scaled)
    else:
        ceiled = math.ceil(scaled)
    decimals = max(0, sig - 1 - exp)
    return round(sign * ceiled * scale, decimals)


def fmt_sig(value: float, sig: int = 3) -> str:
    """有効数字表記整形."""
    if value == 0:
        return "0"
    v = abs(value)
    exp = math.floor(math.log10(v))
    decimals = max(0, sig - 1 - exp)
    if decimals == 0:
        return f"{int(round(value))}"
    return f"{value:.{decimals}f}"


def kgf_to_N(kgf: float) -> float:
    """kgf -> N (SUCCES 3桁切り上げ換算)."""
    return ceil_sig(kgf * G_SUCCES, 3)


def kg_cm2_to_N_mm2(stress: float) -> float:
    """kg/cm2 -> N/mm2 (1 kg/cm2 = 0.0981 N/mm2, SUCCES 3桁切り上げ換算)."""
    return ceil_sig(stress * (G_SUCCES / 100.0), 3)


def kg_cm_to_kN_mm(moment_kg_cm: float) -> float:
    """kg・cm -> kN・mm (1 kg・cm = 0.0981 kN・mm, SUCCES 3桁切り上げ換算)."""
    return ceil_sig(moment_kg_cm * (G_SUCCES / 100.0), 3)


def kg_m_to_kN_mm(moment_kg_m: float) -> float:
    """kg・m -> kN・mm (1 kg・m = 9.81 kN・mm, SUCCES 3桁切り上げ換算)."""
    return ceil_sig(moment_kg_m * G_SUCCES, 3)


def kg_m_to_N_m(w_kg_m: float) -> float:
    """kg/m -> N/m."""
    return ceil_sig(w_kg_m * G_SUCCES, 3)


def kg_cm_to_N_mm(w_kg_cm: float) -> float:
    """kg/cm -> N/mm (1 kg/cm = 0.981 N/mm)."""
    return ceil_sig(w_kg_cm * (G_SUCCES / 10.0), 3)


def kg_m2_to_N_m2(q_kg_m2: float) -> float:
    """kgf/m2 -> N/m2."""
    return ceil_sig(q_kg_m2 * G_SUCCES, 3)


def fmt_N(kgf: float) -> str:
    return f"{fmt_sig(kgf_to_N(kgf), 3)} N"


def fmt_N_mm2(stress: float) -> str:
    return f"{fmt_sig(kg_cm2_to_N_mm2(stress), 3)} N/mm²"


def fmt_kN_mm(moment_kg_cm: float) -> str:
    return f"{fmt_sig(kg_cm_to_kN_mm(moment_kg_cm), 3)} kN・mm"


def fmt_N_m2(q_kg_m2: float) -> str:
    return f"{fmt_sig(kg_m2_to_N_m2(q_kg_m2), 3)} N/m²"


def fmt_N_mm(w_kg_cm: float) -> str:
    return f"{fmt_sig(kg_cm_to_N_mm(w_kg_cm), 3)} N/mm"


def fmt_N_m(w_kg_m: float) -> str:
    return f"{fmt_sig(kg_m_to_N_m(w_kg_m), 3)} N/m"


def cm_to_mm(val_cm: float) -> float:
    return round_half_up(val_cm * 10.0, 2)

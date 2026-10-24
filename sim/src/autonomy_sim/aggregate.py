"""L1 聚合模块：幂均值族 F_σ 与闸门复合指标（SPEC_estimators §9 E9.1；附录 §6）。

σ–p 对应（附录 §6.5，E3）：CES F_σ(x;w)=(Σ w_i x_i^{(σ−1)/σ})^{σ/(σ−1)} ↔
幂均值指数 p=(σ−1)/σ，σ=1/(1−p)。

- σ=1（p=0）：几何平均 ∏ x_i^{w_i}——表示定理 6.5/6.6 的唯一全公理形式（对数域计算）；
- σ∈(0,1)（p<0）：x_i=0 ⇒ F=0（向 [0,1]^n 的连续延拓，零歼灭 (A4)/AX5 保持），
  但 (A6b) 逐坐标标度序不变仅在 σ=1 成立（引理 6.4；命题 6.7 调和反例）；
- σ>1（p>0）：零歼灭失效——仅作 AX5 松弛压力测试（E3），调用方须显式传入并标注；
- σ≤0（p→−∞，Leontief/min 极限）被 (A2)/AX4 排除，不提供。

闸门复合（附录 §6.6）：A = A_via·F_σ(A_org,…,A_ref; w)；A_via=0 ⇒ A=0 与 σ 无关。
主敏感性带 σ∈[0.5,1]（E3 修正）；权 w_i>0、Σw_i=1（表示定理产出；配置给定，入 metadata）。
"""
import math

MAIN_BAND = (0.5, 1.0)


def p_of_sigma(sigma: float) -> float:
    """CES 参数 σ → 幂均值指数 p=(σ−1)/σ（附录 §6.5）。"""
    sigma = float(sigma)
    if sigma <= 0.0:
        raise ValueError(f"σ 须为正（σ→0 的 Leontief 极限被 (A2)/AX4 排除）: {sigma}")
    return (sigma - 1.0) / sigma


def _check_weights(w) -> tuple:
    w = tuple(float(v) for v in w)
    if not w:
        raise ValueError("权重向量不能为空")
    if any(v <= 0.0 for v in w):
        raise ValueError(f"权重须严格为正（表示定理 w≫0）: {w}")
    if abs(sum(w) - 1.0) > 1e-9:
        raise ValueError(f"权重须归一（Σw=1）: Σw={sum(w)}")
    return w


def _check_components(x) -> tuple:
    x = tuple(float(v) for v in x)
    if any(not 0.0 <= v <= 1.0 for v in x):
        raise ValueError(f"分量须在 [0,1]（(0,1]^n 连续延拓）: {x}")
    return x


def F_sigma(x, w, sigma: float) -> float:
    """幂均值族 F_σ(x;w)（CES 参数化；域 (0,1]^n，连续延拓至 [0,1]^n）。

    p≤0（σ≤1）时任一分量为 0 ⇒ F=0（零歼灭连续延拓）；
    p>0（σ>1）时零分量不歼灭（AX5 失效——压力测试语义，见模块 docstring）。
    """
    x = _check_components(x)
    w = _check_weights(w)
    if len(x) != len(w):
        raise ValueError(f"x 与 w 长度不一致: {len(x)} != {len(w)}")
    p = p_of_sigma(sigma)
    if p == 0.0:  # σ=1：几何平均（对数域）
        acc = 0.0
        for xi, wi in zip(x, w):
            if xi == 0.0:
                return 0.0
            acc += wi * math.log(xi)
        return math.exp(acc)
    if p < 0.0:  # σ<1：零分量 ⇒ 加权和发散 ⇒ F=0（连续延拓）
        if any(xi == 0.0 for xi in x):
            return 0.0
        return sum(wi * xi ** p for xi, wi in zip(x, w)) ** (1.0 / p)
    # p>0（σ>1）：0**p=0，零分量不歼灭（AX5 失效，压力测试）
    return sum(wi * xi ** p for xi, wi in zip(x, w)) ** (1.0 / p)


def geometric_mean(x, w) -> float:
    """几何平均 ∏ x_i^{w_i}（F_σ 的 σ=1 特款；表示定理 6.5/6.6 的唯一全公理形式）。"""
    return F_sigma(x, w, 1.0)


def harmonic_mean(x, w) -> float:
    """调和平均 (Σ w_i/x_i)^{-1}（F_σ 的 σ=0.5 特款；命题 6.7 的 (A6b) 反例对象）。"""
    return F_sigma(x, w, 0.5)


def composite_A(a_via: float, components, w, sigma: float = 1.0) -> float:
    """闸门复合指标 A = A_via·F_σ(components; w)（附录 §6.6；SPEC_estimators E9.1）。

    A_via=0 ⇒ A=0（存续闸门，与 σ 无关）。σ 主带 [0.5,1] 外（σ>1）为 AX5 松弛
    压力测试，须显式传入 sigma 并标注违反公理。
    """
    a_via = float(a_via)
    if not 0.0 <= a_via <= 1.0:
        raise ValueError(f"A_via 须在 [0,1]: {a_via}")
    return a_via * F_sigma(components, w, sigma)

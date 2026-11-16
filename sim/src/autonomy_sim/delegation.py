"""T7 委托治理律（附录 §7.7；SPEC_estimators E12.3 记账约定）。

记账约定（E12.3）：干预流 I := 受托脚本内容（源指示 = 协议参数 (λ,q)，非影响流）；
精确前提：脚本臂不经 S（I(S;A|del)=0）＋等熵转移（自臂 I(S;A)=脚本逐步熵转移=C̃）。
该约定下定理 7.7.1 的线性律在编译模型（β_π 旗标混合）上逐字精确成立：
F_int = (1−m)·F_int^self（真值路径），F_ext = m·C̃·T（脚本熵转移），
A_org = F_int/(F_int+F_ext) = (1−m)·A_org^self。
"""


def f_int_mixed(f_int_self: float, m: float) -> float:
    """混合模型的内部流：脚本臂无 S 流 ⇒ F_int=(1−m)·F_int^self（定理 7.7.1 证明要点）。"""
    _check_m(m)
    return (1.0 - m) * float(f_int_self)


def f_ext_script(script_entropy: float, m: float, T: int) -> float:
    """外部流：脚本内容经 m 份额行动通道注入 ⇒ F_ext=m·C̃·T（C̃=脚本逐步熵转移）。"""
    _check_m(m)
    if script_entropy < 0:
        raise ValueError(f"脚本熵转移 ≥0: {script_entropy}")
    return m * float(script_entropy) * int(T)


def a_org_h1(a_org_self: float, m: float) -> float:
    """定理 7.7.1（H1' 精确前提）：A_org(λ,q)=A_org^self·(1−m)，m=λ(1−q)。"""
    _check_m(m)
    return float(a_org_self) * (1.0 - m)


def a_org_bracket(a_org_self: float, m: float, rho_min: float, rho_max: float) -> tuple:
    """零松弛（η_μ=0）代数夹逼；有 selector 混合误差时必须改用双误差函数。"""
    _check_m(m)
    if not 0 < rho_min <= rho_max:
        raise ValueError(f"须 0<ρ_min≤ρ_max: ({rho_min},{rho_max})")
    lo = float(a_org_self) * (1.0 - m) / (1.0 - m + m * rho_max)
    hi = float(a_org_self) * (1.0 - m) / (1.0 - m + m * rho_min)
    return lo, min(1.0, hi)


def a_org_two_error_bracket(m: float, rho_min: float, rho_max: float,
                            phi_minus: float, phi_plus: float,
                            eta_mu: float) -> tuple:
    """v0.7 双误差夹逼 [L,U]（SPEC_experiments DEL-1⑤⑥）。

    实际比值为 (a+u)/(a+u+d+v)，|u|,|v|≤eta_mu；L 最小化分子并最大化
    外部流，U 反向优化。phi_0∈[phi_minus,phi_plus] 时两端分别取最坏值。
    非负流量/正分母域由 (x)_+=max(x,0) 表达；区间可退化为 [0,1]。
    """
    _check_m(m)
    if not 0 < rho_min <= rho_max:
        raise ValueError(f"须 0<ρ_min≤ρ_max: ({rho_min},{rho_max})")
    if not 0.0 <= phi_minus <= phi_plus:
        raise ValueError(f"须 0≤φ_-≤φ_+: ({phi_minus},{phi_plus})")
    if eta_mu < 0:
        raise ValueError(f"η_μ≥0: {eta_mu}")
    a = 1.0 - m
    n_min = max(0.0, a - eta_mu)
    d_max = m * rho_max + phi_plus + eta_mu
    lo = n_min / (n_min + d_max) if n_min + d_max > 0 else 0.0
    n_max = a + eta_mu
    d_min = max(0.0, m * rho_min + phi_minus - eta_mu)
    hi = n_max / (n_max + d_min) if n_max + d_min > 0 else 1.0
    return lo, min(1.0, hi)


def m_of_lambda_q(lam: float, q: float) -> float:
    """未治理委托份额 m=λ(1−q)（附录 §7.7 构造）。"""
    if not (0.0 <= lam <= 1.0 and 0.0 <= q <= 1.0):
        raise ValueError(f"λ,q∈[0,1]: ({lam},{q})")
    return lam * (1.0 - q)


def a_composite_delegated(a_self: float, m: float, w_org: float) -> float:
    """推论 7.7.3（E7 复合修正）：A(λ,q)=A_self·(1−m)^{w_org}（其余分量不变时）。"""
    _check_m(m)
    if not 0.0 <= w_org <= 1.0:
        raise ValueError(f"w_org∈[0,1]: {w_org}")
    return float(a_self) * (1.0 - m) ** float(w_org)


def _check_m(m: float) -> None:
    if not 0.0 <= m <= 1.0:
        raise ValueError(f"m∈[0,1]: {m}")

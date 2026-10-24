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
    """命题 7.7.2 夹逼界（无 H1'，ρ=C_del/C_self∈[ρ_min,ρ_max]，上端对 1 取 min）。"""
    _check_m(m)
    if not 0 < rho_min <= rho_max:
        raise ValueError(f"须 0<ρ_min≤ρ_max: ({rho_min},{rho_max})")
    lo = float(a_org_self) * (1.0 - m) / (1.0 - m + m * rho_max)
    hi = float(a_org_self) * (1.0 - m) / (1.0 - m + m * rho_min)
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

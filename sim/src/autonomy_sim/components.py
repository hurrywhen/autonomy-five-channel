"""分量真值模块：A_goal / A_epi / A_ref（SPEC_estimators §4–§6；附录 §5.3/5.5/5.6）。

第 4 步范围（E4.5/E5.4/E6.4）：公式层真值在显式输入上闭合——
- A_goal：输入 (U_eff, Endorse, Θ_grid)；U_eff 的 MaxEnt-IRL 恢复属场景步接线。
- A_epi（2026-10-15 精度化口径）：real 轨=相对真值精度——逐步 (E_t,B_t) 联合由
  propagate 的 ESZ 边缘化，κ 协议映射显式传入；rob 轨在 E5.4 对抗族上枚举 sup 精度损失。
- A_ref：输入系综联合表 p(θ_π,M)；系综生成（P3.3）属场景步接线。

退化约定：A_goal 的 Fix=∅ 报 Hausdorff 区间（E9，裁剪标注）；A_ref 的 H(θ_π)=0
报区间 [0, f2·f3]（E6.4），均置 degenerate 标志——禁止 0/0 静默通过。
"""
import math
from collections import namedtuple

import numpy as np

from .di import entropy_nats, mi_nats
from .interventions import GammaSpec, apply_gamma
from .propagate import truth_step_joints

GoalTruth = namedtuple("GoalTruth", ["point", "lo", "hi", "degenerate", "eps_min", "clipped"])
EpiReal = namedtuple("EpiReal", ["a_epi_real", "d_bar", "tvs"])
EpiRob = namedtuple("EpiRob", ["a_epi_rob", "d_sup", "profile"])
RefTruth = namedtuple("RefTruth", ["point", "lo", "hi", "degenerate"])


# ---------- A_goal（附录 §5.3，命题 5.4＋E9） ----------

def _d(u, v) -> float:
    """Θ 上欧氏距离（canonical 参数化后，E4.2）。"""
    return float(np.linalg.norm(np.subtract(np.atleast_1d(u), np.atleast_1d(v), dtype=float)))


def _d_to_set(u, s) -> float:
    return min(_d(u, v) for v in s) if s else math.inf


def fix_points(endorse, theta_grid, tol: float = 1e-12) -> list:
    """Fix(Endorse) 在有限网格上的枚举：d(Endorse(U),U) ≤ tol。"""
    return [u for u in theta_grid if _d(endorse(u), u) <= tol]


def eps_min(endorse, theta_grid) -> float:
    """ε_min = min_{U∈Θ} d(Endorse(U),U)（连续函数在紧集上可达；网格枚举）。"""
    return min(_d(endorse(u), u) for u in theta_grid)


def approx_fix_set(endorse, theta_grid, tol: float = 1e-12):
    """E9 退化预案：返回 (ε_min, Fix_{ε_min})——近似不动点集，恒非空。"""
    em = eps_min(endorse, theta_grid)
    return em, [u for u in theta_grid if _d(endorse(u), u) <= em + tol]


def banach_fixed_point(endorse, u0, tol: float = 1e-12, max_iter: int = 100000):
    """Banach 迭代 U_{k+1}=Endorse(U_k) 至步长 < tol（定理 5.3(b)，压缩模 c<1）。"""
    u = u0
    for _ in range(max_iter):
        u_next = endorse(u)
        if _d(u_next, u) < tol:
            return u_next
        u = u_next
    raise RuntimeError(f"Banach 迭代未在 {max_iter} 步内收敛（tol={tol}）")


def truth_A_goal(u_eff, endorse, theta_grid, tol: float = 1e-12) -> GoalTruth:
    """A_goal = 1 − d(U_eff,Fix)/d_c（命题 5.4；d_c=max_{U∈Θ}d(U,Fix)）。

    Fix=∅（H-U 失败）⇒ E9 退化预案：Fix_{ε_min}＋Hausdorff 区间
    [1−(d_H+ε_min)/d_c, 1−max(0,d_H−ε_min)/d_c]（d_c 对 Fix_{ε_min} 重定义）；
    区间与 [0,1] 取交并标注 clipped；d_c=0（Fix_{ε_min}=Θ）⇒ [0,1]（E4.5）。
    数值裁剪契约（v0.3，沿 di.truth_A_org E3 约定）：u_eff 在网格凸包内 ⇒ d≤d_c
    为数学事实，浮点残差致点值越出 [0,1] 时 1e-9 容差内归位；更大越界保持原值
    交由调用方检出（不静默）。
    """
    grid = list(theta_grid)
    fix = fix_points(endorse, grid, tol)
    if fix:
        d_c = max(_d_to_set(u, fix) for u in grid)
        d = _d_to_set(u_eff, fix)
        a = 1.0 - d / d_c if d_c > 0 else 1.0
        # 数值裁剪（沿 di.truth_A_org 的 E3 契约，v0.3）：u_eff 为网格边缘均值 ⇒ 落在
        # 网格凸包内 ⇒ d≤d_c 是数学事实；浮点残差（~1e-16）可致 a 越出 [0,1]，1e-9
        # 容差内归位（更大越界保持原值，交由调用方/复合层检出——不做静默掩盖）。
        if a < 0.0 and -a <= 1e-9:
            a = 0.0
        elif a > 1.0 and a - 1.0 <= 1e-9:
            a = 1.0
        return GoalTruth(point=a, lo=a, hi=a, degenerate=False, eps_min=0.0, clipped=False)
    em, fset = approx_fix_set(endorse, grid, tol)
    d_c = max(_d_to_set(u, fset) for u in grid)
    if d_c <= 0:
        return GoalTruth(point=None, lo=0.0, hi=1.0, degenerate=True, eps_min=em, clipped=True)
    d_h = _d_to_set(u_eff, fset)
    lo = 1.0 - (d_h + em) / d_c
    hi = 1.0 - max(0.0, d_h - em) / d_c
    clipped = lo < 0.0 or hi > 1.0
    return GoalTruth(point=None, lo=max(0.0, lo), hi=min(1.0, hi),
                     degenerate=True, eps_min=em, clipped=clipped)


# ---------- A_epi（附录 §5.5，E11 双轨；2026-10-15 精度化口径） ----------

def truth_A_epi_real(model, T: int, bucket_map) -> EpiReal:
    """实现轨（进复合指标）：A_epi^real = 1 − D̄，D̄=(1/T)Σ_t E[TV(B_t, δ_{κ(E_t)})]
    = 1 − (1/T)Σ_t P(B_t=κ(E_t))——相对真实环境的失准（精度/失真口径，E5.1）。

    逐步 (E_t,B_t) 联合由 propagate 的 ESZ 决策时联合边缘化（对 (G,M,R,Z) 求和，E5.4）；
    逐步 distortion_t = 1 − accuracy_t 即 E[TV]（TV(B,δ_k)=1−B(k) 逐点恒等）。
    bucket_map：长度 n_E 的 κ 映射（值域 0..n_B−1），显式传入（派生规则见
    wiring.derive_bucket_map）。零语义：A_epi=0 ⟺ 信念全程对真值桶赋零概率。
    退化约定：逐步 joint 无法正常给出（T≤0 或传播缺步，不应发生）⇒ raise。
    """
    al = model.alphabet
    bmap = np.asarray(bucket_map, dtype=int)
    if bmap.shape != (al.n_E,) or np.any(bmap < 0) or np.any(bmap >= al.n_B):
        raise ValueError(f"bucket_map 须为长度 n_E={al.n_E}、值域 [0,{al.n_B}) 的映射")
    joints = truth_step_joints(model, T)
    if T <= 0 or len(joints) != T:
        raise ValueError(f"逐步 joint 无法正常给出：T={T}，实得 {len(joints)} 步")
    e_idx = np.arange(al.n_E)
    tvs = []
    for aux in joints:
        esz = np.asarray(aux["ESZ"], float).reshape(
            al.n_E, al.n_G, al.n_B, al.n_M, al.n_R, al.n_Z)
        p_eb = esz.sum(axis=(1, 3, 4, 5))  # (n_E, n_B) 决策时联合边缘
        accuracy_t = float(p_eb[e_idx, bmap].sum())
        tvs.append(1.0 - accuracy_t)
    d_bar = float(np.mean(tvs))
    return EpiReal(a_epi_real=1.0 - d_bar, d_bar=d_bar, tvs=tvs)


def truth_A_epi_rob(model0, s_grid, T: int, symbol: int, bucket_map) -> EpiRob:
    """稳健轨（设计对偶量，不进复合指标）：A_epi^rob = 1 − sup_{s∈grid} D̄_acc(γ_s)。

    E5.4 对抗族：向常值符号核的混合 γ_s（s=ess sup TV 上界为预算 β= max grid）；
    D̄_acc=相对真值的精度损失；sup 语义不变，D̄_acc(s) 单调性由测试数值核验。
    """
    profile = []
    for s in s_grid:
        mg = apply_gamma(model0, GammaSpec.mix_constant(float(s), symbol))
        profile.append((float(s), truth_A_epi_real(mg, T, bucket_map).d_bar))
    d_sup = max(d for _, d in profile)
    return EpiRob(a_epi_rob=1.0 - d_sup, d_sup=d_sup, profile=profile)


# ---------- A_ref（附录 §5.6，E10） ----------

def truth_A_ref(joint_theta_m, p_endorse: float, lam_ref: float) -> RefTruth:
    """A_ref = [I(M;θ_π)/H(θ_π)]·Pr[ΔG≠0⇒经Endorse]·Λ_ref（命题 5.8）。

    joint_theta_m：系综联合表（行 θ_π、列 M，E6.4）。H(θ_π)=0（系综退化，E10）
    ⇒ 报区间 [0, p_endorse·lam_ref] 并置 degenerate——禁止 0/0 静默通过。
    """
    for name, v in (("p_endorse", p_endorse), ("lam_ref", lam_ref)):
        if not 0.0 <= float(v) <= 1.0:
            raise ValueError(f"{name} 须在 [0,1]: {v}")
    j = np.asarray(joint_theta_m, dtype=float)
    if j.ndim != 2 or np.any(j < 0) or j.sum() <= 0:
        raise ValueError("联合表须为二维非负且总质量为正")
    h_theta = entropy_nats(j.sum(axis=1))
    if h_theta <= 0.0:
        return RefTruth(point=None, lo=0.0, hi=float(p_endorse) * float(lam_ref), degenerate=True)
    fidelity = mi_nats(j) / h_theta
    point = fidelity * float(p_endorse) * float(lam_ref)
    return RefTruth(point=point, lo=point, hi=point, degenerate=False)

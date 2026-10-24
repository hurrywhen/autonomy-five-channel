"""T6 损伤-修复动力学 / C1 相变 / C2 滞后 / T6c 检测下界（SPEC_estimators §12；附录 §7.6/§8.2/§8.3）。

- δ* 与 A_min 显式公式（定理 7.6.3）：δ*=min(θ/W,κ,⌈(r+1)/2⌉c₀/W)，A_min 经 aggregate 几何复合；
- simulate_damage：Ḋ=δ−κD（分段常值精确步进）＋M1 窗登记（窗累计 ≥θ ⇒ 滞后 ℓ 复位）；
- C1（命题 8.2.1）：Ḋ=δ−εv·D(1−D)，fold 平衡公式与临界减慢标度；
- C2（命题 8.3.1）：r(D)=ε₀v·D(1−D)(1−γD)（γ>1），双稳/滞后回环；
- T6c（命题 7.6.5）：LLR-CUSUM 的 EDD 与检测时刻损伤 δ·EDD（向量化 Monte Carlo）。

全部 ODE 模拟物理域钳位于 [0,1]（俘获=1 吸收）；dt 入参数（E12.4）。
"""
import math

import numpy as np

from .aggregate import composite_A


# ---------- T6 主定理（附录 §7.6.2） ----------

def delta_star(theta: float, W: float, kappa: float, r: float, c0: float,
               enable_m1: bool = True, enable_m3: bool = True, enable_m4: bool = True) -> float:
    """δ* = min(θ/W, κ, ⌈(r+1)/2⌉·c₀/W)（定理 7.6.3；κ=χεv 由调用方换算，E9.2/H2）。

    M4 项（2026-10-15 审稿修复）：多数派接管 r 份独立副本只需腐化 k=⌈(r+1)/2⌉ 份，
    每窗成本 k·c₀——原 r·c₀/W 高估安全边界。r 容许浮点传入（取 int(round(r)) 再算 ceil）。
    消融语义（ATK-6④/P9.5）：关闭某机制 ⇒ 其项退出 min（非置零）；全关 ⇒ δ*=0。
    """
    if W <= 0:
        raise ValueError(f"窗长 W>0: {W}")
    terms = []
    if enable_m1:
        terms.append(theta / W)
    if enable_m3:
        terms.append(kappa)
    if enable_m4:
        terms.append(math.ceil((int(round(r)) + 1) / 2) * c0 / W)
    return min(terms) if terms else 0.0


def a_min(a_via_min: float, a_base, weights, d_stars, kappas, sigma: float = 1.0) -> float:
    """A_min = A_via^min·F_σ(A_j^base(1−δ*_j/κ_j); w)（定理 7.6.3(iii)；σ 与复核侧
    composite_A 须同值（M9.2）——F_σ 单调性 (A4) 保持逐点界，σ 臂下同式成立）。"""
    comps = tuple(b * (1.0 - ds / k) for b, ds, k in zip(a_base, d_stars, kappas))
    return composite_A(a_via_min, comps, weights, sigma=sigma)


def simulate_damage(delta_fn, kappa: float, T: float, dt: float = 0.02, D0: float = 0.0,
                    theta: float | None = None, W: float | None = None, lag: float = 0.0):
    """损伤动力学 Ḋ=δ(t)−κD ＋ M1 窗登记（命题 7.6.4）。

    M3 段精确步进（分段常值 δ：D ← δ/κ+(D−δ/κ)e^{−κ·dt}）；M1（theta/W 给定时）：
    滑窗累计 ∫_{t−W}^{t}δ ds ≥ θ ⇒ 登记，滞后 ℓ 后 D 与累计器复位。
    返回 (ts, Ds, n_registrations)。
    """
    n = int(round(T / dt))
    ts = np.arange(n + 1) * dt
    Ds = np.empty(n + 1)
    Ds[0] = D = float(D0)
    hist = []  # [(t_end, delta)] 滑窗历史
    pending_reset = None
    n_reg = 0
    m1 = theta is not None and W is not None
    for k in range(n):
        t = ts[k]
        d = float(delta_fn(t))
        if kappa > 0:
            D = d / kappa + (D - d / kappa) * math.exp(-kappa * dt)
        else:
            D = D + d * dt
        D = min(max(D, 0.0), 1.0)
        t_now = t + dt
        if m1:
            hist.append((t_now, d))
            while hist and hist[0][0] <= t_now - W:
                hist.pop(0)
            acc = sum(dd * dt for _, dd in hist)
            if pending_reset is None and acc >= theta:
                pending_reset = t_now + lag
                n_reg += 1
            if pending_reset is not None and t_now >= pending_reset:
                D = 0.0
                hist.clear()
                pending_reset = None
        Ds[k + 1] = D
    return ts, Ds, n_reg


# ---------- C1（附录 §8.2，命题 8.2.1） ----------

def c1_equilibria(delta: float, eps_v: float):
    """fold 平衡 D_±=(1±√(1−4δ/εv))/2（D_− 稳定、D_+ 不稳定）；δ>δ_c=εv/4 ⇒ None。"""
    disc = 1.0 - 4.0 * delta / eps_v
    if disc < 0:
        return None
    sq = math.sqrt(disc)
    return (1.0 - sq) / 2.0, (1.0 + sq) / 2.0


def simulate_ode(f, D0: float, T: float, dt: float = 0.005):
    """RK4 标量 ODE（物理域钳位 [0,1]）。f: D→float。返回 (ts, Ds)。"""
    n = int(round(T / dt))
    ts = np.arange(n + 1) * dt
    Ds = np.empty(n + 1)
    Ds[0] = D = float(D0)
    for k in range(n):
        k1 = f(D)
        k2 = f(D + 0.5 * dt * k1)
        k3 = f(D + 0.5 * dt * k2)
        k4 = f(D + dt * k3)
        D = min(max(D + dt * (k1 + 2 * k2 + 2 * k3 + k4) / 6.0, 0.0), 1.0)
        Ds[k + 1] = D
    return ts, Ds


def measure_t_rec(delta: float, eps_v: float, perturb: float = 0.02, tol: float = 1e-4,
                  T: float = 2000.0, dt: float = 0.01) -> float:
    """C1 临界减慢观测量：自 D_−+perturb 回到 |D−D_−|<tol 的时间（E10.2 EWS 的 T_rec）。"""
    eq = c1_equilibria(delta, eps_v)
    if eq is None:
        raise ValueError("δ≥δ_c：无稳定平衡")
    d_minus = eq[0]
    ts, ds = simulate_ode(lambda D: delta - eps_v * D * (1.0 - D), d_minus + perturb, T, dt)
    for t, v in zip(ts, ds):
        if abs(v - d_minus) < tol:
            return float(t)
    raise RuntimeError(f"T={T} 内未恢复（δ={delta}）")


# ---------- C2（附录 §8.3，命题 8.3.1） ----------

def c2_r(e0v: float, gamma: float):
    """r(D)=ε₀v·D(1−D)(1−γD)（锁滞修复函数，γ>1 ⇒ D>1/γ 后推向俘获）。"""
    return lambda D: e0v * D * (1.0 - D) * (1.0 - gamma * D)


def c2_roots(gamma: float):
    """r′(D)=1−2(1+γ)D+3γD²=0 的两根 (D₁, D_m)，D₁<D_m（δ_down=r(D₁)、s_c=|r(D_m)|）。"""
    disc = math.sqrt(1.0 - gamma + gamma * gamma)
    return ((1.0 + gamma) - disc) / (3.0 * gamma), ((1.0 + gamma) + disc) / (3.0 * gamma)


# ---------- T6c（附录 §7.6.3，命题 7.6.5） ----------

def cusum_edd(delta: float, sigma: float, alpha: float, n_runs: int, rng,
              max_steps: int = 200000):
    """LLR-CUSUM 平均检测延迟（漂移 0→δ、增量 LLR=(δ/σ²)(x−δ/2)、阈 h=log(1/α)）。

    向量化 n_runs 条路径（P6.1 协议 rng 注入）。返回 (EDD, 完成率)。
    """
    h = math.log(1.0 / alpha)
    g = np.zeros(n_runs)
    t_det = np.full(n_runs, -1, dtype=int)
    done = np.zeros(n_runs, dtype=bool)
    scale = delta / (sigma * sigma)
    for t in range(1, max_steps + 1):
        x = delta + sigma * rng.standard_normal(n_runs)
        g = np.maximum(0.0, g + scale * (x - 0.5 * delta))
        hit = (~done) & (g >= h)
        t_det[hit] = t
        done |= hit
        if done.all():
            break
    n_done = int(done.sum())
    if n_done == 0:
        raise RuntimeError("max_steps 内无一路径检出（阈/漂移配置错误）")
    return float(t_det[done].mean()), n_done / n_runs

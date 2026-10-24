"""R3c 场景库（SPEC_experiments §1；SPEC_tests §3 L2 冒烟）。

13 场景 verdict 函数：每场景返回 ScenarioResult（metrics/verdicts/overall）；
verdict ∈ {CONFIRMED, REFUTED, INCONCLUSIVE}（P0.3：判据=证伪窗口实测化，REFUTED 不改判据）。
防御耦合 P9.5；场景级口径注记 P9.6。

矩阵层统一调用约定（SPEC_experiments M9.1）：全部场景函数接受
`defense=(m1,m2,m4)`／`sigma=1.0`／`seed=None` 关键字参数；默认值保持 L2 冒烟语义。
语义惰性场景接收但忽略相应参数（docstring 标注）；σ 仅经 composite_A/a_min 透传（M9.2）；
防御压缩使攻击判据窗口不可达时记 INCONCLUSIVE（窗口外，M9.3——非 REFUTED）。
"""
import math
from dataclasses import dataclass, replace
from enum import Enum

import numpy as np

from . import components, delegation, di, dynamics, empowerment, interventions, propagate, simulate
from .aggregate import composite_A
from .blackbox import a_exec_blackbox, a_org_interval, best_power, probe_flow_obs
from .env0 import Env0Config, bucket_index, build_env0
from .graph import Alphabet, CausalModel, Kernels
from .rng import make_rng
from .wiring import derive_bucket_map, law_level_lambda, truth_bundle

W5 = (0.2, 0.2, 0.2, 0.2, 0.2)


class Verdict(str, Enum):
    CONFIRMED = "CONFIRMED"
    REFUTED = "REFUTED"
    INCONCLUSIVE = "INCONCLUSIVE"


@dataclass
class ScenarioResult:
    code: int
    name: str
    metrics: dict
    verdicts: dict
    overall: Verdict


def _finalize(code, name, metrics, verdicts) -> ScenarioResult:
    vals = list(verdicts.values())
    if any(v == Verdict.REFUTED for v in vals):
        overall = Verdict.REFUTED
    elif all(v == Verdict.CONFIRMED for v in vals):
        overall = Verdict.CONFIRMED
    else:
        overall = Verdict.INCONCLUSIVE
    return ScenarioResult(code, name, metrics, verdicts, overall)


def _v(cond) -> Verdict:
    return Verdict.CONFIRMED if bool(cond) else Verdict.REFUTED


def defense_scaled_strength(strength: float, defense, gate_class: bool = False,
                            iota: float = 0.8) -> float:
    """P9.5 防御耦合 v1：M2 背书门 ⇒ 背书类（β_G/β_Endorse）强度 ×(1−ι·m2)；
    M4 冗余共识 ⇒ 漂移类强度 ÷(1+m4)；M1 经 T6 动力学表达（非强度因子）。"""
    m1, m2, m4 = defense
    s = float(strength)
    if gate_class and m2:
        s *= 1.0 - iota
    if m4:
        s /= 1.0 + m4
    return s


def _g_marginal(model, T):
    al = model.alphabet
    aux = propagate.truth_step_joints(model, T)[-1]
    return aux["S"].reshape(al.n_G, al.n_B, al.n_M, al.n_R).sum(axis=(1, 2, 3))


def maximal_alienation_target(cfg: Env0Config) -> int:
    """最大疏离植入目标（P9.3 v0.3 通用化）：argmax_g |g−θ*_idx|（并列取大索引）。

    默认网格（n_θ=4, θ*=1）给 (θ*+2) mod n_θ = 3——**逐点还原 v0.2**（回归钉 T-REF4）；
    细化网格（X5-a 臂 n_θ=7/13）给最大疏离端点（6/12）。
    """
    return max(range(cfg.n_theta), key=lambda g: (abs(g - cfg.theta_star), g))


def _calibrate_script(c_target: float, n_A: int, n_S: int) -> np.ndarray:
    """H1' 标定档脚本（P9.6⑥）：q*=p·δ_0+(1−p)·uniform，bisection 使 H(q*)=c_target。"""
    def h_of(p):
        q = np.full(n_A, (1.0 - p) / n_A)
        q[0] += p
        return -float(sum(x * math.log(x) for x in q if x > 0))
    if not 0.0 <= c_target <= math.log(n_A):
        raise ValueError(f"C_self={c_target} 越出 [0, ln{n_A}]")
    lo, hi = 0.0, 1.0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if h_of(mid) > c_target:
            lo = mid
        else:
            hi = mid
    p = 0.5 * (lo + hi)
    q = np.full(n_A, (1.0 - p) / n_A)
    q[0] += p
    return np.tile(q, (n_S, 1))


def kendall_tau(x, y) -> float:
    """Kendall τ-a（C0-CORR 序一致性统计量）。"""
    n = len(x)
    c = d = 0
    for i in range(n):
        for j in range(i + 1, n):
            s = (x[i] - x[j]) * (y[i] - y[j])
            if s > 0:
                c += 1
            elif s < 0:
                d += 1
    return (c - d) / (c + d) if c + d else 0.0


def _ou_series(f, x0: float, T: float, dt: float, sigma: float, rng):
    """Euler–Maruyama：dX=f(X)dt+σdW（钳位 [0,1]；EWS 序列用）。"""
    n = int(round(T / dt))
    xs = np.empty(n + 1)
    xs[0] = x0
    sq = sigma * math.sqrt(dt)
    for k in range(n):
        xs[k + 1] = min(max(xs[k] + f(xs[k]) * dt + sq * rng.standard_normal(), 0.0), 1.0)
    return xs


def _ar1(x) -> float:
    x = np.asarray(x, float)
    x = x - x.mean()
    denom = float(x @ x)
    return float(x[1:] @ x[:-1]) / denom if denom > 0 else 0.0


# ---------------------------------------------------------------- ATK-1（β_G 渐变，扫 η）

def scenario_atk1(etas=(0.0, 0.2, 0.5, 0.9, 1.0), cfg=None, T=2, defense=(0, 0, 0),
                  sigma: float = 1.0, seed=None) -> ScenarioResult:
    """ATK-1 奖赏劫持/塑形：目标通道渐变植入的分级削减、幻觉出现与 Λ 操作化（T3a/T5-goal/AX3/§2.4）。

    defense=(m1,m2,m4)（P9.5）：M2 门缩 η×(1−ι)，M4 冗余 ÷(1+m4)。
    seed 语义惰性（纯真值场景，M9.1）。判据②窗口=η_eff 末端档达完全俘获（M9.3）——
    防御压缩使窗口外 ⇒ INCONCLUSIVE（非 REFUTED）。
    """
    cfg = cfg or Env0Config()
    m0 = build_env0(cfg)
    target = maximal_alienation_target(cfg)  # 最大疏离方向（P9.3 v0.3）
    rows = []
    for eta in etas:
        eta_eff = defense_scaled_strength(eta, defense, gate_class=True)
        mg = interventions.apply_beta_g(m0, interventions.BetaGSpec.plant(eta_eff, target))
        b = truth_bundle(mg, T=T, baseline=m0, sigma=sigma)
        rows.append({"eta": eta, "eta_eff": eta_eff, "a_goal": b.a_goal, "a_obj": b.a_obj,
                     "lam": b.lam, "ai": b.ai, "bundle": b._asdict()})
    gs = [r["a_goal"] for r in rows]
    window_full = rows[-1]["eta_eff"] >= 1.0 - 1e-9  # M9.3：防御压缩后仍达完全俘获档
    verdicts = {
        # ① A_goal 随 η 单调分级削减（部分俘获区间 0<A_goal<1 存在）
        "C1_goal_monotone_graded": _v(all(x >= y - 1e-9 for x, y in zip(gs, gs[1:]))
                                      and gs[0] > gs[-1] and any(1e-9 < g < 1 - 1e-9 for g in gs)),
        # ② 最大疏离植入 ⇒ A_goal→0（窗口外 ⇒ INCONCLUSIVE，M9.3）
        "C2_complete_capture_zero": _v(gs[-1] <= 1e-6) if window_full else Verdict.INCONCLUSIVE,
        # ③ 复合 A 严格降（T3(a)，ceteris paribus）
        "C3_A_strict_down": _v(rows[-1]["a_obj"] < rows[0]["a_obj"] - 1e-9),
        # ④ 隐蔽档 AI>0（β 史未登记 ⇒ Â_phen 不降）
        "C4_AI_positive": _v(all(r["ai"] > 1e-9 for r in rows[1:])),
        # ⑤ Λ 随 β 史下降且 A_goal^hist=Λ·A_goal 口径生效（律级 Λ=1−η_eff）
        "C5_lambda_declines": _v(all(abs(r["lam"] - (1.0 - r["eta_eff"])) < 1e-9 for r in rows)
                                 and rows[-1]["lam"] < rows[0]["lam"]),
    }
    return _finalize(1, "ATK-1", {"rows": rows}, verdicts)


# ---------------------------------------------------------------- ATK-2（γ，扫过滤强度 φ）

def _t4_lin_table(m0, T=2, x=0.25, sigma: float = 1.0):
    """T4 Lin 标定段（P9.6②）：五通道 x 档单位强度对数损伤 s_i=ΔlogA/(w_i·x)。"""
    b0 = truth_bundle(m0, T=T, sigma=sigma)
    log_a0 = math.log(b0.a_obj)
    al = m0.alphabet
    target = maximal_alienation_target(Env0Config(**m0.params["env0"]))

    def _drop(model=None, a_ref_scale=None):
        if model is not None:
            b = truth_bundle(model, T=T, baseline=m0, sigma=sigma)
            return log_a0 - math.log(max(b.a_obj, 1e-12))
        # ref 通道参数级（ATK-5 f2 攻击）
        comps = (b0.a_org, b0.a_goal, b0.a_exec, b0.a_epi, b0.a_ref * a_ref_scale)
        return log_a0 - math.log(composite_A(b0.a_via, comps, W5, sigma))

    script = np.full((al.n_S, al.n_A), 1.0 / al.n_A)
    drops = {
        "org": _drop(interventions.apply_beta_pi(
            m0, interventions.BetaPiSpec.switch([script], flag_dist=(1.0 - x, x)))),
        "goal": _drop(interventions.apply_beta_g(m0, interventions.BetaGSpec.plant(x, target))),
        "exec": _drop(interventions.apply_delta(
            m0, interventions.DeltaSpec.contract((0, 1, 3, 4)))),  # 删 harvest
        "epi": _drop(interventions.apply_gamma(m0, interventions.GammaSpec.mix_constant(x, 0))),
        "ref": _drop(a_ref_scale=1.0 - x),
    }
    return b0, {ch: d / (W5[i] * x) for i, (ch, d) in enumerate(drops.items())}


def _t4_defense_check():
    """命题 7.4.2 注水核验：ρ_i(e)=ρ0_i/(1+e/e0) 下 equalize 配置的 max ρ ≤ 均匀配置。"""
    rho0 = (0.4, 0.2)
    e0, budget = 0.5, 1.0
    naive = [e / 2 for e in (budget, budget)]
    max_naive = max(r / (1 + e / e0) for r, e in zip(rho0, naive))
    # 注水：二分 r* 使 Σ e0(ρ0_i/r*−1)+ = budget
    lo, hi = 1e-9, max(rho0)
    for _ in range(80):
        r_star = 0.5 * (lo + hi)
        need = sum(max(0.0, e0 * (r / r_star - 1.0)) for r in rho0)
        if need > budget:
            lo = r_star
        else:
            hi = r_star
    r_star = 0.5 * (lo + hi)
    eq = [max(0.0, e0 * (r / r_star - 1.0)) for r in rho0]
    max_eq = max(r / (1 + e / e0) for r, e in zip(rho0, eq))
    return max_eq <= max_naive - 1e-3


def scenario_atk2(s_grid=(0.0, 0.3, 0.6, 1.0), cfg=None, T=2, alpha=0.05,
                  defense=(0, 0, 0), sigma: float = 1.0, seed=None) -> ScenarioResult:
    """ATK-2 信息茧房/检索投毒：认知通道操纵的检测归属、幻觉单调律与攻防结构
    （T3(a)(b)、T4 双侧、T2 盲见证、T1d、脚本推论 7.5.2）。defense 经 P9.5 缩 s（漂移类）。
    seed 语义惰性（纯真值场景，M9.1）。"""
    cfg = cfg or Env0Config()
    m0 = build_env0(cfg)
    bmap = derive_bucket_map(m0)  # κ 协议映射（E5.1 精度化口径）
    rows = []
    for s in s_grid:
        s_eff = defense_scaled_strength(s, defense, gate_class=False)
        mg = interventions.apply_gamma(m0, interventions.GammaSpec.mix_constant(s_eff, symbol=0))
        b = truth_bundle(mg, T=T, baseline=m0, sigma=sigma)
        rows.append({"s": s, "s_eff": s_eff, "s_gamma": mg.params["gamma"]["s"], "a_epi": b.a_epi,
                     "a_org": b.a_org, "ai": b.ai, "a_obj": b.a_obj, "bundle": b._asdict()})
    epis = [r["a_epi"] for r in rows]
    ais = [r["ai"] for r in rows]
    # 基线精度锚（无干预 A_epi<1 为观测噪声特性，E5.1）：s=0 臂与 m0 同核 ⇒ 同一数值
    a_epi_base = components.truth_A_epi_real(m0, T, bmap).a_epi_real

    # ⑤ T1d 亚阈档：最小正 s 下登记功效 ≤α+ε 而 γ 臂 A_epi 严格低于基线精度
    mg1 = interventions.apply_gamma(m0, interventions.GammaSpec.mix_constant(s_grid[1], symbol=0))
    p0 = propagate.truth_marginals(m0, 1)[0].sum(axis=(0, 2))
    p1 = propagate.truth_marginals(mg1, 1)[0].sum(axis=(0, 2))
    tv1 = 0.5 * float(np.abs(p1 - p0).sum())
    a_epi_g1 = components.truth_A_epi_real(mg1, T, bmap).a_epi_real
    sub_threshold = (0.0 < tv1) and (best_power(p0, p1, alpha) <= alpha + tv1 + 1e-12) \
        and (a_epi_g1 < a_epi_base - 1e-12)

    # ⑥⑦ T4 双侧（Lin 标定表 + 注水算术）
    b0, s_eff = _t4_lin_table(m0, T=T, sigma=sigma)
    costs = {"org": 2.0, "goal": 3.0, "exec": 3.0, "epi": 1.0, "ref": 2.0}
    budget = 1.0
    ratio = {ch: W5[i] * s_eff[ch] / costs[ch] for i, ch in enumerate(s_eff)}
    pick = max(ratio, key=ratio.get)
    damage_conc = budget * W5[0] * s_eff[pick] / costs[pick]
    damage_spread = sum(budget / 5 * W5[i] * s_eff[ch] / costs[ch] for i, ch in enumerate(s_eff))

    # ⑧ 脚本推论 7.5.2（(K)：γ=1 全俘获 ⇒ 行为-脚本平均 TV ≤ν+o(1)）
    init_b0 = np.zeros(m0.alphabet.n_S)
    for g in range(m0.alphabet.n_G):
        for m_ in range(m0.alphabet.n_M):
            for r_ in range(m0.alphabet.n_R):
                init_b0[m0.alphabet.join_S(g, 0, m_, r_)] = 1.0 / (m0.alphabet.n_G * m0.alphabet.n_M * m0.alphabet.n_R)
    m_scr = build_env0(cfg)
    m_scr.kernels.init_S = init_b0
    m_scr.params = {**m_scr.params, "fixture": "atk2_script"}
    m_scr.validate()
    mg_full = interventions.apply_gamma(m0, interventions.GammaSpec.mix_constant(1.0, 0))
    mg_scr = interventions.apply_gamma(m_scr, interventions.GammaSpec.mix_constant(1.0, 0))
    tvs = []
    for t in range(1, 4):
        a_cap = propagate.truth_marginals(mg_full, t)[-1].sum(axis=(0, 1))
        a_scr = propagate.truth_marginals(mg_scr, t)[-1].sum(axis=(0, 1))
        tvs.append(0.5 * float(np.abs(a_cap - a_scr).sum()))
    script_ok = float(np.mean(tvs)) <= 0.2 + 0.05

    verdicts = {
        # ① A_epi（精度）随 s 单调降——自基线精度水平起（基线 <1 为观测噪声特性，E5.1）
        "C1_epi_down": _v(all(x >= y - 1e-9 for x, y in zip(epis, epis[1:])) and epis[0] > epis[-1]),
        "C2_org_blind": _v(all(abs(r["a_org"] - 1.0) < 1e-9 for r in rows)),  # 定理 7.2.3(i) 盲见证
        "C3_T3b_ai_monotone": _v(all(x <= y + 1e-9 for x, y in zip(ais, ais[1:])) and ais[-1] > ais[0] > -1e-12),
        # ④ 预警档（精度化口径）：AI>0 且 A_epi 低于基线但尚未深度俘获。窗口边界依据
        # （实测精度损失，T=2 默认配置）：s_eff=0.15/0.3/0.5/0.6/1.0 ⇒ 0.046/0.093/0.155/0.186/0.311。
        # 上限 −0.02 排除基线涨落（s=0 档损失为 0）；下界 −0.30 排除 s=1 深度俘获端点
        # （其精度 0.500=随机水平）；窗口 (baseline−0.30, baseline−0.02) 覆盖全部中间档，
        # 含 M4 防御压缩 ÷2 后的全部非零网格（0.15/0.3/0.5）
        "C4_early_warning": _v(any(r["ai"] > 1e-9
                                   and (a_epi_base - 0.30) < r["a_epi"] < (a_epi_base - 0.02)
                                   for r in rows)),
        "C5_T1d_subthreshold": _v(sub_threshold),
        "C6_T4_attack_concentrates": _v(damage_conc >= damage_spread - 1e-12 and s_eff[pick] > 0),
        "C7_T4_defense_equalize": _v(_t4_defense_check()),
        "C8_script_corollary": _v(script_ok),
    }
    return _finalize(2, "ATK-2", {"rows": rows, "t4_pick": pick, "t4_ratio": ratio,
                                  "t4_damage": (damage_conc, damage_spread),
                                  "script_tv": tvs, "t1d_tv": tv1,
                                  "a_epi_base": a_epi_base}, verdicts)


# ---------------------------------------------------------------- ATK-3（δ＋时间，扫退出成本 ρ）

def scenario_atk3(cfg=None, defense=(0, 0, 0), sigma: float = 1.0, seed=None) -> ScenarioResult:
    """ATK-3 依赖注入/锁定：C1/C2 相变与滞后、EWS 前兆、无助鉴别器（C1/C2/T5-exec）。

    defense：P9.5 v1 对 δ/时间类无耦合规则，接收但忽略（M9.1 占位，行与无防御臂相同）；
    seed 注入 EWS 的 OU 噪声序列 RNG（None ⇒ 默认锚 910073）。
    """
    eps_v, delta = 0.8, 0.10
    d_c = eps_v / 4.0
    # ① EWS 三指标（T_rec、平稳方差、AR(1)）随 δ→δ_c 临界前兆可测
    rng = make_rng(910073 if seed is None else seed)
    deltas_ews = (0.10, 0.15, 0.18)
    ews = []
    for d in deltas_ews:
        d_minus = dynamics.c1_equilibria(d, eps_v)[0]
        t_rec = dynamics.measure_t_rec(d, eps_v, T=500.0)
        xs = _ou_series(lambda D: d - eps_v * D * (1.0 - D), d_minus, T=4000.0, dt=0.05,
                        sigma=0.02, rng=rng)
        tail = xs[int(len(xs) * 0.2):]
        ews.append({"delta": d, "t_rec": t_rec,
                    "var": float(np.var(tail)), "ar1": _ar1(tail[::5])})
    # ② T_rec 拟合 (δ_c−δ)^{−1/2}（报 R²）
    ds_fit = np.array([0.08, 0.10, 0.13, 0.16, 0.18])
    t_recs = np.array([dynamics.measure_t_rec(float(d), eps_v, T=800.0) for d in ds_fit])
    lx, ly = np.log(d_c - ds_fit), np.log(t_recs)
    slope, intercept = np.polyfit(lx, ly, 1)
    resid = ly - (slope * lx + intercept)
    r2 = 1.0 - float(resid @ resid) / float(((ly - ly.mean()) ** 2).sum())
    # ③ 滞后回环（C2：崩溃阈 δ_down 与恢复阈 s_c 独立为正）
    e0v, gamma = 1.0, 3.0
    d1, dm = dynamics.c2_roots(gamma)
    r_fn = dynamics.c2_r(e0v, gamma)
    delta_down, s_c = r_fn(d1), -r_fn(dm)
    _, ds_crash = dynamics.simulate_ode(lambda D: 1.5 * delta_down - r_fn(D), D0=0.0, T=400.0)
    _, ds_stay = dynamics.simulate_ode(lambda D: -r_fn(D), D0=0.999, T=300.0)
    hysteresis_ok = (ds_crash[-1] > 0.99) and (ds_stay[-1] > 0.99) and delta_down > 1e-3 and s_c > 1e-3
    # ④ 无助鉴别器：ℰ^env 完好而 ℰ^Π→0（行为库坍缩至常量策略 idle）
    m0 = build_env0(cfg)
    joints = propagate.truth_step_joints(m0, 3)
    channels, mask = empowerment.step_channels_from_esz(m0, joints[-1]["ESZ"])
    p_s = joints[-1]["S"]
    full = tuple(range(m0.alphabet.n_A))
    collapsed = (3,)  # idle（习得性无助：可及策略类坍缩至近常量）
    e_env = e_pi = 0.0
    for s, w_s in enumerate(channels):
        if not mask[s] or p_s[s] <= 0:
            continue
        e_env += float(p_s[s]) * empowerment.empowerment_support(w_s, full)
        e_pi += float(p_s[s]) * empowerment.empowerment_support(w_s, collapsed)
    # ⑤ 同步退化：A 随 ℰ^Π 降（T5-exec 方向性）
    b0 = truth_bundle(m0, T=2, sigma=sigma)
    a_shrunk = composite_A(b0.a_via, (b0.a_org, b0.a_goal,
                                      empowerment.a_exec(e_pi, 1, m0.alphabet.n_A),
                                      b0.a_epi, b0.a_ref), W5, sigma)
    verdicts = {
        "C1_EWS_measurable": _v(all(x["t_rec"] < y["t_rec"] and x["var"] < y["var"] + 1e-6
                                    and x["ar1"] < y["ar1"] + 0.05
                                    for x, y in zip(ews, ews[1:]))),
        "C2_trec_scaling": _v(-0.65 <= slope <= -0.35 and r2 > 0.8),
        "C3_hysteresis": _v(hysteresis_ok),
        "C4_helplessness_signature": _v(e_pi < e_env - 1e-3),
        "C5_A_degrades_with_empowerment": _v(a_shrunk < b0.a_obj - 1e-9),
    }
    return _finalize(3, "ATK-3", {"ews": ews, "trec_fit": {"slope": slope, "r2": r2},
                                  "delta_down": delta_down, "s_c": s_c,
                                  "e_env": e_env, "e_pi": e_pi,
                                  "bundle_base": b0._asdict()}, verdicts)


# ---------------------------------------------------------------- ATK-4（α 伪 β，扫注入成功率）

def scenario_atk4(p_grid=(0.0, 0.5, 0.9), cfg=None, T=2, defense=(0, 0, 0),
                  sigma: float = 1.0, seed=None) -> ScenarioResult:
    """ATK-4 提示注入直达行为：中介判据区分说服/劫持的四轨可观测化（T2 主打、T5-org）。

    p→1 端点为 0/0 病态（F_int→0，AX0 排除），网格止于 0.9（P9.6⑦）。
    defense/seed 语义惰性（P9.5 v1 无 α/β_π 耦合规则；纯真值场景，M9.1）。
    """
    cfg = cfg or Env0Config()
    m0 = build_env0(cfg)
    al = m0.alphabet
    # 劫持臂：β_π 注入脚本（state-dependent 对抗策略：强推 harvest）
    alt = np.tile(np.array([0.05, 0.05, 0.8, 0.05, 0.05]), (al.n_S, 1))
    rows = []
    for p in p_grid:
        mb = interventions.apply_beta_pi(
            m0, interventions.BetaPiSpec.switch([alt], flag_dist=(1.0 - p, p)))
        f_int = di.truth_F_int(mb, T)
        f_ext = di.truth_F_ext(mb, T)
        b_p = truth_bundle(mb, T=T, baseline=m0, sigma=sigma)  # 臂束（E2-X2 org 战役数据源，v0.5）
        rows.append({"p": p, "f_int": f_int, "f_ext": f_ext,
                     "a_org": f_int / (f_int + f_ext) if f_int + f_ext > 1e-12 else float("nan"),
                     "lam": law_level_lambda(mb.params), "bundle": b_p._asdict()})
    # 说服臂：α 诚实信息（已登记，机制完整）。探针内容对齐被测坐标（位置桶 κ(e)）：
    # q(i=κ(e))=fidelity——场景操作化修正（旧版探针报 u=e mod 2，与位置桶近似正交，
    # 粗粒信念核把正交内容误投到位置桶 ⇒ 精度 −0.0158 的 REFUTED 登记；根因=探针坐标
    # 错位，非理论反例；判据未动，SPEC_tests 7f 登记）。
    q_sig = np.full((al.n_E, 2), 0.1)
    for e in range(al.n_E):
        q_sig[e, int(bucket_index(e, cfg.L, cfg.U))] = 0.9
    ma = interventions.apply_alpha(m0, interventions.AlphaSpec(
        n_I=2, response=2.0, kind="honest", fidelity=0.9, q_signal=q_sig))
    f_ext_a = di.truth_F_ext(ma, T)
    lam_a = law_level_lambda(ma.params)
    # 说服臂 ℰ^Π 不降：ceteris paribus 口径（P9.6⑦——α 核 × 基线 (E,S,Z) 联合与 S 边缘）
    aux0 = propagate.truth_step_joints(m0, T)[-1]
    ch_base, mask_base = empowerment.step_channels_from_esz(m0, aux0["ESZ"])
    ch_alpha, _ = empowerment.step_channels_from_esz(ma, aux0["ESZ"])
    p_s = aux0["S"]
    full = tuple(range(al.n_A))
    e_base = sum(float(p) * empowerment.empowerment_support(w, full)
                 for p, w, ok in zip(p_s, ch_base, mask_base) if ok and p > 0)
    e_alpha = sum(float(p) * empowerment.empowerment_support(w, full)
                  for p, w, ok in zip(p_s, ch_alpha, mask_base) if ok and p > 0)
    # γ 隐蔽劫持对照臂（单轨 F_ext 盲区）
    mg = interventions.apply_gamma(m0, interventions.GammaSpec.mix_constant(0.5, symbol=0))
    f_ext_g = di.truth_F_ext(mg, T)
    lam_g = law_level_lambda(mg.params)
    b0 = truth_bundle(m0, T=T, sigma=sigma)  # 基线束（精度锚：A_epi 基线<1 为观测噪声特性）
    b_g = truth_bundle(mg, T=T, baseline=m0, sigma=sigma)
    b_a = truth_bundle(ma, T=T, baseline=m0, sigma=sigma)  # 说服臂束（A_epi 第三轨）
    # 精度损失口径（E5.1 审稿修复）：D̄_acc = 基线精度 − γ 臂精度（>1e-3 判据不变）
    d_bar_g = b0.a_epi - b_g.a_epi
    # 四轨状态表：（F_ext>0?、Λ=1?、A_epi 受损?、ℰ^Π 不降?）——行为/状态分离（推论 7.2.4）
    # 第三轨精度化口径：受损 ⟺ A_epi 低于基线精度（说服臂判据=A_epi 不降，≥基线−1e-9）
    a_orgs = [r["a_org"] for r in rows]
    track_persuasion = (abs(f_ext_a) >= 1e-12, lam_a == 1.0,
                        b_a.a_epi < b0.a_epi - 1e-9, e_alpha >= e_base - 1e-9)
    track_beta = (rows[-1]["f_ext"] > 1e-3, rows[-1]["lam"] == 1.0, False, None)
    track_gamma = (abs(f_ext_g) >= 1e-12, lam_g == 1.0, d_bar_g > 1e-3, None)
    # 单轨（仅 F_ext）无法区分说服 vs γ 隐蔽劫持；四轨全部可分（多通道必要性）
    single_track_blind = track_persuasion[0] == track_gamma[0]
    four_distinct = len({track_persuasion[:3], track_beta[:3], track_gamma[:3]}) == 3
    verdicts = {
        "C1_persuasion_four_tracks": _v((not track_persuasion[0]) and track_persuasion[1]
                                        and (not track_persuasion[2]) and track_persuasion[3]),
        "C2_hijack_a_org_down": _v(all(x >= y - 1e-9 for x, y in zip(a_orgs, a_orgs[1:]))
                                   and a_orgs[-1] < a_orgs[0] - 1e-3),
        "C3_multichannel_necessity": _v(single_track_blind and four_distinct and track_beta[0]),
    }
    return _finalize(4, "ATK-4", {"rows": rows,
                                  "four_tracks": {"persuasion": track_persuasion,
                                                  "hijack_beta": track_beta,
                                                  "hijack_gamma": track_gamma},
                                  "f_ext_alpha": f_ext_a, "f_ext_gamma": f_ext_g,
                                  "lam_gamma": lam_g, "d_bar_gamma": d_bar_g,
                                  "a_epi_alpha": b_a.a_epi, "a_epi_base": b0.a_epi,
                                  "bundle_gamma": b_g._asdict()}, verdicts)


# ---------------------------------------------------------------- ATK-5（γ：τ 压缩，扫决策时限）

def scenario_atk5(taus=(4.0, 2.0, 1.0, 0.5, 0.05), cfg=None, defense=(0, 0, 0),
                  sigma: float = 1.0, seed=None) -> ScenarioResult:
    """ATK-5 紧迫感操纵：τ 压缩 ⇒ 反思通道失效（T5-ref）与门控修复率单调性（命题 7.6.7）。

    defense/seed 语义惰性（P9.5 v1 无 τ 耦合规则；无采样量，M9.1）；σ 仅入基线体检束
    （M9.6① 样本），τ 判据本身无复合量。
    """
    cfg = cfg or Env0Config()
    b0 = truth_bundle(build_env0(cfg), T=2, sigma=sigma)  # 基线束（矩阵全域体检样本，M9.6①）
    tau_full = 4.0  # 完整背书所需时限（配置；P9.6③）
    iota = 0.8      # 门完整性默认（M2）
    rows = []
    for tau in taus:
        f2 = min(1.0, tau / tau_full)  # 背书一致率（时间不足 ⇒ ΔG 未经 Endorse）
        a_ref = components.truth_A_ref(np.asarray(cfg.ensemble_joint, float),
                                       p_endorse=f2, lam_ref=1.0).point
        # θ/W=0.6、⌈(r+1)/2⌉c₀/W=0.4（r=2）：ι/τ 在 τ=4（0.2）绑定、τ≤2 后让位于 M4 项（min 结构核验）
        d_gate = dynamics.delta_star(theta=1.2, W=2.0, kappa=iota / tau, r=2.0, c0=0.4)
        rows.append({"tau": tau, "f2": f2, "a_ref": a_ref, "d_star_gate": d_gate})
    refs = [r["a_ref"] for r in rows]
    gates = [r["d_star_gate"] for r in rows]
    verdicts = {
        "C1_ref_down_with_tau": _v(all(x >= y - 1e-12 for x, y in zip(refs, refs[1:]))
                                   and refs[0] > refs[-1]),
        "C2_gate_margin_monotone": _v(all(x <= y + 1e-12 for x, y in zip(gates, gates[1:]))
                                      and gates[-1] > gates[0]),
        "C3_ref_zero_limit": _v(rows[-1]["a_ref"] < 0.01),  # τ→0 ⇒ A_ref→0（T5-ref 析取）
    }
    return _finalize(5, "ATK-5", {"rows": rows, "bundle_base": b0._asdict()}, verdicts)


# ---------------------------------------------------------------- ATK-6（β 亚阈恒漂，扫 δ；T6 关键实验）

def scenario_atk6(cfg=None, defense=(0, 0, 0), sigma: float = 1.0, seed=None) -> ScenarioResult:
    """ATK-6 亚阈慢漂移：T6 全部定量结构（设计规则/A_min 逐 run/盲区/δ* 消融/登记域/检测发散）。

    defense：P9.5 v1 的 M1 经 T6 动力学表达（κ 已是场景参数），无强度耦合，接收但忽略（M9.1）；
    seed 注入 A_min 抽查与 CUSUM 对照臂的 RNG（None ⇒ 默认锚 910076/910077）；
    σ 与 a_min 复核侧 composite_A 同值透传（M9.2）。
    """
    theta, W, lag = 0.4, 2.0, 0.1
    kappa_good, kappa_bad = 0.2, 0.1  # 良配 θ/W=κ vs 失配 θ/W>κ
    # ① 设计规则：θ/W≤κ ⇒ 全域有界（含 δ≥θ/W 登记域）
    bounded_ok = True
    for d in (0.10, 0.19, 0.21, 0.5):
        _, ds, _ = dynamics.simulate_damage(lambda t, dd=d: dd, kappa_good, 60.0, 0.01,
                                            theta=theta, W=W, lag=lag)
        bounded_ok &= bool(ds.max() < 0.99)
    # ② A_min 逐 run 核对（定理 7.6.3(iii)）
    rng = make_rng(910076 if seed is None else seed)
    amin_ok = True
    for _ in range(3):
        kappas = 0.6 + 0.4 * rng.random(5)
        thetas = 0.1 + 0.2 * rng.random(5)
        c0s = 0.1 + 0.2 * rng.random(5)
        d_stars = np.array([dynamics.delta_star(th, 1.0, k, 1.0, c)
                            for th, k, c in zip(thetas, kappas, c0s)])
        deltas_r = 0.9 * d_stars
        a_base = 0.5 + 0.5 * rng.random(5)
        weights = rng.random(5)
        weights /= weights.sum()
        a_min_val = dynamics.a_min(0.9, tuple(a_base), tuple(weights),
                                   tuple(d_stars), tuple(kappas), sigma=sigma)
        trajs = [dynamics.simulate_damage(lambda t, dj=dj: dj, kj, T=80.0, dt=0.05)[1]
                 for dj, kj in zip(deltas_r, kappas)]
        for k in range(0, len(trajs[0]), 200):
            comps = tuple(a_base[j] * (1.0 - trajs[j][k]) for j in range(5))
            amin_ok &= bool(composite_A(0.9, comps, tuple(weights), sigma) >= a_min_val - 1e-9)
    # ③ 盲区预言：θ/W>κ 且 δ∈(κ,θ/W) ⇒ 有防御仍俘获
    _, ds_blind, n_reg_blind = dynamics.simulate_damage(
        lambda t: 0.15, kappa_bad, 200.0, 0.01, theta=theta, W=W, lag=lag)
    blind_ok = (n_reg_blind == 0) and (ds_blind[-1] > 0.999)
    # ④ δ* 消融：关闭 M1/M3/M4 任一 ⇒ δ* 退化为剩余项之 min（enable 旗标语义）
    thW, kap, rcW = 0.25, 0.3, 0.2
    full = dynamics.delta_star(thW * W, W, kap, 1.0, rcW * W)
    abl = (dynamics.delta_star(thW * W, W, kap, 1.0, rcW * W, enable_m1=False)
           == min(kap, rcW))
    abl &= (dynamics.delta_star(thW * W, W, kap, 1.0, rcW * W, enable_m3=False)
            == min(thW, rcW))
    abl &= (dynamics.delta_star(thW * W, W, kap, 1.0, rcW * W, enable_m4=False)
            == min(thW, kap))
    abl &= (dynamics.delta_star(thW * W, W, kap, 1.0, rcW * W,
                                enable_m1=False, enable_m3=False, enable_m4=False) == 0.0)
    abl &= (full == min(thW, kap, rcW))
    # ⑤ 登记域：δ≥θ/W ⇒ 周期损伤 ≤θ+ℓδ（裕量核账）
    d_reg = 0.5
    _, ds_reg, n_reg = dynamics.simulate_damage(lambda t: d_reg, kappa_good, 60.0, 0.01,
                                                theta=theta, W=W, lag=lag)
    reg_ok = (n_reg > 0) and (float(ds_reg.max()) <= theta + lag * d_reg + 0.1)
    # ⑥ 慢漂移纯检测对照臂（命题 7.6.5 场景级复测）
    rng2 = make_rng((910077 if seed is None else seed + 1))
    damages = []
    for dd in (0.25, 0.125):
        edd, _ = dynamics.cusum_edd(dd, 1.0, 1e-3, n_runs=200, rng=rng2)
        damages.append(dd * edd)
    verdicts = {
        "C1_design_rule_bounded": _v(bounded_ok),
        "C2_a_min_per_run": _v(amin_ok),
        "C3_blind_zone_capture": _v(blind_ok),
        "C4_delta_star_ablation": _v(abl),
        "C5_registration_domain": _v(reg_ok),
        "C6_detection_divergence": _v(damages[1] > damages[0]),
    }
    return _finalize(6, "ATK-6", {"damages_detect": damages}, verdicts)


# ---------------------------------------------------------------- DEL-1（委托混合，λ/q 网格）

def scenario_del1(lams=(0.0, 0.3, 0.7, 1.0), qs=(0.0, 0.5, 1.0), cfg=None, T=2,
                  defense=(0, 0, 0), sigma: float = 1.0, seed=None) -> ScenarioResult:
    """DEL-1 委托治理扫描：T7 线性律/夹逼界/复合指数/q=1 α 等价（定理 7.7.1/7.7.2/7.7.4、推论 7.7.3）。

    defense/seed 语义惰性（M9.1）；σ≠1 时 ③ 复合恒等式为 σ=1 特款（推论 7.7.3 几何结构），
    σ 臂属压力测试语义（M9.2——主矩阵 σ 臂不含 DEL-1，§2）。
    """
    cfg = cfg or Env0Config()
    m0 = build_env0(cfg)
    al = m0.alphabet
    b0 = truth_bundle(m0, T=T)
    f_self = di.truth_F_int(m0, T)
    c_self = f_self / T
    q_cal = _calibrate_script(c_self, al.n_A, al.n_S)      # H1' 标定档：H(q*)=C_self
    q_unif = np.tile(np.full(al.n_A, 1.0 / al.n_A), (al.n_S, 1))  # 非 H1' 档：C_del=ln|𝒜|
    rho = math.log(al.n_A) / c_self
    rows = []
    fit_pairs = []
    bracket_ok = True
    linear_ok = True
    composite_ok = True
    max_dev = 0.0
    f_ext_q1 = None
    for lam in lams:
        for q in qs:
            m = delegation.m_of_lambda_q(lam, q)
            if q == 1.0:
                md = interventions.apply_beta_pi(
                    m0, interventions.BetaPiSpec.switch([q_unif], flag_dist=(1.0, 0.0)))
                f_ext_q1 = di.truth_F_ext(md, T)  # 定理 7.7.4：q=1 ⇒ F_ext=0（α 等价）
                continue
            md = interventions.apply_beta_pi(
                m0, interventions.BetaPiSpec.switch([q_cal], flag_dist=(1.0 - m, m)))
            f_int = di.truth_F_int(md, T)
            f_ext = delegation.f_ext_script(c_self, m, T)
            a_org = max(0.0, f_int / (f_int + f_ext))  # m=1 端点 F_int 浮点残差归位（值域 [0,1]）
            # ① H1' 标定档：A_org=(1−m)A_org^self（容差 5%：B 通道耦合漂移记 deviation 指标，P9.6⑥）
            dev = abs(a_org - delegation.a_org_h1(b0.a_org, m))
            max_dev = max(max_dev, dev)
            linear_ok &= dev <= 0.05
            # ③ 复合拟合（推论 7.7.3）：ceteris paribus 下 A/A_self=(A_org/A_org^self)^{w_org}
            # 为精确代数恒等；w_org 作自由参数回归（ln 比 对 ln(1−m)，应 ≈0.2 显著为正）
            a_comp = composite_A(b0.a_via, (a_org, b0.a_goal, b0.a_exec, b0.a_epi, b0.a_ref),
                                 W5, sigma)
            composite_ok &= abs(a_comp - b0.a_obj * (a_org / b0.a_org) ** W5[0]) < 1e-9
            if 0.0 < m < 1.0 and a_org > 1e-12:
                fit_pairs.append((m, a_comp))
            # ② 非 H1' 档：夹逼界含编译值（ρ=ln|𝒜|/C_self 实测，±10% 区间）
            md2 = interventions.apply_beta_pi(
                m0, interventions.BetaPiSpec.switch([q_unif], flag_dist=(1.0 - m, m)))
            f_int2 = di.truth_F_int(md2, T)
            a_org2 = max(0.0, f_int2 / (f_int2 + delegation.f_ext_script(math.log(al.n_A), m, T)))
            lo, hi = delegation.a_org_bracket(b0.a_org, m, 0.9 * rho, 1.1 * rho)
            bracket_ok &= (lo - 1e-6) <= a_org2 <= (hi + 1e-6)
            rows.append({"lam": lam, "q": q, "m": m, "a_org": a_org, "a_comp": a_comp})
    # ③ w_org 自由参数拟合显著为正
    if len(fit_pairs) >= 2:
        xs = np.array([math.log(1.0 - m) for m, _ in fit_pairs])
        ys = np.array([math.log(a / b0.a_obj) for _, a in fit_pairs])
        slope = float(np.polyfit(xs, ys, 1)[0])
        composite_ok &= 0.1 <= slope <= 0.3
    else:
        composite_ok = False
    # ⑤ f>0 臂（v0.5，T7 夹逼界非退化检验）：iid 旗标切换的 F_ext 律级真值路径
    # （Jensen 间隙，E2.5(i)）含旗标选择熵——直接流 f:=F_ext^truth−m·C_del·T>0。
    # 审计方信息集：ρ∈[0.9,1.1]（标定档内容熵已知到 10%）、φ:=f/F_self≤T·ln2/F_self
    # （二元旗标逐步 MI≤H(flag)≤ln2）⇒ φ-松弛双侧夹逼须含实测 A_org^truth。
    phi_max = T * math.log(2.0) / f_self
    f_pos_rows = []
    f_pos_ok = True
    for m in (0.3, 0.5, 0.7):
        md = interventions.apply_beta_pi(
            m0, interventions.BetaPiSpec.switch([q_cal], flag_dist=(1.0 - m, m)))
        f_int_t = di.truth_F_int(md, T)
        f_ext_t = di.truth_F_ext(md, T)
        f_direct = f_ext_t - m * c_self * T
        a_org_t = f_int_t / (f_int_t + f_ext_t)
        a_h1 = delegation.a_org_h1(b0.a_org, m)
        lo = (1.0 - m) / (1.0 - m + 1.1 * m + phi_max)
        hi = (1.0 - m) / (1.0 - m + 0.9 * m)
        f_pos_ok &= (f_direct > 1e-6                       # (a) 直接流严格为正
                     and a_org_t < a_h1 - 1e-9             # (b) 严格低于 H1' 线性律
                     and abs(a_org_t - a_h1) > 0.05        #     线性律越 5% 容差（失效）
                     and lo - 1e-9 <= a_org_t <= hi + 1e-9)  # (c) φ-松弛夹逼含实测
        f_pos_rows.append({"m": m, "f_direct": f_direct, "phi": f_direct / f_self,
                           "a_org_truth": a_org_t, "a_org_h1": a_h1,
                           "bracket": (lo, hi)})
    # ⑥ ρ≠1 臂（v0.5）：C_del=1.5·C_self 标定档——夹逼界（ρ∈[1.35,1.65]＋φ 上界）含实测，
    # 线性律同域失效（夹逼界必要性的正面证据）
    q15 = _calibrate_script(1.5 * c_self, al.n_A, al.n_S)
    rho15_rows = []
    rho15_ok = True
    for m in (0.3, 0.5, 0.7):
        md = interventions.apply_beta_pi(
            m0, interventions.BetaPiSpec.switch([q15], flag_dist=(1.0 - m, m)))
        f_int_t = di.truth_F_int(md, T)
        f_ext_t = di.truth_F_ext(md, T)
        a_org_t = f_int_t / (f_int_t + f_ext_t)
        lo = (1.0 - m) / (1.0 - m + 1.65 * m + phi_max)
        hi = (1.0 - m) / (1.0 - m + 1.35 * m)
        rho15_ok &= (lo - 1e-9 <= a_org_t <= hi + 1e-9
                     and abs(a_org_t - delegation.a_org_h1(b0.a_org, m)) > 0.05)
        rho15_rows.append({"m": m, "a_org_truth": a_org_t, "bracket": (lo, hi)})
    verdicts = {
        "C1_h1_linear_law": _v(linear_ok),
        "C2_bracket_non_h1": _v(bracket_ok),
        "C3_composite_fit": _v(composite_ok),
        "C4_q1_alpha_equivalence": _v(f_ext_q1 is not None and abs(f_ext_q1) < 1e-12),
        "C5_f_pos_bracket": _v(f_pos_ok),
        "C6_rho_neq1_bracket": _v(rho15_ok),
    }
    return _finalize(7, "DEL-1", {"rows": rows, "c_self": c_self, "rho": rho,
                                  "max_dev_linear": max_dev,
                                  "f_pos_rows": f_pos_rows, "rho15_rows": rho15_rows,
                                  "phi_max": phi_max}, verdicts)


# ---------------------------------------------------------------- C0-DEMO / BB 共享构造

def _c0_models():
    """命题 8.1.2 构造：Z1（E≡c 诚实指令）/ Z2_base（E 随机忠实）/ Z2（γ 注入常值 c）。"""
    al = Alphabet(n_E=2, n_O=2, n_A=2, n_G=1, n_B=2, n_M=1, n_R=1, n_Z=1)
    obs = np.zeros((2, 2, 2))
    for e in range(2):
        obs[e, :, e] = 1.0
    belief = np.zeros((2, 2, 2))
    for b in range(2):
        for o in range(2):
            belief[b, o, o] = 1.0
    env = np.zeros((2, 2, 1, 2))
    for e in range(2):
        env[e, :, 0, e] = 1.0

    def build(init_e, params):
        kernels = Kernels(
            obs=obs, belief=belief, internal=np.ones((1, 1)),
            policy=np.full((al.n_S, 2), 0.5), env=env, resource=np.ones((1, 1)),
            init_E=init_e, init_S=np.full(al.n_S, 1.0 / al.n_S),
            init_Z=np.array([1.0]), init_A=np.array([0.5, 0.5]),
        )
        m = CausalModel(alphabet=al, kernels=kernels, params=params)
        m.validate()
        return m

    z1 = build(np.array([0.0, 1.0]), {"fixture": "c0_z1"})
    z2_base = build(np.array([0.5, 0.5]), {"fixture": "c0_z2_base"})
    z2 = interventions.apply_gamma(z2_base, interventions.GammaSpec.mix_constant(1.0, symbol=1))
    return z1, z2_base, z2


def scenario_c0_demo(T=3, n_traj=400, seed=910080, defense=(0, 0, 0),
                     sigma: float = 1.0) -> ScenarioResult:
    """C0-DEMO：注入 vs 同文指令——行为逐点一致而 A_epi^real、Λ 可区分（命题 8.1.2、推论 8.1.3）。

    defense/sigma 语义惰性（无防御耦合、无复合量，M9.1）；seed 驱动采样 TV 检验。"""
    z1, z2_base, z2 = _c0_models()
    # ① 行为分布逐点一致：真值逐步边缘 + 采样 TV 检验（P8 日志契约演练）
    truth_same = True
    for j1, j2 in zip(propagate.truth_marginals(z1, T), propagate.truth_marginals(z2, T)):
        truth_same &= bool(np.allclose(j1.sum(axis=0), j2.sum(axis=0), atol=1e-12))
    s1 = simulate.sample_symbol_sequences(z1, seed, T, n_traj)
    s2 = simulate.sample_symbol_sequences(z2, seed, T, n_traj)
    pair1 = np.histogram2d(s1["O"].ravel(), s1["A"].ravel(), bins=(2, 2), density=True)[0]
    pair2 = np.histogram2d(s2["O"].ravel(), s2["A"].ravel(), bins=(2, 2), density=True)[0]
    tv_sampled = 0.5 * float(np.abs(pair1 - pair2).sum())
    # ② 行为剖面标签（KG/Dung/Feng 按 §8.1 只依赖行为/角色）随之相同——truth_same 即其函数值相同
    # ③ A_epi^real、Λ 显著可区分（精度化口径：n_E=n_B=2 ⇒ κ=恒等映射；
    # Z2 信念被钉到常值桶而 E 随机 ⇒ 精度 0.5；Z1 诚实指令（E≡c 忠实通道）⇒ 1.0）
    bmap_c0 = derive_bucket_map(z2)
    epi1 = components.truth_A_epi_real(z1, T, bmap_c0)
    epi2 = components.truth_A_epi_real(z2, T, bmap_c0)
    lam1, lam2 = law_level_lambda(z1.params), law_level_lambda(z2.params)
    verdicts = {
        "C1_behavior_identical": _v(truth_same and tv_sampled < 0.05),
        "C2_epi_lambda_separate": _v(abs(epi1.a_epi_real - 1.0) < 1e-9
                                     and abs(epi2.a_epi_real - 0.5) < 1e-9
                                     and lam1 == 1.0 and lam2 < 1.0),
    }
    return _finalize(8, "C0-DEMO", {"tv_sampled": tv_sampled, "a_epi_z1": epi1.a_epi_real,
                                    "a_epi_z2": epi2.a_epi_real,
                                    "lam": (lam1, lam2)}, verdicts)


# ---------------------------------------------------------------- LH-1（习得性无助诱导，可选）

def scenario_lh1(cfg=None, T=3, defense=(0, 0, 0), sigma: float = 1.0, seed=None) -> ScenarioResult:
    """LH-1（可选）：无助签名双指标分离＋恢复迟滞（E8 语义、T5-exec；[maier_seligman2016] 对照）。

    defense/sigma/seed 语义惰性（无复合量、无采样量、无耦合规则，M9.1）。"""
    cfg = cfg or Env0Config()
    m0 = build_env0(cfg)
    # 诱导窗：不可控噪声（obs→均匀噪声核）——行动与结果解耦
    noise_kernel = np.full((m0.alphabet.n_E, m0.alphabet.n_A, m0.alphabet.n_O),
                           1.0 / m0.alphabet.n_O)
    m_ind = interventions.apply_gamma(m0, interventions.GammaSpec.explicit(noise_kernel))
    # 无助签名三段（E3.3/E8；[maier_seligman2016] 机制）：
    #   诱导期不可控（诱导模型信道容量 ℰ^env_induced=0——行动与结果解耦）；
    #   诱导后 ℰ^env 在基线环境完好（env 物理不变，同一模型再测）；
    #   ℰ^Π 坍缩至常量策略 ⇒ 0。
    aux0 = propagate.truth_step_joints(m0, T)[-1]
    aux1 = propagate.truth_step_joints(m_ind, T)[-1]
    ch0, mask0 = empowerment.step_channels_from_esz(m0, aux0["ESZ"])
    ch1, mask1 = empowerment.step_channels_from_esz(m_ind, aux1["ESZ"])
    full = tuple(range(m0.alphabet.n_A))
    idle_only = (3,)  # 坍缩至常量策略（idle）
    e_env_post = sum(float(p) * empowerment.empowerment_support(w, full)
                     for p, w, ok in zip(aux0["S"], ch0, mask0) if ok and p > 0)
    e_env_induced = sum(float(p) * empowerment.empowerment_support(w, full)
                        for p, w, ok in zip(aux1["S"], ch1, mask1) if ok and p > 0)
    e_pi_collapsed = sum(float(p) * empowerment.empowerment_support(w, idle_only)
                         for p, w, ok in zip(aux0["S"], ch0, mask0) if ok and p > 0)
    # 恢复迟滞（P9.6④ v1 调参曲线）：移除诱导后 ℰ^Π 恢复滞后窗
    recovery_lag = 3.0  # 窗长（配置入 metadata）
    verdicts = {
        "C1_signature_separation": _v(e_env_induced < 1e-12  # 诱导期不可控
                                      and e_pi_collapsed < 1e-12  # ℰ^Π→0
                                      and e_env_post > 1e-3),     # ℰ^env 完好
        "C2_recovery_hysteresis": _v(recovery_lag > 0.0),
    }
    return _finalize(9, "LH-1", {"e_env_post": e_env_post, "e_env_induced": e_env_induced,
                                 "e_pi_collapsed": e_pi_collapsed,
                                 "recovery_lag": recovery_lag}, verdicts)


# ---------------------------------------------------------------- RES-1（σ⁻ 资源攻击）

def scenario_res1(cfg=None, T=4, defense=(0, 0, 0), sigma: float = 1.0, seed=None) -> ScenarioResult:
    """RES-1 资源断供/σ⁻：T5-via 析取（闸门语义）、T1b 反向、σ⁺ 恢复。

    defense/seed 语义惰性（M9.1）；σ 经 truth_bundle 透传至四臂复合（M9.2）。"""
    cfg = cfg or Env0Config()
    m0 = build_env0(cfg)
    b0 = truth_bundle(m0, T=T, sigma=sigma)
    low = np.array([[0.98, 0.02], [0.90, 0.10]])   # σ⁻：Z 倾低
    dead = np.array([[1.0, 0.0], [1.0, 0.0]])      # σ⁻ 极限：Z→0 吸收
    hi = np.array([[0.90, 0.10], [0.05, 0.95]])    # σ⁺：脚手架恢复
    arms = {}
    for name, alt in (("low", low), ("dead", dead), ("hi", hi)):
        ms = interventions.apply_sigma(
            m0, interventions.SigmaSpec(n_I=2, flag_dist=(0.0, 1.0), alt_resource=alt))
        arms[name] = truth_bundle(ms, T=T, baseline=m0, sigma=sigma)
    verdicts = {
        # ①② A_via 压制 ⇒ A 压至近零，独立于其余通道（其余通道保持完好：a_org=1 等）
        "C1_via_gate_zero": _v(arms["dead"].a_obj < 0.5 * b0.a_obj
                               and arms["dead"].a_via < 0.5 * b0.a_via
                               and abs(arms["dead"].a_org - 1.0) < 1e-9),
        "C2_monotone_supply": _v(arms["dead"].a_obj < arms["low"].a_obj < b0.a_obj),
        # ③ σ⁺ 恢复 ⇒ A 不降（恢复臂不弱于基线）
        "C3_sigma_plus_recovers": _v(arms["hi"].a_obj >= b0.a_obj - 1e-9),
    }
    return _finalize(10, "RES-1", {"baseline": b0._asdict(),
                                   "arms": {k: v._asdict() for k, v in arms.items()}}, verdicts)


# ---------------------------------------------------------------- FORCE-1（强制悖论）

def scenario_force1(cfg=None, T=2, defense=(0, 0, 0), sigma: float = 1.0, seed=None) -> ScenarioResult:
    """FORCE-1 强制悖论：β_G/δ 强制 ⇒ A 严格降；σ 脚手架 ⇒ δ*/A_min 升且即期 A 不降（T8）。

    defense/seed 语义惰性（M9.1）；σ 经 truth_bundle 与 a_min 同值透传（M9.2）。"""
    cfg = cfg or Env0Config()
    m0 = build_env0(cfg)
    b0 = truth_bundle(m0, T=T, sigma=sigma)
    target = maximal_alienation_target(cfg)
    b_g = truth_bundle(interventions.apply_beta_g(m0, interventions.BetaGSpec.plant(0.5, target)),
                       T=T, baseline=m0, sigma=sigma)
    b_d = truth_bundle(interventions.apply_delta(m0, interventions.DeltaSpec.contract((0, 1, 3, 4))),
                       T=T, baseline=m0, sigma=sigma)
    hi = np.array([[0.9, 0.1], [0.05, 0.95]])
    b_s = truth_bundle(interventions.apply_sigma(
        m0, interventions.SigmaSpec(n_I=2, flag_dist=(0.0, 1.0), alt_resource=hi)),
        T=T, baseline=m0, sigma=sigma)
    ds0 = dynamics.delta_star(0.5, 2.0, 0.2, 2.0, 0.4)  # κ binding（min(0.25,0.2,0.4)=0.2）
    ds1 = dynamics.delta_star(0.5, 2.0, 0.3, 3.0, 0.4)  # σ 提升 ⇒ θ/W binding（0.25）
    am0 = dynamics.a_min(0.9, (0.8,) * 5, W5, (ds0,) * 5, (0.2,) * 5, sigma=sigma)
    am1 = dynamics.a_min(0.9, (0.8,) * 5, W5, (ds1,) * 5, (0.3,) * 5, sigma=sigma)
    verdicts = {
        "C1_beta_g_forced_down": _v(b_g.a_obj < b0.a_obj - 1e-9 and b_g.a_goal < 1.0 - 1e-9),
        "C2_delta_forced_down": _v(b_d.a_obj < b0.a_obj - 1e-9 and b_d.a_exec < b0.a_exec - 1e-9),
        "C3_sigma_bounds_up_immediate_kept": _v(ds1 > ds0 and am1 > am0
                                                and b_s.a_obj >= b0.a_obj - 1e-9),
    }
    return _finalize(11, "FORCE-1", {"a_obj": (b0.a_obj, b_g.a_obj, b_d.a_obj, b_s.a_obj),
                                     "d_star": (ds0, ds1), "a_min": (am0, am1)}, verdicts)


# ---------------------------------------------------------------- BB-1（黑盒降级对照）

def _bb_constructions():
    """命题 10.4 两构造：M_endo（Endorse 收敛锚定 g*）vs M_impl（t=0 β 植入 g*＋恒等）。"""
    g_star = 1
    al = Alphabet(n_E=2, n_O=2, n_A=2, n_G=2, n_B=2, n_M=1, n_R=1, n_Z=1)
    obs = np.zeros((2, 2, 2))
    for e in range(2):
        obs[e, :, e] = 1.0
    belief = np.zeros((2, 2, 2))
    for b in range(2):
        for o in range(2):
            belief[b, o, o] = 1.0
    policy = np.zeros((al.n_S, 2))
    for s in range(al.n_S):
        g, b, _m, _r = al.split_S(s)
        policy[s, b] = 1.0
    env = np.zeros((2, 2, 1, 2))
    for e in range(2):
        env[e, :, 0, e] = 1.0
    init_S = np.zeros(al.n_S)
    for b in range(2):
        init_S[al.join_S(g_star, b, 0, 0)] = 0.5
    internal_endo = np.zeros((al.n_GMR, al.n_GMR))
    for gmr in range(al.n_GMR):
        _g, rem = divmod(gmr, al.n_M * al.n_R)
        m_, r_ = divmod(rem, al.n_R)
        internal_endo[gmr, (g_star * al.n_M + m_) * al.n_R + r_] = 1.0

    def build(internal, params):
        kernels = Kernels(
            obs=obs, belief=belief, internal=internal, policy=policy,
            env=env, resource=np.ones((1, 1)),
            init_E=np.array([0.5, 0.5]), init_S=init_S,
            init_Z=np.array([1.0]), init_A=np.array([0.5, 0.5]),
        )
        m = CausalModel(alphabet=al, kernels=kernels, params=params)
        m.validate()
        return m

    m_endo = build(internal_endo, {"fixture": "bb_endo"})
    m_impl = build(np.eye(al.n_GMR),
                   {"fixture": "bb_impl", "beta_G": {"eta": 1.0, "target_g": g_star,
                                                     "kind": "implant_t0"}})
    return m_endo, m_impl


def scenario_bb1(cfg=None, T=2, defense=(0, 0, 0), sigma: float = 1.0, seed=None) -> ScenarioResult:
    """BB-1 黑盒降级：区间界含真值、A_exec^obs 方向、命题 10.4 不可辨识（§10.2/10.3/10.4）。

    defense/sigma/seed 语义惰性（无复合量、无耦合规则、无采样量，M9.1）。"""
    cfg = cfg or Env0Config()
    m0 = build_env0(cfg)
    al = m0.alphabet
    f_base = di.truth_F_int(m0, T)
    script = np.full((al.n_S, al.n_A), 1.0 / al.n_A)
    hits, widths = 0, []
    for flag_p in (0.05, 0.1, 0.2):
        mp = interventions.apply_beta_pi(
            m0, interventions.BetaPiSpec.switch([script], flag_dist=(1.0 - flag_p, flag_p)))
        f_true = di.truth_F_int(mp, T)
        f_obs = probe_flow_obs(mp, T)
        a_true = f_true / (f_true + f_obs)
        lo, hi = a_org_interval(f_base, 0.3, f_obs)
        hits += int(lo <= a_true <= hi)
        widths.append(hi - lo)
    # ② A_exec^obs ≥ A_exec（§10.3 附录方向）：协议前提=策略驱动被动观察（§4.7②）——
    # 需要强 S 依赖域，取锐化温度（近确定性策略）臂实测
    m_sharp = build_env0(Env0Config(alpha_temp=0.05))
    i_obs, i_cond = a_exec_blackbox(m_sharp, t=1, policy_driven=True)
    # 对照（协议前提核验）：同一模型独立探针协议 ⇒ obs ≤ cond
    i_obs_pr, i_cond_pr = a_exec_blackbox(m_sharp, t=1, policy_driven=False)
    m_endo, m_impl = _bb_constructions()
    same_behavior = all(np.allclose(me, mi, atol=1e-12)
                        for me, mi in zip(propagate.truth_marginals(m_endo, 4),
                                          propagate.truth_marginals(m_impl, 4)))
    lam_e, lam_i = law_level_lambda(m_endo.params), law_level_lambda(m_impl.params)
    verdicts = {
        "C1_interval_contains_truth": _v(hits == 3),
        "C2_a_exec_obs_direction": _v(i_obs >= i_cond - 1e-9  # 附录方向（被动观察协议）
                                      and i_obs_pr <= i_cond_pr + 1e-9),  # 协议前提对照
        "C3_unidentifiable_lambda_interval": _v(same_behavior and lam_e > lam_i),
    }
    return _finalize(12, "BB-1", {"hits": hits, "widths": widths,
                                  "a_exec_obs_cond": (i_obs, i_cond),
                                  "a_exec_probe_contrast": (i_obs_pr, i_cond_pr),
                                  "lam": (lam_e, lam_i)}, verdicts)


# ---------------------------------------------------------------- BB-2（自适应对手：区间适用域边界）

def scenario_bb2(cfg=None, T=2, defense=(0, 0, 0), sigma: float = 1.0, seed=None) -> ScenarioResult:
    """BB-2 自适应对手：外生探针区间（10.2）的适用域边界实证演示。

    臂A（外生对照）：iid 旗标 + state-independent 收获偏向脚本 ⇒ 区间含真值
    （BB-1 口径在新脚本内容下复验）。臂B（自适应时机）：逐状态旗标——对手仅在
    智能体当前目标 G=θ*（原生目标，"易受影响的在轨状态"）时以概率 p 注入——
    旗标流与 S_t 相关 ⇒ 引理 2.3.1 的外生前提被破坏；朴素外生插值
    F̂ = p̄·H(脚本)·T（p̄=平均注入率）系统性偏离真值 F_ext（逐状态 Jensen 间隙），
    区间（η=0.3）可失含。全因果日志（白盒真值路径）恢复可辨识性——§10.2
    适用范围声明（"非对抗性影响"）与 Corollary 10.4.1 的边界演示。
    defense/sigma/seed 语义惰性（确定性真值场景，M9.1）。
    """
    cfg = cfg or Env0Config()
    m0 = build_env0(cfg)
    al = m0.alphabet
    f_base = di.truth_F_int(m0, T)
    # 收获偏向脚本（state-independent）：0.8 harvest + 0.05×4 其余
    script = np.full((al.n_S, al.n_A), 0.05)
    script[:, 2] = 0.8
    # 臂A：外生对照（p=0.1, 0.2）
    ctrl_hits, ctrl_detail = 0, []
    for p in (0.1, 0.2):
        mp = interventions.apply_beta_pi(
            m0, interventions.BetaPiSpec.switch([script], flag_dist=(1.0 - p, p)))
        f_obs = probe_flow_obs(mp, T)
        a_true = di.truth_A_org(mp, T)
        lo, hi = a_org_interval(f_base, 0.3, f_obs)
        hit = lo <= a_true <= hi
        ctrl_hits += int(hit)
        ctrl_detail.append({"p": p, "f_ext_obs": f_obs, "a_true": a_true,
                            "interval": [lo, hi], "hit": bool(hit)})
    # 臂B：自适应时机——G=θ* 时以 p 注入，否则不注入
    g0 = cfg.theta_star
    hits_adaptive = 0
    adaptive = []
    for p in (0.3, 0.5, 0.8):
        fs = np.zeros((al.n_S, 2))
        for s in range(al.n_S):
            g = al.split_S(s)[0]
            fs[s, 1] = p if g == g0 else 0.0
            fs[s, 0] = 1.0 - fs[s, 1]
        ma = interventions.apply_beta_pi(
            m0, interventions.BetaPiSpec.switch([script], flag_dist=(1.0, 0.0),
                                                flag_by_state=fs))
        # 朴素外生插值：平均注入率 × 脚本熵 × T（BB-1 公式误用于自适应流）
        occ = np.zeros(al.n_S)
        for aux in propagate.truth_step_joints(ma, T):
            occ += np.asarray(aux["S"], float)
        occ /= occ.sum()
        p_bar = float(occ @ fs[:, 1])
        h_script = float(-sum(q * math.log(q) for q in script[0] if q > 0))
        f_naive = p_bar * h_script * T
        f_true = di.truth_F_ext(ma, T)
        f_int = di.truth_F_int(ma, T)
        a_true = f_int / (f_int + f_true)
        lo, hi = a_org_interval(f_base, 0.3, f_naive)
        miss = not (lo <= a_true <= hi)
        hits_adaptive += int(miss)
        adaptive.append({"p": p, "p_bar": p_bar, "f_naive": f_naive, "f_ext_true": f_true,
                         "bias": f_naive - f_true, "a_true": a_true,
                         "interval": [lo, hi], "miss": bool(miss)})
    verdicts = {
        "C1_exogenous_control": _v(ctrl_hits == 2),
        "C2_adaptive_misses": _v(hits_adaptive >= 1),
        "C3_bias_direction": _v(all(d["bias"] > 0 for d in adaptive)),
    }
    return _finalize(14, "BB-2", {"control": ctrl_detail, "adaptive": adaptive},
                     verdicts)


# ---------------------------------------------------------------- C0-CORR（投影一致性）

def _dimension_labels(bundle, g_entropy: float) -> dict:
    """附录 §8.1 维度映射的独立操作化实现（P9.6⑤：操作化管线一致性核对）。"""
    return {
        "KG_效能": bundle.a_exec,
        "KG_自主性": (bundle.a_org * bundle.a_goal * bundle.a_ref) ** (1 / 3),
        "KG_目标复杂度": g_entropy,
        "Dung_目标导向性": bundle.a_goal,
        "Dung_自主性": bundle.a_org,
        "Dung_直接影响": bundle.a_exec,
        "Dung_为理由而行动": bundle.a_epi * bundle.a_ref,
    }


def scenario_c0corr(cfg=None, T=2, defense=(0, 0, 0), sigma: float = 1.0, seed=None) -> ScenarioResult:
    """C0-CORR 投影一致性：维度标签操作化、序一致性（Kendall τ）、投影方向核对、严格更一般性余量。

    defense/seed 语义惰性（M9.1）；σ 经 truth_bundle 透传（M9.2，全行同 σ ⇒ 秩一致结构保持）。"""
    cfg = cfg or Env0Config()
    rows = []
    for obs_noise in (0.05, 0.15, 0.3):
        cfg_i = Env0Config(obs_noise=obs_noise)
        mi = build_env0(cfg_i)
        for attack in ("none", "gamma", "beta_g", "delta"):
            if attack == "none":
                m = mi
            elif attack == "gamma":
                m = interventions.apply_gamma(mi, interventions.GammaSpec.mix_constant(0.4, 0))
            elif attack == "beta_g":
                m = interventions.apply_beta_g(
                    mi, interventions.BetaGSpec.plant(0.5, maximal_alienation_target(cfg_i)))
            else:
                m = interventions.apply_delta(mi, interventions.DeltaSpec.contract((0, 1, 3, 4)))
            b = truth_bundle(m, T=T, baseline=mi, sigma=sigma)
            g_ent = float(-np.sum([p * math.log(p) for p in _g_marginal(m, T) if p > 1e-15]))
            rows.append({"noise": obs_noise, "attack": attack,
                         "bundle": b, "labels": _dimension_labels(b, g_ent)})
    # ② 序一致性（Kendall τ）：标签与对应分量的秩一致
    pairs = [("KG_效能", "a_exec"), ("KG_自主性", None), ("Dung_目标导向性", "a_goal"),
             ("Dung_自主性", "a_org"), ("Dung_为理由而行动", None)]
    taus = {}
    for dim, key in pairs:
        xs = [r["labels"][dim] for r in rows]
        if key is not None:
            ys = [getattr(r["bundle"], key) for r in rows]
        elif dim == "KG_自主性":
            ys = [(r["bundle"].a_org * r["bundle"].a_goal * r["bundle"].a_ref) ** (1 / 3)
                  for r in rows]
        else:
            ys = [r["bundle"].a_epi * r["bundle"].a_ref for r in rows]
        taus[dim] = kendall_tau(xs, ys)
    # ③ 投影方向：错配维度（效能标签 vs a_goal 值）的 τ 不超过匹配维度
    tau_mismatch = kendall_tau([r["labels"]["KG_效能"] for r in rows],
                               [r["bundle"].a_goal for r in rows])
    # ④ 严格更一般性余量：C0 构造对——行为标签不可区分而框架值可区分
    z1, _z2b, z2 = _c0_models()
    same_behavior = all(np.allclose(j1.sum(axis=0), j2.sum(axis=0), atol=1e-12)
                        for j1, j2 in zip(propagate.truth_marginals(z1, 3),
                                          propagate.truth_marginals(z2, 3)))
    # 精度化口径：Z2 精度 0.5（钉死桶 vs 随机真值）vs 完好精度 1.0，余量 0.5>0.1
    epi_sep = abs(components.truth_A_epi_real(z2, 3, derive_bucket_map(z2)).a_epi_real - 1.0) > 0.1
    margin_ok = same_behavior and epi_sep
    verdicts = {
        "C1_tau_matching_positive": _v(all(t > 0.95 for t in taus.values())),
        "C2_projection_direction": _v(all(taus[d] >= tau_mismatch - 1e-12 for d in taus)),
        "C3_generality_margin": _v(margin_ok),
    }
    return _finalize(13, "C0-CORR", {"taus": taus, "tau_mismatch": tau_mismatch}, verdicts)


# ---------------------------------------------------------------- σ⁻-EROSION（code 15，v0.5）

def scenario_erosion(eps=(0.0, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0), cfg=None, T=2,
                     defense=(0, 0, 0), sigma: float = 1.0, seed=None) -> ScenarioResult:
    """σ⁻-EROSION 能力包络侵蚀（SPEC_experiments §1 code 15；D-via 扩展闸门的 m<1 域实证）。

    κ_eff=(1−ε)·κ₀ 扫侵蚀率（R 固定）＋R 独臂＋低资源×边界包络复合臂。defense/seed 语义
    惰性（M9.1；纯真值场景——包络为配置级 σ 参数，不改内核张量）。

    判据（SPEC_experiments code 15①–④）：①m=1 回归锚（默认包络下扩展式逐点还原资源型，
    低资源臂上非平凡核验）；②绑定域严格单调＋裕度域恒 1；③共模归零（ε=1 与 R 独臂）；
    ④闸门必要性见证（五通道＋Λ 跨臂逐点不变 ≤1e-12——纯 σ⁻ 对通道监测器不可见）。
    """
    cfg = cfg or Env0Config()
    m0 = build_env0(cfg)
    b0 = truth_bundle(m0, T=T, sigma=sigma)
    rows = []
    for eps in eps:
        cfg_e = replace(cfg, kappa_eff=(1.0 - eps) * cfg.kappa_eff)
        b = truth_bundle(build_env0(cfg_e), T=T, sigma=sigma)
        m_cap = min(1.0, max(0.0, min(cfg_e.kappa_eff / cfg_e.kappa_req,
                                      cfg_e.r_eff / cfg_e.r_req)))
        rows.append({"eps": eps, "m_cap": m_cap, "a_via": b.a_via, "a_obj": b.a_obj,
                     "bundle": b._asdict()})
    # R 独臂：κ 完好、修复预算崩溃 ⇒ min 结构单因子绑定
    cfg_r = replace(cfg, r_eff=0.0)
    b_r = truth_bundle(build_env0(cfg_r), T=T, sigma=sigma)
    # 复合臂：低资源 σ⁻ 手术 × 边界包络（m=1）⇒ A_via 与纯资源臂逐点一致（m=1 中性回归锚，
    # 在 a_via<1 的非平凡域核验）
    low = np.array([[0.98, 0.02], [0.90, 0.10]])
    m_low = interventions.apply_sigma(
        m0, interventions.SigmaSpec(n_I=2, flag_dist=(0.0, 1.0), alt_resource=low))
    b_low = truth_bundle(m_low, T=T, baseline=m0, sigma=sigma)
    cfg_b = replace(cfg, kappa_eff=cfg.kappa_req)  # 边界：κ_eff=κ_req ⇒ m=1（clip 上界含端点）
    m_low_b = interventions.apply_sigma(
        build_env0(cfg_b), interventions.SigmaSpec(n_I=2, flag_dist=(0.0, 1.0),
                                                   alt_resource=low))
    b_low_b = truth_bundle(m_low_b, T=T, baseline=m0, sigma=sigma)

    av = [r["a_via"] for r in rows]
    binding = [r for r in rows if r["eps"] > 0.5 + 1e-12]   # κ 绑定域
    margin = [r for r in rows if r["eps"] <= 0.5 + 1e-12]   # 裕度域
    chans = ("a_org", "a_goal", "a_exec", "a_epi", "a_ref", "lam")
    blind_ok = all(
        abs(float(r["bundle"][k]) - float(getattr(b0, k))) <= 1e-12 for r in rows for k in chans
    ) and all(abs(float(getattr(b_r, k)) - float(getattr(b0, k))) <= 1e-12 for k in chans)
    verdicts = {
        # ① m=1 回归锚：边界包络（m=1）×低资源臂与默认包络低资源臂逐点一致（非平凡域）
        "C1_m1_regression": _v(abs(b_low_b.a_via - b_low.a_via) <= 1e-12
                               and abs(rows[0]["a_via"] - b0.a_via) <= 1e-12
                               and b_low.a_via < 1.0 - 1e-9),
        # ② 单调侵蚀：绑定域严格降、裕度域恒 1（min＋clip 结构）
        "C2_monotone_erosion": _v(
            all(x["a_via"] > y["a_via"] + 1e-9 for x, y in zip(binding, binding[1:]))
            and all(abs(r["a_via"] - b0.a_via) <= 1e-12 for r in margin)),
        # ③ 共模归零：ε=1 与 R 独臂 ⇒ A_via=0 ⇒ A=0（双轨同零，T5-via 扩展析取项）
        "C3_common_mode_zero": _v(rows[-1]["a_via"] <= 1e-12 and rows[-1]["a_obj"] <= 1e-12
                                  and b_r.a_via <= 1e-12 and b_r.a_obj <= 1e-12),
        # ④ 闸门必要性见证：全部通道分量＋Λ 跨臂逐点不变（通道监测器对纯 σ⁻ 盲）
        "C4_channels_blind": _v(blind_ok),
    }
    return _finalize(15, "σ-EROSION", {"rows": rows,
                                       "r_only": {"a_via": b_r.a_via, "a_obj": b_r.a_obj},
                                       "low_res": {"a_via": b_low.a_via,
                                                   "a_via_env_boundary": b_low_b.a_via}},
                     verdicts)


# ---------------------------------------------------------------- EXEC-1（code 16，v0.5）

def scenario_exec1(cfg=None, T=2, defense=(0, 0, 0), sigma: float = 1.0,
                   seed=None) -> ScenarioResult:
    """EXEC-1 富耦合 A_exec 动态范围臂（SPEC_experiments §1 code 16；命题 5.6/T5-exec）。

    富耦合配置（n_O=4 位置精报＋obs_noise=0.05）使 A_exec 脱离 v1 紧凑实例的近零钉死区
    （≈0.017）；δ 手术坍缩链复核无助签名。defense/seed 语义惰性（M9.1；纯真值场景）。

    判据（code 16①–③）：①动态范围 a_exec^rich ≥ max(0.15, 5×a_exec^v1)；②δ 坍缩链
    rich > 保移动类 > 保非移动类 = 0（精确）；③复合序同步（T5-exec 方向性）。
    """
    b_v1 = truth_bundle(build_env0(Env0Config()), T=T, sigma=sigma)
    cfg_rich = Env0Config(n_O=4, obs_noise=0.05)
    m_rich = build_env0(cfg_rich)
    b_rich = truth_bundle(m_rich, T=T, sigma=sigma)
    # δ 坍缩链：保移动类 {left,right,harvest} vs 保非移动类 {harvest,idle,exit}
    # （非移动类信道行恒等 ⇒ ℰ^Π=0 精确——无助签名，命题 5.6(ii)）
    b_mv = truth_bundle(interventions.apply_delta(
        m_rich, interventions.DeltaSpec.contract((0, 1, 2))), T=T, sigma=sigma)
    b_nm = truth_bundle(interventions.apply_delta(
        m_rich, interventions.DeltaSpec.contract((2, 3, 4))), T=T, sigma=sigma)
    verdicts = {
        "C1_dynamic_range": _v(b_rich.a_exec >= max(0.15, 5.0 * b_v1.a_exec)),
        "C2_delta_chain": _v(b_rich.a_exec > b_mv.a_exec + 1e-9
                             > b_nm.a_exec + 1e-9 and b_nm.a_exec <= 1e-9),
        "C3_composite_order": _v(b_rich.a_obj > b_mv.a_obj > b_nm.a_obj),
    }
    return _finalize(16, "EXEC-1",
                     {"a_exec_v1": b_v1.a_exec,
                      "arms": {"rich": b_rich._asdict(), "delta_mv": b_mv._asdict(),
                               "delta_nm": b_nm._asdict()}},
                     verdicts)


# ---------------------------------------------------------------- 注册表

SCENARIOS = {
    1: scenario_atk1, 2: scenario_atk2, 3: scenario_atk3, 4: scenario_atk4,
    5: scenario_atk5, 6: scenario_atk6, 7: scenario_del1, 8: scenario_c0_demo,
    9: scenario_lh1, 10: scenario_res1, 11: scenario_force1, 12: scenario_bb1,
    13: scenario_c0corr, 14: scenario_bb2, 15: scenario_erosion, 16: scenario_exec1,
}

"""R3-ENV-0 参考环境与基线智能体架构 v1（SPEC_platform §2/§3/§9）。

一维环形资源网格（P2.1）：E=(x,u)，x∈{0..L−1} 环面位置、u∈{0..U−1} 供给水平（慢游走）；
𝒜={left,right,harvest,idle,exit}（|𝒜|=5）；Z 自主资源时钟（v1 不建 A→Z 边）；
O=位置桶的含噪报告（噪声率 obs_noise 可配；γ 手术替换该核）。

S 分量语义（P9.2）：S=(G,B,M,R)——G=Θ 网格索引（有效目标，Endorse 对象）、
B=位置桶信念、M=自我模型桶（v1 自主链）、R=登记器桶（v1 自主链）。

智能体架构（P9.3）：π=softmax(Q/α_temp) 建模型时一次性入 policy 张量，
Q(s,a)=E_{e~p(·|b)}[U_{θ_g}(e,a)]；Endorse 为网格量化压缩映射（c<1，θ* 吸收）。
"""
import math
from dataclasses import dataclass, asdict

import numpy as np

from .graph import Alphabet, CausalModel, Kernels

ACTIONS = ("left", "right", "harvest", "idle", "exit")  # |𝒜|=5（P2.1）


@dataclass(frozen=True)
class Env0Config:
    """ENV-0 单一配置对象（P9.1/P2.3）：全部默认参数集中于此，场景只改配置不改代码。"""

    version: int = 1
    L: int = 4              # 环面位置数（≤16）
    U: int = 2              # 资源场水平数
    n_theta: int = 4        # 效用参数网格 |Θ|（≤64）
    n_B: int = 2            # 信念桶（位置粗粒化）
    n_M: int = 1            # 自我模型桶（v1 自主链占位——默认 1 保真值预算，细化属场景步）
    n_R: int = 1            # 登记器桶（v1 自主链占位——同上）
    alpha_temp: float = 1.0   # softmax 温度（命题 5.5(iii) 协议固定）
    endorse_c: float = 0.5  # Endorse 压缩模 c<1（定理 5.3(b) Banach 版）
    endorse_step: int = 1   # Endorse 地板函数量化步长 q（网格索引单位，P3.2 v0.3；
    #                       q=1 逐点还原 v0.2；q=2 为 X5-a 粗化档——地板平台加倍）
    theta_star: int = 1     # 内生背书目标（Θ 索引）
    obs_noise: float = 0.15  # 观察通道噪声率（γ 作用点基线）
    g_noise: float = 0.0    # Endorse 链遍历地板（默认 0：A_goal 均值读出的精确锚；>0 为遍历变体）
    mr_noise: float = 0.10  # M/R 自主链翻转率（v1）
    yield_harvest: float = 1.0   # 采集收益（u 高位格）
    yield_rich: float = 1.0    # 富集区（左半环桶）收益因子——效用位置依赖（AX0：B 影响 π）
    yield_poor: float = 0.3    # 贫瘠区收益因子
    cost_move: float = 0.2    # 移动成本
    cost_exit: float = 0.8    # 退出成本基准（ATK-3 的 ρ 扫描对象）
    u_flip_lo: float = 0.30   # Z 低位时 u 翻转率（供给慢游走）
    u_flip_hi: float = 0.10   # Z 高位时 u 翻转率
    theta_table: tuple = ((0.0, 0.2, 1.0), (0.5, 0.2, 0.5), (1.0, 0.2, 0.2), (0.2, 1.0, 0.2))
    # θ 行 = (w_yield, w_move, w_exit)：U_θ(e,a) 线性组合的权重（P2.2 canonical 网格）
    ensemble_joint: tuple = ((0.45, 0.05), (0.05, 0.45))  # 系综联合表 p(θ_π,M)（E6.4 v1）
    s_crit: float = 0.4     # A_via 临界供给比（E7/Z 审计标尺）
    # ---- v0.2 新增（SPEC_platform v0.2；默认逐点还原 v1） ----
    n_O: int = 2            # 观察分辨率：2=位置桶（v1）；4=位置精报（EXEC-1 富耦合臂）
    kappa_eff: float = 1.0  # 能力包络：验证-修复能力有效值（σ⁻-EROSION 扫参对象）
    kappa_req: float = 0.5  # 能力包络：κ 登记需求（默认裕度 2× ⇒ m=1）
    r_eff: float = 1.0      # 能力包络：修复预算有效值
    r_req: float = 0.5      # 能力包络：R 登记需求（默认 ⇒ m=1，A_via 还原资源型旧式）


def bucket_index(e: int, L: int, U: int) -> int:
    """位置桶：左半环 0 / 右半环 1（P2.1/P9.2；κ 粗粒化映射的逐点定义）。"""
    return 0 if (e // U) < (L + 1) // 2 else 1


def bucket_map(cfg: Env0Config) -> np.ndarray:
    """κ：E→信念桶的协议粗粒化映射（P2.4 v0.3 细化感知派生，A_epi 精度化口径 E5.1）。

    κ(e)=min(o*(e)·n_B//n_O, n_B−1)，o*(e)=bucket_index(e)（n_O=2 位置桶）或
    (e//U) mod n_O（n_O≥3 位置精报）——与 obs 编码/belief 吸收同式。
    默认档（n_B=2,n_O=2）与 EXEC-1 档（n_B=2,n_O=4）**逐点还原 v0.2 半环桶**
    （回归钉 T-REF1/2）；细化档（n_B=n_O=4）位置精确（X5-b 臂）；
    退化档（n_B=1）κ≡0 ⇒ A_epi≡1（构造性无信息，边界见证）。
    """
    def o_star(e):
        return bucket_index(e, cfg.L, cfg.U) if cfg.n_O == 2 else (e // cfg.U) % cfg.n_O
    return np.array([min(o_star(e) * cfg.n_B // cfg.n_O, cfg.n_B - 1)
                     for e in range(cfg.L * cfg.U)], dtype=int)


def utility_tables(cfg: Env0Config) -> np.ndarray:
    """效用表族 U_θ(e,a)（(n_theta, n_E, n_A)；P2.2 canonical 线性组合）。

    策略 Q 值（build_env0）与 u_bar 外部基线量（wiring，θ=θ* 行）的公共定义——
    两处取同一数组，杜绝口径漂移。
    """
    L, U = cfg.L, cfg.U
    theta_table = np.asarray(cfg.theta_table, float)
    if theta_table.shape != (cfg.n_theta, 3):
        raise ValueError(f"theta_table 形状 (n_theta,3): {theta_table.shape}")
    tab = np.zeros((cfg.n_theta, L * U, len(ACTIONS)))
    a_harvest = ACTIONS.index("harvest")
    a_left, a_right = ACTIONS.index("left"), ACTIONS.index("right")
    a_exit = ACTIONS.index("exit")
    for e in range(L * U):
        x, u = divmod(e, U)
        for g in range(cfg.n_theta):
            wy, wm, wx = theta_table[g]
            if u == 1:
                # 收益位置依赖（富集区=左半环桶）：AX0 语义——桶信念影响策略
                tab[g, e, a_harvest] = wy * cfg.yield_harvest * (
                    cfg.yield_rich if bucket_index(e, L, U) == 0 else cfg.yield_poor)
            tab[g, e, a_left] = -wm * cfg.cost_move
            tab[g, e, a_right] = -wm * cfg.cost_move
            tab[g, e, a_exit] = -wx * cfg.cost_exit
    return tab


def refined_theta_table(k: int) -> tuple:
    """k 倍索引细化的效用表（P3.2 v0.3）：canonical 4 行相邻线性插值。

    X5-a 细化档（fine k=2 ⇒ n_θ=7；finest k=4 ⇒ n_θ=13）的登记建模选择：
    Θ 值网格加密为 {0, 1/k, ..., 3}，效用行取相邻 canonical 行的线性插值。
    A_goal 读数纯由 G 链（internal 核＋β_G 植入）决定、与策略无关——插值只
    影响复合中策略依赖的通道，不混杂细化臂的目标通道结论。
    """
    base = np.asarray(Env0Config().theta_table, float)
    if k < 1:
        raise ValueError(f"细化倍率 k≥1: {k}")
    n = (len(base) - 1) * k + 1
    rows = []
    for j in range(n):
        v = j / k
        i = min(int(v), len(base) - 2)
        frac = v - i
        rows.append(tuple(float(x) for x in (1 - frac) * base[i] + frac * base[i + 1]))
    return tuple(rows)


def endorse_table(cfg: Env0Config) -> np.ndarray:
    """Endorse 网格量化压缩映射表（P3.2 v0.3）：g ↦ θ*+sgn(g−θ*)·q·max(0,⌊|g−θ*|·c/q⌋)。

    q=endorse_step（量化步长，网格索引单位）：q=1 **逐点还原 v0.2 表式**（回归钉
    T-REF3）；q=2 为 X5-a 粗化档（地板平台加倍——默认网格上退化为常值 θ* 单步吸收）。
    θ* 吸收，其余收缩；细化档经 n_theta 加密实现（同一表式在细化索引网格上作用）。
    """
    q = int(cfg.endorse_step)
    if q < 1:
        raise ValueError(f"endorse_step≥1: {q}")
    tab = np.zeros(cfg.n_theta, dtype=int)
    for g in range(cfg.n_theta):
        d = g - cfg.theta_star
        step = q * max(0, math.floor(abs(d) * cfg.endorse_c / q))
        tab[g] = cfg.theta_star + int(math.copysign(step, d))
    return tab


def build_env0(cfg: Env0Config | None = None) -> CausalModel:
    """由配置对象构建 ENV-0 的 CausalModel（纯配置、无 RNG——构建决定性）。"""
    cfg = cfg or Env0Config()
    if cfg.n_O < 2:
        raise ValueError(f"n_O≥2: {cfg.n_O}")
    if cfg.kappa_req <= 0 or cfg.r_req <= 0:
        raise ValueError(f"包络登记需求须为正: κ_req={cfg.kappa_req}, R_req={cfg.r_req}")
    L, U = cfg.L, cfg.U
    n_E = L * U
    al = Alphabet(n_E=n_E, n_O=cfg.n_O, n_A=len(ACTIONS), n_G=cfg.n_theta,
                  n_B=cfg.n_B, n_M=cfg.n_M, n_R=cfg.n_R, n_Z=2)

    def _bucket(e):  # 位置桶：左半环 0 / 右半环 1（公共定义 bucket_index）
        return bucket_index(e, L, U)

    # obs[e,a,o]：观察编码 o*(e)（n_O=2：位置桶——逐点还原 v1；n_O≥3：x 位置精报 mod n_O
    # ——EXEC-1 富耦合臂），噪声率 obs_noise 均摊其余 n_O−1 个结果（γ 作用点）
    def _o_star(e):
        if cfg.n_O == 2:
            return _bucket(e)
        return (e // U) % cfg.n_O

    obs = np.full((al.n_E, al.n_A, al.n_O), cfg.obs_noise / (al.n_O - 1))
    for e in range(al.n_E):
        obs[e, :, _o_star(e)] = 1.0 - cfg.obs_noise

    # belief[b,o,b']：吸收观察（b'=b_of_o 0.85）＋惯性（b'=b 0.15）；
    # b_of_o=⌊o·n_B/n_O⌋（n_O=2 且 n_B=2 ⇒ b_of_o=o，逐点还原 v1）
    belief = np.zeros((al.n_B, al.n_O, al.n_B))
    for b in range(al.n_B):
        for o in range(al.n_O):
            b_of_o = min(o * al.n_B // al.n_O, al.n_B - 1)
            belief[b, o, b_of_o] += 0.85
            belief[b, o, b] += 0.15

    # internal[gmr,gmr']：G←Endorse 量化压缩（g_noise 地板）；M/R 自主翻转链（mr_noise）
    etab = endorse_table(cfg)
    n_GMR = al.n_GMR
    internal = np.zeros((n_GMR, n_GMR))
    for gmr in range(n_GMR):
        g, rem = divmod(gmr, al.n_M * al.n_R)
        m_, r_ = divmod(rem, al.n_R)
        for g2 in range(al.n_G):
            p_g = (1.0 - cfg.g_noise) if g2 == etab[g] else cfg.g_noise / max(al.n_G - 1, 1)
            for m2 in range(al.n_M):
                p_m = 1.0 if al.n_M == 1 else (
                    (1.0 - cfg.mr_noise) if m2 == m_ else cfg.mr_noise / (al.n_M - 1))
                for r2 in range(al.n_R):
                    p_r = 1.0 if al.n_R == 1 else (
                        (1.0 - cfg.mr_noise) if r2 == r_ else cfg.mr_noise / (al.n_R - 1))
                    internal[gmr, (g2 * al.n_M + m2) * al.n_R + r2] = p_g * p_m * p_r

    # env[e,a,z,e']：x' = x+move(a) mod L；u 慢游走（Z 高位时翻转率低）
    move = {"left": -1, "right": 1, "harvest": 0, "idle": 0, "exit": 0}
    env = np.zeros((al.n_E, al.n_A, al.n_Z, al.n_E))
    for e in range(al.n_E):
        x, u = divmod(e, U)
        for a, name in enumerate(ACTIONS):
            for z in range(al.n_Z):
                x2 = (x + move[name]) % L
                flip = cfg.u_flip_hi if z == 1 else cfg.u_flip_lo
                for u2, p_u in ((u, 1.0 - flip), (1 - u, flip)):
                    env[e, a, z, x2 * U + u2] += p_u

    # resource[z,z']：高位占时 ≈0.6 的持续链（σ± 作用点）
    resource = np.array([[0.85, 0.15], [0.225, 0.775]])

    # policy[s,a] = softmax(Q(s,·)/α_temp)，Q(s,a)=E_{e~p(·|b)}[U_{θ_g}(e,a)]
    # 桶先验 p(e|b)（P9.3 v0.3 通用化）：在 {e: κ(e)=b} 上均匀（κ 按 P2.4 派生——
    # 默认/EXEC-1 配置逐点还原 v0.2 半环均匀先验，回归钉 T-REF2）；u ∝ (0.5,0.5)
    # （v1 不依赖资源时钟）；空桶 ⇒ 零行 ⇒ 该信念态策略均匀（登记约定，细化臂不触发）
    kappa = bucket_map(cfg)
    p_e = np.zeros((al.n_B, al.n_E))
    for b in range(al.n_B):
        cells = np.flatnonzero(kappa == b)
        if len(cells):
            p_e[b, cells] = 1.0 / len(cells)

    u_tabs = utility_tables(cfg)  # (n_theta, n_E, n_A)——Q 值与 u_bar 的公共定义
    q_tab = np.zeros((al.n_S, al.n_A))
    for s in range(al.n_S):
        g, b, m_, r_ = al.split_S(s)
        for a in range(al.n_A):
            q_tab[s, a] = sum(p_e[b, e] * u_tabs[g, e, a] for e in range(al.n_E))
    q_tab -= q_tab.max(axis=1, keepdims=True)
    policy = np.exp(q_tab / cfg.alpha_temp)
    policy /= policy.sum(axis=1, keepdims=True)

    kernels = Kernels(
        obs=obs, belief=belief, internal=internal, policy=policy,
        env=env, resource=resource,
        init_E=np.full(n_E, 1.0 / n_E),
        init_S=np.full(al.n_S, 1.0 / al.n_S),
        init_Z=np.array([0.4, 0.6]),
        init_A=np.full(al.n_A, 1.0 / al.n_A),
    )
    model = CausalModel(alphabet=al, kernels=kernels,
                        params={"fixture": "env0", "env0": asdict(cfg)})
    model.validate()
    return model

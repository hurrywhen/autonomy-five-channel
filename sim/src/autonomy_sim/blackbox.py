"""黑盒降级规则（附录 §10；SPEC_estimators E12.5/E12.6）。

- **10.2 黑盒 A_org 区间界**：行动通道随机化探针（β_π 编译、state-independent 脚本、
  flag=探针指示）下 F_ext^obs=I(脚本^T;A^T)（引理 2.3.1：=DI，无需 S 可观测；
  真值路径由编译结构精确给出 flag·H(脚本)·T，采样插件路径对照）；
  区间 [F(1−η)/(F(1−η)+F_obs), min(1, F(1+η)/(F(1+η)+F_obs))] 包含真值的语义前提
  = F_int 漂移 ≤η（η 不足时不含，作反面控制）。
- **10.3 黑盒 A_exec（协议标签义务）**：策略驱动被动观察 ⇒ obs ≥ cond（状态熵混入，
  附录方向）；独立探针 ⇒ obs ≤ cond（A⊥S 条件化去噪）——方向依赖协议，
  见 R2_文献待查证事项.md §4.7②。
- **Λ（E12.6 标记级）**：手术史含 β/γ（未登记通道）⇒ 0.5 约定值；无 ⇒ 1.0。
  Endorse 事件级 Λ（附录 §4.4）随 ATK-1/ATK-5 场景步落地。
"""
import math

import numpy as np

from .di import mi_nats
from .empowerment import step_channels_from_esz
from .propagate import truth_step_joints

_SURGERY_HISTORY_KEYS = ("beta_pi", "beta_G", "beta_Endorse", "gamma")


def lambda_history(params: dict) -> float:
    """Λ 标记级（E12.6）：手术史含 β/γ ⇒ 0.5；无 ⇒ 1.0（事件级 Λ 属场景步）。"""
    return 0.5 if any(k in params for k in _SURGERY_HISTORY_KEYS) else 1.0


def best_power(p0, p1, alpha: float) -> float:
    """水平 α 最优（随机化 NP）检验功效：按似然比降序贪心填充（无穷比零成本拒绝）。"""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    order = sorted(range(len(p0)),
                   key=lambda o: (p1[o] / p0[o] if p0[o] > 0 else math.inf), reverse=True)
    level = power = 0.0
    for o in order:
        if p0[o] <= 0:
            power += p1[o]
            continue
        take = min(p0[o], alpha - level)
        if take <= 0:
            break
        power += (take / p0[o]) * p1[o]
        level += take
    return power
    return 0.5 if any(k in params for k in _SURGERY_HISTORY_KEYS) else 1.0


def probe_flow_obs(model, T: int) -> float:
    """10.2 黑盒可观测外部流 F_ext^obs=I(脚本^T;A^T)=flag·H(脚本)·T（nats）。

    前提：模型经 apply_beta_pi 且 n_I=2（self/探针指示），π_1 为 state-independent
    脚本（各行相同 ⇒ 脚本内容即行动，iid 外源 ⇒ 引理 2.3.1 MI=DI）。
    """
    info = model.params.get("beta_pi")
    if info is None or info["n_I"] != 2:
        raise ValueError("probe_flow_obs 需 β_π 编译模型（n_I=2：self/探针指示）")
    n_A, flag = info["n_A_base"], info["flag_dist"]
    pol = model.kernels.policy.reshape(model.alphabet.n_S, n_A, 2)
    script = pol[:, :, 1] / flag[1]
    if not np.allclose(script, script[0], atol=1e-12):
        raise ValueError("π_1 非 state-independent：探针脚本约定被违反")
    h_script = float(-np.sum([p * math.log(p) for p in script[0] if p > 0]))
    return flag[1] * h_script * T


def a_org_interval(f_base: float, eta: float, f_ext_obs: float) -> tuple:
    """10.2 区间界：[F(1−η)/(F(1−η)+F_obs), min(1, F(1+η)/(F(1+η)+F_obs))]。"""
    if not 0.0 <= eta <= 1.0:
        raise ValueError(f"漂移容差 η∈[0,1]: {eta}")
    if f_base < 0 or f_ext_obs < 0:
        raise ValueError("流量须非负")
    lo = f_base * (1.0 - eta) / (f_base * (1.0 - eta) + f_ext_obs)
    hi = f_base * (1.0 + eta) / (f_base * (1.0 + eta) + f_ext_obs)
    return lo, min(1.0, hi)


def a_exec_blackbox(model, t: int, policy_driven: bool) -> tuple:
    """10.3 双协议观测量 (obs, cond)（nats，未归一）。

    obs  = I(A_t;O_{t+1})（不条件化 S）；cond = E_{S_t}[I(A_t;O_{t+1}|S_t=s)]。
    policy_driven=True（被动观察协议）：A~π(·|s) 混合；False（独立探针协议）：A 均匀独立。
    """
    aux = truth_step_joints(model, t + 1)[t]
    channels, mask = step_channels_from_esz(model, aux["ESZ"])
    p_s, pol = aux["S"], model.kernels.policy
    n_A = model.alphabet.n_A
    q = (p_s @ pol) if policy_driven else np.full(n_A, 1.0 / n_A)
    # obs：W̄[a,o']=Σ_s p(s)u(a|s)W_s[a,o']/q_a（q_a=0 的行不进 MI）
    joint_obs = np.zeros((n_A, model.alphabet.n_O))
    for s, w_s in enumerate(channels):
        if not mask[s]:
            continue
        u = pol[s] if policy_driven else np.full(n_A, 1.0 / n_A)
        joint_obs += float(p_s[s]) * (u[:, None] * w_s)
    i_obs = mi_nats(joint_obs)
    # cond：E_s[I(u_s;W_s)]
    i_cond = 0.0
    for s, w_s in enumerate(channels):
        if not mask[s] or p_s[s] <= 0:
            continue
        u = pol[s] if policy_driven else np.full(n_A, 1.0 / n_A)
        i_cond += float(p_s[s]) * mi_nats(u[:, None] * w_s)
    return i_obs, i_cond

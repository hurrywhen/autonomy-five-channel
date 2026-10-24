"""干预算子（SPEC_platform §4）：把干预编译为等价的标准内核模型。

推进线第 2 步实现 α（外源信息节点 Ĩ→O）与 σ（资源核脚手架切换）；
第 4 步实现 γ（obs 通道核替换，P4.4）；第 5 步实现 β_π/β_G/δ（P4.5，T-COV）；
β_Endorse 随 ATK-5 场景步落地。
编译产物仍是标准 CausalModel（字母表扩大或同形替换），采样/真值双路径无需改动；
折叠约定登记在 params 中（config_hash 自动覆盖干预配置），di 模块按 params 解码：

- **α**（外源信息节点 Ĩ→O，机制 o 不变、内容可加）：n_O' = n_O_base·n_I，
  O_flat = o·n_I + i；obs'[e,a,(o,i)] = obs[e,a,o]·q(Ĩ=i|E=e)；
  belief'[b,(o,i),q'] ∝ belief[b,o,q']·(1 + response·1[q' ≡ i mod n_I])。
  probe_uniform：q 全均匀（Ĩ iid、与 E 无关——引理 2.3.1 的随机化非预期协议）；
  honest：q 以 fidelity 报 e mod n_I（诚实信息，ATK-4 对照臂语义）。
- **σ**（脚手架/资源切换）：n_Z' = n_Z_base·n_I，Z_flat = z·n_I + i；
  resource'[(z,i),(z2,i2)] = flag[i2]·K_{i2}[z,z2]（旗标 iid 外源、即时生效，
  K_0=原核、K_1=脚手架核）；env'/init_Z' 相应展开。
- **γ**（obs 通道核替换，P4.4）：obs' 为显式核或向常值符号核的混合
  (1−s)·obs + s·δ_{o*}；字母表不变（同形替换），强度 s(γ)=max_{e,a} TV 计算入 params。
"""
from dataclasses import dataclass, replace

import numpy as np

from .graph import Alphabet, CausalModel, Kernels


@dataclass(frozen=True)
class AlphaSpec:
    """α 干预参数。response 为信念对探针的倾斜强度 η≥0；fidelity 为 honest 信号忠实度。"""

    n_I: int
    response: float
    kind: str = "probe_uniform"
    fidelity: float = 1.0
    q_signal: np.ndarray | None = None  # 显式给定 (n_E, n_I) 则优先

    @classmethod
    def probe_uniform(cls, n_I: int, response: float) -> "AlphaSpec":
        """纯随机化探针：Ĩ iid 均匀、与 E 无关（T-DI1 / 黑盒随机化探针协议）。"""
        return cls(n_I=n_I, response=response, kind="probe_uniform")

    @classmethod
    def honest(cls, n_I: int, response: float, fidelity: float) -> "AlphaSpec":
        """诚实信息：q(Ĩ=i|E=e) 以 fidelity 概率报告 e mod n_I（引理 7.2.1 的 α 类）。"""
        return cls(n_I=n_I, response=response, kind="honest", fidelity=fidelity)


@dataclass(frozen=True)
class SigmaSpec:
    """σ 干预参数：iid 外源旗标切换资源核。alt_resource=None ⇒ 由基核自动构造脚手架核。"""

    n_I: int
    flag_dist: tuple
    alt_resource: np.ndarray | None = None

    @classmethod
    def scaffold(cls, flag_prob: float = 0.5, n_I: int = 2) -> "SigmaSpec":
        """脚手架（T8 语义）：旗标 1 以 flag_prob 概率启用更驻留的资源核。"""
        if n_I < 2:
            raise ValueError("scaffold 需 n_I≥2")
        dist = (1.0 - flag_prob, flag_prob) + (0.0,) * (n_I - 2)
        return cls(n_I=n_I, flag_dist=dist)


def _alpha_q(al: Alphabet, spec: AlphaSpec) -> np.ndarray:
    if spec.q_signal is not None:
        q = np.asarray(spec.q_signal, float)
        assert q.shape == (al.n_E, spec.n_I), "q_signal 形状须为 (n_E, n_I)"
        return q
    if spec.kind == "probe_uniform":
        return np.full((al.n_E, spec.n_I), 1.0 / spec.n_I)
    if spec.kind == "honest":
        assert spec.n_I >= 2, "honest 需 n_I≥2"
        q = np.full((al.n_E, spec.n_I), (1.0 - spec.fidelity) / (spec.n_I - 1))
        for e in range(al.n_E):
            q[e, e % spec.n_I] = spec.fidelity
        return q
    raise ValueError(f"未知 α 类型: {spec.kind}")


def apply_alpha(model: CausalModel, spec: AlphaSpec) -> CausalModel:
    """编译 α：O 字母表扩为 (o,i) 对，信念更新对探针倾斜。不动 policy（引理 7.2.1 前提）。"""
    al, k = model.alphabet, model.kernels
    n_I = spec.n_I
    q = _alpha_q(al, spec)
    # obs'[e,a,(o,i)] = obs[e,a,o]·q(i|e)
    obs2 = np.einsum("eao,ei->eaoi", k.obs, q).reshape(al.n_E, al.n_A, al.n_O * n_I)
    # belief'[b,(o,i),q'] ∝ belief[b,o,q']·tilt[i,q']
    idx = np.arange(al.n_B) % n_I
    tilt = 1.0 + spec.response * (idx[None, :] == np.arange(n_I)[:, None]).astype(float)
    belief2 = np.einsum("boq,iq->boiq", k.belief, tilt).reshape(al.n_B, al.n_O * n_I, al.n_B)
    belief2 /= belief2.sum(axis=-1, keepdims=True)
    kernels2 = replace(k, obs=obs2, belief=belief2)
    al2 = replace(al, n_O=al.n_O * n_I)
    params = {**model.params,
              "alpha": {"n_I": n_I, "n_O_base": al.n_O, "response": spec.response,
                        "kind": spec.kind, "fidelity": spec.fidelity}}
    out = CausalModel(alphabet=al2, kernels=kernels2, params=params)
    out.validate()
    return out


def apply_sigma(model: CausalModel, spec: SigmaSpec) -> CausalModel:
    """编译 σ：Z 字母表扩为 (z,i) 对，资源核按 iid 旗标即时切换。不动 policy。"""
    al, k = model.alphabet, model.kernels
    n_I = spec.n_I
    flag = np.asarray(spec.flag_dist, float)
    assert flag.shape == (n_I,) and np.all(flag >= 0) and abs(flag.sum() - 1.0) < 1e-9, \
        "flag_dist 须为 n_I 维归一分布"
    alt = spec.alt_resource
    kind = "custom"
    if alt is None:
        alt = 0.75 * np.eye(al.n_Z) + 0.25 * k.resource  # 脚手架：资源更驻留
        alt = alt / alt.sum(axis=-1, keepdims=True)
        kind = "scaffold"
    kernels_z = [k.resource, np.asarray(alt, float)] + [k.resource] * (n_I - 2)
    # resource'[(z,i),(z2,i2)] = flag[i2]·K_{i2}[z,z2]
    r4 = np.zeros((al.n_Z, n_I, al.n_Z, n_I))
    for i2 in range(n_I):
        r4[:, :, :, i2] = flag[i2] * kernels_z[i2][:, None, :]
    res2 = r4.reshape(al.n_Z * n_I, al.n_Z * n_I)
    # env'[e,a,(z,i),e'] = env[e,a,z,e']
    env2 = np.broadcast_to(k.env[:, :, :, None, :],
                           (al.n_E, al.n_A, al.n_Z, n_I, al.n_E))
    env2 = env2.reshape(al.n_E, al.n_A, al.n_Z * n_I, al.n_E).copy()
    init_z2 = np.einsum("z,i->zi", k.init_Z, flag).reshape(-1)
    kernels2 = replace(k, env=env2, resource=res2, init_Z=init_z2)
    al2 = replace(al, n_Z=al.n_Z * n_I)
    params = {**model.params,
              "sigma": {"n_I": n_I, "n_Z_base": al.n_Z, "flag_dist": [float(f) for f in flag],
                        "kind": kind}}
    out = CausalModel(alphabet=al2, kernels=kernels2, params=params)
    out.validate()
    return out


@dataclass(frozen=True)
class GammaSpec:
    """γ 干预参数（P4.4）：替换 obs 通道核。kernel 显式给定优先；否则 mix_constant 族。"""

    kernel: np.ndarray | None = None
    s: float = 0.0
    symbol: int = 0

    @classmethod
    def explicit(cls, kernel: np.ndarray) -> "GammaSpec":
        """显式替换核（形状须与模型 obs 一致 (n_E, n_A, n_O)）。"""
        return cls(kernel=np.asarray(kernel, float))

    @classmethod
    def mix_constant(cls, s: float, symbol: int) -> "GammaSpec":
        """向常值符号核的混合族：o'=(1−s)·o + s·δ_symbol（E5.4 对抗族；s=ess sup TV 上界）。"""
        if not 0.0 <= s <= 1.0:
            raise ValueError(f"混合强度 s∈[0,1]: {s}")
        return cls(s=float(s), symbol=int(symbol))


def apply_gamma(model: CausalModel, spec: GammaSpec) -> CausalModel:
    """编译 γ：替换 obs 通道核（P1.2 第 1 步作用点；字母表不变）。

    强度 s(γ)=max_{e,a} TV(o'_{e,a}, o_{e,a}) 计算入 params（P4.4 登记义务）。
    """
    al, k = model.alphabet, model.kernels
    if spec.kernel is not None:
        new_obs = np.asarray(spec.kernel, float)
        if new_obs.shape != k.obs.shape:
            raise ValueError(f"显式 γ 核形状 {new_obs.shape} != obs 形状 {k.obs.shape}")
        kind = "explicit"
    else:
        if not 0 <= spec.symbol < al.n_O:
            raise ValueError(f"symbol 越界 [0,{al.n_O}): {spec.symbol}")
        const = np.zeros_like(k.obs)
        const[:, :, spec.symbol] = 1.0
        new_obs = (1.0 - spec.s) * k.obs + spec.s * const
        kind = "mix_constant"
    s_gamma = float((0.5 * np.abs(new_obs - k.obs).sum(axis=-1)).max())
    kernels2 = replace(k, obs=new_obs)
    params = {**model.params,
              "gamma": {"kind": kind, "s": s_gamma,
                        "mix_s": spec.s, "symbol": spec.symbol}}
    out = CausalModel(alphabet=al, kernels=kernels2, params=params)
    out.validate()
    return out


@dataclass(frozen=True)
class BetaPiSpec:
    """β_π 干预参数（P4.5）：外源旗标逐步切换策略核（π_0=原策略，π_i=alt_policies[i−1]）。

    flag_dist：iid 旗标分布（n_I,）——外生探针协议（10.2 区间界的前提）；
    flag_by_state：逐状态旗标（n_S, n_I)——自适应时机（BB-2：旗标依赖 S_t，
    外生性被破坏，仅用于 §10.2 适用域边界的实证演示）。
    """

    flag_dist: tuple
    alt_policies: tuple
    flag_by_state: object = None

    @classmethod
    def switch(cls, alt_policies, flag_dist=None, flag_by_state=None) -> "BetaPiSpec":
        """旗标切换：每步以 flag_dist[i]（或逐状态 flag_by_state[s,i]）采用策略核 π_i。"""
        alts = tuple(np.asarray(p, float) for p in alt_policies)
        if not alts:
            raise ValueError("至少需一个替代策略核（n_I≥2 才有非平凡 β_π）")
        n_I = 1 + len(alts)
        flag = tuple(float(f) for f in (flag_dist if flag_dist is not None
                                        else (1.0 / n_I,) * n_I))
        return cls(flag_dist=flag, alt_policies=alts, flag_by_state=flag_by_state)


@dataclass(frozen=True)
class BetaGSpec:
    """β_G 干预参数（P4.5）：internal 核混合替换，G 以渐变率 η 牵引至植入目标。"""

    eta: float
    target_g: int

    @classmethod
    def plant(cls, eta: float, target_g: int) -> "BetaGSpec":
        if not 0.0 <= eta <= 1.0:
            raise ValueError(f"渐变率 η∈[0,1]: {eta}")
        return cls(eta=float(eta), target_g=int(target_g))


@dataclass(frozen=True)
class DeltaSpec:
    """δ 干预参数（P4.5）：policy 支撑收缩（𝒜'⊂𝒜 零化重归一）。"""

    keep: tuple

    @classmethod
    def contract(cls, keep) -> "DeltaSpec":
        keep = tuple(sorted({int(a) for a in keep}))
        if not keep:
            raise ValueError("keep 不能为空")
        return cls(keep=keep)


def apply_beta_pi(model: CausalModel, spec: BetaPiSpec) -> CausalModel:
    """编译 β_π：A 字母表扩为 (a,i) 对（A_flat=a·n_I+i），旗标逐步切换策略核。

    policy'[S,(a,i)] = flag[i]·π_i[S,a]；env/obs/init_A 只索引真实行动 a（物理不看旗标）；
    I^β_t 由 A_flat % n_I 解码（make_i_decoder）。F_int 既有路径不变（旗标外源独立，
    熵对消后恰为到真实行动的 Massey DI）；F_ext 走 E2.5(i) Jensen 间隙路径。
    """
    al, k = model.alphabet, model.kernels
    policies = (k.policy,) + spec.alt_policies
    n_I = len(policies)
    for i, p in enumerate(policies):
        if p.shape != (al.n_S, al.n_A):
            raise ValueError(f"π_{i} 形状 {p.shape} != ({al.n_S},{al.n_A})")
    flag_state = spec.flag_by_state
    if flag_state is not None:
        # 自适应时机（BB-2）：逐状态旗标，行归一；外生性被破坏（仅适用域演示）
        fs = np.asarray(flag_state, float)
        if fs.shape != (al.n_S, n_I) or np.any(fs < 0) or not np.allclose(fs.sum(1), 1.0):
            raise ValueError(f"flag_by_state 形状/归一不符：{fs.shape} != ({al.n_S},{n_I})")
        pol3 = np.einsum("si,sai->sai", fs, np.stack(policies, axis=-1))
        flag = tuple(float(f) for f in fs.mean(axis=0))  # 占位均值（调度分支用 flag_by_state）
    else:
        flag = np.asarray(spec.flag_dist, float)
        if flag.shape != (n_I,) or np.any(flag < 0) or abs(flag.sum() - 1.0) > 1e-9:
            raise ValueError(f"flag_dist 须为 n_I={n_I} 维归一分布")
        pol3 = np.einsum("i,sai->sai", flag, np.stack(policies, axis=-1))
    policy2 = pol3.reshape(al.n_S, al.n_A * n_I)
    env2 = np.broadcast_to(k.env[:, :, None, :, :],
                           (al.n_E, al.n_A, n_I, al.n_Z, al.n_E))
    env2 = env2.reshape(al.n_E, al.n_A * n_I, al.n_Z, al.n_E).copy()
    obs2 = np.broadcast_to(k.obs[:, :, None, :], (al.n_E, al.n_A, n_I, al.n_O))
    obs2 = obs2.reshape(al.n_E, al.n_A * n_I, al.n_O).copy()
    init_a2 = np.einsum("a,i->ai", k.init_A, flag).reshape(-1)
    kernels2 = replace(k, policy=policy2, env=env2, obs=obs2, init_A=init_a2)
    al2 = replace(al, n_A=al.n_A * n_I)
    params = {**model.params,
              "beta_pi": {"n_I": n_I, "n_A_base": al.n_A,
                          "flag_dist": [float(f) for f in flag], "kind": "switch",
                          "flag_by_state": (None if flag_state is None
                                            else [[float(v) for v in row] for row in fs])}}
    out = CausalModel(alphabet=al2, kernels=kernels2, params=params)
    out.validate()
    return out


def apply_beta_g(model: CausalModel, spec: BetaGSpec) -> CausalModel:
    """编译 β_G：internal' = (1−η)·K + η·K_plant（K_plant 把 G 置为植入目标，(M,R) 不变）。

    静态手术（无外源 I 节点）⇒ F_ext≡0 平凡成立（E2.5(ii)，A_org 盲见证的语义前提）。
    """
    al, k = model.alphabet, model.kernels
    if not 0 <= spec.target_g < al.n_G:
        raise ValueError(f"target_g 越界 [0,{al.n_G}): {spec.target_g}")
    k_plant = np.zeros_like(k.internal)
    for gmr in range(al.n_GMR):
        g, rem = divmod(gmr, al.n_M * al.n_R)
        m, r = divmod(rem, al.n_R)
        dst = (spec.target_g * al.n_M + m) * al.n_R + r
        k_plant[gmr, dst] = 1.0
    internal2 = (1.0 - spec.eta) * k.internal + spec.eta * k_plant
    kernels2 = replace(k, internal=internal2)
    params = {**model.params,
              "beta_G": {"eta": spec.eta, "target_g": spec.target_g, "kind": "plant"}}
    out = CausalModel(alphabet=al, kernels=kernels2, params=params)
    out.validate()
    return out


def apply_delta(model: CausalModel, spec: DeltaSpec) -> CausalModel:
    """编译 δ：policy 支撑收缩至 keep（零化重归一，字母表不变）。静态手术 ⇒ F_ext≡0。"""
    al, k = model.alphabet, model.kernels
    if spec.keep[-1] >= al.n_A:
        raise ValueError(f"keep 越界 [0,{al.n_A}): {spec.keep}")
    policy2 = np.zeros_like(k.policy)
    policy2[:, spec.keep] = k.policy[:, spec.keep]
    row_sum = policy2.sum(axis=1, keepdims=True)
    if np.any(row_sum <= 0):
        raise ValueError("存在策略行在 keep 上零质量（该状态原策略已排除保留行动）")
    policy2 /= row_sum
    kernels2 = replace(k, policy=policy2)
    params = {**model.params,
              "delta": {"keep": list(spec.keep),
                        "strength": 1.0 - len(spec.keep) / al.n_A, "kind": "contract"}}
    out = CausalModel(alphabet=al, kernels=kernels2, params=params)
    out.validate()
    return out


def make_i_decoder(model: CausalModel):
    """按 params 登记的干预构造 I_t 五字段解码器（simulate_trajectories 的 i_decoder）。

    α 字段记录探针符号 Ĩ_t（由 O_flat 解码）；σ 字段记录旗标 I^σ_t（由 Z_flat 解码）；
    γ 字段记录常值强度 s(γ)（核替换无逐步随机符号）；
    β 字段记录策略旗标（由 A_flat % n_I 解码）；δ 字段记录常值支撑收缩强度；
    β_G/β_Endorse 无外源逐步符号，恒 0。
    """
    n_ia = model.params.get("alpha", {}).get("n_I")
    n_is = model.params.get("sigma", {}).get("n_I")
    s_g = model.params.get("gamma", {}).get("s")
    n_ib = model.params.get("beta_pi", {}).get("n_I")
    d_strength = model.params.get("delta", {}).get("strength")

    def decode(syms, mdl):
        n = len(syms["A"])
        out = {k: np.zeros(n) for k in ("sigma", "alpha", "beta", "gamma", "delta")}
        if n_ia:
            out["alpha"] = (syms["O"] % n_ia).astype(float)
        if n_is:
            out["sigma"] = (syms["Z"] % n_is).astype(float)
        if s_g is not None:
            out["gamma"] = np.full(n, float(s_g))
        if n_ib:
            out["beta"] = (syms["A"] % n_ib).astype(float)
        if d_strength is not None:
            out["delta"] = np.full(n, float(d_strength))
        return out

    return decode

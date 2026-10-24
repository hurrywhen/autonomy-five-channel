"""分量束接线（SPEC_platform P9.4）：ENV-0 编译模型的六分量＋Λ＋Â_phen/AI 真值计算。

口径（P9.4）：
- A_org=di.truth_A_org；A_goal=components.truth_A_goal（U_eff=S 边缘模态 G 白盒直读）；
- A_exec=E3.7 信道＋Π_t 支撑（P9.3），基线 S_t 边缘加权，n=1 规范化 log|𝒜|；
- A_epi=truth_A_epi_real（**相对真值精度**（2026-10-15 审稿修复，E5.1）：逐模型对自身
  (E_t,B_t) 联合计命中率均值；κ 由 derive_bucket_map 派生——基线因观测噪声 <1，
  特性非 bug；原"γ 臂对无 γ 基线、无 γ ⇒ 1"反事实约定废止）；
- A_ref=E6.4 联合表（配置 ensemble_joint）×背书一致率×Λ；
- A_via=min{1, z̄_high/s_crit, m}（**v0.2 扩展闸门**：m=clip(min(κ_eff/κ_req, R_eff/R_req),0,1)
  能力包络裕度——配置默认 m=1 逐点还原资源型旧式；θ 不入闸门）；
- Λ=律级操作化（law_level_lambda）；Â_phen=登记史重建分量复合；AI=Â_phen−A_obj；
- u_bar=外部基线量（E7.1：逐步 (E_t,A_t) 联合下 U_θ* 期望，θ*=内生背书目标；
  非分量、不入复合——E2 外部效度分析数据源）。

性能约定（SPEC_experiments M9.4）：truth_bundle 为内容寻址 LRU 缓存（确定性精确记忆化），
矩阵层 rep/σ 重复 cell 的模型计算由此摊销。
"""
import math
from collections import OrderedDict, namedtuple

import numpy as np

from . import components, di, empowerment, propagate
from .aggregate import composite_A
from .env0 import Env0Config, bucket_map as _env0_bucket_map, endorse_table, utility_tables
from .graph import model_content_hash

Bundle = namedtuple("Bundle", [
    "a_org", "a_goal", "a_exec", "a_epi", "a_ref", "a_via",
    "lam", "a_obj", "a_phen", "ai", "u_bar",
])

W5_DEFAULT = (0.2, 0.2, 0.2, 0.2, 0.2)


def law_level_lambda(params: dict) -> float:
    """Λ 律级操作化（P9.4）：β_G⇒1−η；β_π⇒flag 自方份额；隐蔽 γ⇒1−s(γ)；否则 1.0。"""
    if "beta_G" in params:
        return 1.0 - float(params["beta_G"]["eta"])
    if "beta_pi" in params:
        return float(params["beta_pi"]["flag_dist"][0])
    if "gamma" in params:
        return 1.0 - float(params["gamma"]["s"])
    return 1.0


def _truth_a_exec(model, joints, n_A: int) -> float:
    """A_exec：E3.7 信道＋Π_t 支撑（策略非零质量支撑集），S_T 边缘加权。"""
    channels, mask = empowerment.step_channels_from_esz(model, joints[-1]["ESZ"])
    p_s = joints[-1]["S"]
    e_pi = 0.0
    for s, w_s in enumerate(channels):
        if not mask[s] or p_s[s] <= 0:
            continue
        support = tuple(a for a in range(n_A) if model.kernels.policy[s, a] > 1e-9)
        e_pi += float(p_s[s]) * empowerment.empowerment_support(w_s, support)
    return empowerment.a_exec(e_pi, n=1, n_A=n_A)


def _truth_a_ref(cfg: Env0Config, lam: float) -> float:
    """A_ref：E6.4 系综联合表 × 背书一致率 × Λ（lam 显式给定）。"""
    r_res = components.truth_A_ref(np.asarray(cfg.ensemble_joint, float),
                                   p_endorse=1.0, lam_ref=lam)
    return r_res.point if not r_res.degenerate else r_res.hi


def derive_bucket_map(model) -> np.ndarray:
    """κ：E→信念桶的协议粗粒化映射派生（A_epi 精度化口径，E5.1；规则=SPEC_platform P2.4）。

    规则：params 含 env0 配置（L、U、n_B、n_O）⇒ `env0.bucket_map`（细化感知派生
    κ(e)=min(o*(e)·n_B//n_O, n_B−1)，与 obs 编码/belief 吸收同式——默认与 EXEC-1
    配置逐点还原 v0.2 半环桶）；否则若 n_E==n_B（如 C0 fixture）⇒ 恒等映射；
    否则 raise（登记不可计算，不静默）。
    """
    cfg_dict = model.params.get("env0")
    if cfg_dict is not None:
        return _env0_bucket_map(Env0Config(**cfg_dict))
    al = model.alphabet
    if al.n_E == al.n_B:
        return np.arange(al.n_B, dtype=int)
    raise ValueError(f"bucket_map 不可派生：params 无 env0 配置且 n_E({al.n_E}) != n_B({al.n_B})")


_BUNDLE_CACHE: OrderedDict = OrderedDict()
_BUNDLE_CACHE_CAP = 128  # 分量元组为 9 浮点，内存可忽略（M9.4）


_Components = namedtuple("_Components", [
    "a_org", "a_goal", "a_exec", "a_epi", "a_ref", "a_via", "lam",
    "a_exec_phen", "a_epi_phen", "a_ref_phen", "u_bar",
])


def truth_bundle(model, T: int = 2, baseline=None, weights=W5_DEFAULT,
                 sigma: float = 1.0) -> Bundle:
    """ENV-0 编译模型的分量束（真值模式，T 为 DI/传播视界）。

    baseline：无干预参照模型——仅 Â_phen 的登记史重建参照轨使用（A_epi 精度化后
    逐模型自闭合，不再依赖反事实对照）；无手术模型调用时与自身对照。
    sigma：复合 CES 参数（M9.2——σ 只经 composite_A 进入，分量真值 σ-无关）。

    内容寻址 LRU 缓存（M9.4）：缓存对象为 **σ-无关分量元组**（含 phen 轨分量）；
    σ 相关量（a_obj/a_phen/ai）由缓存分量即时复合 ⇒ σ 臂共享同一分量缓存。
    指纹覆盖 params＋内核，原地变异安全；矩阵层 rep/σ 重复 cell 经此摊销。
    """
    key = (model_content_hash(model), int(T),
           model_content_hash(baseline) if baseline is not None else None,
           tuple(float(w) for w in weights))
    comp = _BUNDLE_CACHE.get(key)
    if comp is None:
        comp = _truth_components_impl(model, T, baseline)
        if len(_BUNDLE_CACHE) >= _BUNDLE_CACHE_CAP:
            _BUNDLE_CACHE.popitem(last=False)
        _BUNDLE_CACHE[key] = comp
    else:
        _BUNDLE_CACHE.move_to_end(key)
    comps5 = (comp.a_org, comp.a_goal, comp.a_exec, comp.a_epi, comp.a_ref)
    a_obj = composite_A(comp.a_via, comps5, weights, sigma=float(sigma))
    a_phen = composite_A(comp.a_via, (1.0, 1.0, comp.a_exec_phen, comp.a_epi_phen, comp.a_ref_phen),
                         weights, sigma=float(sigma))
    return Bundle(a_org=comp.a_org, a_goal=comp.a_goal, a_exec=comp.a_exec,
                  a_epi=comp.a_epi, a_ref=comp.a_ref, a_via=comp.a_via, lam=comp.lam,
                  a_obj=a_obj, a_phen=a_phen, ai=a_phen - a_obj, u_bar=comp.u_bar)


def _truth_components_impl(model, T: int, baseline) -> _Components:
    cfg_dict = model.params.get("env0")
    if cfg_dict is None:
        raise ValueError("truth_bundle 需 ENV-0 构建的模型（params 含 'env0' 配置）")
    cfg = Env0Config(**cfg_dict)
    al = model.alphabet
    joints = propagate.truth_step_joints(model, T)

    # A_org（来源）
    a_org = di.truth_A_org(model, T)

    # A_goal（目标）：U_eff=G 边缘均值（白盒直读；分级俘获连续谱操作化，P9.4）
    etab = endorse_table(cfg)
    g_marg = joints[-1]["S"].reshape(al.n_G, al.n_B, al.n_M, al.n_R).sum(axis=(1, 2, 3))
    u_eff = float(np.dot(g_marg, np.arange(al.n_G)))
    endorse_fn = lambda u: float(etab[int(round(u))])
    g_res = components.truth_A_goal(u_eff, endorse_fn, [float(i) for i in range(al.n_G)])
    a_goal = g_res.point if not g_res.degenerate else g_res.hi

    # A_exec（执行，实轨）
    a_exec = _truth_a_exec(model, joints, al.n_A)

    # A_epi（认知）：相对真值精度（E5.1 审稿修复口径）——逐模型对自身 (E_t,B_t) 联合计；
    # 无"无 γ ⇒ 1"约定：基线因观测噪声同样 <1（特性非 bug，T1c D1 口径）
    bmap = derive_bucket_map(model)
    a_epi = components.truth_A_epi_real(model, T, bmap).a_epi_real

    # A_ref（反思）与 Λ（律级）
    lam = law_level_lambda(model.params)
    a_ref = _truth_a_ref(cfg, lam)

    # A_via（可行性，v0.2 扩展闸门）：min{1, Z 高位占时/s_crit, 能力包络裕度 m}
    # （σ 编译模型按扁平约定 z=1 分箱解码；m=clip(min(κ_eff/κ_req, R_eff/R_req),0,1)，
    # 配置默认 (1,0.5,1,0.5) ⇒ m=1 逐点还原资源型旧式——v1 矩阵数值不变，P9.4）
    n_is = int(model.params.get("sigma", {}).get("n_I", 1))
    z_occ = float(np.mean([aux["Z"][n_is:2 * n_is].sum() for aux in joints]))
    m_cap = min(1.0, max(0.0, min(cfg.kappa_eff / cfg.kappa_req,
                                  cfg.r_eff / cfg.r_req)))
    a_via = min(1.0, z_occ / cfg.s_crit, m_cap)

    # u_bar（外部基线量，E7.1）：U_θ* 在逐步 (E_t,A_t) 联合下的期望（真值精确；
    # β_π 扁平模型先对旗标维边缘化出真实行动混合律 π̄）
    u_tab = utility_tables(cfg)[cfg.theta_star]           # (n_E, n_A_base)
    pol = model.kernels.policy
    if "beta_pi" in model.params:
        info = model.params["beta_pi"]
        pol = pol.reshape(al.n_S, int(info["n_A_base"]), int(info["n_I"])).sum(axis=2)
    u_bar = 0.0
    for aux in joints:
        p_ea = aux["ESZ"].sum(axis=2) @ pol               # p(E_t,A_t)
        u_bar += float((p_ea * u_tab).sum())
    u_bar /= len(joints)

    # Â_phen（E9.4 v1）：登记史重建——A_org/A_goal 自评恒 1；A_epi^phen=参照轨真值精度
    # （自我模型假设通道 nominal；精度化口径下与旧约定 1−s_reg 在基线等价——s_reg=0 时
    # 参照轨即基线）；A_exec/A_ref 取无干预参照轨（baseline 或自身），Λ^phen=1
    ref = baseline if baseline is not None else model
    ref_cfg = Env0Config(**ref.params["env0"])
    ref_joints = propagate.truth_step_joints(ref, T) if ref is not model else joints
    a_exec_phen = _truth_a_exec(ref, ref_joints, ref.alphabet.n_A)
    a_epi_phen = components.truth_A_epi_real(ref, T, derive_bucket_map(ref)).a_epi_real
    a_ref_phen = _truth_a_ref(ref_cfg, 1.0)
    return _Components(a_org=a_org, a_goal=a_goal, a_exec=a_exec, a_epi=a_epi, a_ref=a_ref,
                       a_via=a_via, lam=lam,
                       a_exec_phen=a_exec_phen, a_epi_phen=a_epi_phen, a_ref_phen=a_ref_phen,
                       u_bar=u_bar)

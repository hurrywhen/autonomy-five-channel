"""有向信息（DI）与互信息：真值路径（SPEC_estimators §2；附录定义 2.3.A/B、引理 2.3.1/7.2.1、命题 5.2）。

全部信息量以 nats 计（log 底 e）。两层接口：

**序列联合表层**（T-DI2 回归锚）：entropy_nats / mi_nats / mi_seq / massey_di_seq
作用于显式序列联合张量（轴序：X^T 各轴在前、Y^T 各轴在后）。

**模型层**（T-DI1/T-ORG/T-MED）：
- truth_F_int = I(S^T→A^T)（Massey 定义 2.3.A）：A-历史树精确滤波，
  逐项 H(A_t|A^{t−1}) − E[H(π(·|S_t))]（E5 架构下 A_t 给定 S^t 的条件律即 π(·|S_t)）。
- truth_F_ext = I(I^T→A^T‖S^T)（Kramer Def.4 因果条件化，定义 2.3.B，条件集 S^t）：
  = Σ_t [H(A_t|A^{t−1},S^t) − H(A_t|A^{t−1},S^t,I^t)]。
  对 α/σ/γ 类干预（有效策略 π̃(·|s,i) 与 i 无关——apply_alpha/apply_sigma 不触碰
  policy 内核，实现时按键名核验）两项均恒等于 E[H(π(·|S_t))]：第一项经 S 边缘路径、
  第二项经 (S,O) 联合边缘路径独立计算后取差——引理 7.2.1 的精确零残余流即此恒等。
  β_π（旗标切换策略）走 Jensen 间隙路径（E2.5(i)，第 5 步 T-COV 落地）；
  β_G/β_Endorse/δ 静态手术（无外源 I 节点）⇒ F_ext≡0 平凡成立（E2.5(ii)）；
  β_π×α 复合显式 NotImplementedError（拒绝给出静默错误值）。
- truth_A_org = F_int/(F_int+F_ext)；分母为 0（0/0 病态，AX0 排除）⇒ ValueError。
- truth_probe_mi_di：外源探针的 I(Ĩ^T;A^T) 与 I(Ĩ^T→A^T)，(Ĩ,A)-历史树精确枚举
  （引理 2.3.1 的真值模式锚）。
- probe_belief_mi / sigma_resource_mi：中介见证 I(Ĩ_t;B_t)、I(I^σ_t;Z_t) 逐步值
  （T-MED 的非空判据——证明"经中介的流存在而残余流为零"）。
"""
import numpy as np

from .graph import CausalModel, kernel_fingerprint, model_content_hash
from .propagate import truth_step_joints

# F_ext 调度（SPEC_estimators E2.5）：
# - beta_pi（旗标切换策略）⇒ Jensen 间隙路径（通用后验路径，第 5 步 T-COV 落地）；
# - beta_G/beta_Endorse/delta（静态手术，无外源 I 节点）⇒ F_ext≡0 平凡成立；
# - 无上述键（α/σ/γ 或无干预）⇒ 引理 7.2.1 双项零残余路径。
SURGERY_KEYS = ("beta_pi", "beta_G", "beta_Endorse", "delta")


# ---------------------------------------------------------------- 序列联合表层

def entropy_nats(p) -> float:
    """离散分布的熵（nats）。输入自动归一（容许浮点漂移）。"""
    p = np.asarray(p, dtype=float).ravel()
    s = p.sum()
    if s <= 0:
        return 0.0
    p = p / s
    p = p[p > 0]
    return float(-(p * np.log(p)).sum())


def mi_nats(j2: np.ndarray) -> float:
    """二元联合表的互信息 I(X;Y)（nats）。"""
    j2 = np.asarray(j2, dtype=float)
    return entropy_nats(j2.sum(axis=1)) + entropy_nats(j2.sum(axis=0)) - entropy_nats(j2)


def mi_seq(joint: np.ndarray, T: int, nx: int, ny: int) -> float:
    """序列联合（轴序 X^T 后 Y^T）的互信息 I(X^T;Y^T)（nats）。"""
    j = np.asarray(joint, dtype=float).reshape(nx ** T, ny ** T)
    return mi_nats(j)


def massey_di_seq(joint: np.ndarray, T: int, nx: int, ny: int) -> float:
    """Massey 有向信息 I(X^T→Y^T)=Σ_t I(X^t;Y_t|Y^{t−1})（定义 2.3.A，nats）。

    joint 轴序：X_1..X_T 各轴在前、Y_1..Y_T 各轴在后。
    """
    joint = np.asarray(joint, dtype=float)
    total = 0.0
    for t in range(1, T + 1):
        tail = tuple(range(t, T)) + tuple(range(T + t, 2 * T))
        jt = joint.sum(axis=tail) if tail else joint  # 截断到前 t 步：(nx,)^t + (ny,)^t
        # I(X^t;Y_t|Y^{t−1}) = H(Y^t) − H(Y^{t−1}) − H(X^t Y^t) + H(X^t Y^{t−1})
        hy_t = entropy_nats(jt.sum(axis=tuple(range(t))))
        hy_tm1 = entropy_nats(jt.sum(axis=tuple(range(t + 1))))
        hxy_t = entropy_nats(jt)
        hxy_tm1 = entropy_nats(jt.sum(axis=2 * t - 1))  # 只求和 Y_t 轴（jt 末轴）
        total += hy_t - hy_tm1 - hxy_t + hxy_tm1
    return total


# ---------------------------------------------------------------- 模型层：复合步核

def _n_I(model: CausalModel) -> int:
    return int(model.params.get("alpha", {}).get("n_I", 1))


def _init_u(model: CausalModel) -> np.ndarray:
    """p(U_1)，U = (E,S,Z,A_prev)，扁平序 ((e·n_S+s)·n_Z+z)·n_A+ap。"""
    k = model.kernels
    return np.einsum("e,s,z,a->esza", k.init_E, k.init_S, k.init_Z, k.init_A).reshape(-1)


_STEP_KERNEL_CACHE: dict = {}
_STEP_KERNEL_CACHE_CAP = 4  # 内存上限护栏（大 n_U 模型逐出最旧条目）


def _step_kernel(model: CausalModel) -> np.ndarray:
    """复合步核 stepK[u_src, b, u_dst]：分支 b = i·n_A + a（i=Ĩ_t，无 α 时 n_I=1）。

    给定 U_t=(E,S,Z,A_prev)，一步内复合 O_t→B_t→S'_t→A_t 与 Z'_t→E_{t+1} 的完整转移，
    输出分支 (Ĩ_t, A_t) 与新状态 U_{t+1}=(E_{t+1},S_{t+1},Z_{t+1},A_t) 的联合核。
    构建成本 O(n_U²·n_I·n_A) 高 ⇒ 按内核指纹缓存（graph.kernel_fingerprint）。
    """
    key = (kernel_fingerprint(model), _n_I(model))
    sk = _STEP_KERNEL_CACHE.get(key)
    if sk is not None:
        return sk
    sk = _build_step_kernel(model)
    if len(_STEP_KERNEL_CACHE) >= _STEP_KERNEL_CACHE_CAP:
        _STEP_KERNEL_CACHE.pop(next(iter(_STEP_KERNEL_CACHE)))
    _STEP_KERNEL_CACHE[key] = sk
    return sk


def _build_step_kernel(model: CausalModel) -> np.ndarray:
    al, k = model.alphabet, model.kernels
    n_I = _n_I(model)
    n_U = al.n_E * al.n_S * al.n_Z * al.n_A
    eye = np.eye(n_U).reshape(al.n_E, al.n_S, al.n_Z, al.n_A, n_U)
    # 1. O_t ~ obs[E, A_prev]（α 模型的 O 含 (o,i) 对）
    p1 = np.einsum("eszah,eao->eszaoh", eye, k.obs)
    # 2. B_t ~ belief[B, O_t]
    jr = p1.reshape(al.n_E, al.n_G, al.n_B, al.n_M, al.n_R, al.n_Z, al.n_A, al.n_O, n_U)
    jb = np.einsum("egbmrzaoh,boq->egqmrzaoh", jr, k.belief)
    # 3. (G,M,R) 内部更新
    jt = jb.transpose(0, 1, 3, 4, 2, 5, 6, 7, 8)
    jw = jt.reshape(al.n_E, al.n_GMR, al.n_B, al.n_Z, al.n_A, al.n_O, n_U)
    jn = np.einsum("ewbzaoh,wg->egbzaoh", jw, k.internal)
    # 4. A_t ~ policy[S']
    jn4 = jn.reshape(al.n_E, al.n_G, al.n_M, al.n_R, al.n_B, al.n_Z, al.n_A, al.n_O, n_U)
    js = jn4.transpose(0, 1, 4, 2, 3, 5, 6, 7, 8).reshape(
        al.n_E, al.n_S, al.n_Z, al.n_A, al.n_O, n_U)
    ja = np.einsum("ewzcoh,wa->ewzcoah", js, k.policy)
    # 5. Z' ~ resource[Z,·]；E' ~ env[E,A_t,Z',·]
    p6 = np.einsum("ewzcoah,zZ,eaZf->fwZaoh", ja, k.resource, k.env)
    # p6 轴: (E', S', Z', A_t, O_t, U_src)；分解 O = (o_base, i) 并求和 o_base
    n_O_base = al.n_O // n_I
    p7 = p6.reshape(al.n_E, al.n_S, al.n_Z, al.n_A, n_O_base, n_I, n_U).sum(axis=4)
    # → (E', S', Z', A_t, i, U_src)；组装 stepK[u_src, b=i·n_A+a, u_dst=g·n_A+a]
    # （a 同时出现在分支与目标状态中，须按对角切片赋值，不能整体 reshape）
    n_ESZ = al.n_E * al.n_S * al.n_Z
    p7r = p7.reshape(n_ESZ, al.n_A, n_I, n_U)  # (g, a, i, u_src)
    stepK = np.zeros((n_U, n_I * al.n_A, n_U))
    for a in range(al.n_A):
        stepK[:, a::al.n_A, a::al.n_A] = p7r[:, a, :, :].transpose(2, 1, 0)
    return stepK


# ---------------------------------------------------------------- 模型层：F_int / F_ext / A_org

_SCALAR_CACHE: dict = {}
_SCALAR_CACHE_CAP = 512  # 值为浮点，内存可忽略（M9.4 延伸：矩阵 rep/σ 重复 cell 摊销）


def _memo_scalar(name: str, model: CausalModel, T: int, compute) -> float:
    """真值标量的内容寻址记忆化（确定性纯函数 (model, T) → float；指纹含 params＋内核）。"""
    key = (name, model_content_hash(model), int(T))
    if key not in _SCALAR_CACHE:
        if len(_SCALAR_CACHE) >= _SCALAR_CACHE_CAP:
            _SCALAR_CACHE.pop(next(iter(_SCALAR_CACHE)))
        _SCALAR_CACHE[key] = float(compute())
    return _SCALAR_CACHE[key]


def truth_F_int(model: CausalModel, T: int) -> float:
    """F_int = I(S^T→A^T)（Massey，nats）：A-历史树精确计算。内容寻址记忆化（M9.4）。"""
    return _memo_scalar("F_int", model, T, lambda: _truth_F_int_impl(model, T))


def _truth_F_int_impl(model: CausalModel, T: int) -> float:
    al = model.alphabet
    n_I = _n_I(model)
    stepK = _step_kernel(model)
    n_U = stepK.shape[0]
    transB = stepK.reshape(n_U, n_I, al.n_A, n_U).sum(axis=1)  # (u, a, u')
    emitB = transB.sum(axis=2)                                  # (u, a)
    h_pi = np.array([entropy_nats(row) for row in model.kernels.policy])
    idx = np.arange(n_U)
    s_of_u = (idx // (al.n_A * al.n_Z)) % al.n_S
    Ps = np.zeros((n_U, al.n_S))
    Ps[idx, s_of_u] = 1.0
    Q = _init_u(model)[:, None]
    total = 0.0
    for _ in range(T):
        Ja = np.einsum("uh,ua->ah", Q, emitB)  # p(A_t, a^{t−1})
        h_cond = entropy_nats(Ja) - entropy_nats(Ja.sum(axis=0))  # H(A_t|A^{t−1})
        Q = np.einsum("uh,uav->vah", Q, transB).reshape(n_U, -1)
        p_s = Q.sum(axis=1) @ Ps                                  # p(S'_t)
        total += h_cond - float(p_s @ h_pi)                       # −H(A_t|A^{t−1},S^t)
    return total


def _f_ext_beta_pi(model: CausalModel, T: int) -> float:
    """E2.5(i)：β_π 旗标切换策略的 F_ext ——混合条件律的 Jensen 间隙（nats）。

    F_ext = Σ_t E_{S_t}[H(π̄(·|S_t)) − Σ_i flag_i·H(π_i(·|S_t))]，
    π̄ = Σ_i flag_i·π_i（对真实行动的边缘条件律）；π_i 由扁平策略张量与 flag 重建；
    S_t 边缘由 propagate 精确提取。π̄≠π_i（旗标改变给定 S_t 的条件律）⇒ 严格为正。

    逐状态旗标（BB-2 自适应时机）：flag_i 代以 flag[S_t,i]，即逐状态的
    条件互信息 I(I_t; A_t | S_t)——旗标给定 S_t 后仍含外源随机性，
    I_t 不携带 S_t 之外关于 A^{t−1} 的信息 ⇒ 与 Kramer 因果条件化逐项一致。
    """
    info = model.params["beta_pi"]
    n_I, n_A = info["n_I"], info["n_A_base"]
    flag_state = info.get("flag_by_state")
    pol = model.kernels.policy.reshape(model.alphabet.n_S, n_A, n_I)
    h_js = np.array([entropy_nats(row) for row in pol.sum(axis=2)])  # H(π̄(·|s))
    if flag_state is not None:
        fs = np.asarray(flag_state, float)  # (n_S, n_I)
        for i in range(n_I):
            w_i = fs[:, i]
            active = w_i > 0
            if not active.any():
                continue
            h_i = np.zeros_like(w_i)
            h_i[active] = [entropy_nats(row) for row in pol[active, :, i] / w_i[active, None]]
            h_js -= w_i * h_i
    else:
        flag = np.asarray(info["flag_dist"], float)
        for i in range(n_I):
            if flag[i] <= 0:
                continue
            h_i = np.array([entropy_nats(row) for row in pol[:, :, i] / flag[i]])
            h_js -= flag[i] * h_i
    return sum(float(aux["S"] @ h_js) for aux in truth_step_joints(model, T))


def truth_F_ext(model: CausalModel, T: int) -> float:
    """F_ext = I(I^T→A^T‖S^T)（Kramer Def.4 因果条件化，nats）。调度（E2.5）：

    - β_π：Jensen 间隙路径（_f_ext_beta_pi）；
    - β_G/β_Endorse/δ（静态手术，无外源 I 节点）⇒ F_ext≡0 平凡成立；
    - α/σ/γ 类（π̃ 与 I 无关）下由引理 7.2.1 恒等于 0：逐项
      H(A_t|A^{t−1},S^t)（S 边缘路径）− H(A_t|A^{t−1},S^t,I^t)（(S,O) 联合边缘路径），
      两项数学上同为 E[H(π(·|S_t))]，独立路径计算后取差（容差内精确为 0）。
    β_π×α 复合暂不支持（显式报错）。

    内容寻址记忆化（M9.4）。
    """
    return _memo_scalar("F_ext", model, T, lambda: _truth_F_ext_impl(model, T))


def _truth_F_ext_impl(model: CausalModel, T: int) -> float:
    if "beta_pi" in model.params:
        if "alpha" in model.params:
            raise NotImplementedError("β_π×α 复合手术的 F_ext 路径未实现（E2.5：场景步按需扩展）")
        return _f_ext_beta_pi(model, T)
    if set(model.params) & {"beta_G", "beta_Endorse", "delta"}:
        return 0.0  # 静态手术：干预过程为空 ⇒ F_ext≡0 平凡成立（E2.5(ii)）
    h_pi = np.array([entropy_nats(row) for row in model.kernels.policy])
    total = 0.0
    for aux in truth_step_joints(model, T):
        term1 = float(aux["S"] @ h_pi)            # H(A_t|A^{t−1},S^t)
        term2 = float(aux["SO"].sum(axis=1) @ h_pi)  # H(A_t|A^{t−1},S^t,I^t)
        total += term1 - term2
    return total


def truth_A_org(model: CausalModel, T: int) -> float:
    """A_org = F_int/(F_int+F_ext)。分母为 0（0/0 病态，AX0 排除）⇒ ValueError。

    数值裁剪：F_ext 双项路径的浮点残差（~1e-16）可使比值越出命题 5.2 区间 (0,1]，
    1e-9 容差内归位（更大越界保持原值，交由调用方/测试检出——不做静默掩盖）。
    内容寻址记忆化（M9.4）。
    """
    return _memo_scalar("A_org", model, T, lambda: _truth_A_org_impl(model, T))


def _truth_A_org_impl(model: CausalModel, T: int) -> float:
    f_int = truth_F_int(model, T)
    f_ext = truth_F_ext(model, T)
    denom = f_int + f_ext
    if abs(denom) < 1e-12:
        raise ValueError("F_int+F_ext=0（0/0 病态）：违反 AX0（命题 5.2(i) 的前提）")
    a = f_int / denom
    if a > 1.0 and a - 1.0 <= 1e-9:
        return 1.0
    if a < 0.0 and -a <= 1e-9:
        return 0.0
    return a


# ---------------------------------------------------------------- 模型层：探针与中介见证

def truth_probe_mi_di(model: CausalModel, T: int) -> tuple:
    """外源探针的 (I(Ĩ^T;A^T), I(Ĩ^T→A^T))（nats），(Ĩ,A)-历史树精确枚举。

    模型须经 apply_alpha（params['alpha']['n_I']≥2）。引理 2.3.1：随机化外源协议下两者相等。
    """
    al = model.alphabet
    n_I = _n_I(model)
    if n_I < 2:
        raise ValueError("模型未经 apply_alpha（params['alpha']['n_I']≥2）：无探针可测")
    stepK = _step_kernel(model)
    n_U = stepK.shape[0]
    emitB = stepK.sum(axis=2)  # (u, b)，b = i·n_A + a
    Q = _init_u(model)[:, None]
    di_total = 0.0
    mi_total = None
    for t in range(1, T + 1):
        J = np.einsum("uh,ub->bh", Q, emitB)  # p(b_t, h)
        # 轴展开：(i_t, a_t) + 历史数字 (i_{t−1},a_{t−1},…,i_1,a_1)
        Jf = J.reshape(n_I, al.n_A, *([n_I, al.n_A] * (t - 1)))
        i_axes = tuple(range(0, 2 * t, 2))
        JA = Jf.sum(axis=i_axes)                      # p(A_t, a^{t−1})
        h_a_given_aprev = entropy_nats(JA) - entropy_nats(JA.sum(axis=0))
        h_a_given_both = entropy_nats(Jf) - entropy_nats(Jf.sum(axis=1))
        di_total += h_a_given_aprev - h_a_given_both  # I(Ĩ^t;A_t|A^{t−1})
        Q = np.einsum("uh,ubv->vbh", Q, stepK).reshape(n_U, -1)
        if t == T:
            perm = list(range(0, 2 * T, 2)) + list(range(1, 2 * T, 2))
            Jt = Jf.transpose(perm).reshape(n_I ** T, al.n_A ** T)
            mi_total = mi_nats(Jt)
    return mi_total, di_total


def probe_belief_mi(model: CausalModel, T: int) -> list:
    """中介见证：逐步 I(Ĩ_t; B_t)（nats）。"""
    al = model.alphabet
    n_I = _n_I(model)
    if n_I < 2:
        raise ValueError("模型未经 apply_alpha：无探针")
    out = []
    for aux in truth_step_joints(model, T):
        so = aux["SO"].reshape(al.n_G, al.n_B, al.n_M, al.n_R, al.n_O // n_I, n_I)
        pbi = so.sum(axis=(0, 2, 3, 4))  # p(B_t, Ĩ_t)
        out.append(mi_nats(pbi))
    return out


def sigma_resource_mi(model: CausalModel, T: int) -> list:
    """中介见证：逐步 I(I^σ_t; Z_t)（nats）。"""
    n_Is = model.params.get("sigma", {}).get("n_I")
    if not n_Is:
        raise ValueError("模型未经 apply_sigma：无 σ 旗标")
    out = []
    for aux in truth_step_joints(model, T):
        pz = aux["Z"].reshape(-1, n_Is)  # p(Z_t 基值, I^σ_t)
        out.append(mi_nats(pz))
    return out

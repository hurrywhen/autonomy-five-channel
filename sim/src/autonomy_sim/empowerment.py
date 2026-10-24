"""执行分量真值：信道容量（支撑枚举＋Blahut–Arimoto）与策略类 empowerment（SPEC_estimators §3）。

E3.6 接口：信道 W 为 |𝒜|×|𝒪| 行随机矩阵（显式给定）；策略类 Π 以输入支撑限制表示
（P3.5 的确定性策略子集 ⟺ 行动子集单纯形，conv(Π)=支撑约束单纯形）。
信道容量双入口（E3.2）：blahut_arimoto（核心迭代，适面内点信道）与
channel_capacity（循环顶点方向上升＋KKT 精度证书——I(q) 凹 ⇒ 坐标级最优即全局最优，
边界最优信道亦在证书容差内闭合）。
由模型内核导出 n 步信道与 E_t[·] 期望属场景步接线（第 6/7 步）。
全部信息量以 nats 计。
"""
import math

import numpy as np


def _check_channel(W) -> np.ndarray:
    W = np.asarray(W, dtype=float)
    if W.ndim != 2 or W.shape[0] < 1 or W.shape[1] < 1:
        raise ValueError(f"W 须为二维非空矩阵: {W.shape}")
    if np.any(W < 0) or not np.all(np.isfinite(W)) or not np.allclose(W.sum(axis=1), 1.0):
        raise ValueError("W 须为行随机矩阵（非负、有限、行归一）")
    return W


def _mi_of_input(W: np.ndarray, q: np.ndarray) -> float:
    """I(q;W)（nats）：输入分布 q 经信道 W 的互信息。"""
    out = q @ W
    d = np.zeros(W.shape[0])
    for a in range(W.shape[0]):
        if q[a] == 0.0:
            continue
        row, o = W[a], out
        mask = row > 0  # q_a>0 且 row>0 ⇒ out>0，除法安全
        d[a] = float((row[mask] * np.log(row[mask] / o[mask])).sum())
    return float(q @ d)


def blahut_arimoto(W, tol: float = 1e-12, max_iter: int = 100000):
    """离散无记忆信道容量 C = max_q I(q;W)（nats）。返回 (C, q*)。

    命题 5.6(i)：C ≤ log|𝒜|；表格环境精确求值（E3.2）。
    停止准则带精度证书：C ∈ [I(q), max_a D(W_a‖out)]，gap<tol 即停
    （最优输入含零分量时 q 收敛很慢，值证书仍快速闭合）。
    """
    W = _check_channel(W)
    n_A = W.shape[0]
    q = np.full(n_A, 1.0 / n_A)
    for _ in range(max_iter):
        out = q @ W
        with np.errstate(divide="ignore", invalid="ignore"):
            ratio = np.divide(W, out, out=np.ones_like(W), where=out > 0)
            d_kl = np.where(W > 0, W * np.log(ratio), 0.0).sum(axis=1)  # D(W_a‖out)
        c_now = float(q @ d_kl)
        # BA 更新：q'_a ∝ q_a·exp(D(W_a‖out))（I(q) 单调不减）
        r = q * np.exp(d_kl - d_kl.max())
        r /= r.sum()
        q = r
        if float(d_kl.max()) - c_now < tol:
            break
    else:
        raise RuntimeError(f"Blahut–Arimoto 未在 {max_iter} 次迭代内收敛（tol={tol}）")
    return _mi_of_input(W, q), q


def _kl_rows_to_out(W: np.ndarray, out: np.ndarray) -> np.ndarray:
    """D(W_a‖out) 逐行（out 在行正质量处零测 ⇒ inf）。"""
    d = np.full(W.shape[0], np.inf)
    for a in range(W.shape[0]):
        mask = W[a] > 0
        if np.all(out[mask] > 0):
            d[a] = float((W[a][mask] * np.log(W[a][mask] / out[mask])).sum())
    return d


def _golden_max(f, tol: float = 1e-13, max_iter: int = 300):
    """[0,1] 上凹函数的黄金分割最大化，返回 (s*, f*)（含端点比较）。"""
    best_s, best_f = 0.0, f(0.0)
    if f(1.0) > best_f:
        best_s, best_f = 1.0, f(1.0)
    lo, hi = 0.0, 1.0
    gr = (math.sqrt(5.0) - 1.0) / 2.0
    c1, c2 = hi - gr * (hi - lo), lo + gr * (hi - lo)
    f1, f2 = f(c1), f(c2)
    for _ in range(max_iter):
        if hi - lo < tol:
            break
        if f1 < f2:
            lo, c1, f1 = c1, c2, f2
            c2 = lo + gr * (hi - lo)
            f2 = f(c2)
        else:
            hi, c2, f2 = c2, c1, f1
            c1 = hi - gr * (hi - lo)
            f1 = f(c1)
    s = 0.5 * (lo + hi)
    if f(s) > best_f:
        best_s, best_f = s, f(s)
    return best_s, best_f


def _capacity_two_input(W, tol: float = 1e-13):
    """2 输入信道容量：I(t)=I((t,1−t);W) 关于 t 凹 ⇒ 黄金分割精确求解。"""
    W = _check_channel(W)
    if W.shape[0] != 2:
        raise ValueError("_capacity_two_input 仅限 2 输入信道")
    t, c = _golden_max(lambda s: _mi_of_input(W, np.array([s, 1.0 - s])), tol=tol)
    return c, np.array([t, 1.0 - t])


def _ba_run(W: np.ndarray, n_iter: int, q0: np.ndarray | None = None) -> np.ndarray:
    """固定迭代次数的 BA（无证书兜底：活动集循环内面细化用；q0 暖启动）。"""
    n_A = W.shape[0]
    q = np.full(n_A, 1.0 / n_A) if q0 is None else np.asarray(q0, float) / np.sum(q0)
    for _ in range(n_iter):
        out = q @ W
        with np.errstate(divide="ignore", invalid="ignore"):
            ratio = np.divide(W, out, out=np.ones_like(W), where=out > 0)
            d_kl = np.where(W > 0, W * np.log(ratio), 0.0).sum(axis=1)
        r = q * np.exp(d_kl - d_kl.max())
        q = r / r.sum()
    return q


def channel_capacity(W, kkt_tol: float = 1e-9, max_rounds: int = 40):
    """信道容量 C = max_q I(q;W)（nats）：活动集循环＋KKT 夹逼证书。

    最优边面（黄金分割精确）热启动活动支撑；每轮在支撑面上求解（1 元平凡、2 元黄金
    分割、≥3 元 BA——真支撑上面内点几何收敛；慢速面登记后转暖启动细化），近零分量
    塌缩剔除；随后在全信道上核验 KKT 证书 gap = max_a D(W_a‖out) − I(q)：≤ kkt_tol
    即返回（真值被 [c, c+gap] 夹逼）；违反来自面外 ⇒ 激活该行；来自面内 ⇒ 面解未精，
    暖启动继续细化。边界最优由塌缩步处理，不做单纯形上的慢速爬升（近退化信道在一阶
    方法下的病态见 T-COV δ 行实测）。轮次耗尽时返回历史最优夹逼（gap ≤ 1e-6），
    再超则报错。
    """
    W = _check_channel(W)
    n_A = W.shape[0]
    if n_A == 1:
        return 0.0, np.array([1.0])
    if n_A == 2:
        return _capacity_two_input(W)
    # 最优边面热启动（顶点 I=0 平凡）
    best_c0, best_pair = -1.0, (0, 1)
    for i in range(n_A):
        for j in range(i + 1, n_A):
            c_ij, _ = _capacity_two_input(W[[i, j], :])
            if c_ij > best_c0:
                best_c0, best_pair = c_ij, (i, j)
    active = sorted(best_pair)
    q_face = None
    slow_faces = set()
    best = None  # (gap, c, q) 历史最优夹逼
    for _ in range(max_rounds):
        sub = W[active, :]
        key = tuple(active)
        if len(active) == 1:
            q_face = np.array([1.0])
        elif len(active) == 2 and q_face is None:
            _, q_face = _capacity_two_input(sub)
        elif key not in slow_faces:
            try:
                _, q_face = blahut_arimoto(sub, tol=1e-12, max_iter=20000)
            except RuntimeError:
                slow_faces.add(key)  # 真支撑面内点几何收敛远在此限内；超限即病态面
                q_face = _ba_run(sub, 5000, q0=q_face)
        else:
            q_face = _ba_run(sub, 5000, q0=q_face)
        q = np.zeros(n_A)
        q[active] = q_face
        # 塌缩：剔除面解的近零分量（面选大了），下轮重解
        tiny = {a for a in active if q[a] < 1e-9}
        if tiny and len(active) - len(tiny) >= 2:
            active = [a for a in active if a not in tiny]
            q_face = None
            continue
        d_all = _kl_rows_to_out(W, q @ W)
        c_val = _mi_of_input(W, q)
        gap = float(d_all.max() - c_val)
        if best is None or gap < best[0]:
            best = (gap, c_val, q.copy())
        if gap <= kkt_tol:
            return c_val, q
        worst = int(np.argmax(d_all))
        if worst in active:
            slow_faces.add(key)  # 面解未精：下轮暖启动继续细化
            continue
        active = sorted(active + [worst])
        q_face = None
    if best is not None and best[0] <= 1e-6:
        return best[1], best[2]
    raise RuntimeError(f"channel_capacity：活动集 {max_rounds} 轮未收敛（tol={kkt_tol}）")


def empowerment_support(W, support) -> float:
    """ℰ^Π：Π = 支撑限于 support 的策略类（conv(Π)=支撑单纯形）⇒ 子信道容量（nats）。

    无助签名（E3.3）：|support|=1（行为库坍缩为常量策略）⇒ ℰ^Π=0 精确；
    ℰ^env = empowerment_support(W, 全行动集) 与 Π 无关。
    """
    W = _check_channel(W)
    support = tuple(sorted({int(a) for a in support}))
    if not support:
        raise ValueError("support 不能为空")
    if support[-1] >= W.shape[0]:
        raise ValueError(f"support 越界: {support}（|𝒜|={W.shape[0]}）")
    if len(support) == 1:
        return 0.0  # 单一可行行动 ⇒ I(A;O)=0 恒成立（赋能坍缩，命题 5.6(ii)）
    c, _ = channel_capacity(W[list(support), :])
    return c


def a_exec(emp_nats: float, n: int, n_A: int) -> float:
    """A_exec = ℰ^Π/(n·log|𝒜|)（附录 §5.4 规范化；同底对数，AX6a）。"""
    if n < 1 or n_A < 2:
        raise ValueError(f"n≥1 且 |𝒜|≥2: n={n}, |𝒜|={n_A}")
    return float(emp_nats) / (n * math.log(n_A))


def step_channels_from_esz(model, esz):
    """单步信道导出（SPEC_estimators E3.7）：由 (E,S,Z) 决策时联合构造逐状态信道。

    W_s[a,o'] = Σ_{e,z} p(e,z|s)·M[e,a,z,o']，M[e,a,z,o']=Σ_{e'} env[e,a,z,e']·obs[e',a,o']
    （行动经环境转移与观察双亲通道影响下一步观察；esz 为 propagate 的 "ESZ" 键——
    S 更新后的决策时联合 p(E_t,S_t,Z_t)）。返回 (channels, mask)：
    mask[s]=False 表示 p(s)=0（后验无定义，调用方按基线 S_t 边缘加权时剔除）。
    """
    al, k = model.alphabet, model.kernels
    esz = np.asarray(esz, dtype=float)
    if esz.shape != (al.n_E, al.n_S, al.n_Z):
        raise ValueError(f"ESZ 形状 {esz.shape} != ({al.n_E},{al.n_S},{al.n_Z})")
    m_eazo = np.einsum("eazf,fao->eazo", k.env, k.obs)
    channels, mask = [], []
    for s in range(al.n_S):
        jez = esz[:, s, :]
        tot = float(jez.sum())
        if tot <= 0.0:
            channels.append(None)
            mask.append(False)
            continue
        channels.append(np.einsum("ez,eazo->ao", jez / tot, m_eazo))
        mask.append(True)
    return channels, mask

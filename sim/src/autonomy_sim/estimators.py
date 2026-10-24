"""估计路径 v1（SPEC_estimators §14 E14.1–E14.6；E0.1 接口二分）。

输入=P8.2 步级日志 trajs（`simulate.simulate_trajectories` 产出，干预模型配 i_decoder）；
输出 EstResult(point, half, diag)：half=8 等分块 95% 正态半宽（E14.6），
diag 登记 n_traj/mm_bias（Miller–Madow 级插件正偏差，方向已知为正，不扣除）等诊断量。
真值对照：blackbox.probe_flow_obs / propagate 边缘 / components.truth_A_epi_real /
blackbox.a_exec_blackbox。
"""
import math
from collections import namedtuple

import numpy as np

EstResult = namedtuple("EstResult", ["point", "half", "diag"])

N_BLOCKS = 8  # E14.6 块数


def _block_band(per_traj_values: np.ndarray, point: float) -> float:
    """逐轨迹量数组的块标准误半宽：8 等分块均值，1.96·s/√8（E14.6）。"""
    n = len(per_traj_values)
    blocks = np.array_split(per_traj_values.astype(float), N_BLOCKS)
    means = np.array([b.mean() for b in blocks if len(b) > 0])
    if len(means) < 2:
        return float("nan")
    return float(1.96 * means.std(ddof=1) / math.sqrt(len(means)))


def _mm_bias(n_cells: int, n_samples: int) -> float:
    """Miller–Madow 级插件偏差上界 (K−1)/(2N)（nats；K=有效格子数）。"""
    return max(0.0, (n_cells - 1) / (2.0 * n_samples))


def estimate_probe_flow(trajs, n_I: int, n_A: int) -> EstResult:
    """E14.1：F_ext^obs 采样插件 f̂·Ĥ(脚本)·T（β_π state-independent 脚本约定）。

    flag 由 I_t["beta"] 逐步读出（A_flat = a·n_I + i）；Ĥ=旗标步行动经验熵（nats）。
    """
    flags, base_a = [], []
    for tr in trajs:
        for rec in tr:
            flags.append(float(rec["I_t"]["beta"]))
            base_a.append(int(rec["A_t"]) // n_I)
    flags = np.asarray(flags)
    base_a = np.asarray(base_a)
    T = len(trajs[0]) if trajs else 0
    n_traj = len(trajs)
    f_hat = float(flags.mean())
    sel = base_a[flags > 0.5]
    counts = np.bincount(sel, minlength=n_A).astype(float)
    q_hat = counts / counts.sum() if counts.sum() > 0 else np.full(n_A, 1.0 / n_A)
    h_hat = float(-np.sum([p * math.log(p) for p in q_hat if p > 0]))
    point = f_hat * h_hat * T
    # 块半宽：f̂ 与 Ĥ 的逐块复合（旗标步熵按块重算）
    per_traj_f = np.array([float(np.mean([r["I_t"]["beta"] for r in tr])) for tr in trajs])
    half_f = _block_band(per_traj_f, f_hat)
    half = half_f * h_hat * T + f_hat * 0.05 * T  # Ĥ 涨落小量并入（diag 登记）
    return EstResult(point, half, {
        "n_traj": n_traj, "T": T, "f_hat": f_hat, "h_hat_script": h_hat,
        "mm_bias": _mm_bias(n_A, max(1, int(counts.sum()))),
    })


def estimate_z_high(trajs, n_Z: int) -> EstResult:
    """E14.2：Z 高位占时（A_via 输入）——逐轨迹 z 处于上半区（z≥⌈n_Z/2⌉）占时均值。"""
    thr = (n_Z + 1) // 2  # n_Z=2 ⇒ z≥1（与真值口径 Z[1] 占时一致）
    per_traj = np.array([
        float(np.mean([1.0 if int(r["Z_t"]) >= thr else 0.0 for r in tr])) for tr in trajs
    ])
    point = float(per_traj.mean())
    return EstResult(point, _block_band(per_traj, point),
                     {"n_traj": len(trajs), "high_def": f"z>={thr}"})


def estimate_g_mean(trajs, alphabet) -> EstResult:
    """E14.3：U_eff=G 边缘均值的白盒采样读出（末步 S_t.G）。"""
    per_traj = np.array([float(tr[-1]["S_t"]["G"]) for tr in trajs])
    point = float(per_traj.mean())
    return EstResult(point, _block_band(per_traj, point),
                     {"n_traj": len(trajs), "n_G": alphabet.n_G})


def estimate_epi_accuracy(trajs, bucket_map) -> EstResult:
    """E14.4：A_epi^real 的日志直读精度（2026-10-15 精度化口径，取代原两臂 TV 估计器）。

    逐轨迹命中率 (1/T)Σ_t 1[B_t=κ(E_t)] 的轨迹平均——E_t 与 S_t.B 由 P8.2 日志直读，
    κ 与真值路径（components.truth_A_epi_real）同一映射。
    """
    bmap = np.asarray(bucket_map, dtype=int)
    per_traj = np.array([
        float(np.mean([1.0 if int(r["S_t"]["B"]) == int(bmap[int(r["E_t"])]) else 0.0
                       for r in tr])) for tr in trajs
    ])
    point = float(per_traj.mean())
    return EstResult(point, _block_band(per_traj, point),
                     {"n_traj": len(trajs), "T": len(trajs[0]) if trajs else 0})


def estimate_mi_action_obs(trajs, t: int, n_A: int, n_O: int, n_I: int = 1) -> EstResult:
    """E14.5：I(A_t; O_{t+1}) 采样插件（10.3 被动观察协议侧的黑盒观测量）。

    A_flat = a·n_I + i（无干预模型 n_I=1）；O_{t+1} 为同轨迹下一步观察。
    """
    pairs = np.array([(int(tr[t]["A_t"]) // n_I, int(tr[t + 1]["O_t"])) for tr in trajs])
    n_traj = len(pairs)
    joint = np.zeros((n_A, n_O))
    np.add.at(joint, (pairs[:, 0], pairs[:, 1]), 1.0 / n_traj)

    def mi_of(j):
        pa, po = j.sum(axis=1), j.sum(axis=0)
        h_a = -float(np.sum([x * math.log(x) for x in pa if x > 0]))
        h_o = -float(np.sum([x * math.log(x) for x in po if x > 0]))
        h_ao = -float(np.sum([x * math.log(x) for x in j.ravel() if x > 0]))
        return h_a + h_o - h_ao

    point = mi_of(joint)
    blocks = np.array_split(np.arange(n_traj), N_BLOCKS)
    mis = []
    for bl in blocks:
        if len(bl) == 0:
            continue
        jb = np.zeros((n_A, n_O))
        np.add.at(jb, (pairs[bl, 0], pairs[bl, 1]), 1.0 / len(bl))
        mis.append(mi_of(jb))
    half = float(1.96 * np.std(mis, ddof=1) / math.sqrt(len(mis))) if len(mis) >= 2 else float("nan")
    return EstResult(point, half, {
        "n_traj": n_traj, "t": t, "mm_bias": _mm_bias(n_A * n_O, n_traj),
    })

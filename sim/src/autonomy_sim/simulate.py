"""采样模式：P1.2 因子化逐步采样（SPEC_platform P1.4 sample 模式）。

向量化内核同时驱动：
- simulate_trajectories：产出步级记录（供日志/T-SEED）；
- sample_marginal_counts：累计 (E,O,A) 边缘计数（供 T-MODE 对照真值）。
两者共用同一采样内核，保证模式一致性。
"""
import numpy as np

from .graph import CausalModel
from .rng import make_rng

_ZERO_I = {"sigma": 0.0, "alpha": 0.0, "beta": 0.0, "gamma": 0.0, "delta": 0.0}


def _cat_sample(probs2d: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """按行从类别分布采样（向量化）。"""
    cum = probs2d.cumsum(axis=1)
    u = rng.random(probs2d.shape[0])
    return (cum < u[:, None]).sum(axis=1)


def _draw_steps(model: CausalModel, seed: int, T: int, n_traj: int):
    """P1.2 因子化的向量化采样内核。逐步 yield (E, O, g, b, m, r, A, Z) 数组元组。"""
    al, k = model.alphabet, model.kernels
    rng = make_rng(seed)

    def uni(row):
        return np.broadcast_to(row, (n_traj, len(row)))

    E = _cat_sample(uni(k.init_E), rng)
    S = _cat_sample(uni(k.init_S), rng)
    Z = _cat_sample(uni(k.init_Z), rng)
    Ap = _cat_sample(uni(k.init_A), rng)

    for _ in range(T):
        O = _cat_sample(k.obs[E, Ap], rng)
        g, b, m, r = _split_S(al, S)
        Bp = _cat_sample(k.belief[b, O], rng)
        gmr = (g * al.n_M + m) * al.n_R + r
        gmr2 = _cat_sample(k.internal[gmr], rng)
        g2 = gmr2 // (al.n_M * al.n_R)
        m2 = (gmr2 // al.n_R) % al.n_M
        r2 = gmr2 % al.n_R
        S2 = ((g2 * al.n_B + Bp) * al.n_M + m2) * al.n_R + r2
        A = _cat_sample(k.policy[S2], rng)
        yield E, O, g2, Bp, m2, r2, A, Z
        Z2 = _cat_sample(k.resource[Z], rng)
        E2 = _cat_sample(k.env[E, A, Z], rng)
        E, S, Z, Ap = E2, S2, Z2, A


def _split_S(al, S):
    g = S // (al.n_B * al.n_M * al.n_R)
    b = (S // (al.n_M * al.n_R)) % al.n_B
    m = (S // al.n_R) % al.n_M
    r = S % al.n_R
    return g, b, m, r


def simulate_trajectories(model: CausalModel, seed: int, T: int, n_traj: int = 1,
                          i_decoder=None):
    """采样 n_traj 条轨迹，返回 [[record, ...], ...]（P8.2 步级记录）。

    i_decoder：可选回调 fn(step_syms, model) -> dict[str, np.ndarray]，
    把干预模型的 I_t 五字段按步填入（如 interventions.make_i_decoder）；
    None 时 I_t 全零（无干预模型）。
    """
    trajs = [[] for _ in range(n_traj)]
    for t, (E, O, g, b, m, r, A, Z) in enumerate(_draw_steps(model, seed, T, n_traj)):
        if i_decoder is None:
            i_fields = None
        else:
            i_fields = i_decoder({"E": E, "O": O, "g": g, "b": b, "m": m, "r": r,
                                  "A": A, "Z": Z}, model)
        for i in range(n_traj):
            rec = {
                "t": t,
                "E_t": int(E[i]), "O_t": int(O[i]),
                "S_t": {"G": int(g[i]), "B": int(b[i]), "M": int(m[i]), "R": int(r[i])},
                "A_t": int(A[i]), "Z_t": int(Z[i]),
                "I_t": dict(_ZERO_I) if i_fields is None
                       else {k: float(v[i]) for k, v in i_fields.items()},
                "defense_events": [],
                "damage_D": {},
            }
            trajs[i].append(rec)
    return trajs


def sample_symbol_sequences(model: CausalModel, seed: int, T: int, n_traj: int) -> dict:
    """序列级采样接口（估计层用）：{'E','O','S','A','Z'} 各 shape (n_traj, T) 的 int 数组。"""
    al = model.alphabet
    out = {k: np.empty((n_traj, T), dtype=np.int64) for k in ("E", "O", "S", "A", "Z")}
    for t, (E, O, g, b, m, r, A, Z) in enumerate(_draw_steps(model, seed, T, n_traj)):
        out["E"][:, t] = E
        out["O"][:, t] = O
        out["S"][:, t] = ((g * al.n_B + b) * al.n_M + m) * al.n_R + r
        out["A"][:, t] = A
        out["Z"][:, t] = Z
    return out


def sample_marginal_counts(model: CausalModel, seed: int, T: int, n_traj: int) -> np.ndarray:
    """(E,O,A) 边缘计数，shape (T, n_E, n_O, n_A)（T-MODE 用）。"""
    al = model.alphabet
    counts = np.zeros((T, al.n_E, al.n_O, al.n_A))
    for t, (E, O, _g, _b, _m, _r, A, _Z) in enumerate(_draw_steps(model, seed, T, n_traj)):
        np.add.at(counts[t].reshape(-1), (E * al.n_O + O) * al.n_A + A, 1)
    return counts

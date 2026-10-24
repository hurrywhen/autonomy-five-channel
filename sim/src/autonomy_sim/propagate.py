"""真值模式：联合分布精确前向传播（SPEC_platform P1.4 truth 模式）。

按 P1.2 因子化对联合分布 p[E_t, S_t, Z_t, A_{t-1}] 做精确推进：
- truth_marginals：逐步 (E_t, O_t, A_t) 精确边缘（T-MODE 与场景用）；
- truth_step_joints：逐步精确联合/边缘字典（DI 真值模块的中介见证与条件熵用）。
"""
import numpy as np

from .graph import CausalModel


def _forward(model: CausalModel, T: int):
    """逐步推进，yield ((E,O,A) 边缘, 辅助边缘字典)。"""
    al, k = model.alphabet, model.kernels
    # 联合分布 p[E, S, Z, A_prev]
    p = np.einsum("e,s,z,a->esza", k.init_E, k.init_S, k.init_Z, k.init_A)
    for _ in range(T):
        # 1. O_t ~ obs[E, A_prev]
        jo = np.einsum("esza,eao->eszao", p, k.obs)
        # 2. B_t ~ belief[B, O_t]（S_flat 拆为 (G,B,M,R)）
        jr = jo.reshape(al.n_E, al.n_G, al.n_B, al.n_M, al.n_R, al.n_Z, al.n_A, al.n_O)
        jb = np.einsum("egbmrzao,boq->egqmrzao", jr, k.belief)
        # 3. (G,M,R) 内部更新（GMR 组重排为连续轴）
        jt = jb.transpose(0, 1, 3, 4, 2, 5, 6, 7)  # (E,G,M,R,B',Z,Aprev,O)
        jw = jt.reshape(al.n_E, al.n_GMR, al.n_B, al.n_Z, al.n_A, al.n_O)
        jn = np.einsum("ewbzao,wh->ehbzao", jw, k.internal)
        # 4. A_t ~ policy[S']；S' 由 (G,M,R)' 与新 B' 重组
        jn4 = jn.reshape(al.n_E, al.n_G, al.n_M, al.n_R, al.n_B, al.n_Z, al.n_A, al.n_O)
        js = jn4.transpose(0, 1, 4, 2, 3, 5, 6, 7).reshape(
            al.n_E, al.n_S, al.n_Z, al.n_A, al.n_O)
        ja = np.einsum("euzco,ua->euzcoa", js, k.policy)
        # 本步 (E,O,A) 精确边缘
        marg = ja.sum(axis=(1, 2, 3))
        aux = {
            "S": js.sum(axis=(0, 2, 3, 4)),      # p(S'_t)
            "SO": js.sum(axis=(0, 2, 3)),        # p(S'_t, O_t) 联合
            "Z": js.sum(axis=(0, 1, 3, 4)),      # p(Z_t)
            "ESZ": js.sum(axis=(3, 4)),          # p(E_t, S_t, Z_t) 决策时联合（S 更新后；信道导出用）
        }
        yield marg, aux
        # 5. Z/E 推进到下一步：p'[E', S', Z', A_t]
        p = np.einsum("euzcoa,zZ,eazf->fuZa", ja, k.resource, k.env)


def truth_marginals(model: CausalModel, T: int) -> list:
    """返回长度为 T 的列表，第 t 项为 (E_t, O_t, A_t) 的精确边缘张量 (n_E, n_O, n_A)。"""
    return [marg for marg, _ in _forward(model, T)]


def truth_step_joints(model: CausalModel, T: int) -> list:
    """逐步精确联合/边缘字典列表，键：'S' (n_S,)、'SO' (n_S,n_O)、'Z' (n_Z,)、'ESZ' (n_E,n_S,n_Z)。"""
    return [aux for _, aux in _forward(model, T)]

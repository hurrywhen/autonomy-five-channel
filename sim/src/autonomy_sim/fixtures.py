"""L0 测试用玩具模型（小规模确定性构造）。

不是 R3-ENV-0（SPEC_platform §2）——ENV-0 随场景需求在后续推进线建立。
本 fixture 只要求：字母表小、张量归一、动力学非退化（供 T-SEED/T-MODE 等 L0 测试）。
"""
import numpy as np

from .graph import Alphabet, CausalModel, Kernels
from .rng import make_rng


def toy_model() -> CausalModel:
    al = Alphabet(n_E=4, n_O=4, n_A=3, n_G=2, n_B=3, n_M=2, n_R=2, n_Z=2)
    rng = make_rng(4242)

    # obs[e,a,o]：以 0.7 概率忠实报告 e（噪声通道），与 a 无关
    obs = np.full((al.n_E, al.n_A, al.n_O), 0.3 / al.n_O)
    for e in range(al.n_E):
        obs[e, :, e % al.n_O] += 0.7

    # belief[b,o,q]：倾向吸收观察（q=o%n_B 加权 0.6），保留惯性 0.3
    belief = np.full((al.n_B, al.n_O, al.n_B), 0.1 / al.n_B)
    for b in range(al.n_B):
        for o in range(al.n_O):
            belief[b, o, o % al.n_B] += 0.6
            belief[b, o, b] += 0.3

    # internal：近恒等＋小扰动
    internal = np.full((al.n_GMR, al.n_GMR), 0.2 / al.n_GMR)
    internal += 0.8 * np.eye(al.n_GMR)

    # policy：确定性构造的 softmax 策略
    scores = rng.random((al.n_S, al.n_A)) * 2.0
    scores -= scores.max(axis=1, keepdims=True)
    policy = np.exp(scores)
    policy /= policy.sum(axis=1, keepdims=True)

    # env[e,a,z,e']：e' 受行动与资源驱动的环面游走
    env = np.full((al.n_E, al.n_A, al.n_Z, al.n_E), 0.25 / al.n_E)
    for e in range(al.n_E):
        for a in range(al.n_A):
            for z in range(al.n_Z):
                e_next = (e + (a - 1) + z) % al.n_E
                env[e, a, z, e_next] += 0.75

    # resource：近恒等二元链
    resource = np.array([[0.8, 0.2], [0.3, 0.7]])

    def _rand_dist(n):
        v = rng.random(n) + 0.05
        return v / v.sum()

    kernels = Kernels(
        obs=obs, belief=belief, internal=internal, policy=policy,
        env=env, resource=resource,
        init_E=_rand_dist(al.n_E), init_S=_rand_dist(al.n_S),
        init_Z=_rand_dist(al.n_Z), init_A=_rand_dist(al.n_A),
    )
    model = CausalModel(alphabet=al, kernels=kernels,
                        params={"fixture": "toy_model", "version": 1})
    model.validate()
    return model


def toy_model_uniform_policy() -> CausalModel:
    """零点语义见证变体：π 不依赖 S（全均匀——遥控/覆写）⇒ F_int=0（T-ORG 用）。"""
    model = toy_model()
    al = model.alphabet
    model.kernels.policy = np.full((al.n_S, al.n_A), 1.0 / al.n_A)
    model.params = {**model.params, "fixture": "toy_model_uniform_policy"}
    model.validate()
    return model


def random_model(rng, n_E: int = 3, n_O: int = 3, n_A: int = 3,
                 n_G: int = 2, n_B: int = 2, n_M: int = 2, n_R: int = 1, n_Z: int = 2) -> CausalModel:
    """随机 CausalModel（T-T1a 随机配置扫描用）：全部核随机归一＋0.05 全支撑地板。

    随机性只经注入的 rng（P6.1 协议）；小字母表保证真值路径廉价。
    """
    al = Alphabet(n_E=n_E, n_O=n_O, n_A=n_A, n_G=n_G, n_B=n_B, n_M=n_M, n_R=n_R, n_Z=n_Z)

    def rnd(*shape):
        v = rng.random(shape) + 0.05
        return v / v.sum(axis=-1, keepdims=True)

    kernels = Kernels(
        obs=rnd(al.n_E, al.n_A, al.n_O), belief=rnd(al.n_B, al.n_O, al.n_B),
        internal=rnd(al.n_GMR, al.n_GMR), policy=rnd(al.n_S, al.n_A),
        env=rnd(al.n_E, al.n_A, al.n_Z, al.n_E), resource=rnd(al.n_Z, al.n_Z),
        init_E=rnd(al.n_E), init_S=rnd(al.n_S), init_Z=rnd(al.n_Z), init_A=rnd(al.n_A),
    )
    model = CausalModel(alphabet=al, kernels=kernels, params={"fixture": "random_model"})
    model.validate()
    return model


def toy_model_exec_deterministic() -> CausalModel:
    """T-COV δ 行见证构造（SPEC_estimators E3.7）：确定性环境/观察＋信念直接吸收。

    E_{t+1}=(E_t+A_t−1) mod 4 确定性移位；obs 忠实（O_t=E_t）；B_t=O_t（直接吸收）
    ⇒ 后验 p(e|s)=δ_s，逐状态单步信道为 one-hot 移位族，容量解析锚：
    ℰ(全行动)=log3、ℰ(删一行动)=log2、ℰ(单行动)=0（Faith 严格降精确成立）。
    """
    al = Alphabet(n_E=4, n_O=4, n_A=3, n_G=1, n_B=4, n_M=1, n_R=1, n_Z=1)
    obs = np.zeros((al.n_E, al.n_A, al.n_O))
    for e in range(al.n_E):
        obs[e, :, e] = 1.0  # 忠实、与 a 无关
    belief = np.zeros((al.n_B, al.n_O, al.n_B))
    for b in range(al.n_B):
        for o in range(al.n_O):
            belief[b, o, o] = 1.0  # B_t = O_t（直接吸收）
    internal = np.ones((al.n_GMR, al.n_GMR))  # (1,1) 恒等
    policy = np.full((al.n_S, al.n_A), 1.0 / al.n_A)
    env = np.zeros((al.n_E, al.n_A, al.n_Z, al.n_E))
    for e in range(al.n_E):
        for a in range(al.n_A):
            env[e, a, 0, (e + a - 1) % al.n_E] = 1.0  # 确定性移位
    resource = np.ones((al.n_Z, al.n_Z))
    kernels = Kernels(
        obs=obs, belief=belief, internal=internal, policy=policy,
        env=env, resource=resource,
        init_E=np.full(al.n_E, 0.25), init_S=np.full(al.n_S, 1.0 / al.n_S),
        init_Z=np.array([1.0]), init_A=np.full(al.n_A, 1.0 / al.n_A),
    )
    model = CausalModel(alphabet=al, kernels=kernels,
                        params={"fixture": "toy_model_exec_deterministic", "version": 1})
    model.validate()
    return model


def toy_model_epi_deterministic() -> CausalModel:
    """T-EPI 见证构造（SPEC_estimators E5.4）：确定性环境/观察/信念吸收——B_t=O_t 精确成立。

    E_t≡0（点质量初始＋恒等环境）；obs 忠实（O_t=E_t，与 A 无关）；belief 直接吸收
    （B_t=O_t）。γ_s 混合常值符号 ⇒ B_t^{(γ)}=(1−s)δ_0+sδ_1，TV(B^{(γ)},B^{(0)})=s 解析成立；
    s=1 ⇒ 两臂信念支撑不交（TV=1 ⇒ A_epi^real=0 的见证）。
    """
    al = Alphabet(n_E=2, n_O=2, n_A=2, n_G=1, n_B=2, n_M=1, n_R=1, n_Z=1)
    obs = np.zeros((al.n_E, al.n_A, al.n_O))
    for e in range(al.n_E):
        obs[e, :, e] = 1.0  # 忠实、与 a 无关
    belief = np.zeros((al.n_B, al.n_O, al.n_B))
    for b in range(al.n_B):
        for o in range(al.n_O):
            belief[b, o, o] = 1.0  # B_t = O_t（直接吸收）
    internal = np.ones((al.n_GMR, al.n_GMR))  # (1,1) 恒等
    policy = np.full((al.n_S, al.n_A), 1.0 / al.n_A)  # n_S=2（S≡B）
    env = np.zeros((al.n_E, al.n_A, al.n_Z, al.n_E))
    for e in range(al.n_E):
        env[e, :, :, e] = 1.0  # 恒等环境
    resource = np.ones((al.n_Z, al.n_Z))
    kernels = Kernels(
        obs=obs, belief=belief, internal=internal, policy=policy,
        env=env, resource=resource,
        init_E=np.array([1.0, 0.0]), init_S=np.array([0.5, 0.5]),
        init_Z=np.array([1.0]), init_A=np.array([0.5, 0.5]),
    )
    model = CausalModel(alphabet=al, kernels=kernels,
                        params={"fixture": "toy_model_epi_deterministic", "version": 1})
    model.validate()
    return model

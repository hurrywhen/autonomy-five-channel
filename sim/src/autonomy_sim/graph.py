"""时展因果图内核（SPEC_platform P1.1/P1.2）。

字母表（P1.1）：E 环境、O 观察、A 行动、S=(G,B,M,R) 内部状态、Z 资源流，全离散有限。
扁平化约定：S_flat = ((G*n_B + B)*n_M + M)*n_R + R；GMR_flat = (G*n_M + M)*n_R + R。

每步因子化（P1.2，E5 架构——观察经信念吸收）：
  1. O_t  ~ obs[E_t, A_{t-1}, ·]                     （γ 作用点）
  2. B_t  ~ belief[B_{t-1}, O_t, ·]                  （观察经信念更新吸收）
  3. (G,M,R)_t ~ internal[(G,M,R)_{t-1}, ·]          （内部更新律；β 作用点）
  4. A_t  ~ policy[S_t, ·]                           （β_π/δ 作用点）
  5. Z_t  ~ resource[Z_{t-1}, ·]；E_{t+1} ~ env[E_t, A_t, Z_t, ·]  （σ± 作用点）
"""
from dataclasses import dataclass
import hashlib
import json

import numpy as np


@dataclass(frozen=True)
class Alphabet:
    n_E: int
    n_O: int
    n_A: int
    n_G: int
    n_B: int
    n_M: int
    n_R: int
    n_Z: int = 1

    @property
    def n_S(self) -> int:
        return self.n_G * self.n_B * self.n_M * self.n_R

    @property
    def n_GMR(self) -> int:
        return self.n_G * self.n_M * self.n_R

    def split_S(self, s: int):
        """S_flat -> (G, B, M, R)。"""
        g, rem = divmod(s, self.n_B * self.n_M * self.n_R)
        b, rem = divmod(rem, self.n_M * self.n_R)
        m, r = divmod(rem, self.n_R)
        return g, b, m, r

    def join_S(self, g: int, b: int, m: int, r: int) -> int:
        return ((g * self.n_B + b) * self.n_M + m) * self.n_R + r


@dataclass
class Kernels:
    """转移张量集合（行末轴为条件分布轴）。"""

    obs: np.ndarray       # P(O_t|E_t,A_{t-1})        (n_E, n_A, n_O)
    belief: np.ndarray    # P(B_t|B_{t-1},O_t)        (n_B, n_O, n_B)
    internal: np.ndarray  # P(GMR_t|GMR_{t-1})        (n_GMR, n_GMR)
    policy: np.ndarray    # P(A_t|S_t)                (n_S, n_A)
    env: np.ndarray       # P(E_{t+1}|E_t,A_t,Z_t)    (n_E, n_A, n_Z, n_E)
    resource: np.ndarray  # P(Z_t|Z_{t-1})            (n_Z, n_Z)
    init_E: np.ndarray    # (n_E,)
    init_S: np.ndarray    # (n_S,)
    init_Z: np.ndarray    # (n_Z,)
    init_A: np.ndarray    # A_{-1} 的初始分布 (n_A,)


@dataclass
class CausalModel:
    """P1.1/P1.2 模型内核：字母表＋转移张量＋参数描述。"""

    alphabet: Alphabet
    kernels: Kernels
    params: dict  # 配置参数（P2.3 登记对象；入 config_hash）

    def validate(self, tol: float = 1e-9) -> None:
        """T-TENSOR：形状精确、元素有限非负、末轴归一、字母表闭合。"""
        al = self.alphabet
        k = self.kernels
        expect = {
            "obs": (al.n_E, al.n_A, al.n_O),
            "belief": (al.n_B, al.n_O, al.n_B),
            "internal": (al.n_GMR, al.n_GMR),
            "policy": (al.n_S, al.n_A),
            "env": (al.n_E, al.n_A, al.n_Z, al.n_E),
            "resource": (al.n_Z, al.n_Z),
            "init_E": (al.n_E,),
            "init_S": (al.n_S,),
            "init_Z": (al.n_Z,),
            "init_A": (al.n_A,),
        }
        for name, shape in expect.items():
            arr = getattr(k, name)
            assert isinstance(arr, np.ndarray) and arr.shape == shape, (
                f"{name} 形状错误: {getattr(arr, 'shape', None)} != {shape}"
            )
            assert np.all(np.isfinite(arr)) and np.all(arr >= 0), f"{name} 含非法元素"
            assert np.allclose(arr.sum(axis=-1), 1.0, atol=tol), f"{name} 末轴不归一"

    def to_dict(self) -> dict:
        """config_hash 的规范化输入（P2.3/P8.1）。"""
        al = self.alphabet
        k = self.kernels
        return {
            "alphabet": {f: getattr(al, f) for f in ("n_E", "n_O", "n_A", "n_G", "n_B", "n_M", "n_R", "n_Z")},
            "params": self.params,
            "kernel_hashes": {
                name: _arr_hash(getattr(k, name))
                for name in ("obs", "belief", "internal", "policy", "env", "resource",
                             "init_E", "init_S", "init_Z", "init_A")
            },
        }


def _arr_hash(arr: np.ndarray) -> str:
    return hashlib.sha1(np.ascontiguousarray(arr).tobytes()).hexdigest()[:12]


def _json_fallback(obj):
    """M9.4：params 中非 JSON 类型（ndarray 脚本张量等）的内容哈希兜底。"""
    if isinstance(obj, np.ndarray):
        return _arr_hash(obj)
    return str(obj)


def model_content_hash(model: "CausalModel") -> str:
    """规范化内容哈希（params＋内核；非 JSON 类型兜底）——内容寻址缓存键（M9.4）。

    与 logschema.config_hash 同式（那边取 12 字符前缀入 P8.1 metadata），此处全 hex。
    """
    return hashlib.sha1(
        json.dumps(model.to_dict(), sort_keys=True, default=_json_fallback).encode()
    ).hexdigest()


def kernel_fingerprint(model: "CausalModel") -> tuple:
    """内核内容指纹（di 步核缓存键；含字母表与全部转移张量哈希）。"""
    al, k = model.alphabet, model.kernels
    return (
        tuple(getattr(al, f) for f in ("n_E", "n_O", "n_A", "n_G", "n_B", "n_M", "n_R", "n_Z")),
        tuple((name, _arr_hash(getattr(k, name)))
              for name in ("obs", "belief", "internal", "policy", "env", "resource",
                           "init_E", "init_S", "init_Z", "init_A")),
    )

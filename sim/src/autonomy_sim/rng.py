"""随机性协议（SPEC_platform §6）。

唯一合法随机源：numpy.random.Generator(PCG64)（P6.1）。
种子派生（P6.2）：seed = 30000 + scenario_code*1000 + config_code*97 + rep，rep∈[0,30)；
矩阵外实验用独立段（≥900000）。
"""
import numpy as np

BASE_SEED = 30000
OUT_OF_MATRIX_BASE = 900000
REPS = 30


def derive_seed(scenario_code: int, config_code: int, rep: int) -> int:
    """P6.2 派生规则。scenario_code/config_code 分配见 SPEC_experiments 注册表。"""
    if not (0 <= rep < REPS):
        raise ValueError(f"rep 越界 [0,{REPS}): {rep}")
    if scenario_code < 0 or config_code < 0:
        raise ValueError("scenario_code/config_code 须非负")
    return BASE_SEED + scenario_code * 1000 + config_code * 97 + rep


def make_rng(seed: int) -> np.random.Generator:
    """P6.1 唯一 RNG 构造入口。"""
    return np.random.Generator(np.random.PCG64(seed))

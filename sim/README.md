# R3 仿真与实验 · 总规约

**版本**: v0.1（规约先行版，2026-10-04）
**定位**: 路线图 R3 阶段工作区。产出目标（input §9）：实验报告＋`autonomy-bench`。本目录任何实现代码之前，必须先有对应 SPEC 条目并通过评审；实现严格遵循 TDD（SPEC_tests.md）。

## 权威依据

- **理论与场景**: `input/framework_v2_en.md`（v2.2 英文权威版；中文版 `input/智能体自主性统一理论框架_v2.md` 为译文版）§3 形式化体系、§5 测量与估计规范、§6 仿真与实验规范。
- **证明与交接**: `docs/math_appendix_v1_en.md`（英文权威版）§3（图与手术）、§5（分量良构性）、§7（定理）、§8（C0–C2 命题）、§9（copula）、§10（可辨识性）；**§13.3 R3 交接注记为本阶段直接输入**。
- **全因果日志的必要性论证**: 附录命题 10.4（Λ 黑盒原则上不可辨识）——平台规范的第一性要求（input §6.1）。

## 核心工程原则

1. **规约先行**：任何 .py 文件落盘前，其语义、接口、验收标准须已写入对应 SPEC 文档。规约变更须先改 SPEC 再改代码。
2. **TDD**：先写测试（红）→ 实现（绿）→ 重构。每个 SPEC 条目至少一个测试锚点（SPEC_tests.md 注册表）；无测试不合并。
3. **真值可算优先（R3a/R3b 的基石）**：平台内核采用**离散有限字母表表格环境**，全部信息论量（DI、MI、TV、entropy、empowerment、Λ）在真值模式下按定义**枚举精确计算**；有限样本估计器（R3b）再对照真值研究偏差/方差（input 风险 R2 的应对：仿真真值标定）。
4. **种子可复现**：一切随机性经显式 RNG 派生（SPEC_platform §6）；30 种子矩阵外，任何报告数字须可由 `runs/` 清单重放。
5. **证伪纪律**：实验判据是定理的证伪窗口（input §4、§6.2），verdict=REFUTED 时不许改判据——登记、分析、上报 input 修订（SPEC_experiments §6）。

## 技术栈（钉死）

- Python 3.12（系统解释器）＋ **numpy 2.3.5**（系统已装）。
- **测试框架：stdlib `unittest`**（本机离线，PyPI 不可用；不得引入 pytest/scipy 等新依赖——如确有必要，先修订本规约并登记理由与获取渠道）。
- 日志/结果格式：NDJSON＋CSV＋Markdown 报告；不引入重型库。
- 约定沿用 `refs/fetch_verify.py` 风格：stdlib 为主、脚本顶部 docstring 写用法。

## 阶段划分

| 阶段 | 内容 | 规约 | 完成判据 |
|---|---|---|---|
| **R3a** 平台内核 | 时展因果图仿真器（E5 架构）、全因果日志、五类干预算子、防御机制 M1–M4/P1–P8 | `SPEC_platform.md` | P 系列测试全绿（SPEC_tests §4） |
| **R3b** 估计层 | 真值计算模块＋有限样本估计器＋黑盒降级（区间界/单侧界/Λ 区间） | `SPEC_estimators.md` | E 系列测试全绿（SPEC_tests §5） |
| **R3c** 场景库与矩阵 | ATK-1~6＋DEL-1＋C0-DEMO＋RES-1＋FORCE-1＋BB-1＋C0-CORR（＋可选 LH-1）、实验矩阵执行、verdict 报告 = `autonomy-bench`；理论-实验覆盖矩阵见 SPEC_experiments §4 | `SPEC_experiments.md` | X 系列测试全绿＋完整矩阵跑通＋实验报告 |
| **R3c+** 补充分析（2026-10-13） | BB-2 自适应对手臂（scenario 14；`flag_by_state` 逐状态旗标）＋权重/σ 后验敏感性（`analysis_weights_sigma.py`）＋4 张数据图（`make_figures.py` → `latex/figures/`） | `SPEC_experiments.md` §8 | T-BB2×4（unittest）全绿＋bb2 组 30/30 CONFIRMED |
| R3d（后续另立项） | LLM 基质对接（基质中立性第二支柱） | 另立 SPEC | — |

## 目录结构（规划）

```
sim/
  README.md              本文件（总规约）
  SPEC_platform.md       平台规约（模型内核/日志/干预/防御/种子）
  SPEC_estimators.md     分量与复合指标估计规约（真值＋估计＋黑盒）
  SPEC_experiments.md    实验规约（场景库/矩阵/verdict 判据/产出；§8 补充实验 2026-10-13）
  SPEC_tests.md          TDD 测试计划（L0–L3 注册表）
  src/autonomy_sim/      实现（R3a 起按 TDD 建立）
  tests/                 测试（先于实现建立；unittest 风格，pytest 兼容）
  analysis_weights_sigma.py  权重/σ 后验敏感性（只读 runs/ 分量束；SPEC_experiments §8）
  analysis_p3.py         P3 分析包（外部效度/通道消融/备选聚合/Faith 逐行；SPEC_experiments §8）
  analysis_exec1_weights.py  EXEC-1 富耦合实例权重/弹性敏感性重跑（2026-10-21，五审 Major 第3条；
                             只读 exec1/results.csv 真值束，不重新仿真 → analysis_exec1_weights.json）
  analysis_sensitivity_arms.py  X5 构念效度敏感性臂（2026-10-22，六审 R1：x-a 背书量化四档 ATK-1
                             重跑＋连续极限闭式校验；x-b κ 细化三档 ATK-2 网格重评分；真值模式
                             确定性重跑（非后验重算）→ analysis_sensitivity_arms.json；
                             平台前提 SPEC_platform v0.3，回归钉 T-REF×7）
  make_figures.py        数据图生成（→ latex/figures/；fig_ahi 含无防御 cell 虚线口径；2026-10-22 起
                         全部图内只留 panel 标号与坐标信息，结论一律入图注；R9 起 pdf.fonttype=42
                         TrueType 嵌入——原 Type 3 字体无 ToUnicode 映射（pdffonts uni=no），是评审侧
                         图区文本抽取乱码三轮误报的根因；数据锚点回归：slope −0.5039、AHI 0.3745）
  runs/                  实验产出（gitignore；每跑一份 manifest 登记）
```

## 验证层级

- **L0 单元**：函数/类级正确性（RNG 确定性、schema 校验、张量归一）。
- **L1 数学性质**：把定理/引理编码为断言（AX5 零歼灭、表示定理数值见证、引理 2.3.1 的 MI=DI、Kramer Property 2 反例、T6 动力学界、C1/C2 平衡点公式等）——理论回归的防线。
- **L2 场景**：每个 ATK/DEL/C0 场景的冒烟测试（短视界、单种子、判据函数可运行且方向正确）。
- **L3 矩阵**：小规模回归矩阵（2 种子）入 CI；完整矩阵（30 种子）为批处理，产出入 `runs/`。

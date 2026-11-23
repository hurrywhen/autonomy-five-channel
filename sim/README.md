# 仿真与实验 · 总规约

> **R22 当前注记（2026-11-23）**：权威口径为 `SPEC_estimators.md` v1.8、`SPEC_experiments.md` v1.8 和英文 `latex/`；下方 R3 路线只作建设史。R22 撤回 R21 将“A 漏/C 覆盖”归于条件设计、将“双漏”归于插件偏差的不可识别归因（basic/percentile 构造、条件化和随机流同时不同）。新增 `r22_interval_contrast.py`：同一批轨迹 bootstrap 复制上计算 **A=basic-share-conditional、B=percentile-share-conditional、C=percentile-joint**；B/C 为匹配 percentile 的通道传播对比，A/B 为区间构造对比，A/C 仍为混合对比。字段改 `descriptive_interval_method_contrast`，完整报告 2×2 覆盖模式，不作正式偏差分解或单因果归因；偏差/RMSE 由精确真值多种子模拟独立报告。C 逐值复现 R21，匹配 A 只是补充重算；正式证书仍报告原 R21 A，NRI 仍 INDETERMINATE＋逻辑包络。完整网格 `analysis_r22_detection_study.json` 为 16 种子×{2048,8192}×200；运行全套 **429 项**测试：`python3 -m unittest discover -s tests -q`；`analysis_r22_joint_audit.py --check`、`analysis_r22_detection_study.py --check`（后者重算完整匹配网格，较慢）与 R15–R21 复核均只读。历史 R11–R21 工件不改写（R21 字节不变）。本轮创建不可变 tag `v1.5-r22` 与两环境冻结重放清单；用户决定 R22 不设页数上限；version DOI 与外部执行仍未完成。
>
> **R21 历史注记（2026-11-22）**：权威口径为 `SPEC_estimators.md` v1.7、`SPEC_experiments.md` v1.7 和英文 `latex/`；下方 R3 路线只作建设史。R21 在 R20 基础上闭合复合采样区间条件化范围与覆盖解释两项缺口（检测规则/三态敏感性/估计器不变）：高于检测限约定的复合采样区间重命名为**来源份额条件复合采样区间**（`r21_guards.py`，SHARE_CONDITIONAL_SAMPLING_BASIC_BOOTSTRAP＋每区间 conditioning_scope＋证书级 composite_interval_conditioning 政策；仅传播来源份额、其余通道固定为插件/结构点、非完整联合不确定度；份额自身区间保持无条件）；**逻辑包络锚点包含与采样统计覆盖分开报告**（永不合并/跨类比较为估计器优劣）；新增**联合轨迹 bootstrap 补充诊断**（`r21_joint_bootstrap.py`：每重采样重算全部通道＋复合，保留批内协方差，执行按序列分层独立重采样；工件级、非证书报告语义、不消除插件偏差）；正文欠覆盖**双因归因**（DI 插件偏差＋条件化设计），检测研究并列份额条件/联合覆盖量化后者（**该 A/C 单因果量化由 R22 撤回**；`analysis_r21_detection_study.json`：份额条件复现 R20；联合 RNI 16/16→14/16、avg 15/16→13/16、NRI 0/16）。运行全套 **406 项**测试：`python3 -m unittest discover -s tests -q`；`analysis_r21_joint_audit.py --check`、`analysis_r21_detection_study.py --check`（后者重算完整网格含联合 bootstrap，较慢）与 R15–R20 复核均只读。`EXTERNAL_VALIDATION_PROTOCOL.md` 仅设计冻结。历史 R11–R20 manifest/results/verdict/validation 不改写（R20 工件字节不变），旧 a_org/a_via/Bundle 不冒充当前构念。本轮创建不可变 tag `v1.4-r21` 与两环境冻结重放清单；version DOI 仍待 Zenodo 归档。
>
> **R20 历史注记（2026-11-22）**：R20 闭合近零检测可执行性、区间敏感性语义、真实区间传播与测试设计四项缺口：近零检测改预声明数据驱动规则并纳入正式证书（`r20_detection.py`＋`r20_guards.py`，basic 偏差校正 bootstrap 区间三态，真值规则降级 oracle-assisted 夹具专用，采样基线 INTERVAL 无标量）；区间敏感性三态（相同宽区间永不解释为一致）；真实区间传播＋类型区分；测试解耦（R19 实证不变量改快照回归）；预声明 16 种子检测研究（369 项测试，103 页）。该轮工件只读保留并被 R21 supersede（复合区间条件化命名与覆盖语义升级；工件字节不变）。
>
> **R19 历史注记（2026-11-22）**：R19 证书升级层级感知 schema（`r19_guards.py`，L0 独立内部因果归因、通道四态、点值/区间分离＋复合区间单调传播、IRL/薄日志/零熵/零总流降级）；修复 R18 跨环境重放失败（规范化容量输入＋不可变证据绑定＋逐字段容差，失败记录 `runs/20261122_r19/REPLAY_FAILURE_R18.md` 保留）；修正 state_autonomy_RNI 资源门缺陷；敏感性分解与后验冻结阈值术语；8 种子采样研究（319 项测试）。该轮工件只读保留并被 R20 supersede（检测判定与区间语义升级；工件字节不变）。
>
> **R18 历史注记（2026-11-21）**：R18 最终证书升级为完整剖面 schema（`r18_guards.py`，点值 L2）；R17-native 组合式夹具被联合日志端到端审计 supersede（`native_joint_audit.py`、`analysis_r18_native_joint_audit.json`）；开环零值量词改支持集相对、期末观察/观察序列约定分离；权重结果统一称精确敏感性；外部协议 TOST/非劣效方向精确化（273 项测试）。该轮工件只读保留；其联合审计跨环境重放失败由 R19 修复并记录。
>
> **R17 历史注记（2026-11-19）**：R17 将多步执行改为预承诺开环序列干预核并加入反馈复制反例；当前结构/历史形成并列输出，Lambda 时间原点显式；新增 R17-native T=3 基准、权重闭单纯形对数界/半空间、外部等价/非劣效设计（251 项测试）。该轮工件只读保留。

**历史版本**: v0.1（规约先行版，2026-10-04）
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

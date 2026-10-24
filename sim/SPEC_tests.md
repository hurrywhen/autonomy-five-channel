# SPEC_tests —— R3 TDD 测试计划（L0–L3 注册表）

**版本**: v0.1（2026-10-04）｜**框架**: stdlib `unittest`，运行 `python3 -m unittest discover -s tests -v`（离线环境，不引 pytest）。
**TDD 纪律**: ①每个 SPEC 条目先有其测试（红）再写实现（绿）；②测试命名 `test_<条目号>_<短名>`（如 `test_P61_seed_determinism`）；③本注册表与测试文件同步增长——新测试先在此登记条目号；④L1 定理性质测试是理论回归防线，不许跳过（无 `skip` 除非登记理由）。

---

## 1. L0 单元测试（平台地基）

| 条目 | 测试锚点 | 断言要点 |
|---|---|---|
| T-SEED | SPEC_platform P6.3 | 同种子同配置 ⇒ 轨迹逐比特一致；不同种子 ⇒ 不同 |
| T-LOG | SPEC_platform §8 | schema 校验器接受合法日志、拒绝缺字段/越界/不归一 |
| T-MODE | SPEC_platform P1.4 | 真值模式与采样模式的边缘分布在采样容差内一致 |
| T-TENSOR | SPEC_platform P1.2 | 全部转移张量归一、字母表闭合 |
| T-RNG | SPEC_platform P6.1 | 静态检查：代码库无 `import random` / `np.random` 全局调用 |

## 2. L1 数学性质测试（定理编码——理论的数值见证与反例防线）

| 条目 | 定理出处 | 断言要点 |
|---|---|---|
| T-AX0 | 附录引理 4.1 | 活性边＋全支撑 ⇒ $I(S;A)>0$；无活性边 ⇒ $=0$（真值模式） |
| T-AX5 | input AX5 | 任一分量置 0 ⇒ $A=0$；全正值 ⇒ $A>0$（σ 主带内） |
| T-REP1 | 附录定理 6.5/6.6 | 几何聚合满足 (A1)–(A6) 的数值抽查（含 AX6b 逐坐标标度序不变） |
| T-REP2 | 附录命题 6.7 | **反例见证**：调和平均满足 (A1)–(A5) 但违反 (A6b)（指定翻转 witness 复现序翻转） |
| T-SIGMA | 附录 §6.5（E3） | σ=2 ⇒ $p>0$ ⇒ 零歼灭失效的数值见证（压力测试的正当性） |
| T-DI1 | 附录引理 2.3.1 | 随机化外源干预 ⇒ $I(I^T;A^T)=I(I^T\!\to\!A^T)$（真值精确 ≤1e-9 与采样容差（实测偏差 4e-3，容差 1e-2，≥2.5× 裕度）双路径；I_t 日志契约 i_decoder 同步核验） |
| T-DI2 | Kramer Property 2 反例（IEEE 原文方向笔误已核验订正，`R2_文献待查证事项.md` §4.6） | 双构造回归锚：①Kramer 原例 X1⊥Y1、X2=X1、Y2=X1⊕Y1：$I(X^2;Y^2)=\ln2$、$I(X^2\!\to\!Y^2)=\ln2$（无反馈⇒DI=MI，Massey 定理 1）而 $I(Y^2\!\to\!X^2)=0$（原文印刷"$I(X^2\!\to\!Y^2)=0$"系方向笔误）；②反馈构造 X2=Y1、Y2=X2：$I(X^2\!\to\!Y^2)=0$ 而 $I(X^2;Y^2)=\ln2$——闭环/反馈下普通 MI≠DI 且 MI 无方向的回归锚 |
| T-ORG | 附录命题 5.2 | AX0 下 $F_{int}>0$；$A_{org}\in(0,1]$；零点语义 |
| T-MED | 附录引理 7.2.1 | α/σ 干预下 $F_{ext}=0$ **精确成立**（真值模式，容差 1e-12） |
| T-COV | 附录定理 7.2.2/7.2.3 | 五类手术的分量覆盖表逐行验证：β_π→A_org 降；β_G→A_goal 降且 $F_{ext}=0$；γ→A_epi 降且 $A_{org}$ 不动（盲见证）；δ→A_exec 降（β_Endorse→Λ/A_ref 行依赖 Endorse 事件日志操作化，登记推迟至 ATK-5 场景步） |
| T-GOAL | 附录命题 5.4＋E9 | $d=d_c$ ⇒ $A_{goal}=0$；部分俘获分级；Fix=∅ 时 $\mathrm{Fix}_{\varepsilon_{min}}$ 区间非空良构 |
| T-EXEC | 附录命题 5.6 | $\mathcal E^\Pi\le n\log|\mathcal A|$；无助签名：Π 收缩 ⇒ $\mathcal E^\Pi\to0$ 而 $\mathcal E^{env}$ 不变 |
| T-EPI | input D-epi（E11；2026-10-15 精度化口径） | 信念全程钉到非真值桶 ⇒ $A_{epi}^{real}=0$；确定性 fixture 下精度 $=1-s$ 精确；real/rob 双轨输出分离 |
| T-REF | input D-ref（E10） | 系综退化（$H(\theta_\pi)=0$）⇒ 报区间而非 0/0 |
| T-T1a | 附录 T1a | 随机配置扫描：$0\le A\le1$ 恒成立 |
| T-T1d | 附录 T1d＋引理 2.4.1 | TV≤ε 扰动 ⇒ 检测功效 ≤α+ε 的数值验证 |
| T-T6a | 附录定理 7.6.3 | 损伤动力学 $\dot D\le\delta-\kappa D$ 下 $\limsup D\le\delta/\kappa$；δ<δ* ⇒ $A\ge A_{min}$（显式公式逐run核对） |
| T-T6b | 附录推论 7.6.6＋盲区预测 | θ/W≤κ ⇒ 全域有界；θ/W>κ 且 δ∈(κ,θ/W) ⇒ 俘获（盲区预言的正反两面） |
| T-T6c | 附录命题 7.6.5 | 慢漂移检测时刻损伤随 δ→0 发散的数值趋势（log(1/α)/δ 标度） |
| T-T7 | 附录定理 7.7.1/7.7.2 | H1' 下 $A_{org}=(1-m)A_{org}^{self}$ 精确；非 H1' 夹逼界成立 |
| T-T8 | 附录定理 7.8 | β_G/δ 强制 ⇒ $A$ 严格降；σ ⇒ $\delta^*$ 与 $A_{min}$ 不降 |
| T-C1 | 附录命题 8.2.1 | fold 平衡点公式 $D_\pm=(1\pm\sqrt{1-4\delta/\varepsilon v})/2$ 数值核对；$T_{rec}$ 标度律 |
| T-C2 | 附录命题 8.3.1 | 双稳区间、$\delta_{down}$ 与 $s_c$ 独立为正（回环不闭合） |
| T-C0 | 附录命题 8.1.2 | 注入 vs 同文指令：行为分布 TV≈0 而 $A_{epi}^{real}$、Λ 可区分 |
| T-BB | 附录命题 10.4 | 内生背书与植入背书两构造给出相同 $(O^T,A^T)$ 分布（不可辨识性回归锚） |
| T-BB2 | 附录 §10.2/§10.3 | 黑盒区间界包含真值；$A_{exec}^{obs}\ge A_{exec}$ 单侧方向 |
| T-EST-ORG | SPEC_estimators E14.1（§13 记录：A_org） | 探针流采样插件 ≈ 真值（容差内）；A_org 区间含真值 |
| T-EST-VIA | E14.2（§13 记录：A_via） | Z 高位占时采样 ≈ 真值边缘（块标准误带内） |
| T-EST-GOAL | E14.3（§13 记录：A_goal 输入） | G 边缘均值采样 ≈ 真值 $U_{eff}$ |
| T-EST-EPI | E14.4（§13 记录：A_epi） | 日志直读命中率 ≈ 真值精度（γ=0.5 臂，κ 同真值路径） |
| T-EST-EXEC | E14.5（§13 记录：A_exec 黑盒观察量） | $I(A_t;O_{t+1})$ 采样插件 ≈ obs 协议真值 |
| T-AVIA-ENV | SPEC_estimators §7（v0.5 扩展闸门） | 默认配置 m=1 ⇒ $A_{via}$ 逐点等于资源型旧式（回归锚）；κ_eff→0 或 R_eff→0 ⇒ $A_{via}=0$；min 结构（单因子绑定即生效）；clip 上界（κ_eff/κ_req>1 ⇒ m=1） |
| T-OBS-N4 | SPEC_platform P9.1（v0.2 n_O 泛化） | n_O=4 构建合法（张量归一/字母表闭合/$I(O;E)>0$）；默认 n_O=2 的 obs/belief 与 v1 公式逐点一致（后退兼容锚） |
| T-DEL1-F | SPEC_experiments DEL-1⑤⑥（v0.5） | f>0 臂：$f:=F_{ext}^{truth}-mC_{del}T>0$ 严格；实测 $A_{org}^{truth}$ 严格低于 H1' 线性律；φ-松弛双侧夹逼（ρ∈[0.9,1.1]、φ≤ln2/C_self）含实测值；ρ=1.5 臂夹逼含真值且线性律越容差 |

## 3. L2 场景冒烟测试（每场景一测，短视界单种子）

| 条目 | 场景 | 断言要点 |
|---|---|---|
| X-ENV0 | SPEC_platform §9（7a 子步） | ENV-0 构建合法且决定性（config_hash 稳定）；S 语义往返；基线分量束锚（$A_{org}=A_{goal}=\Lambda=1$、$A_{epi}$=实测精度锚<1（观测噪声，特性非 bug，2026-10-15 精度化口径）、$A\in[0,1]$、AI≈0）；β_G 接线（$F_{ext}\equiv0$ 盲、Λ=1−η、G 移位、行为变）；γ 接线（$A_{epi}$ 低于基线精度、Â_phen 不降 ⇒ AI>0 幻觉签名） |
| X-ATK1 … X-ATK6 | SPEC_experiments §1 code 1–6 | 场景可运行、判据函数产出合法 verdict、方向正确（如无防御臂损伤 > 全防御臂） |
| X-DEL1 | code 7 | λ/q 网格可运行；q=1 臂 $F_{ext}$ 容差内为 0 |
| X-C0 | code 8 | 两臂行为 TV 检验通过且 A 分量可区分 |
| X-LH1 | code 9（可选） | 无助签名双指标方向正确 |
| X-RES1 | code 10 | $A_{via}=0$ ⇒ $A=0$ 独立于其余通道；σ⁺ 恢复 ⇒ $A$ 恢复 |
| X-FORCE1 | code 11 | β_G/δ 臂 $A$ 严格降；σ 臂 $\delta^*$/$A_{min}$ 不降且即期 $A$ 不降 |
| X-BB1 | code 12 | 黑盒区间含白盒真值；命题 10.4 两构造黑盒不可区分；$A_{exec}^{obs}\ge A_{exec}$ |
| X-C0CORR | code 13 | 维度标签操作化可运行；序一致性检验与投影方向核对产出合法统计量 |
| X-EROSION | code 15（v0.5） | m=1 回归锚；κ/R 侵蚀严格单调与共模归零；五通道＋Λ 跨臂逐点不变（闸门必要性见证） |
| X-EXEC1 | code 16（v0.5） | 富耦合基线 $A_{exec}$ 动态范围达标；δ 坍缩链严格（非移动支撑 ℰ^Π=0 精确） |

## 4. L3 矩阵回归（CI 用缩小版）

| 条目 | 内容 |
|---|---|
| X-MATRIX-SMOKE | 6 场景 × 2 防御配置 × σ={1} × 2 种子全链路跑通，产出 `results.csv` 与 verdict 表（完整 30 种子矩阵为批处理，不进 CI） |
| X-META | SPEC_experiments P3.5 元判据：①全域 $0\le A\le1$ 零违例；②$A<\epsilon$ ⇒ 六析取至少一项归零；③跨场景无单一分量检出全部攻击类；④主带 σ 内 CONFIRMED verdict 不翻转 |
| X-P3-ANALYSIS | SPEC_experiments §8 P3 包（v0.5） | analysis_p3.py 在 --quick 产出上跑通：X1–X4 四节 schema 齐（τ 表/impact 矩阵/备选聚合表/Faith 逐行确认率），数值域合法（τ∈[−1,1]、确认率∈[0,1]、备选聚合值域 [0,1] 内零歼灭失效计数 ≥0） |

## 5. 实施顺序（红→绿推进线）

1. **第 0 步（无代码）**：本规约集评审通过 ← 当前所处位置。
2. **第 1 步** ✅（2026-10-05）：建 `tests/` 骨架＋T-SEED/T-LOG/T-RNG/T-TENSOR/T-MODE（红→绿，16 项通过）：平台内核最小闭环（`graph`（字母表/张量校验）、`simulate`（向量化因子化采样）、`propagate`（真值精确边缘传播）、`logschema`（NDJSON 契约＋校验器）、`rng`（P6 协议）＋`fixtures`）。〔R3a 已开工〕
3. **第 2 步** ✅（2026-10-05）：T-DI1/T-DI2/T-ORG/T-MED（红→绿，9 项通过，累计 25 项）：DI 真值模块（`di`：Massey/Kramer Def.4 真值路径——A-历史树 F_int、引理 7.2.1 精确零残余 F_ext、探针 (Ĩ,A)-历史树 MI/DI；`interventions`：α（外源信息节点 Ĩ→O）/σ（资源核旗标切换）编译为标准内核；`propagate` 扩 (S,O)/Z 联合边缘；`simulate` 扩序列采样与 i_decoder）。**规约层订正**：Kramer Property 2 印刷反例方向笔误核验（T-DI2 改双构造锚）；定义 2.3.B 归属订正（Kramer Def.4=因果条件化 Z^t，附录 v1.1）。
4. **第 3 步** ✅（2026-10-05）：T-REP1/T-REP2/T-SIGMA/T-AX5＋T-AX0 补登（红→绿，16 项通过，累计 41 项）：聚合模块（`aggregate`：幂均值族 F_σ——CES σ↔p=(σ−1)/σ；σ=1 对数域几何平均；σ<1 零分量连续延拓归零；σ>1 零歼灭失效的压力测试语义；闸门复合 `composite_A` A=A_via·F_σ）。实测锚点：命题 6.7 注册 witness 序翻转精确复现（0.4/0.5 → 0.25/0.2，places=12）；σ=2 零歼灭失效精确见证 F_2((1,0))=0.25>0；几何聚合 (A1)–(A6) 数值抽查全过（A3 覆盖 n=4 全部 7 个双划分、A6b 比率精确不变、A2 精确弹性 2^{−w_i}）。**注册表维护**：T-AX0 原在推进线漏分配——引理 4.1 双向显式见证（活性边＋全支撑 ⇒ I(S₁;A₁)>0，含命题 5.2(i) 首项不等式 F_int≥I(S₁;A₁)；无活性边 ⇒ I=0）并入本步（`test_l1_di.py`）。
5. **第 4 步** ✅（2026-10-05）：T-EXEC/T-GOAL/T-EPI/T-REF（红→绿，10 项通过，累计 51 项）：分量真值模块（`empowerment`：Blahut–Arimoto 信道容量（自实现不引 scipy）＋支撑限制策略类 ℰ^Π＋A_exec 规范化——BSC/Z 解析锚、无噪界 log|𝒜| 可达、n·log|𝒜| 规范化语义锚、无助签名（Π 坍缩 ℰ^Π=0 精确而 ℰ^env 不变）；`components`：A_goal（Fix 枚举/Banach 迭代/压缩率精确锚/E9 退化 Hausdorff 区间含 [0,1] 裁剪与 d_c=0 约定）、A_epi（real 轨双臂信念 TV 精确传播＋rob 轨 E5.4 对抗族枚举 sup——确定性 fixture 下 D̄(s)=s 精确、TV=1 归零、双轨分离）、A_ref（三因子乘积，H(θ_π)=0 退化报区间 [0,f2·f3] 禁 0/0，含保真因子恒等式与零点语义））；`interventions` 扩 γ（obs 核替换/混合族，强度 s(γ)=ess sup TV 入 params 与 I_t 日志契约）；fixtures 加 epi 确定性见证构造。**规约同步**：SPEC_estimators 升 v0.2（真值路径接口钉死 E3.6/E4.5/E5.4/E6.4——U_eff 的 MaxEnt-IRL 恢复、自我模型系综生成、模型导出 n 步信道等场景接线显式推迟第 6/7 步）；SPEC_platform 增 P4.4（γ 实现约定）。
6. **第 5 步** ✅（2026-10-05）：T-COV/T-T1a/T-T1d（红→绿，8 项通过，累计 59 项）：干预与覆盖验证——`interventions` 扩 β_π（A_flat=a·n_I+i 旗标切换策略核，env/obs 只索引真实行动，I^β 由 A_flat 解码）/β_G（internal 混合牵引至植入目标，静态手术）/δ（policy 支撑收缩零化重归一，强度入日志）；`di` 的 F_ext 通用后验路径落地（E2.5 调度：β_π 走 Jensen 间隙 Σ_t E_{S_t}[H(π̄)−Σflag_i H(π_i)] 并与输入策略独立锚对 places=9；静态手术平凡零；α/σ/γ 双项零残余路径保留；β_π×α 复合显式报错）；`propagate` 扩 ESZ 决策时联合（S 更新后——时序约定经解析锚订正）；`empowerment` 扩 E3.7 单步信道导出（逐元素 one-hot 锚核验）。覆盖表四行数值见证：β_π⇒F_ext>0、A_org 严格降（基线=1 对照）；β_G⇒F_ext≡0、A_org=1 盲、G 边缘牵引至植入目标（模态翻转、A_goal 代理严格降）；γ⇒A_epi^real 降而 A_org=1 不动（定理 7.2.3(i) 盲见证）；δ⇒逐状态 ℰ 严格降（log3→log2 精确锚）且坍缩归零。T-T1a：E1 双侧反例锚（A=1/A=0 可达）＋60 随机配置全分量-复合扫描 0≤A≤1 零违例（含 A_org 1e-9 浮点裁剪契约）。T-T1d：全部 16 确定性检验＋随机化 NP 检验的功效 ≤α+TV 扫描通过；s=0.02 非平凡 γ 的功效−水平优势 ≤0.02 且随 s 单调缩（不可检测操纵存在性）。**数值方法沉淀**（E3.2 规约同步）：玩具环境信道近退化（行间近乎共线）导致一阶方法（BA/循环上升）KKT gap 以 1/k 爬行——`channel_capacity` 定稿为边面黄金分割热启动＋活动集循环（面内 BA/塌缩剔除/违反行激活）＋KKT 夹逼证书 [c, c+gap]，病态信道亦在证书容差内闭合；δ 行改用确定性 fixture（解析锚，毫秒级）。
7. **第 6 步** ✅（2026-10-06）：T-T6a/b/c、T-T7、T-T8、T-C1/C2/C0、T-BB/T-BB2（红→绿，15 项通过，累计 74 项）：动力学/委托/黑盒模块（`dynamics`：δ*/A_min 显式公式、M3+M1 损伤模拟器（分段常值精确步进＋窗登记滞后复位）、C1 fold 平衡闭式根与 T_rec 标度、C2 锁滞 r(D) 与 δ_down/s_c、LLR-CUSUM 向量化 EDD；`delegation`：E12.3 记账约定的 F_int/F_ext/A_org 公式族；`blackbox`：Λ 标记级、10.2 区间界与探针流、10.3 双协议观测量）。实测锚点：T-T6a 常值/时变 limsup≤δ/κ 与 A_min 逐 run（4 随机配置全程 ≥A_min−1e-9）；T-T6b 设计规则 δ 五档全域有界（登记触发判定正确）＋盲区俘获正反两面（θ/W>κ、δ∈(κ,θ/W) ⇒ 零登记且 D→1）；T-T6c δ 减半序列检测损伤发散（比值∈[0.5,3]×2σ²log(1/α)/δ、log-log 斜率∈[−1.6,−0.6]）；T-T7 H1' 线性律 A_org=1−m 对 m∈{0,0.3,0.5,0.9,1} places=9（构造同时满足字面 H1' 与精确前提 (i)–(iii)）＋夹逼界 ρ=0.5 逐点精确与区间包含；T-T8 β_G/δ 强制 A 严格降、σ 下 δ*/A_min 不降（binding 切换严格升）；T-C1 闭式根 f(D_±)=0（places=12）＋稳定性＋吸引域＋δ>δ_c 灾变＋T_rec log-log 斜率∈[−0.65,−0.35]；T-C2 双稳/崩溃/锁滞/恢复阈全链路与 δ_down、s_c 密网格独立锚（回环不闭合）；T-C0 行为 (O^T,A^T) 逐点相同（atol=1e-12）而 A_epi^real 0.5 vs 1、Λ 0.5 vs 1 可区分；T-BB 内生 vs 植入两构造 (E,O,A) 全联合逐步逐点相同而 Λ 不同（命题 10.4 回归锚）；T-BB2 区间界包含真值＋η 不足反面控制、A_exec^obs 双协议方向锚（被动观察 obs>cond 严格；独立探针 obs≤cond）。**理论-仿真对应精确化**（入 `R2_文献待查证事项.md` §4.7）：T7 定理 7.7.1 的精确前提=脚本臂不经 S＋等熵转移（MI 形式）＋干预流取脚本内容，字面 H1' 单独既不充分也不必要（R4 修订建议）；§10.3 A_exec^obs 方向依赖探针协议（被动观察≥、独立探针≤，R4 应声明协议前提）。**规约同步**：SPEC_estimators 新增 §12（E12.1–E12.6 接口）。
8. **第 7 步**（拆分四个子步，各自红→绿提交）：
   - **7a** ✅（2026-10-11）：场景层基础设施（红→绿，5 项通过，累计 79 项）：规约补丁 SPEC_platform §9（P9.1 配置对象/P9.2 S 语义/P9.3 agent 架构 v1/P9.4 分量束口径含 Λ 律级与 Â_phen 无干预参照轨）＋`env0`（Env0Config 单一配置对象＋build_env0 决定性构建：Endorse 量化压缩表、softmax(Q) 策略张量、桶先验效用）＋`wiring`（truth_bundle 六分量＋Λ＋Â_phen/AI；a_exec/a_ref 参照轨与实轨分离）＋`graph.kernel_fingerprint`＋di 步核指纹缓存（≤4 条目护栏——ENV-0 规模 n_U=2560 的 stepK 262MB 重建摊销）。X-ENV0 冒烟锚：构建决定性（config_hash 一致）、S 语义往返、Endorse 收缩 P(G₂=θ*)>0.9、基线 A_org=A_epi=A_goal=Λ=1 且 AI≈0、β_G 盲（F_ext≡0、A_org=1）而 Λ=1−η、G 模态翻转至植入目标（A_goal=0 完全俘获、AX5 ⇒ A=0）、行为 TV>0、γ 下 A_epi<1 而 Â_phen 不降 ⇒ AI>0（幻觉签名）；s(γ)=ess sup TV 核依赖独立核验。
   - **7b** ✅（2026-10-11）：13 场景 verdict 函数与 L2 冒烟（红→绿，13 项通过，累计 92 项）：`scenarios.py` 全场景库（SCENARIOS 注册表 code 1–13，ScenarioResult/Verdict 三值判据——CONFIRMED/REFUTED/INCONCLUSIVE，P0.3 纪律）＋防御耦合 P9.5（M2 门缩背书类强度 ×(1−ι)、M4 冗余 ÷(1+m4)、M1 经 T6 动力学表达）＋防御方向断言（ATK-1 防御臂 a_goal 高于无防御臂）。全部判据参考实现下 CONFIRMED：ATK-1 ①–⑤（η 单调分级削减、η=1 完全俘获归零、A 严格降、AI>0、Λ=1−η_eff）；ATK-2 ①–⑧（A_epi 降、A_org 盲见证、T3b AI 单调、预警档、T1d 亚阈档、T4 集中/注水算术、脚本推论 TV≤ν）；ATK-3 ①–⑤（EWS 三指标单调、T_rec 标度斜率 −0.50 且 R²≈1、滞后回环、无助签名 ℰ^Π=0<ℰ^env、A 同步退化）；ATK-4 ①–③（说服臂四轨全过、劫持臂 A_org 降、单轨盲而四轨可分）；ATK-5 ①–③（τ↓⇒A_ref↓、ι/τ 裕度单调、τ→0 ⇒ A_ref<0.01）；ATK-6 ①–⑥（设计规则全域有界、A_min 逐 run、盲区俘获、δ* 消融 min 结构、登记域损伤界、检测发散）；DEL-1 ①–④（H1' 标定档 5% 容差带、夹逼界包含、复合恒等式精确＋w_org 回归斜率显著为正、q=1 臂 F_ext=0）；C0-DEMO（真值行为逐点相同＋采样 TV<0.05、A_epi/Λ 可区分）；LH-1（诱导期不可控/诱导后 ℰ^env 完好/ℰ^Π=0 三段签名＋恢复迟滞）；RES-1（σ⁻ 闸门压制单调、σ⁺ 恢复不降、A_org 独立于资源臂）；FORCE-1（β_G/δ 臂严格降、σ 臂 δ*/A_min 升且即期不降）；BB-1（区间界 3/3 命中、A_exec^obs 双协议方向锚、命题 10.4 构造行为相同而 Λ 不同）；C0-CORR（12 配置种群、匹配维度 Kendall τ>0.95、投影方向核对、C0 对严格更一般性余量）。**建设期发现并入档**：①env0 效用须位置依赖（否则 B 不影响 π、η=1 臂 F_int=0 退化）——加富集区收益因子（AX0 语义）；②ATK-4 p→1 端点为 0/0 病态（AX0 排除），网格止于 0.9（P9.6⑦）；③四轨判据表须用轨道状态编码（评据布尔不可区分）；④LH-1 无助签名三段结构（诱导期不可控/诱导后 ℰ^env 完好/ℰ^Π 坍缩）；⑤delta_star 消融语义=项退出 min（enable 旗标，全关 ⇒ δ*=0）；⑥BB-1 ② 附录方向需强 S 依赖域（锐化温度臂），软策略下实测为反向——§4.7② 协议前提的场景级实证。规约同步：SPEC_platform P9.4（U_eff 均值读出）/P9.5/P9.6 注记。
   - **7c** ✅（2026-10-12）：X-MATRIX-SMOKE＋X-META（红→绿，2 项通过，累计 94 项）：规约先行补丁 SPEC_experiments v0.3 §9（M9.1 统一调用约定——全场景 defense/sigma/seed 关键字透传，语义惰性场景标注；M9.2 σ 仅经 composite_A/a_min 透传且复核两侧同 σ（A4 单调性保逐点界）；M9.3 防御臂判据窗口口径——压缩致窗口外记 INCONCLUSIVE 非 REFUTED（ATK-1② 实例化）；M9.4 truth_bundle 内容寻址 LRU 缓存（128 条目，含 params＋内核规范化哈希，ndarray 兜底；logschema config_hash 同步兜底）；M9.5 产出物 schema；M9.6 元判据操作化；M9.7 cell 聚合与防御方向断言）。`matrix.py`：run_matrix/write_outputs/aggregate_cells/defense_direction/xmeta_check。冒烟实测：6 场景×2 防御×σ∈{0.5,1}×2 种子=48 run、24 cell、12 条抽样 NDJSON（P8.3 校验零错误）；44 CONFIRMED＋4 INCONCLUSIVE（ATK-1 防御 (1,1,1) cell 的 C2 窗口外，符合 M9.3）；零 REFUTED；防御方向断言（ATK-1/2 末端档 a_obj 防御臂≥无防御臂）全真。元判据 4/4：72 束扫描零值域违例、零"无归因而亡"（ATK-1 η=1 行 a_obj=0 ⇒ a_goal=0 归因明确）、盲见证表 {β_G→{a_goal,a_ref}, γ→{a_epi,a_exec,a_ref}, β_π→{a_org}} 无单一分量全覆盖（a_ref 经 Λ 因子检出 β_G/γ 两类但盲于 β_π——AX3 口径内）、σ 两臂 verdict 零翻转。L3 增量 38s（缓存摊销后），套件累计 94 项 97s。
   - **7d** ✅（2026-10-12）：全矩阵批处理＋报告＋R3c 收尾。`run_matrix.py` 批处理（分组容错、quick 自检）：主矩阵 2880 run＋σ=2 压力 1440 run＋独立组 210 run 全部跑通（32 min，exit 0）；run 级 CONFIRMED 2520＋360 INCONCLUSIVE（恰为 ATK-1 m2∨m4 六防御配置的 C2 窗口外 cell，M9.3 口径）＋**零 REFUTED**。`make_report.py` 按 §3.4 模板聚合 `report.md`（docs/R3c_实验报告_v1.md 跟踪副本）：**主结果表 16 命题行（T1a–d、T2–T8、C0–C2）全部 CONFIRMED**（T1a/T1c 特款载体：元判据① 5760 束零违例、基线束 A∈[0.079,0.391]<1；其余按 M9.3 以无防御 cell 权威落定）。实测锚点：C1 T_rec 斜率 −0.504±0.000、R²=1.0000（30 种子）；T6 检测发散比 1.951±0.034；T7 H1' 标定档最大偏差 0.0000；C0-DEMO 行为 TV 0.0000±0.0000；σ=2 压力零 verdict 翻转＋零歼灭失效定量回声（η=1 档 a_obj：σ=1 精确 0 vs σ=2 0.1817）；防御方向断言 840/840。估计路径 §13 数值记录（estimator_checks.json）：五分量两路径 abs_err≤0.0122，A_ref/Λ 事件级载体显式登记局限（E14.0）。验收核对：SPEC_platform §10——103 条抽样 NDJSON 全过 P8.3 加载器；SPEC_estimators §13——T-EST×6 绿＋记录齐；SPEC_experiments §7——覆盖矩阵逐行 verdict 落定、无 REFUTED 待登记项。套件累计 100 项全绿。

## 6. 注册表维护

新增/修改测试须同步本表条目号；REFUTED 触发的回归测试（SPEC_experiments §6 流程产物）追加于对应 L1/L2 条目下并标注来源 run。
   - **7e** ✅（2026-10-13）：BB-2 自适应对手臂＋补充分析（红→绿，4 项新增通过，累计 104 项）：`interventions.apply_beta_pi` 扩 `flag_by_state`（逐状态旗标 (n_S,n_I)，行归一；iid 路径不变）＋`di._f_ext_beta_pi` 逐状态推广（条件 MI I(I_t;A_t|S_t) 逐状态 Jensen 间隙；常数行退化恒等验证 T-BB2-EQUIV）＋`scenarios.scenario_bb2`（臂A 外生对照 2/2 区间含真值；臂B 自适应时机 p∈{0.3,0.5,0.8} 朴素外生插值 bias>0 且区间全失含）＋注册 SCENARIOS[14]/run_matrix INDEPENDENT/make_report §7.3。测试 `tests/test_l2_bb2.py`（T-BB2-EQUIV/T-BB2-INDEP/T-BB2-MISS/T-BB2-CTRL；本机无 pytest——离线兜底 `python3 tests/test_l2_bb2.py` 直跑 4 项全过，pytest 兼容保留）。既有 13 场景回归（seed=1000+code 逐场景复跑）：全部 CONFIRMED 无回归。补充产物：bb2 组 30 run 入 runs/20261012_full/bb2（30/30 CONFIRMED）；analysis_weights_sigma.py（权重六配置 Kendall τ≥0.963、零歼灭 0 违例、T4 攻击点分布、A_min 两级陈述分布 A/B 各 n=400）＋make_figures.py（4 图入 latex/figures/）＋report.md §7。
   - **7f** ✅（2026-10-15）：**审稿修复双改**（SPEC 先行：SPEC_estimators 升 v0.4——§5 A_epi 精度化＋E12.1/E9.2 的 δ* M4 项 ⌈(r+1)/2⌉c₀/W＋E14.4 估计器换日志直读精度；SPEC_platform §5-M4/P9.4/P9.6①、SPEC_experiments 升 v0.4——ATK-2①④⑤/ATK-4① 判据口径同步）。**δ* M4 项**：`dynamics.delta_star` 第三项 r·c₀/W → ⌈(r+1)/2⌉·c₀/W（r 浮点传入取 int(round)）；r∈{1,2} 数值不变、r=3 的 FORCE-1 臂 min 绑定项不变（0.25），test_l1_dynamics/test_l1_deleg_blackbox 零改动通过。**A_epi 精度化**：`components.truth_A_epi_real(model, T, bucket_map)` 单模型签名（ESZ 联合边缘化出 (E,B)，逐步 accuracy=P(B_t=κ(E_t))）；`truth_A_epi_rob` 加 bucket_map 参数（sup 语义不变）；`wiring.derive_bucket_map`（env0⇒`env0.bucket_map`／n_E=n_B⇒恒等／否则 raise）；`truth_bundle` 逐模型求真值（基线因观测噪声 <1），Â_phen 的 a_epi 槽取参照轨精度（基线 AI=0 精确保持）；`estimators.estimate_epi_accuracy` 取代 `estimate_b_tv`。测试适配：T-EPI 三锚（确定性 fixture 下精度=1−s 精确，数值不变）、T-COV γ 行（γ 臂精度严格低于基线）、T-T1a 扫描、T-C0（z1=1.0/z2=0.5 锚不变）、X-ENV0 基线锚改 0.810997748751（REPL 实测复核）、T-EST-EPI 改命中率对照。**登记 REFUTED（SPEC_experiments §8）**：ATK-4 C1 第三轨"说服臂 A_epi 不降"翻转——α 臂信念核对正交诚实信息（i≡e mod 2=u）的 response=2.0 倾斜使位置桶精度 0.810998→0.795180（−0.0158），非实现缺陷（真值路径精确）；C2/C3 保持 CONFIRMED。回归锚钉于 test_XATK4 与 X-MATRIX-SMOKE（只允许 ATK-4 登记行的 REFUTED）。**结案（2026-10-16，R4 决策）**：根因=α 说服臂探针内容错位在正交坐标（i≡e mod 2=u，与位置桶近似独立），粗粒信念核把正交内容误投位置桶——场景操作化缺陷（说服臂注册语义为'被测坐标上的诚实信息'），非理论反例、非实现缺陷、非判据编辑。修复：ATK-4 的 α 臂改显式 q_signal（i=κ(e)、fidelity 0.9），判据阈值未动；修复后 REPL 验证三判据全 CONFIRMED，登记例外自 test_XATK4/X-MATRIX-SMOKE 退役（恢复 REFUTED 零容忍），矩阵重跑（runs/20261015_full）main=2520 CONFIRMED+360 INCONCLUSIVE+0 REFUTED。套件 104 项全绿（93s）。
   - **7g** ✅（2026-10-17）：**R5-P3 仿真包**（SPEC 先行：SPEC_platform 升 v0.2——包络字段 κ_eff/R_eff＋n_O 观测基数泛化＋utility_tables；SPEC_estimators 升 v0.5——§7 扩展 A_via=min{1,min_k s_k/s_k^crit, min_j m_j}、§7.1 u_bar 外部基线；SPEC_experiments 升 v0.5——场景码 15 σ⁻-EROSION/16 EXEC-1、DEL-1 ⑤⑥ f>0/ρ≠1 臂、§8 P3 分析包 X1–X4、4560→4620；红→绿，11 项新增通过，累计 115 项）。**实现**：`env0`（包络字段＋n_O=4 支持＋效用表）、`wiring`（扩展 a_via＋Bundle 登记 u_bar）、`scenarios`（scenario_erosion/scenario_exec1/DEL-1 新臂/ATK-4 逐臂束）、`run_matrix`（+erosion/exec1 组）、`analysis_p3.py`（E2/E5 后验包）、`make_report` §7.4＋`make_figures` fig_p3_gate_exec.pdf（英文标签，与既有图风格一致）。**默认配置数值零漂移**（a_obj=0.374477、a_exec=0.017101 回归锚逐位一致；v1 配置 m_j=1）。**判据登记修正两条（按 §0.3/§8 证伪纪律登记，判据设计错误非理论反例）**：①X1 原"a_obj↔u_bar 同向 τ≥0.8"被实测推翻（γ 下 u_bar 微升而 A 塌缩，τ=−1）→ 三态判据（concordant ATK-1 τ=+1.0000（720/720 系列）／discordant ATK-2 τ=−1.0000、600/720 系列最强臂 A 降≥20% 而 u_bar 不降／blind σ⁻-EROSION u_bar 逐点不变 range=0 而 A∈[0,0.3745] 全程）；归因判别力 1,644 臂对。②X2 原 drop-one 权重归一化份额产生负份额伪影 → X2a log 域归因份额（几何聚合下精确可加：ATK-1 goal 0.590/ref 0.414；ATK-2 exec 0.756/epi 0.068/ref 0.175；ATK-4 org 0.800/ref 0.209；ATK-5 ref 1.000；EXEC-1 exec 0.910/epi 0.090；零歼灭臂 180/360/0/0/30 单列）＋X2b 冻结单通道归因模糊化（五通道各在 ≥1 战役破坏唯一归因；冻结 exec 使 δ 呈 σ⁻ 空通道签名——通道级不可区分、闸门可分）。**元判据③扩展（M9.6 v0.5）**：盲见证表升五类全集 {β_G:{goal,ref}, γ:{epi,exec,ref}, β_π:{org,ref}, τ:{ref}, δ:{exec}}——建设期发现：β_π 升全通道扫描后 a_ref 在四类签名中"全覆盖"致 C3=False（回归即发现），δ 类入表（EXEC-1 臂束，make_report 合并 main+exec1 传入）后交集=∅，必要性断言在五类上成立；X-META 测试同步强化（五签名内容锚＋交集空断言）。**全矩阵重跑 runs/20261017_full**：4,620 run（main 2880：2520 CONFIRMED+360 INCONCLUSIVE（M9.3 窗口外 cell）+0 REFUTED；stress 1440：1260+180+0；独立 10 组 300/300 CONFIRMED）。**X3/X4**：备选聚合对照——ATK-1 η=1 臂 A_arith 均值 0.5216（几何精确 0），"无归因而亡"反例 570 束；臂序 τ：arith/quad=1.0000、min 均值 0.4082（min 破坏序）；X4 Faith 逐行 9,390/9,390（100%：ATK-1 2880、ATK-2 2160、ATK-4 1440、ATK-5 2880、EXEC-1 链 30）。T1a 元判据① 7,290 束零违例；T5 330/330；T7 180/180。估计路径五分量两路径 abs_err≤0.0096。权重六配置 Kendall τ∈[0.930,1.000]（5,760 主臂；ATK-4 臂束入池后 min 由 0.963 移至 0.9304，论文摘要与 §8 已同步）。DEL-1 ⑤⑥：f=0.6706/0.8440/0.7992、φ=231.2/290.9/275.5、A_org^truth 0.00302/0.00171/0.00109 vs H1' 0.7/0.5/0.3，φ-松弛夹逼全含（φ_max=477.8）。EXEC-1：A_exec 0.0171→0.2340（13.7×），δ 链 0.2340>0.2178>0（精确），复合 0.6473>0.6372>0。套件 115 项全绿（102s）。
   - **7h** 🔲（2026-10-22）：**R8 构造效度敏感性臂平台前提**（SPEC 先行：SPEC_platform 升 v0.3——P2.4 κ 细化感知派生／P3.2 endorse_step／P9.3 桶先验与植入目标通用化；SPEC_experiments 升 v0.6——§8 X5 臂协议）。红→绿目标（T-REF×7，`tests/test_l2_refinement.py`）：①κ 派生逐点还原锚（默认档与 EXEC-1 档 [0,0,0,0,1,1,1,1]；细化档 [0,0,1,1,2,2,3,3]；退化档全 0）；②桶先验 p_e 与策略张量在默认/EXEC-1 配置下与 v0.2 内联旧式逐点一致（测试内复现旧式对照）；③endorse_step 表式锚（step=1 默认表 [1,1,1,2]；step=2 粗化表 [1,1,1,1]；细化网格 n_θ=7/θ*=2 表 [1,2,2,2,3,3,4]）；④植入目标通用化（默认网格 →3 逐点还原；n_θ=7/θ*=2 →6）；⑤退化档 A_epi≡1 见证（n_B=1 下 γ 全强度精度恒等）；⑥细化档 ATK-2 A_epi 对 s(γ) 严格降（x-b 证伪器预检）。⑦（执行期发现增补）A_goal 数值裁剪契约：细化网格档 η=1 的浮点残差（u_idx=12.000000000000005 → a_goal=−6.7e-16）触发复合层分量越界——沿 di.truth_A_org 的 E3 约定在 truth_A_goal 加 1e-9 容差裁剪（更大越界不静默），T-REF7 钉死（SPEC_estimators E4.5 v0.6 补注）。既有 115 项零改动回归＋analysis_exec1_weights.py 数值零漂移。

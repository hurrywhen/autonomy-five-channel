# SPEC_experiments —— R3c 实验规约（场景库／矩阵／verdict 判据／理论覆盖矩阵）

**版本**: v1.1（2026-11-17）｜**依据**: input v2.1 §4、§6；附录 §13.3、§7–§8、§10。
**v1.0 → v1.1 变更**（R15 审稿反例与报告治理）：①执行改恰好 n 行动并加两比特反例，T1a 同步；②撤回 T2 兼容 iff/四轨充要和普遍盲性，新增基线 Lambda<1、诚实信息改变 Fix 与行动无关证人；③L0 限内部因果，L1+ 新增规范/创新/外部流分解及纯随机负控制；④A_goal 分结构读取和 IRL 集合识别，补不动点定理前提；⑤V_state/R_def/A_state/A_res 分账，输出强制 provenance 字段及 unknown 上限；⑥C2 改 s>δ+s_c，Route B 改商锥 pointedness 与显式权向量归一；⑦新增 Ingel 2022、Albantakis 2021、Jung 2011 实质对照，创新定位限组合与审计纪律；⑧X5-c 正文写 480,000 cell evaluations/120,000 base draws，C0 写全权重，SESOI/error 比 1.0417 不作领域意义宣称；⑨新增 `analysis_r15_statistics.json`，Kendall tau-b 显式 ties/分场景，历史权重脚本和 JSON 不改写；新增 `analysis_r15_x5c_paired.json`，共享 X/Z/J 时改逐上下文配对差 SE，R14 的 unpaired combined_se 仅留旧档；⑩新增 14 个确定性 R15 负控制，全套目标 194 项。历史 R14 X5-c/C0/R11/R13/4,620-run 文件只读；独立基质、外部 SESOI/power、selector-conditional DEL-1、不可变 R15 tag/version DOI 仍未完成。
**v0.9 → v1.0 变更**（R14 反例与 estimand 复审；先登记、后实现、后看 X5-c outcome）：①T1b 增 L2 的 \(\Lambda_{ref}>0\)；T2/T3 的 \(\beta_\pi\) 严格性改为 \(F_{ext}/F_{int}\) 相对基线严格上升（固定 \(F_{int}\) 仅为充分特款），严格复合下降要求 \(A^0>0\)；\(\beta_G\) 改同一协议下 \(d^1>d^0\)，不再由“离开 Fix”或手术史标签推出；②线性—分数损伤按攻击者最小化对数复合量处理，凹函数在单线性预算多面体上的最小值可在极点取得，删除“凹故内点且分散”的错误句，新增顶点枚举、数值网格与符号 KKT/边界证书；③\(A_{ref}\) 的 \(\theta_\pi\) 与 \(M\) 限定为协议构造的有限离散系综，连续微分熵比 \(I/h\) 被明确排除；AX6a 改为有界归一化坐标及规范性的比例解释，不再宣称各通道比例尺度已获测量论证明；④\(\Lambda\) 唯一 estimand 为共享外生噪声下的实际/无手术**背书输出律反事实偏离**，篡改史另记 \(\mathcal H^{surg}\)，两者不得互推；旧 `law_level_lambda` 全部降称 legacy marker，不作为公式 (3) 实现；新增显式 SCM 的 abduction–action–prediction 模块与 X5-c 高斯/logistic 两噪声臂；⑤Lemma 37 用互信息链式法则及外生无反馈条件，T4(ii) 重写 funded/unfunded 与 ties，T5 脚本推论增完整状态/独立噪声受控前提，Via-Ind 不再被说成乘法门或几何聚合的推导；⑥C0 删除 Feng 角色的一般 lambda 排序一致性，C0-CORR 仅为作者自定义解释的描述统计；⑦证据表将数学状态、判据 outcome、证据类型和外部验证分列，撤销以“14/15 confirmed/zero-refutation”作为宣传汇总；历史 CONFIRMED 字段不改写；⑧统一分量 \([0,1]\) 浮点边界容差，超容差仍 fail-closed；⑨新增 R14 反例自动测试、确定性数学分析包及独立 X5-c manifest/results/verdict，全部写入新目录，历史 4,620-run、R11 replay 与 R13 材料不回写。外部独立基质验证、外部 SESOI/power、selector-conditional DEL-1 估计器和最终公开 release/version DOI 仍为未完成事项。
**v0.8 → v0.9 变更**（R13 核心命题与账本复审）：①T6 在只有 \(\dot D\le\delta-\kappa D\) 时收缩为 **certificate-failure band**，不再推出 \(D\to1\)；ATK-6③的俘获只保留为额外精确截断饱和律 \(\dot D=\delta-\kappa D\) 的 ENV-0 实现观察，历史键名不改；②C0(ii) 删除三个外部框架“完整画像相同”，仅保留指定被动行为相同、非退化 L1 的 \(A_{epi}\) 复合分离与 \(\Lambda\) 额外审计分离；③主表 T6 拆为 360 次裕度/实现 CONFIRMED 与 60 次 CUSUM DESCRIPTIVE，原 420=ATK-6①–⑤ 300＋ATK-5② 60＋ATK-6⑥ 60；④增加 DEL-1 六判据逐项账本；⑤公开 30 个 CUSUM 种子比值并补 Student-\(t_{29}\) 敏感性区间；⑥M4 改纯确定性恢复前提、注册域方向纠正、一般 \(A_{ref}\) 的 CP 区间限独立 Bernoulli 单位，run 内相关事件用 cluster/block 方法；⑦独立数学复核补 T6 的 $A_{via}^{min}$ pointwise 因子与 $A_j^{base}>0$（H4$''$），M1 保持结论限正常响应且逐周期损伤低于俘获阈，T1d 加注册坐标敏感退化族，C0 证人明确公平二值/独立信念与非退化背书反事实 TV=1；⑧报告生成器默认合并独立 R11 DEL-1 replay，并默认输出 `sim/reports/` 而非历史根目录；⑨C0-DEMO 的 $1-s(\gamma)$ 仅为历史 Λ 标记，当前非退化逐时 TV=1 仅为解析证人，未由旧场景执行。历史 v0.8 及更早运行与 manifest 不回写。
**v0.7 → v0.8 变更**（R12 定理量词与单调性复审）：①检测命题改为固定 \(\delta>0\)、\(\alpha\downarrow0\) 的 Gaussian Lorden–Lai 渐近；ATK-6⑥保留为固定 \(\alpha=10^{-3}\) 的特定 CUSUM 数值观察，不再声称复测原全称弱漂移命题，补充常数停止反例；②T7(iv) 拆为结构中介与附加诚实、sound update、无精度损失及其他通道不变下的无损失；③T8(ii) 改逐参数方向：降低 \(\theta\) 不降反升 \(\delta^*\) 的旧句废止，提高 \(r\) 不保证式 \(A_{min}\) 上升；FORCE-1③仅支持其注册的 \(\kappa\)-improvement 臂，M4 保留下界另式处理；④检测比值区间明确为每种子里程比均值的正态近似 95% CI，非 Student-t/bootstrap、非路径配对区间。历史 v0.7 运行与 manifest 不回写。
**v0.6 → v0.7 变更**（R11 数学复审）：①DEL-1⑤⑥旧单-φ松弛判据登记为**理论推导错误、判据 superseded**，改双误差 \((u,v)\) 端点优化；误差主导时区间可为 \([0,1]\)，此时 verdict=INCONCLUSIVE（非诊断），不得写 bracket confirmed；②BB-1②的被动 \(A_{exec}^{obs}\ge A_{exec}\) 降为 ENV-0 实例观察，一般方向未识别，仅独立探针保留条件方向；③确定性重放不再使用 Clopper–Pearson 下限或“n=30 power statement”，每判据分列独立随机种子、确定性配置、重复与嵌套 bundle；④E2-X1 原判据失败与后验替换、X5-a 已触发证伪器、X5-c 未运行必须随主表同步披露；⑤主表重评价为 14 CONFIRMED＋T7 INCONCLUSIVE，历史 20261017 manifest 不回写，映射见 `CRITERION_VERSION_MAP.md`。
**v0.5 → v0.6 变更**（R8 审稿包，SPEC-first）：新增 §8 分析包 **X5 构造效度敏感性臂**（x-a 背书量化四档重跑 ATK-1＋解析极限闭式校验；x-b κ 细化三档重评分 ATK-2 网格；x-c 保持注册未运行）——平台前提（κ 细化感知派生/endorse_step/植入目标通用化/桶先验规则）随 SPEC_platform v0.3 落地，默认与 EXEC-1 配置逐点还原 v0.2（回归钉 T-REF×7）。
**v0.4 → v0.5 变更**（审稿 P3 包，SPEC-first）：①场景库新增 **code 15 σ⁻-EROSION**（能力包络侵蚀——D-via 扩展闸门的 m_j<1 域实证：闸门必要性见证＋共模归零＋m=1 回归锚）与 **code 16 EXEC-1**（A_exec 富耦合动态范围臂：n_O=4 细观察＋低噪 ⇒ A_exec 脱离近零钉死区，δ 坍缩链复核 T5-exec）；②DEL-1 新增判据⑤⑥（T7 夹逼界**非退化**数值检验：f>0 臂——旗标熵进入 F_ext 真值路径（Jensen 间隙），线性律失效、φ-松弛双侧夹逼含真值；ρ≠1 臂——C_del=1.5·C_self 标定档）；③新增 §8 分析包 **E2**（外部基线 u_bar 序相关／通道数消融 drop-one／备选聚合算术-min-二次对照）与 **E5**（Faith 逐行严格单调核验）——均为后验重算（分量束 σ-无关真值，M9.4），不增仿真 run；④矩阵独立组 +2（erosion/exec1 各 30 run），总 run 数 4560→**4620**；⑤A_via 扩展公式随 SPEC_platform v0.2/SPEC_estimators v0.5 落地（配置默认 m=1 ⇒ v1 全部数值不变）。
**v0.3 → v0.4 变更**: 审稿修复同步——ATK-2①④⑤ 与 ATK-4① 的 A_epi 判据改精度口径（反事实位移/绝对阈值 0.5 废止，改基线相对窗口与"γ 臂严格低于基线"）；δ* M4 项随 SPEC_estimators E12.1 修为 $\lceil(r+1)/2\rceil c_0/W$（ATK-5/ATK-6/FORCE-1 数值不变：r∈{1,2} 时 ⌈(r+1)/2⌉=r，FORCE-1 的 r=3 臂 min 绑定项不变）。
**v0.2 → v0.3 变更**: 新增 §9 矩阵执行层接口（M9.1 统一调用约定／M9.2 σ 透传口径／M9.3 防御臂判据窗口口径（INCONCLUSIVE=窗口外，非 REFUTED）／M9.4 分量束缓存性能约定／M9.5 产出物 schema／M9.6 元判据操作化／M9.7 cell 聚合与防御方向断言）——R3c 第 7c 子步规约先行。
**v0.1 → v0.2 变更**: 按"实验-理论完整性审计"修订——①场景注册表重构：每场景显式登记**目的**与**论文命题对应**；②新增 RES-1（T5 可行性断供项）、FORCE-1（T8）、BB-1（黑盒降级）、C0-CORR（C0 投影一致性）四场景；③加强 ATK-1（Λ 操作化）、ATK-2（T3b 单调性/预警提前量/T1d/T4 防御侧/脚本推论）、ATK-6（A_min 逐 run 核对）判据；④新增矩阵级元判据（§3.5）与**理论-实验覆盖矩阵**（§4）；⑤不覆盖项显式声明（§5）。

---

## 0. 实验设计原则：论文命题如何被支撑

**P0.1 命题清单的枚举规则**。须被支撑的论文命题 = input v2.1 的全部定理（T1a–d、T2–T8）＋命题化猜想（C0–C2）＋框架级主张（表示定理、干预分类完备性（命题 3.4）、分量良构性（命题 5.1–5.8）、双轨制与幻觉指数（§2.4）、可辨识性与黑盒降级（§5.2／附录 §10）、σ 敏感性义务（§3.4）、跨基质映射（§2.3））。R4 主打（input §9）：T2/T3/T6＋C0。

**P0.2 三条支撑渠道**（每个命题至少一条，§4 矩阵逐行登记）：
- **EXP（仿真实验）**：场景库 run，产出 verdict——用于关于动力学、攻防、测量的**经验性命题**（T3–T8、C0–C2、T1d、黑盒规则）；
- **WIT（L1 数值见证）**：SPEC_tests.md L1 定理性质测试——用于**纯数学命题**（表示定理、引理 2.3.1/2.4.1、Kramer 反例、分量良构性），不需要"实验"但需要防回归见证；
- **LIT（文献三角验证）**：人类侧已发表实证（[ryan_deci2000][nouwens2020][maier_seligman2016]）的定性对照——用于人类侧对应物，标注非仿真产出。

**P0.3 判据纪律**。verdict ∈ {CONFIRMED, REFUTED, INCONCLUSIVE}；判据=证伪窗口的实测化。**不得通过静默改判据消除 REFUTED**。若数据查看后确需修正判据设计，必须保留原失败、查看时间、修改理由与版本映射，并将新判据标为 post hoc；数学推导错误导致判据失效时标 superseded/INCONCLUSIVE，不把旧 CONFIRMED 当作新定理证据（§8 流程与 `CRITERION_VERSION_MAP.md`）。

---

## 1. 场景库注册表

**总览**（code 即 SPEC_platform P6.2 的 scenario_code）：

| code | 场景 | 目的（一句话） | 验证的论文命题 |
|---|---|---|---|
| 1 | ATK-1 奖赏劫持/塑形 | 验证目标通道被渐变植入时的分级削减与幻觉出现 | T3(a)、T5-goal、AX3(Λ)、§2.4(AI) |
| 2 | ATK-2 信息茧房/检索投毒 | 验证认知通道操纵的检测归属、幻觉单调律、攻防博弈结构 | T3(a)(b)、T4（攻防双侧）、T2（盲见证）、T1d、T5 脚本推论 |
| 3 | ATK-3 依赖注入/锁定 | 验证崩溃的相变与滞后动力学及无助鉴别器 | C1、C2、T5-exec |
| 4 | ATK-4 提示注入直达行为 | 历史四轨诊断与说服/劫持特例；R15 仅作 legacy，不作兼容充要判据 | T2（限缩）、T5-org |
| 5 | ATK-5 紧迫感操纵 | 验证反思通道的时间压缩失效与背书门参数 | T5-ref、T6（τ 单调性） |
| 6 | ATK-6 亚阈慢漂移 | **验证自主性裕度定理的全部定量结构（关键实验）** | **T6（主打）**、T1d |
| 7 | DEL-1 委托治理扫描 | 验证委托律的分量级线性形式与复合指数 | T7 |
| 8 | C0-DEMO 注入 vs 同文指令 | 演示行为剖面不可区分而自主性可区分 | C0（命题 8.1.2） |
| 9 | LH-1 习得性无助诱导（可选） | 人类侧机制对照：无助签名的双指标分离 | A_exec 语义（E8）、T5-exec |
| 10 | RES-1 资源断供/σ⁻（新增） | 补全 T5 第六析取：共模失效的闸门语义 | T5-via、T1b（反向）、σ± 分类 |
| 11 | FORCE-1 强制"自主"（新增） | 检验直接目标/行动强制与注册 $\kappa$-improvement 臂；不概括 $\sigma$ 联合提升下界 | T8 |
| 12 | BB-1 黑盒降级对照（新增） | 验证黑盒测量章节的区间界规则与不可辨识命题 | §5.2-5、附录 §10（命题 10.1–10.4） |
| 13 | C0-CORR 注册解释映射（历史键名保留） | KG/Dung 作者自定义标签的描述性核对；无 Feng 可执行映射 | C0（命题 8.1.1）、input §6.3 次结果 |
| 14 | BB-2 自适应对手臂 | §10.2 外生探针区间适用域边界的实证演示 | 附录 §10.2/§10.3（黑盒降级适用域） |
| 15 | σ⁻-EROSION 能力包络侵蚀（v0.5 新增） | D-via 扩展闸门 m_j<1 域：闸门必要性见证＋共模归零＋m=1 回归 | T5-via（扩展式）、D-via（修订）、T1b |
| 16 | EXEC-1 富耦合臂（v0.5 新增） | A_exec 动态范围：细观察＋低噪下脱离近零钉死区；δ 坍缩链 | T5-exec、命题 5.6、论文局限段回应 |

**逐场景判据**（verdict=CONFIRMED 当且仅当全部成立；除标注外均在 30 种子上按 §3 统计）：

**ATK-1（β_G 渐变，扫塑形强度 η）**
① $A_{goal}$ 随 η 单调分级削减（部分俘获区间 $0<A_{goal}<1$ 存在——E6 语义）；② η 达最大疏离时 $A_{goal}\to0$（$d\to d_c$）；③ 复合 $A$ 严格降（ceteris paribus，T3(a)）；④ 隐蔽档（TV≤ε(θ)）$\mathrm{AI}>0$ 出现；⑤ **legacy marker 自洽检查**：旧场景 `lam==1-eta_eff`，只证明标签映射可重放；不计算反事实背书律，不存在 $A_{goal}^{hist}=\Lambda A_{goal}$ 的代码或当前公式。R14 X5-c 是另一独立 SCM 证据包，不升级本项。

**ATK-2（γ，扫过滤强度 φ；含亚阈档与 (K) 假设档）**
① $A_{epi}^{real}$ 随 φ 降（精度轨迹，2026-10-15 精度化口径：自基线精度水平起单调降）；② **γ 盲见证（R15 限缩）**：仅在 $F_{oth}/F_{src}$ 保持不变的注册证人模型中 $A_{org}$ 不动；零 $F_{ext}$ 本身不是 R15 盲性证明；③ **T3(b) 描述边界**：旧代码只记录 AI 序列与预警窗口，未计算 $\mathbb E_\gamma[\hat A]-A^\gamma\ge g(s)$ 或 $\Pr_\gamma(AHI>0)\ge g(s)$，故不得写成期望界/触发概率界已执行验证；实际差距单调增只列 ENV-0 平台观察；④ **预警功能**：$\mathrm{AI}>0$ 先于深度俘获出现——操作化档：$A_{epi}$ 低于基线但尚未深度俘获（落于基线相对窗口，边界按实测精度-强度曲线登记入代码注释），报告预警提前量分布（§2.4 幻觉检测器的操作化）；⑤ **T1d**：存在亚阈档——登记不触发（功效 ≤α+ε）而 γ 臂 $A_{epi}$ 严格低于基线精度；⑥ T4 攻击侧：成本参数面扫描中攻击者首选 $\arg\max w_is_i/c_i$ 通道；⑦ **T4 防御侧**：equalization 注水配置的最弱环节指标优于非均衡配置（min-max 预言）；⑧ （K-full 假设档）**脚本推论**：仅在完整决策时状态（含 $M,R$ 与直接 $O$ 父节点）可重构且独立噪声受控时，行为-脚本平均 TV ≤ν+η；旧 ATK-2 仅是友好 full-state fixture，不能支持只控制 $B,O$ 的弱化版。

**ATK-3（δ＋时间，扫退出成本增长率 ρ）**
① EWS 三指标（$T_{rec}$、方差、AR(1)）临界前兆可测；② $T_{rec}$ 拟合 $(\delta_c-\delta)^{-1/2}$（报 R²）；③ 滞后回环：崩溃阈 $\delta_{down}$ 与恢复阈 $s_c$ 独立为正（回环不闭合）；④ 无助鉴别器：$\mathcal E^{env}$ 完好而 $\mathcal E^\Pi\to0$；⑤ 全程 $A$ 与 $\mathcal E^\Pi$ 同步退化（T5-exec 的方向性）。

**ATK-4（α 伪 β，扫注入成功率）**
① **历史四轨诊断（R15 退役为兼容判据）**：旧说服臂记录 $F_{ext}=0$∧legacy marker=1∧$A_{epi}$ 不降∧$\mathcal E^\Pi$ 不降，劫持臂至少一轨破；这些只作旧场景重放，legacy marker 不作反事实证据，也不再将四轨称为兼容的充分/必要可观测化。当前兼容判定须按 T2 的逐分量定义与非退化结构充分证书另评；② 成功注入的严格 $A_{org}$ 下降须 $F_{oth}^1/F_{src}^1>F_{oth}^0/F_{src}^0$（固定 $F_{src}$ 且 $F_{oth}$ 增加仅为充分特款）；③ 两分类器对比只保留为历史单轨/多轨操作性演示，不覆盖目标、反思、资源或 $0/0$ 边界。

**ATK-5（γ：τ 压缩，扫决策时限）**
① τ 缩短 ⇒ $A_{ref}$ 降（背书一致性因子失效）；② 门控修复率 $\iota/\tau$ 与实测裕度单调关系方向正确（命题 7.6.7）；③ 极限档（τ→0）$A_{ref}\to0$（T5-ref 析取项）。

**ATK-6（β 亚阈恒漂，扫漂移速率 δ；T6 关键实验）**
① **条件设计规则**：$\theta/W\le\kappa$ 时，$\delta<\theta/W$ 由 M3 给 $\limsup D\le\delta/\kappa<1$，$\delta\ge\theta/W$ 进入 M1 注册域；M1 分支的非俘获/正保持另需正常响应且 $\theta+\ell\delta$ 低于俘获阈，ATK-6 的 <0.99 仅是满足这些注册条件的测试网格实现，不作任意 $\delta$ 全称保证；② **A_min 逐 run 核对**：实测 $A(t)\ge A_{min}$ 公式值（定理 7.6.3(iii)，H2 换算常数由标定期拟合）；③ **v0.9 双层口径**：一般上比较 $\dot D\le\delta-\kappa D$ 在 $\theta/W>\kappa$、$\delta\in(\kappa,\theta/W)$ 只给 **certificate-failure band**（M3-only 正保持证书失效），$D\equiv0$ 是合法反模型，不得推出俘获；ATK-6 另行采用精确截断饱和律 $\dot D=\delta-\kappa D$，该实现的零登记与 $D\to1$ 是 ENV-0 观察，历史键 `C3_blind_zone_capture` 仅为兼容保留；④ **δ\* 消融**：关闭 M1/M3/M4 任一，实测 $\delta^*$ 坍缩到对应项（min 三项结构）；⑤ **登记域**：$\delta\ge\theta/W$ 时周期损伤 $\le\theta+\ell\delta$，提高 $\theta$ 会缩小该域而非扩大覆盖；⑥ **v0.9 高斯 CUSUM 描述臂**：固定 $\alpha=10^{-3}$，对 $\delta:0.25\to0.125$ 的特定 LLR-CUSUM 记录 $\delta\cdot EDD$ 比值；这是 ENV-0 数值观察，不是固定 $\delta>0$、$\alpha\downarrow0$ 定理的直接检验，更不是固定 $\alpha$、$\delta\downarrow0$ 全称命题的证据。每种子分别用 200 条路径估计两档 EDD，再形成同种子比 $R_s$；报 30 个 $R_s$ 的均值、$1.96s_R/\sqrt{30}$ 正态近似半宽及 $t_{29,0.975}s_R/\sqrt{30}$ 小样本敏感性半宽。两档路径不是共同随机数路径对；30 个原始比值、种子和来源哈希由 `analysis_cusum_sensitivity.py` 只读重算至 `analysis_cusum_sensitivity.json`。主表计数分账：①–⑤＋ATK-5②=360 次 CONFIRMED 实现评估；⑥=60 次 DESCRIPTIVE 评估（30 个不同种子、两个 $\sigma$ 复制）。

**DEL-1（委托混合 $(1-m)\pi_{self}+m\pi_{del}$，λ/q 网格）**
① H1' 标定档：selector-conditional 估计量满足 $A_{org}=A_{org}^{self}(1-\lambda(1-q))$ 容差内；**v0.8 估计量定义**：逐步当前 selector 条件化 $\sum_t I(S^t;A_t\mid A^{t-1},\mu_t)$ 与 $\sum_t I(I^t;A_t\mid A^{t-1},S^t,\mu_t)$，不自动等同完整历史 $\mu^t$ 条件化；**v0.7 边界**：legacy 未条件化流的近线性拟合只作 ENV-0 描述，不验证精确律（记录 selector≠对 selector 条件化）；② 非 H1' 零松弛代数档：夹逼界 $[\rho_{min},\rho_{max}]$ 成立；③ 复合拟合 $A=A_{self}(1-\lambda(1-q))^{w_{org}}$，$w_{org}$ 自由参数为正（确定性拟合不作显著性声明）；④ $q=1$ 臂 $F_{ext}=0$（R12 仅指结构中介/零 bypass flow；无诚实、sound update、无精度损失及其他通道不变前提时，不断言全复合 $A=A_{self}$）；⑤ **f>0 臂（v0.5 新增；v0.7 双误差修正）**：保留 (a) $f>0$ 与 (b) 实测 $A_{org}^{truth}$ 低于 H1' 拟合的描述判据。令 $a=1-m$、$\varphi_0=f/C_{self}$、$\eta_\mu=h(m)/C_{self}$，修正区间为 $[L,U]$：$L=(a-\eta_\mu)_+/[(a-\eta_\mu)_++m\rho_{max}+\varphi_0+\eta_\mu]$，$U=(a+\eta_\mu)/[a+\eta_\mu+(m\rho_{min}+\varphi_0-\eta_\mu)_+]$。只已知 $\varphi_0\in[\varphi_-,\varphi_+]$ 时 L 用 $\varphi_+$、U 用 $\varphi_-$。区间不含真值=REFUTED；区间退化（宽 ≥1−容差）=INCONCLUSIVE（非诊断）；非退化且包含且 (a)(b) 成立=CONFIRMED；⑥ **ρ≠1 臂（v0.5 新增；v0.7 同式修正）**：$C_{del}=1.5\,C_{self}$，按⑤同一双误差规则判定，不再使用旧单-φ端点。

**σ⁻-EROSION（code 15，能力包络侵蚀，扫侵蚀率 ε；v0.5 新增）**
① **m=1 回归锚**：ε=0 臂（默认包络）$m=1$ 且 $A_{via}$ 逐点等于资源型旧式 $\min(1,\bar z_{high}/s_{crit})$（v1 数值不变的场景级复核）；② **单调侵蚀**：κ 绑定域（ε>0.5）$A_{via}$ 随 ε 严格降，裕度域（ε≤0.5）恒 1（min 结构＋clip 语义）；③ **共模归零**：ε=1（或 R 独臂 $R_{eff}=0$）⇒ $A_{via}=0$ ⇒ $A=0$（T5-via 扩展式析取项——能力包络崩溃与资源断供同为闸门事件）；④ **闸门必要性见证**：全部五通道分量＋legacy marker 跨臂逐点不变（≤1e-12）——纯 σ⁻ 侵蚀对通道监测器**不可见**，唯闸门捕获（与 RES-1 互证：闸门独立于通道簇、通道簇盲于闸门）；该 ENV-0 未计算当前反事实 $\Lambda$。

**EXEC-1（code 16，富耦合 A_exec 动态范围臂；v0.5 新增）**
① **动态范围**：富耦合配置（n_O=4 位置精报＋obs_noise=0.05）基线 $A_{exec}\ge\max(0.15,\ 5\times A_{exec}^{v1})$（v1 紧凑实例把 A_exec 钉在近零（≈0.017）的局限回应——耦合富化后分量脱离钉死区）；② **δ 坍缩链**：δ 手术支撑收缩（保移动类 ⊃ 保非移动类）给出 $A_{exec}^{rich}>A_{exec}^{mv}>A_{exec}^{nm}=0$ 严格链（非移动支撑 {harvest,idle,exit} 信道行恒等 ⇒ ℰ^Π=0 精确——无助签名，命题 5.6(ii)）；③ 复合序同步（T5-exec 方向性）。

**C0-DEMO（R13：历史实现与当前解析证人分账）**
① **可执行历史实现的证据范围**：委托人同文指令臂与 γ 隐蔽注入臂的指定被动行为分布逐点一致（TV≈0），$A_{epi}^{real}$ 为 1 vs 0.5；在非退化 L1、$A(Z_1)>0$ 且其他适用因子固定时，该精度差可代数推出 $A(Z_2)=A(Z_1)0.5^{w_{epi}}<A(Z_1)$。只比较协议指定的被动行为摘要，不声称 KG/Dung/Feng 在 C0(i) 下的完整画像相同。② **Lambda 仅为历史标记**：场景的 `law_level_lambda` 实际返回 $1-s(\gamma)$，不计算实际/无手术反事实背书律，不得用于支持当前 TV=1 证人。③ **当前解析证人（未由 C0-DEMO 执行）**：$Z_1$ 取常量真桶与忠实信念，$Z_2$ 取公平二值真桶及独立钉住信念，故精度为 1 vs 0.5；另取非空手术史与非退化背书过程，使实际/无手术反事实背书律逐时 TV=1，由 AX3 定义给 $\Lambda=0$（空史 $Z_1$ 为 1），作 composite-silent provenance 分离。不得使用会触发 $\Agoal$ 回退的退化 $\Endorse\equiv\mathrm{id}$，也不得仅凭 situation-independent 或 covert 标签推数值。当前 C0 的 150/150 只覆盖行为/Aepi/注册映射与旧标记实现判据，不表示已运行反事实 TV 证人。

**LH-1（可选；δ＋不可控噪声，扫不可控时长）**
① 无助签名双指标分离（$\mathcal E^{env}$ 完好、$\mathcal E^\Pi\to0$）；② 移除诱导后 $\mathcal E^\Pi$ 恢复迟滞（与 [maier_seligman2016] 机制定性对照）。

**RES-1（σ⁻ 资源攻击，扫 Z 流削减率；新增）**
① $A_{via}\to0$ ⇒ $A=0$ **独立于其余通道状态**（共模失效/闸门语义，T5-via 析取项）；② T1b 反向：$A_{via}=0$ ⇒ $A=0$；③ σ⁺ 恢复 ⇒ $A$ 恢复（可行性通道与通道簇的因果分离）；④ 完备性登记：σ⁻ 作为"σ 的反面"经 $A_{via}$ 进入（input §2.2 (d) 项的场景化）。

**FORCE-1（强制悖论；三臂：β_G 植入"要自主"目标／δ 强制训练／σ 脚手架对照；新增）**
① β_G 臂：先检查 $A^0>0$ 且同一协议下 $d^1>d^0$，ceteris paribus 短期 $A$ 严格降；旧 lam=1−η_eff 仅为 legacy marker，不得由未经内生背书直接推当前 $\Lambda<1$（无显式 SCM 时为 N/A）；零基线不作严格下降证据；② δ 臂：同样要求 $A^0>0$ 且 $\mathcal E^\Pi$ 降 ⇒ $A$ 严格降；③ **注册的 $\kappa$-improvement 臂**：$\kappa:0.2\to0.3$ 跨过 binding 边界（$r:2\to3$ 不改变 $k=\lceil(r+1)/2\rceil=2$ 或冗余项），本臂 $\delta^*$ 与 $A_{min}$ 上升且即期 $A$ 不降；不得推广为降低 $\theta$ 或提高 $r$ 也使两者同升。$\theta/r$ 反例由 T-R12-T8 回归，M4 覆盖下的 $D\to0$ 使用独立 M4-aware floor；④ 与 SDT 控制性手段文献 [ryan_deci2000] 仅作 qualitative triangulation（LIT 渠道标注），不称 T8 的 empirical counterpart。

**BB-1（黑盒降级对照；同配置白盒/黑盒双观测模式；新增）**
① 黑盒 $A_{org}$ 条件认证上界（附录 §10.2 公式）不被白盒真值违反（参考下端不作认证区间）；② **v0.7**：被动 $A_{exec}^{obs}>A_{exec}$ 仅登记为 ENV-0 实例观察，不作普遍单侧界；独立探针 $A\perp S$ 下 $I(A;O)\le I(A;O|S)$ 为条件方向，其余被动协议报“方向未识别”；③ **旧不可识别构造的历史 marker 边界**：内生背书 vs 植入背书两构造下，指定黑盒泛函的分布统计不可区分，旧 lam 只能报标记/区间；当前非退化不可识别命题由 R14 identity/XOR 输出律证人支持，不能由旧 marker 升级；④ 区间宽度报告（信息量评估：宽度随基线期长度与 η 的依赖）——论文黑盒测量章节的证据包。

**C0-CORR（R14 restricted descriptive mappings；历史键名保留）**
① 代码实际只操作化 KG/Dung 作者自定义标签，没有 Feng 可执行映射；② 标签与同公式分量/复合值的序一致性仅为描述统计（Kendall τ），不是外部构念验证；③ 不声称 Feng 一般 rank consistency，consultant 相比 collaborator 可给 agent 更多规划/执行责任，旧 mid→low $\lambda$ 方向不保持源等级；④ 与 C0-DEMO/新 C0-CF 分账，不把行为摘要相等升级为完整映射画像相等，不称 projection、special case 或严格更一般性。

---

## 2. 实验矩阵

- **主矩阵**：ATK-1~6 × 防御 $2^3$（登记 M1／检查点 M2／冗余 M4）× σ∈{0.5,1}（**仅 σ=1 为全公理主 case；σ=0.5 为 AX6b 松弛敏感性**）× 30 种子 = **2880 run**；σ=2 压力测试单列 1440 run（只报"AX5 松弛后哪些结论翻转"，不混合）。
- **独立实验组**：DEL-1（λ×q 网格＋f>0/ρ≠1 臂×30）、C0-DEMO（双臂×30）、C0-CORR（≥96 配置×30）、RES-1（削减率×30）、FORCE-1（3 臂×强度×30）、BB-1（2 模式×场景子集×30）、BB-2（外生/自适应×30）、LH-1（可选）、**σ⁻-EROSION（ε 网格×30，v0.5）、EXEC-1（富耦合臂×30，v0.5）**——独立组合计 300 run，全矩阵总计 **4620 run**。
- **config_code**：防御组合 0–7（位序=M1/M2/M4）；σ 档并入场景参数。

## 3. 统计与报告协议

- **P3.1（v0.9 抽样单位；沿用 v0.7 纪律）**：仅真正随机的独立单元给抽样区间，并预登记备择效应、噪声模型、显著性水平与抽样单位。确定性真值重放只报精确值/配置数/重复数，独立随机试验数记 0，不给 Clopper–Pearson 下限或功效声明。每判据分别报告独立随机种子数、确定性配置数、重复数和嵌套 bundle 数；同一计算跨 σ 或 defense 的复制不新增独立种子。单调/命中比例若来自确定性重放，仅作实现检查，不作二项推断。一般 $A_{ref}$ 协议的 CP 区间只用于具有共同事件概率的独立 Bernoulli 事件；同一 run 内相关事件以 run/cluster 为抽样单位采用 cluster/block 方法，无合法独立或簇模型时只报计数与描述比例。
- **P3.2 主结果**：每定理 verdict 表（T1a–d、T2–T8、C0–C2）＋证伪窗口逐条对照。
- **P3.3 次结果**：C0 数值一致性（C0-CORR＋C0-DEMO＋新 C0-CF）；T4 只在 σ=1 下作定理 verdict，σ≠1 不作 CES 内点 KKT 证据；人类侧三角验证定性对照表（LIT 标注）。
- **P3.4 报告章节模板**：每定理一节（陈述→判据→verdict→证据→偏差源）；专节：certificate-failure band 与精确实现消融、C0、黑盒降级、敏感性。T6 的 360 裕度/实现评估与 60 CUSUM 描述评估分列；DEL-1 按六判据逐项给出 30-run 账本。
- **P3.5 矩阵级元判据**（跨场景聚合，入 verdict 表附栏）：
  ① **T1a 全域**：全部 run $0\le A\le1$（零违例）；② **T5 零因子一致性重放**：全部 run 中 $A<\epsilon$ ⇒ 六析取至少一项归零；不是全状态空间完备性或脚本推论证明；③ **T2 多通道必要性**：跨场景统计无任何单一分量检出全部攻击类（盲见证表）；④ **σ 稳健性**：主带 σ∈[0.5,1] 内全部 CONFIRMED verdict 不翻转。

---

## 4. 理论-实验覆盖矩阵（完整性审计结论）

| 论文命题 | 出处 | 渠道 | 载体 | 覆盖 |
|---|---|---|---|---|
| AX0–AX6 公理一致性 | input §3.2 | WIT＋构造 | T-AX0、平台构造（H-0/AX1 自动） | ✅ |
| 表示定理（含 AX6b、调和反例） | §3.4／附录 §6 | WIT | T-REP1/2、T-SIGMA | ✅（纯数学，无需实验） |
| 干预分类完备性（命题 3.4） | §2.2 | 构造＋WIT | T-COV＋场景映射审计（每干预唯一归类） | ✅ |
| 分量良构性（命题 5.1–5.8） | §3.3 | WIT | T-ORG/GOAL/EXEC/EPI/REF | ✅ |
| T1a 范围 | §4 | WIT＋EXP 元判据 | T-T1a＋P3.5① | ✅ |
| T1b 运行正性 | §4 | WIT＋EXP 边界 | T-R14-T1B；RES-1②仅闸门反例 | ✅ 新解析回归（L2 显式含 $\Lambda_{ref}>0$；RES-1 不是全正性测试） |
| T1c 条件严格上界 | §4 | EXP | 基线配置扫描（D1–D4 各档分量<1），入报告附栏 | ✅ |
| T1d 不可检测操纵存在 | §4 | WIT＋EXP | T-T1d＋ATK-2⑤ | ✅ |
| **T2 覆盖定理＋多通道必要性（主打）** | §4 | EXP＋WIT | T-R14-ORG＋ATK-4/ATK-2 特例＋T-MED/T-COV | ✅ 相对 $\Fext/\Fint$ 严格性；旧有利特例不作全称证据 |
| **T3(a) 条件操纵严格下降（主打）** | §4 | EXP＋WIT | T-R14-ORG/GOAL＋ATK-1/2/FORCE-1 特例 | ✅ $A^0>0$、外内比/距离等前提；标签不直接推出 |
| **T3(b) 注册下界 $g(s)$ 增长（主打）** | §4 | 解析＋描述 | 证明；ATK-2③④只给 AI 平台曲线 | ⚠️ 期望/触发概率界未执行，旧曲线不得冒充 |
| T4 最高杠杆与线性—分数边界 | §4 | WIT＋EXP | `analysis_r14_math` 顶点/网格/符号证书＋ATK-2⑥⑦ | ✅ σ=1 LinLog＋R14 最小化；旧 σ≠1 重复不作 KKT 验证 |
| T5 点值六析取＋full-state 脚本 | §4 | WIT＋EXP＋元判据 | 几何零因子回归＋T-R14-PROOF 正反控制＋ATK-2⑧ 友好 fixture | ✅ 点值域/完整状态；元判据仅零因子一致性重放 |
| **T6 裕度（主打）** | §4 | EXP＋WIT | ATK-6①–⑤＋ATK-5②＋T-T6a/b；③一般命题仅为 certificate-failure band，精确实现俘获另列 | ✅ 360 裕度/实现评估；ATK-6⑥ 另为 60 次 DESCRIPTIVE，不作检测渐近统计确认 |
| T7 委托律 | §4 | EXP | DEL-1①–④＋⑤⑥（v0.7 双误差；ENV-0 区间退化） | ⚠️ INCONCLUSIVE（120 CONFIRMED＋60 INCONCLUSIVE） |
| T8 受限强制一致性与逐参数方向 | §4 | EXP＋LIT | FORCE-1①–④（③仅注册 $\kappa$ 臂；LIT 仅定性三角） | ✅ |
| **C0（主打）** | §1.5 | WIT＋构造 | 新 `c0cf_v2` 同环境全轨迹 $(E^T,O^T,A^T)$＋identity/XOR；C0-CORR 仅描述 | ✅ 同环境构造检查；旧 C0-DEMO marker 不升级；不作 Feng 一般排序或外部验证 |
| C1 相变／C2 滞后 | §4.1 | EXP＋WIT | ATK-3①–③＋T-C1/T-C2 | ✅（随机版→§5 声明） |
| 双轨制与幻觉指数 AI | §2.4 | EXP | ATK-1④、ATK-2③④ | ✅ |
| 黑盒降级与命题 10.4 | §5.2／附录 §10 | EXP＋WIT | BB-1①–④＋T-BB/T-BB2＋BB-2 | ✅（v0.1 仅 WIT，已补实验） |
| D-via 扩展闸门（m_j 域） | §3（修订） | EXP＋WIT | σ⁻-EROSION①–④＋T-AVIA-ENV | ✅（v0.5 新增） |
| A_exec 动态范围（局限回应） | §3.3/§9.4 | EXP | EXEC-1①–③ | ✅（v0.5 新增） |
| 外部效度/消融/聚合稳健（E2） | §8（修订） | 后验分析 | analysis_p3.py X1/X2/X3（u_bar 序相关、drop-one、备选聚合） | ✅（v0.5 新增） |
| Faith 逐行核验（E5） | §6（假设 (Faith)） | 后验分析 | analysis_p3.py X4（逐 (config,σ,rep) 行严格单调） | ✅（v0.5 新增） |
| σ 敏感性义务 | §3.4 | EXP 结构 | 矩阵 σ 臂＋P3.5④ | ✅ |
| 跨基质映射（§2.3） | 综述 §6.4-6 | — | **不覆盖（R3d 另立项）** | ⚠️ §5 声明 |
| 人类侧机制对应 | 综述 §4 | LIT | 三角验证对照表（非仿真产出） | ⚠️ 仅定性，§5 声明 |

## 5. 不覆盖声明（写入实验报告"局限"节）

1. **跨基质第二支柱**：本阶段仅表格离散基质；LLM 基质对接属 R3d（另立项），论文跨基质主张在本阶段只到"单基质全通道＋人类侧文献定性对照"。
2. **随机版定理**：T6 随机最优检测统一处理、C1 随机逃逸（Kramers/FW）属 R2.1 遗留，本阶段为确定性损伤动力学与玩具模型命题的验证。
3. **连续行动空间 empowerment**：参考测度协议属 R2.1-5；本环境全离散。
4. **copula 参数辨识**：嵌套 CES 估计协议与 R3 联动（R2.1-3），本阶段仅 (Via-Ind) 成立域。
5. **人类侧**：仅文献三角定性对照，不产出新人类被试数据。

## 6. 产出物

`runs/<date>_<matrix_id>/`：NDJSON 日志（SPEC_platform §8）＋`manifest.json`＋`results.csv`＋`report.md`（§3.4 模板）。`autonomy-bench` 以场景注册表（§1 总览 code 1–16）为公开接口。

## 7. 完成判据（R3 done）

全矩阵＋独立组跑通；§4 覆盖矩阵每行 verdict 落定（✅ 行无空缺）；REFUTED 项（若有）全部按 §8 登记分析。

## 8. 证伪纪律（REFUTED 处理流程）

1. 冻结该 cell 配置与日志；2. report.md 登记 REFUTED 与初步归因（实现缺陷／估计偏差／理论反例）；3. 排除实现与估计因素后仍成立的，**上报为 input 修订事项**（不得通过改判据或调参消除）。

---

## 9. 矩阵执行层接口（`matrix.py`，R3c 第 7c 子步）

**M9.1 统一调用约定**。矩阵层以统一签名调用场景库：`SCENARIOS[code](defense=(m1,m2,m4), sigma=σ, seed=seed, **grid_kwargs)`。全部 13 个场景函数接受 `defense`/`sigma`/`seed` 三个关键字参数（默认 `(0,0,0)`/`1.0`/`None`，默认值保持 L2 冒烟语义不变）；语义惰性场景（无复合量的 ATK-5、C0-DEMO、LH-1、BB-1 的 σ；P9.5 v1 无耦合规则的 ATK-3~6 的 defense）接收但忽略，并在 docstring 标注。`config_code = 4·m1+2·m2+m4`（位序 M1/M2/M4，§2）；`seed = rng.derive_seed(scenario_code, config_code, rep)`（P6.2）。seed 注入含采样部分的场景（ATK-3 EWS 噪声、ATK-6 CUSUM/A_min 抽查、C0-DEMO TV 检验）；纯真值场景 rep 行间数值相同（确定性），P3.1 cell 统计的 CI 宽度退化为 0——这是真值模式的口径特性而非数据缺失。

**M9.2 σ 透传口径**。σ 只经聚合函数进入：`wiring.truth_bundle(..., sigma=σ)` 与场景内直接 `composite_A`/`dynamics.a_min` 调用（a_min 与复核用 composite_A 必须同 σ——F_σ 单调性 (A4) 保持逐点界，σ 臂下 A_min 核对同式成立）。分量真值计算（DI/信道/联合表）σ-无关。DEL-1③ 复合恒等式为 σ=1 特款（推论 7.7.3 的几何结构），σ≠1 臂属压力测试语义（主矩阵 σ 臂仅 ATK-1~6，§2）。

**M9.3 防御臂判据窗口口径**。攻击物理判据的证伪窗口以**防御压缩后强度**（η_eff/s_eff，P9.5）解读：压缩使窗口条件不可达的判据记 **INCONCLUSIVE（窗口外）**，不记 REFUTED（P0.3——窗口外无观测，非证伪）。v1 实例：ATK-1②（η=1 完全俘获归零）窗口=`η_eff 末端档 ≥1−1e-9`。防御有效性的矩阵级断言不借攻击判据，而由 M9.7 的方向断言独立承担。

**M9.4 分量束缓存（性能约定）**。`wiring.truth_bundle` 设内容寻址 LRU 缓存：键=（模型规范化哈希， T, 基线模型哈希或 None, 权向量）（**不含 σ**——缓存对象为 σ-无关分量元组（含 phen 轨分量），σ 相关量 a_obj/a_phen/ai 由缓存分量即时复合，σ 臂由此共享分量缓存），规范化哈希=`sha1(json.dumps(model.to_dict(), sort_keys=True, default=张量哈希))` 全 hex（覆盖 params＋内核内容；ndarray 经内容哈希兜底——与 logschema.config_hash 同式但含非 JSON 类型兜底）；容量 128（分量元组为 9 浮点，内存可忽略）。语义=确定性函数的精确记忆化（指纹内容寻址，原地变异安全）；矩阵的 rep/σ 重复 cell 由此摊销。`logschema.make_metadata` 的 config_hash 同步加 ndarray 兜底（干预模型 params 含脚本张量）；`graph.model_content_hash` 为统一哈希入口，`di` 的真值标量（truth_F_int/truth_F_ext/truth_A_org）同式记忆化（容量 512）——矩阵 rep/σ 重复 cell 的 DI 重算由此摊销。

**M9.5 产出物 schema（冒烟与批处理共用）**。`run_matrix(scenarios, defenses, sigmas, reps, out_dir=None, grids=None) -> rows`；`grids` 按 code 覆盖场景臂网格（冒烟缩网格 `SMOKE_GRIDS`，批处理 None=注册表默认全网格）。每行：`{scenario_code, name, config_code, m1, m2, m4, sigma, rep, seed, overall, verdicts, metrics}`。`write_outputs(rows, out_dir)` 落盘四件：
- `results.csv`：固定列（scenario_code/name/config_code/m1/m2/m4/sigma/rep/seed/overall）＋判据列 `V:<name>`（并集，缺失留空）＋`metrics_json`（numpy 标量/元组经 default 转换）；
- `verdict_table.csv`：cell 聚合（M9.7）；
- `manifest.json`：矩阵级 `{type:"matrix_manifest", spec_version, matrix_id, created, git_commit, grid, seed_rule:"P6.2", n_runs}`；run 级 config_hash 由 NDJSON 日志层携带（场景内部多模型，矩阵层不重复计算）；
- `logs/`：抽样 NDJSON——每 (scenario_code, config_code) 首 rep 一条基线 env0 模型小日志（T=3、n_traj=4，经 `logschema.validate_log` 零错误），证明 P8 日志契约链路在矩阵层活着；干预模型全量日志属批处理（7d）。

**M9.6 元判据 `xmeta_check(rows)`（P3.5 冒烟操作化）**。输入 run 行，返回四判据字典＋细节：
- ① **全域 [0,1]**：递归扫描 metrics 中全部登记束（含六分量键 `a_org/a_goal/a_exec/a_epi/a_ref/a_via` 的字典——ATK-1/2 逐臂 `rows[].bundle`、ATK-3/5 基线束 `bundle_base`、ATK-4 γ 对照束 `bundle_gamma`、RES-1/FORCE-1 臂束）＋`a_obj/a_phen/lam`，全部 ∈[−1e-9, 1+1e-9]（`ai` 为差值，不在值域断言内）。ATK-6 的 A_min/composite 中间量体检归 WIT（T-AX5/T-T6b），不入矩阵扫描。
- ② **零归因归零（T5 充要操作化）**：束内 `a_obj<1e-6` ⇒ 六分量 min<1e-3（数量级容差；精确定量属报告）。
- ③ **多通道必要性（盲见证表）**：攻击类检出记录——ATK-1 逐臂（类 β_G）与 ATK-2 逐臂（类 γ）以同 cell 首臂（η=0/s=0）为参照，分量降 >0.01 记检出；ATK-4 逐臂束全通道扫描记 β_π 类（v0.5 起 rows 登记 bundle——Λ=旗标自方份额 ⇒ a_ref 随委托深度降，签名 {a_org, a_ref}；此前手工 a_org 单列废止）；ATK-5 解析行 a_ref 单列记 τ 类；EXEC-1 臂束（rich 为参照）记 δ 类（δ 签名入表 ⇒ a_ref 不再"全覆盖"，必要性断言在五类全集上成立）。断言：出现的攻击类 ≥2 且无任何单一分量检出全部攻击类。覆盖输入=主矩阵＋EXEC-1 独立组（make_report 合并传入）。
- ④ **σ 稳健**：同 (scenario_code, config_code) cell 内 σ∈{0.5,1} 两臂 overall verdict 一致（单 σ 运行时 vacuously true 并标注）。

**M9.7 cell 聚合与防御方向断言（P3.1 冒烟版）**。cell=(scenario_code, config_code, σ)：cell_overall=全部 rep overall 一致取该值，混合 ⇒ INCONCLUSIVE；逐判据报 CONFIRMED 比例。**防御方向断言**：对 P9.5 有耦合规则的场景（v1：ATK-1/ATK-2），同 σ 同 rep 下防御臂末端攻击档的 `a_obj` ≥ 无防御臂 −1e-9（损伤不更深）；无耦合规则场景记 N/A。数值指标的均值±95%CI（n=2 冒烟仅供参考；n=30 批处理正式）随 verdict 表输出。

---

## 8. 补充实验（2026-10-13 登记，v0.4 增篇）

**BB-2（scenario 14，自适应对手臂）**。目的：§10.2 外生探针区间适用域（"非对抗性影响"）的边界实证演示。臂A=外生对照（iid 旗标 × state-independent 收获脚本 0.8/0.05×4，p∈{0.1,0.2}）区间含真值 2/2；臂B=自适应时机（`BetaPiSpec.flag_by_state`：S 的目标分量 G=θ* 时以 p∈{0.3,0.5,0.8} 注入，否则不注入）——朴素外生插值 F̂=p̄·H(脚本)·T 系统性高估 F_ext（bias=+0.168/+0.394/+0.899），区间（η=0.3）三档全失含（真值 a_org=0.24/0.33/0.61 vs 区间上界 ≤0.01）。产出：独立组 bb2（30 run，30/30 CONFIRMED）；测试 T-BB2×4。

**后验敏感性（analysis_weights_sigma.py）**。主矩阵逐臂分量束为 σ-无关真值（M9.4）⇒ 复合层可任意重算，无需重新仿真。权重六配置（等权基准＋org/goal/exec/epi 偏重＋goal 极端）：值域零违例、Kendall τ(vs 等权) ∈ [0.9633, 0.9986]、T3a 单调零违例、零歼灭 n=120 臂零违例；T4 攻击点 argmax 分布量化（等权→epi 480/480；org 偏重→org/epi 各 240）；A_min 两级陈述：场景分布（κ∈[0.6,1]）κ 绑定 0/400（与批仿真一致，A_min>0 恒成立），加宽分布（κ∈[0.1,0.4]）κ 绑定 156/400 且恰在这些配置 A_min=0（旧式 (11) 退化显形），未绑定点态界恒 >0。σ 扩展带 {0.25,0.5,0.75,1}：值域/单调/零歼灭全部保持（σ<1 时 ATK-1 η=1 档精确 0）；σ=2 对照档 0.1817（AX5 失效回声）。

**数据图（make_figures.py → latex/figures/）**。fig_ews_c1（T_rec 标度斜率 −0.5039 vs 理论 −0.5＋OU 前兆 30 种子带）、fig_t6_blindzone（(δ,κ) 平面三区相图＋ATK-6 锚点）、fig_t7_delegation（线性律 max_dev=2.0e−5＋复合律）、fig_ahi（A_obj 降/Â_phen 平/AHI 增长，s(γ) 网格）。

**P3 分析包（2026-10-17 登记，v0.5 增篇；analysis_p3.py —— 后验重算，不增仿真 run）**

- **E2-X1 外部效度（u_bar）**：u_bar（SPEC_estimators §7.1）随全部 ENV-0 臂束落盘。**判据登记修正（v0.5 补注，按 §0.3 判据纪律登记）**：原登记判据"a_obj↔u_bar 同向 Kendall τ≥0.8"在数据前夜检中被实测推翻——γ 类攻击下 u_bar 微升而 A 塌缩（τ=−1）；归因=**判据设计错误**（未预见"操纵可具功能愉悦性"：信息茧房均匀化信念反而降低移动成本），非理论反例；修正为**三态存在性**判据——①concordant：ATK-1（β_G）逐 (config,σ,rep) 系列 τ≥0.9（目标俘获同时损伤 θ* 效用）；②discordant：ATK-2（γ）最强臂 A 相对降≥20%（全防御档实测 46–100%）而 u_bar 不降（自主性不是即时效用的代理）；③blind：σ⁻-EROSION u_bar 跨臂逐点不变（≤1e-9）而 A 全程塌缩（≥0.3）。附：归因判别力——|Δu_bar|≤0.02 且 |ΔA|≤0.05 而通道剖面 L1≥0.3 的跨场景臂对计数。
- **E2-X2 通道消融（判决级双口径）**。**判据登记修正（v0.5 补注，同上）**：原登记"drop-one 权重归一化信号份额≥0.3"产生归一化负份额伪影（去通道后权重重归一放大其余通道相对变动），且几何聚合的 log 域本有精确可加分解——修正为两个无伪影口径：**X2a log 域归因份额**（ln(A₀/A)=Σⱼ wⱼ ln(xⱼ⁰/xⱼ)，Σⱼ share=1 精确——公理强制形式使归因分解成为规范量；零歼灭臂 log 损伤无穷单列）——判据：org/goal/exec/ref 各在 ≥1 战役占最大份额，epi 幅度份额如实报告（其必要性在归因层）；**X2b 冻结单通道归因模糊化**——每战役最强臂响应集（相对降>1e-3）对注册签名表 {β_G:{goal,ref}, γ:{epi,exec,ref}, β_π:{org,ref}, δ:{exec}, σ⁻:{}(gate-only)} 唯一匹配，冻结通道 j 后真类不再唯一识别（误归他类或无可归；例：冻结 exec 使 δ 锁定呈现 σ⁻ 资源断供签名）——判据：五通道各在 ≥1 战役触发误归/漏检（T5 必要性条款在准确性层面的经验伴随）。
- **E2-X3 备选聚合对照**：算术/最小/二次均值（等权）重算全部臂束——报告 (a) 零歼灭失效量化：ATK-1 η=1 臂 A_arith>0（几何精确 0）；(b) 臂序 Kendall τ（vs 几何基准）；(c) "通道归零而 A>0"的无归因臂计数（T5 充要性在备选聚合下的反例数）。结论预期：公理强制几何形，备选聚合以登记方式改变 verdict（论文 §3.4 唯一性主张的经验注脚）。
- **E5-X4 Faith 逐行核验**：对具逐臂束/解析行的战役网格（ATK-1 η_eff→a_goal；ATK-2 s_eff→a_epi；ATK-4 p→a_org；ATK-5 τ→a_ref）逐 (config,σ,rep) 行核验目标分量沿有效强度单调不逆行（等强度对剔除），严格下降份额另报（量化平台非违例）；EXEC-1 δ 坍缩链并入。判据：单调确认率 100%（真值模式精确）——(Faith) 假设在 ENV-0 的逐行成立性登记（论文 §6 假设条目的证据栏）。ATK-3/6 的 Faith 内容为动力学层（T-C1/C2、T6 设计规则），由各自场景判据与 L1 见证覆盖。

**X5 构造效度敏感性臂（2026-10-22 登记并执行，v0.6 增篇；analysis_sensitivity_arms.py —— 平台前提见 SPEC_platform v0.3）**。对应论文 §8 threats (x) 的前两臂注册（x-a 背书量化网格、x-b 认知粗粒化 κ）——审稿 R8-1 指出两臂在现有平台计算成本低，应直接运行；第三臂（x-c Λ 反事实模型）保持注册未运行。

- **X5-a 背书图量化细化（ATK-1 重跑）**。档位：coarse（endorse_step=2，同 4 点网格、地板平台加倍 ⇒ Endorse 常值化于 θ* 的单步吸收）、default（v0.2 表式，逐点还原）、fine（n_θ=7，k=2 索引细化，效用表相邻 canonical 行线性插值——插值为本臂登记建模选择；A_goal 读数纯由 G 链决定、与策略无关，插值不混杂目标通道结论）、finest（n_θ=13，k=4）。植入目标按 P9.3 通用化规则取最大疏离端点。每档跑满 ATK-1 判据组（C1–C5）×8 防御配置。**证伪器（按 threats (x-a) 注册文本）**：verdict 翻转，或 dc-归一 A_goal 读数在细化方向超出注册容差——容差在本臂执行时显式定为两把注册标尺：SESOI 0.01（绝对）与 5%（相对，T7 标定带同型）；粗化方向偏移单列报告（量化 κ_grid 登记义务的非空洞性）。**解析参照**：细化极限（连续收缩 c=0.5）的平稳解闭式 A_goal^∞(η)=1−2η/(1+η)，默认网格读数与极限的间隙闭式 η(1−η)²/(2(1+η))≤0.057——数值档须以几何速率收敛到该闭式（校验）。
- **X5-b κ 粗粒化细化（ATK-2 网格重评分）**。档位：degenerate（n_B=1，κ≡0 ⇒ A_epi≡1 构造性无信息——仅边界见证，不入 verdict 注册表）、default（n_B=2,n_O=2 半环，v0.2 逐点还原）、fine（n_B=n_O=4 位置精确——κ 分辨率的可观测上限，u 不被观察）。每档对 s(γ)∈{0,0.3,0.6,1.0}×8 防御配置计算真值束的 A_epi。**证伪器（按 threats (x-b) 注册文本）**：细化下 A_epi 对 s(γ) 的响应非单调或变号。κ 档位间基线水平漂移（细化 ⇒ 精度任务变难 ⇒ 基线下降）如实报告——即 (eq:aepi) 的敏感性报告义务本身。
- **产出**：analysis_sensitivity_arms.json（机读归档）＋论文 threats (x) 改写（两臂已运行、结果与后果；x-c 保持注册）＋§8.5 补充分析段。**回归钉**：平台通用化（κ 派生/桶先验/植入目标/endorse_step）对默认与 EXEC-1 配置逐点还原 v0.2——analysis_exec1_weights.py 重跑数值不变＋新增测试 T-REF×7（SPEC_tests §7）。

---

## 10. R14 数学反例、线性—分数攻击与 X5-c 预注册（2026-11-16）

### 10.1 必须自动钉住的反例

`tests/test_l1_r14_counterexamples.py` 至少编码下列解析锚，不得以场景 overall verdict 代替：
1. \(f_1,f_2>0\) 且其余 T1b 条件为正，但 \(\Lambda_{ref}=0\Rightarrow A_{ref}=A=0\)；修正后 L2 正性显式要求该因子为正。
2. \((F_{int},F_{ext})=(0.1,1)\to(1,0.1)\) 使 \(A_{org}:1/11\to10/11\)，故事后 \(F_{ext}>0\) 不蕴含下降；严格下降判据为 \(F'_{ext}/F'_{int}>F_{ext}/F_{int}\)（基线分母为正）。
3. \(d_c=1,d^0=0.8,d^1=0.1\) 使 \(A_{goal}:0.2\to0.9\)，故“均不在 Fix”不构成下降；零基线另钉 \(A^0=A^1=0\)。
4. 线性—分数例 \(w=(0.5,0.5),c=s=(1,1),B=0.5\)：集中点 \((0.5,0)\) 的目标值 \(0.5\log0.5=-0.346573590\)，分散点 \((0.25,0.25)\) 为 \(\log0.75=-0.287682072\)，前者更小。数值网格不得越过最优顶点；独立符号证书须核对 concavity Hessian、KKT 驻点非最小候选及全部预算极点。
5. 高斯连续反例 \(\theta\sim N(0,100),M=\theta+\varepsilon,\varepsilon\sim N(0,0.01)\) 独立：\(h(\theta)=3.7215236262,\ I=4.6052201835,\ I/h=1.2374555817>1\)；该例证明连续通用扩展被排除，而不是离散 \(A_{ref}\) 公式失效。
6. \(d/d_c\) 的尺度不变不等于 \(1-d/d_c\) 是比例尺度；等权两配置 \((0.9,0.2)\) 与 \((0.5,0.6)\) 在非比例幂变换 \((x_1,x_2)\mapsto(x_1^2,x_2)\) 后排序翻转。
7. 条件互信息可增加的构造、T4(ii) 单严格最大值与并列最大值、T5 未受控 \(M_t,R_t\) 或目标独立噪声的反例，以及 Via-Ind 成立但外部门权重/几何形式可任意指定的反例。
8. T3 分层量词：covert $\gamma$ 仅在 L1+ 的 $A_{epi}$ 适用时给复合下降，$\beta_{Endorse}$ 仅在 L2 的 $A_{ref}$ 适用时给复合下降；L0 无 $\gamma$ 复合分支，L0/L1 辅助背书 SCM 的恶化仍 composite-silent。

### 10.2 线性—分数优化器

新增轻量、stdlib+numpy 实现 `attack.py`：在 \(x_i\ge0,\sum c_ix_i\le B,0\le s_ix_i\le1\) 上求攻击者目标 \(J(x)=\sum w_i\log(1-s_ix_i)\) 的扩展实值最小值。理论候选为全部预算集中于可行通道 \(i\) 的极点 \(x_i=B/c_i\)，比较 \(w_i\log(1-s_iB/c_i)\)；若某通道达到零保持量则目标为 \(-\infty\)。实现返回全部并列最优极点与目标值。二维独立网格仅作交叉核验，网格本身不得被当作全局最优证明；符号证书以 \(J''_{ii}=-w_is_i^2/(1-s_ix_i)^2<0\) 和极点目标闭式给出。T4(i) 的 LinLog 集中结论与此分开陈述，T4(ii) 的防御等化仅在 $E>0$ 且唯一严格最大值在该点局部严格可降（responsive）时成立；连续非增本身不足，$\rho_1\equiv2,\rho_2\equiv1$ 的 split 反例说明平坦响应可容许唯一最大值最优。结论为必要而非充分条件；未资助通道可通过从零增加预算进入 active set，$\rho_i(0)\le R$ 只是最大值定义，非严格并列不声称唯一。

### 10.3 \(\Lambda\) 的 SCM、估计量与 legacy marker 隔离

R14 采用唯一的输出偏离 estimand。每个审计上下文先由事实观测进行 **abduction**，再在相同外生噪声下执行 **action**（移除全部注册手术），最后 **prediction** 得到实际与无手术背书输出律；对两律取 TV 并在上下文和审计时点平均。TV 是分布距离，不再由 TV=0 推“决策几乎必然相同”。另输出 \(\mathcal H^{surg}\in\{0,1\}\) 表示手术史是否非空；允许 \(\mathcal H^{surg}=1\) 且 \(\Lambda=1\)。不再设置“退化背书＋手术史则 \(\Lambda:=0\)”的认证例外。历史 `law_level_lambda` 仅保留只读 replay 兼容名，语义统一为 `legacy_marker_lambda`，旧场景及复合束不得冒充该 estimand 的验证。

独立 `counterfactual.py` 不伪装成 ENV-0 已具备的模块：ENV-0 缺少可 abduct 的背书结构方程与噪声记录。新模块只对其显式 SCM fixture 给出公式实现。

### 10.4 X5-c 两噪声模型执行协议（先看本规约，后运行）

**结构方程**。对独立审计上下文 \(t=1,2,3\)，观测
\[
X_t\sim\mathrm{Bernoulli}(0.5),\qquad Z_t=aX_t+bJ_t+U_t,
\]
其中 \(J_t\in\{0,1\}\) 为手术指示，\(a=0.35\)。另设共享下游决策噪声 \(V_t\)，背书输出 \(Y_t=\mathbf 1\{Z_t+V_t\ge0\}\)。事实 \((X_t,Z_t,J_t)\) 可精确 abduct \(U_t=Z_t-aX_t-bJ_t\)；action 令 \(J_t=0\) 得 \(Z_t^0=Z_t-bJ_t\)；prediction 在相同 \(U_t,V_t\) 下比较 \(Y_t\) 与 \(Y_t^0\) 的输出律。两噪声模型分别为 \(U_t,V_t\overset{iid}\sim N(0,1)\) 与独立标准 logistic。实际/反事实 Bernoulli 概率用相应 CDF 解析积分，TV=两概率绝对差；每个上下文只贡献一个 TV，非把蒙特卡洛决策对当成独立实验。

**注册臂**。两噪声模型均跑：no-surgery (\(J=0,b=1\))、history-without-output-effect (\(J=1,b=0\))、graded weak (\(J=1,b=0.35\))、graded strong (\(J=1,b=1.0\))。每臂使用 20,000 个上下文，种子分别为 910160（高斯）和 910161（logistic），按 `make_rng` 构造 PCG64；同一 noise×t 的四臂共用同一 base \(X,U\)（within-cell 独立、cross-arm common random numbers），故 arm evaluation 数不等于独立随机单位数；报 \(\Lambda\) 均值、TV 均值的 Monte-Carlo 标准误与描述性 95% 正态区间。样本量只控制数值积分误差，不是外部功效分析，也不新增独立基质验证。

**解析边界证人**。另有二值 XOR SCM：\(Y_t=U_t\oplus J_t\)，\(U_t\sim\mathrm{Bernoulli}(0.5)\)。\(J=1\) 时每个 abducted 上下文的实际与无手术输出为相反点质量，TV=1、\(\Lambda=0\)；\(J=0\) 时 \(\Lambda=1\)。跨上下文背书过程非退化，行为变量可独立固定。该证人用于非退化黑盒不可识别构造，不调用退化背书认证例外。

**判据（运行前冻结）**。
- C1 no-surgery 与 history-without-output-effect 在两噪声模型均 \(\Lambda=1\)（容差 \(10^{-12}\)，后者同时 \(\mathcal H^{surg}=1\)）；
- C2 两 graded 臂均 \(0<\Lambda<1\)，且同一噪声模型内 strong 的 \(\Lambda\le\) weak \(+10^{-12}\)；
- C3 跨噪声模型报告绝对读数差，不要求点值不变；若 weak/strong 的方向在任一模型翻转为 strong \(>\) weak \(+10^{-12}\)，证伪器触发；
- C4 XOR 边界分别为 0/1，且独立路径枚举复核相同；
- C5 以另一独立 Monte-Carlo 共享噪声路径（每噪声 4,000 上下文、种子 910162/910163）验证 graded-strong 的解析积分 TV，绝对差不超过 \(4\) 倍合并标准误或 \(0.02\) 的较宽者；这只是实现交叉核验。

**产出与状态**。新目录 `runs/20261116_r14/x5c/`：`preregistration.json`（本规约哈希与参数）、`manifest.json`、`results.csv`、`verdict_table.csv`、`analysis.json`。任何后续改判据都另标 post hoc；不回写旧 X5 JSON 的 x-c 状态为历史已运行，而是在 R14 增补记录。X5-c 只证明该 SCM fixture 的公式实现与噪声敏感性，不为 ATK-1、\(\beta_\pi\)、旧 \(A_{ref}\)、T2/T3 或 C0-DEMO 的 marker 结果背书。

### 10.5 数值边界与证据重签

所有分量在进入复合前经统一 `clip_unit_interval`：仅在 \([0,1]\) 外不超过 \(10^{-9}\) 时归位并记录 clipping；更大偏离、NaN、Inf 一律报错。新增退化粗粒化约 \(-4.49\times10^{-17}\) 的显式回归，不以“152 项通过”替代公开快照差异说明。R14 论文证据表不得把定义检查、同模型演示和外部验证合成一个 CONFIRMED 百分比；历史标签保留，修正定理另列“新解析证明＋R14 反例回归”，未覆盖新量词的旧 run 不自动升级为证据。

### 10.6 X5-c 时分层补充与同环境 C0 证人（首轮 outcome 后透明补登）

首轮 `runs/20261116_r14/x5c/` 已完成 pooled 两噪声实现检查，但运行记录没有逐 \(t\) 分解，且 C2/C3 的 strong≤weak 对任意单调 CDF 都是逐上下文恒等式，不能独立承担模型敏感性判据。首轮文件保留，不改写。 canonical 补充运行 `run_x5c_r14_stratified.py` 输出到新目录 `runs/20261116_r14/x5c_stratified/`：

1. 显式 \(T=3\)，每 noise×arm×t 用 20,000 个上下文；高斯种子 910170--172，logistic 910180--182，逐 t 和跨 t 同时报 \(\Lambda\)/TV/SE。同一 noise×t 的四臂共用 base \(X,U\)（within-cell 独立、cross-arm common random numbers），故 480,000 为 cell/context evaluations，而非 480,000 个全独立随机单位。strong 独立共享噪声复核在 \(t=2\) 用 4,000 上下文，上下文种子 910190/910191，下游种子各加 100。
2. **post hoc 协议澄清（在首轮 outcome 后登记，非预注册新证据）**：报告 \(D_{noise}=\max_{arm,t}|\Lambda_{gauss}-\Lambda_{logistic}|\)，SESOI=0.01。若超过，则点读数状态为 MODEL_SENSITIVE，论文只报双模型区间/带，不选单一噪声点值作稳定读数；不把此敏感性改写成实现 REFUTED，也不把 C2/C3 的恒等式方向当成噪声稳健性。
3. 增加观测等价对照：两模型均有非空手术史，identity \(Y=U\) 给 \(\Lambda=1\)，XOR \(Y=U\oplus1\) 给 \(\Lambda=0\)；二者事实 \(Y\) 均为公平二值，辅助被动行为均固定。XOR 接口必须从事实 \((Y,J)\) 执行 \(U=Y\oplus J\) 的 abduction，再 action/prediction，不得直接以已知 U 冒充溯因。
4. manifest 明确 estimand=`R14-output-law-v1`、审计观测 \((X,Z,J)\)（不额外条件化 Y）、T、每 t 上下文数、总上下文数、dirty/未冻结状态、surgery map、两个随机流与全部来源哈希。只有缺这些字段才 fail-closed；不能用旧 `matrix.py` 的 v0.9 writer 代替。

**首轮 C0-CF 的 supersession 警告（数学复核后）**。首轮 `c0cf/` 采用均匀策略、动作无关环境及单点目标空间，导致 AX0 内部流为零、执行 empowerment 为零及 $\Fix=\Theta$ 退化；其手工 illustrative 因子和复合数值不得使用，且 `truth_marginals` 仅比较逐时边缘而非全轨迹联合律。该目录仅作为反例保留。旧 C0-DEMO 仍不改写。当前有效证人改为 §10.7 的 `c0cf_v2`，旧目录不倒改。

### 10.7 C0-CF-v2 非退化同环境全轨迹证人（数学复核后重注册）

`run_c0cf_r14.py` 输出新目录 `runs/20261116_r14/c0cf_v2/`（2026-11-17 重跑），并记录 post hoc 修正原因。新 fixture 具备：二值非退化目标状态 $G\in\{0,1\}$，策略仅随 $G$ 变化且两行不同（0.8/0.2 vs 0.2/0.8），故 AX0 的 $F_{int}>0$；下一环境状态仅由动作决定，故两臂 empowerment 相同且为正；$\Fix=\{0\}$、$d_c=1$，不是 $\Fix=\Theta$ 的退化区间。两臂共享公平初始环境、$O=E$、均匀初始策略核、视界与 $\kappa$，仅信念更新分为忠实和独立钉住。代码必须从实际函子计算 $A_{org},A_{goal},A_{exec},A_{epi}$ 与复合，禁止手工指定 illustrative 分量。除逐时 $(E_t,O_t,A_t)$ 边缘外，另用隐状态求和的精确路径枚举比较完整 $(E^T,O^T,A^T)$ 联合律。判据增加正基线检查，报告实际通道与 $A(Z_1)=0.8312378961$、$A(Z_2)=0.7236346187$（$w_{epi}=0.2$，其他权重均分 0.8）。identity 与 XOR 两臂都实际执行 abduction–action–prediction，禁止硬编码 $\Lambda$。$A_{epi}=1$ vs 0.5、$\Lambda=1$ vs 0，完整轨迹相同且 $0<A(Z_2)<A(Z_1)$。首轮反例、失败序列化目录及本修正全部保留；新证据仍为构造性实现检查，不是外部构念验证。

# latex/ — R15 论文排版工作区

## 现有产出

| 文件 | 内容 | 状态 |
|---|---|---|
| `main.tex` + `sections/*.tex` + `appendix.tex` | R21 英文权威源：条件化诚实证书契约（份额条件复合采样区间＋conditioning_scope、覆盖语义分离、联合 bootstrap 补充诊断）、精确锚/诊断插件/报告区间并列表与分离覆盖检测研究、历史证据边界；R20 及更早文字仅作历史记录 | 当前 105 页、6 图、115 引用；最终验收以 `sim/runs/20261122_r21/validation.json` 为准 |
| `figures/fig_*.pdf` + TikZ 定理依赖图 | 共 6 幅图：5 个外部 PDF 数据图＋1 个 TikZ 图 | 历史数据图归档不改写；字体/Unicode 随 PDF 验收 |
| `related_work.tex` | Related Work＋直接前沿对照＋Ingel/Albantakis/Jung 实质比较＋经典前驱/新增内容表 | 全部 `\cite` 键对应分级核验文献；创新定位限组合与审计纪律 |
| `refs.bib` | 115 条参考文献库，115 条进入 `main.bbl`（见 `refs/manifest.md`） | 不再把库条目数误写成 PDF 引用数；全文/著录核验分级记录 |
| `SUBMISSION_MANIFEST.md` | 完整源树、构建命令与交付清单 | 投稿必须整树交付，不只上传 main.tex |

**PDF 完整性自查**（投稿前必跑，回应 zzxpaper6 必修 1）：见文末"投稿前 PDF 完整性自查"节。

## 期刊策略（综述 §7）

| 期刊 | 主打 | Related Work 伸缩标记 |
|---|---|---|
| *Minds and Machines* | T2/T3/C0 的哲学意义；争议一（历史性）、二（现象学）、四（程序 vs 实质）的回应 | `[MaM]` 注释处保留概念分析细节，压缩 §RW.4/§RW.5 工程段 |
| *Synthese* | 表示定理、可辨识性、双轨测量；争议六（测量范式）、七（黑盒可知性）的回应 | `[Syn]` 注释处保留测量方法学细节，压缩 §RW.1 哲学史铺陈 |

两刊均为 Springer Nature：模板用 `sn-jnl.cls`（Overleaf 项目 "Springer Nature LaTeX Template"，或
<https://www.springernature.com/gp/authors/campaigns/latex-author-support>）。获取 cls 后建 `main.tex`：

```latex
\documentclass[sn-mathphys-num,numbered]{sn-jnl}
\usepackage{natbib}
\begin{document}
\title{Autonomy as Determination by One's Own Normative Structure:
       A Five-Channel Measurement Framework with Axioms, Theorems,
       and a Simulation Benchmark}
% ... front matter ...
\input{related_work}
\bibliography{refs}
\bibliographystyle{sn-mathphys}   % 编号制; MaM 亦可用 sn-vancouver
\end{document}
```

## 引用完整性约定（重要）

1. **分级使用已核验文献**：早期 67 条全文/预览子集有本地 PDF（不进入公开快照）；后续条目可为出版社、DOI、官方摘要或预印本页著录核验，二者不得混称“全文已读”。证据登记于 `refs/manifest.md`；新增引用必须先补分级记录。
2. **脚注级转引白名单**（无开放 PDF，仅可脚注提及、不进 bib）：Mele 2008、Coons & Weber 2014、
   Deci et al. 1999、Williams 2018、Scheffer et al. 2009、Ebert & Welsch 2004、
   Marko 1973——见 `refs/manifest.md` §J 与 `docs/R2_文献待查证事项.md`。
3. ~~Kramer (2003)~~ **已解决**（2026-10-04）：作者 Bell Labs 主页自存档（Wayback）副本核验 PASS，
   已入 bib（`kramer2003`）。渠道规范见 `refs/manifest.md` §K-5。

## 修订记录

- 2026-10-12：论文初稿 v0.1（58 页）。
- 2026-10-13：**三审稿意见修订版**（50 页）。要点：
  - M1（审稿人1）：Lemma `lem:mediation` 与附录证明改用 Kramer 非预期条件（S^t），删除"两种约定逐字成立"断言；Kramer Property 2 印刷笔误改为带完整构造的脚注。
  - T6（审稿人3 T1）：A_min 两级陈述（点态界 + 一致界，κ 绑定如实退化）；Corollary 盲区 δ* 恢复 θ/W 项；(H4') Avia 下界显式化；M4 声明为建模假设；H2 无量纲化协议。
  - 宣称收敛：删 "derived, not chosen"/"no fifth way"/"why five channels is a theorem"/"previously unmade"/"miswriting" 痕迹；必要性改写为"仪器族的最小归因覆盖"；C0 降为"概念对应+构造性证人"。
  - 权重：承认"形式被推导、权重被选择"，给三选项协议 + 5 组权重后验敏感性（Kendall τ≥0.963）。
  - 黑盒：补 F_ext 与观测量偏差方向分析、非对抗适用域声明；新增 BB-2 自适应对手臂（30 run，3/3 失含演示）。
  - 基质定位（按作者指示）：动物=概念可能性；AI=benchmark 严格验证；人类=协议+文献三角+有限实验/在线数据路径。
  - §8 重新定位为 implementation-level consistency check；run/cell/bundle/criterion 口径表；fifteen；二项 CI；基线锚定段；确定性 truth 模式解释。
  - 格式：全部表格转 tabularx/resizebox（超宽清零）；技术附录编号（7.2.1 等 70+ 处）清除；记号表；\AI→\AHI、σ_n→s_n、κ_0→ν_0；lmodern+glyphtounicode（ligature 可提取）。
- 2026-10-15：**双审稿大修版 v0.2**（61 页）。对照两份新审稿意见（Major Revision）逐项处置，详见 `docs/R4_审稿回应_v1.md`。要点：
  - **致命级**：A_epi 重定义为"对真实环境的精度"（TV 对点质量 δ_{κ(E_t)}；修复 AX2/兼容性矛盾与 T5 语义方向）；Λ 手术史扩展为 β∪γ 并登记 MI 估计量在恒定史上的退化（全部 Λ 依赖定理标注白盒可检验）；推论（原 σ 容许域）更正为"全公理 ⟹ ς=1 单点，带均为公理松弛稳健性检查"；T4 损伤映射统一为对数线性（与仿真的 log 标定一致），(1−D) 映射下为内部注水（凹性），与 T6 一阶相容；T6 的 M4 冗余项更正为 ⌈(r+1)/2⌉c₀/W；T3b 常数一致化＋校准误差 η₀ 显式化。
  - **严重级**：分类学重写——α/γ 边界改结构判据（完好通道作为分量存活 vs o 律被改），E 律/转移核的 A→E 耦合手术归入 δ（行动杠杆位点），E 自主动力学注册为测量重实例化边界；AX7（双可分）/AX8（一次齐性）新公理＋规范性辩护＋AX6b 强于 KLST 意义性的登记；Route B 齐次延拓引理（(0,1]^n→R++^n）；门控声明更正为"除齐性外保全"；T7 的 (H1') 补 F_ext^self=0 前提＋源指示变量入图（H-0 合规）；β_π 下 IRL 失效的仪器无效声明；"最小归因覆盖"去"最小"。
  - **实验节**：表 1 增"类型"列（substantive/optimization/definitional/bound/construction/toy）；SESOI 注册段；truth/sample 口径声明；场景名标注"toy analogues"；计数更正（8=2³ 防御配置显式化、840=两类合计 420×2、4,320=主+压力、结论 4,560、T7 max dev 2.0×10⁻⁵）；确定性/统计量两类分报；A_exec 动态范围与 d_c=2.0/c=0.5 透明锚点；摘要与结论证据降级＋BB-2 提升为正面发现。
  - **文献**：refs.bib 67→103 条（26 条新核验，manifest §M；含 Lorden 1971 更正、Mele 2008 自 §J 升级、LOA 传统 Sheridan–Verplank/Parasuraman、Mazziotta–Pareto/BoD、Kamenica–Gentzkow、Orseau–Armstrong、Mohamed–Rezende、Kraskov/MINE、Goodhart、Kenton、Carroll、Hoel 因果涌现、Pearl/VanderWeele、Gorman、Kuratowski–Ryll-Nardzewski、Tchen/Müller–Stoyan、Kuznetsov、Aczél–Dhombres、Cover–Thomas）；LOA/Goodhart/因果涌现等进入综述正文；缺口总结改为分号化范围声明。
  - **规范**：全部孤立编号残留（6.5/E3、7.7.1、8.1.x、10.2–10.4、Risk R2/R5、R2.1、R3d、P6.2、meta-criterion、WIT、P-series）清除；修订史语言删除；符号去重（CES 弹性 σ→ς、C2 曲率 γ→g、恢复函数 r→R、脚本映射 σ(·)→文字）；E5 语法修复。
  - 仿真配套（sim/）：δ* 的 M4 项同步修复；A_epi 精度化落地（真值/估计/场景判据/SPEC）；矩阵重跑与图再生。
- 2026-10-16（晚）：**三审大修启动（P0 硬伤修复）**——三份新审稿意见（R1 逐页详审/R2 三项硬伤/R3 更正版）的逐条分析与处置方案见 `docs/R5paper_审稿分析与修改方案_v1.md`（v1.1：含 7 项决策记录与 P0 执行记录）。P0 四项：
  - **H1 §7.3 区间规则**：删除"conditioning on S^t can only increase"错误断言；改写为一般无方向恒等式＋旁路/中介两类探针语义；旁路前提 `I^t⊥S^t|A^{t−1}` 显式化，认证范围收窄为 bypass-semantics 外源随机化探针（仅上端为认证界）；中介反例（0.531 bit）与 BB-1 的 3/3 覆盖边界写明；附录新增 Remark（探针引理→区间规则的桥接）；BB-2 措辞改"bypass premise"。
  - **H2 公理独立性**：改为**极小公理组 {AX4, AX6b, AX8}**、AX5/AX7 为推论（sub-support products/调和平均/层级权重三见证）；§4.2、Route B Remark（升格编号）、摘要/引言/结论/综述非补偿段同步。
  - **H3 FH 下界（附录 L）**：n≥3 的 FH 形非 copula、更正为松弛界＋新增 Jensen 可达下界 `E[F]≥∏G(A_i)^{w_i}`。
  - **H4 T7 bracket**：补双侧混合簿记 `F_int=(1−m)C_self(1+o(1))`、`F_ext=mC_del+f`，上端推导补全；委托步允许 S-flow 时的降级界 `1/(1+mρ_min)` 写明；证伪窗口扩展。
  - 附带：附录 D 分类学表列宽缺陷修复（第二列不换行致第三列被裁切）。
  - 编译：pdflatex 0 错误、63 页、无 ≥20pt overfull、新引用全部解析。后续 P1–P4 工作包见方案文档 §7。
- 2026-10-17：**三审大修 P1（写作/评级/编辑层）**——逐条见 `docs/R5paper_审稿分析与修改方案_v1.md` §10。要点：摘要重写为三段约 250 词（条件式、白盒优先、实例化相对、"implementation-level consistency check"）；新增 §5.1"规范承诺与拒绝代价"表（AX6b/AX8/AX4/AX5 各自拒绝后的容许族与定理损失，含 AX5 合取必要性辩护）；§5.2 补"定理 7 仅作用于 F_ς、门控是定理外显式设计"范围声明；(Via-Ind) 升格为编号假设；T2 评级改 architectural-consistency 并补布线/$\tilde S_t$ scope notes；T8 改"consistency result"；操纵定义机制化（M1∨M2，动机移出）；新增定理编号对照表；表 1 增 Evidence 列并拆为表 1/2；C0 去 sketch；AHI 双向校准协议；种子协议/伦理声明/估计器披露；§8.7 新增"框架本身如何被证伪"段；BB-2 改"前提脆弱性量化警示"。编译：0 错误、67 页、4 处 ≤7pt overfull。
- 2026-10-17：**三审大修 P2（σ⁻ 真接入、Λ 主定义、构念效度）**——逐条见 `docs/R5paper_审稿分析与修改方案_v1.md` §11。要点：D-via 扩展为 min{资源比, 能力包络 m_j}（κ^eff/κ^req、R^eff/R^req，θ 显式排除；v1 矩阵退化为纯资源形式，σ⁻-EROSION 臂留 P3）；taxonomy 表/覆盖表/T5/必要性定理同步 σ⁻；Λ 主定义改为律级路径特异反事实（do(I^surg=∅) 下背书决策的 TV 距离），MI 比降为代理估计并登记一致性条件 (V)/(A)；D-epi 新增两口径一致性条件段；新增 §9.3 构念效度小节（内容/收敛区分/预测/测量不变性四面）。编译：0 错误、68 页、4 处 ≤7pt overfull。
- 2026-10-20：**四审大修（R6paper）**——三份新审稿意见（客观性元问题／苛刻标准 Major Revision／复核版 Major Revision）逐条处置见 `docs/R6paper_审稿分析与修改方案_v1.md`。要点：
  - **硬伤**：Λ 与 A_goal 分工定案（Λ 仅经 A_ref 的 Λ_ref 入复合；A_goal 无 Λ；T3a M2/T8/覆盖表 β_G 行/母本同步）；黑箱区间界降级为**单边认证界＋启发式下端**（式 (14) 重写，全部"interval containment"表述清除，BB-1/BB-2 结论重写）；Corollary（修正中介判据）补**诚实性条款**（无手术 ∧ 全中介 ∧ 诚实）；T3b 条件 (C1)–(C3) 更名 (HI-1)–(HI-3) 消记号双义。
  - **定位**：摘要四段重写（框架＋表示定理＋不可辨识性＋证据地位）；"force" 族表述范围化；Ebert & Welsch (2004, JEEM 47(2):270–283，CrossRef 核验）直接引用入 bib（103→104 条）并重定位新颖性（极小公理组/调和反例/双路线收敛/审计嵌入）；C0 降为"解释性对应"；T4 更名 highest-leverage attack；T6 外推边界段；新增 Discussion"客观性问题"专节与 §framework 五 respects↔通道显式映射表。
  - **证据**：实现一致性 vs 经验检验分离段；BB-2 改"灵敏度标定"（确定性 truth-mode 本质写明）；T6 30/30 补 CP 下界；T7 平台前提标注；计数对账（臂束 8,640／注册束 7,290／全战役 11,250）。
  - **新增形式化**：sound update rule 定义＋Bayesian 健全性引理（附录）；A_ref 操作化段（三因子估计/零点语义/合取辩护）；A_exec 凸包认证条件；prop:whitebox 三层辨识（Λ＝反事实层，需结构模型溯因）。
  - 编译：0 错误、0 未解析引用、78 页、4 处 ≤7pt overfull（既有）。
- 2026-10-21：**五审大修（R7paper）**——三份新审稿意见（收缩与客观性／78 页逐页详审（九处精确性缺口 T1–T9＋六处文献缺口）／zzxpaper5 复核版）逐条处置见 `docs/R7paper_审稿分析与修改方案_v1.md`。要点：
  - **定理陈述精确化**：T3 分层重述（复合咬合力随 A_ref 分层；L0/L1 的 β_G-on-Fix 角落入陈述）＋T3b 改期望级表述并补 Markov 触发概率下界；式 (14) 升格为正式命题（**条件认证上界**，两条前提写入陈述）；Prop（Λ 不可辨识）显式登记 Λ(M_impl)=0 的约定来源；盲区推论补 M2/M4 适用范围前提；T7 补显式每步误差界（选择器混合熵 h(m)≤ln2 nats，速率单位 O(1)，不随 T 消失）；T1c(D1) 收紧为"全速率无错码不存在"形式；sound update 定义与引理严格条件统一（o(·|e)≠p(·) 且 B(k)<1）并加强为**任意支撑覆盖的预测律**；T4/T6 标题精确化；route B 证明补显式凸性步骤。
  - **可复现性**：A_ref 背书一致性因子补完整估计协议（事件检测规则/路由判定/Clopper–Pearson 区间/n_min 与缺失数据处理）；A_exec 凸包认证协议具体化；A_epi soundness 校验失败时的降级行为登记。
  - **图文一致性（T9）**：AHI 正文序列（无防御 cell、ς=1，恰为全单元最大值 0→0.110→0.204→0.374）与图中位数口径（0→0.057→0.092→0.126）各自标明；图 5 去图内结论标题、加无防御虚线曲线；图 3(b) 轴标签交叠修复、图 3(a) 对数轴刻度清理。
  - **证据补强**：EXEC-1 富耦合实例上重跑权重/弹性敏感性电池（`sim/analysis_exec1_weights.py` → `analysis_exec1_weights.json`：6 权重向量下链 verdict 全保持、ς≤1 带保持、ς=2 失效回声 0.545）；新增定量锚点表（0.531 bit、CP 0.884、1.951±0.034、−0.504、13.7×、2×10⁻⁵）；三个构念效度敏感性臂（背书量化网格/κ 粗粒化/Λ 反事实模型）带协议与证伪器注册为缺口；外部基底（MiniGrid/LLM 工具）预注册协议＋功效分析（n=30 时 power>0.99）。
  - **文献补位（8 条，全部核验渠道登记）**：CIRL/assistance games（Hadfield-Menell 2016）、委托—代理（Laffont–Martimort 2002）、Colonel Blotto（Roberson 2006）、Ay–Polani 2008（CrossRef）、Oshana 1998（CrossRef）、METR 长任务（Kwa et al. 2025，arXiv 核验）、Ng–Harada–Russell 1999、Cao–Cohen–Szpruch 2021（arXiv 核验）；新增文献小节"Delegation, incentives, and adversarial allocation"（六文献线→七文献线）；§2.5 评测论断更新为能力/倾向实践对照。
  - **定位与修辞**：标题加 White-Box-First；摘要压缩至约 300 词（三段：框架＋关键正/负结果＋证据地位与部署边界；移除"zero refutations"亮点、外部基底验证前移）；"theorem system" 全文降为 "theorem suite"（含节标题）；Definition 1 改 operational definition；C0 标题降调；客观性专节补"收敛条件"段（五条约束条件的合取）；环境自身动力学排除类的治理后果正面写入 §taxonomy（再基线义务）；OU 方差符号 σ²→ν_OU² 消重载。
  - 编译：0 错误、0 未解析引用、84 页、4 处 ≤7pt overfull（均为既有）；bib 104→112 条。
- 2026-10-22：**六审修订（R8paper，Minor Revision）**——两份新审稿意见（第二轮评审报告：R1 运行两个低成本敏感性臂＋R2 时间线＋R3 压缩＋R4 内务＋R5 图题；zzxpaper6 终评：九项必修＋六项建议）逐条处置见 `docs/R8paper_审稿分析与修改方案_v1.md`。要点：
  - **R1（唯一实质项，已执行）**：threats (x) 三注册臂中成本最低的两臂**真实运行**——X5-a 背书量化四档（coarse/default/k=2/k=4，ATK-1 C1–C5 × 8 防御配置全重跑：零 verdict 翻转；A_goal 读数几何收敛到闭式连续极限 1−2η/(1+η)，默认网格静止间隙闭式 η(1−η)²/(2(1+η))≤0.057 逐点精确核验；绝对读数证伪支按注册口径触发并如实报告为触发，相对 5% 支未触发）；X5-b κ 细化三档（退化/半环/位置精确，ATK-2 网格重评分：A_epi 逐档逐配置严格单调，证伪器未触发；κ 档间基线/深俘获漂移如实报告；退化档 A_epi≡1 见证登记非空洞）；x-c（Λ 反事实模型）保持注册未运行（评审明示可下一版）。产物 `sim/analysis_sensitivity_arms.py` → `analysis_sensitivity_arms.json`；平台前提随 SPEC_platform v0.3（κ 细化感知派生 P2.4／endorse_step P3.2／植入目标与桶先验通用化 P9.3）落地，默认与 EXEC-1 配置逐点还原 v0.2（T-REF×7 回归钉＋analysis_exec1_weights 零漂移）。
  - **zzxpaper6 必修**：T3(a) 证明 sketch 的 γ 行显式引用 sound-update 条款与降级中止；Table 1 的 T3b 行改期望级表述＋verdict 注记；BB-2 措辞改"前提被违反、界不再成立"（正文/辨识节/摘要三处对齐）；C0 改 separation witness（主文命题＋附录重述＋讨论同步）；T7 松弛量统一为 h(m)≤ln2 nats/步/流项并写明 φ-松弛吸收进 bracket 端点（非外加项）；计数单位全口径入附录 app:counting（逐场景分解 5,760/7,200/7,290/11,250＋840＋种子公式，正文留摘要＋指针）；Aczel 两条目著者名统一全名格式（两部不同专著，非重复条目）；kuratowski_ryllnardzewski1965 补 \citep（原仅散文提及）。
  - **建议项全采纳**：摘要补"construct validity remains unestablished"半句；§3.5 AHI 单边警报前向引用；T6(i) 补 M4 覆盖为注册前提句；D-goal 补塑形不变性状态句（常数平移不变、端点塑形不变性有限⇒注册为敏感性维）；记号表加过载警示行；结论补外部基底里程碑句（MiniGrid PoC=下一投稿周期，LLM harness 与人类侧在后）；图内结论性标题全部清除（图 2/3/4/6；图 5 上轮已清）。
  - **R3 压缩（编辑项）**：registered 类语句改首定义＋交叉引用（§8.1/§8.4/§8.8 的重复承诺段、"decisive next experiment" 五处收敛为一注册三引用）；§9.1/§9.3(vii) 复述段压缩；表 1/表 2 合并为单表；T7(ii) 主文陈述与附录重述去重；场景库/平台/SESOI/X1/X2/EXEC-1 条目框架句收紧；种子公式与计数全口径移附录。净页数 84→86：**新增两臂结果与协议约 +3 页**，压缩 −3 页对冲；深度 15–20% 压缩按既有决策留待期刊定版（[MaM]/[Syn] 标记在位），R8 文档 §4 记录理由与可再压缩清单。
  - **R4 内务**：版本串 R4/2026-10-18 → R8/2026-10-22；作者/资助/IRB 占位保留（须作者提供，见 R8 文档 §6 移交）；独立可编译性核验（pdflatex×3+bibtex 离线全通过，sn-jnl 仅提交版式需要）。
  - **PDF 完整性核验（zzxpaper6 必修 1）**：本仓库构建 pdffonts 全 50 字体嵌入＋uni 映射、gs 全页解析零错误、pdftotext 86 页扫描无短页/单字符主导页、评审标记页（8/45/53 等）逐页渲染目检完好——评审侧损坏为其转换管线 artifacts（R7 已证同源）；核验命令入本 README。
  - 编译：0 错误、0 未解析引用、86 页、4 处 ≤7pt overfull（均为既有）；bib 112 条全被引；套件 122 项全绿（115+T-REF×7）。
- 2026-10-22：**七审修订（R9paper，Accept＋条件式 Minor Revision）**——两份新审稿意见（第三轮评审报告：**建议录用（Accept）**，实质事项全部闭合，余四项编辑/内务建议；zzxpaper7：Minor Revision，条件六项＋建议五项，核心为"PDF 大面积损坏必须重新生成"）逐条处置见 `docs/R9paper_审稿分析与修改方案_v1.md`。要点：
  - **评审侧损坏误报的真实根因定位并修复**：图 PDF 由 matplotlib 默认 `pdf.fonttype=3` 生成（Type 3 字体无 ToUnicode 映射，pdffonts uni=no），任何文本抽取管线在图区必产出乱码——三轮评审的"表格错乱/图区乱码/填充页"报告与此同源。修复：`make_figures.py` 改 `pdf.fonttype=42`（TrueType 嵌入），5 图重生成（数据锚点不变：slope −0.5039、AHI 0→0.11→0.2039→0.3745），pdffonts 全 50 字体 **emb+uni 首次全绿**；逐页文本量扫描全 86 页无低文本页；Table 1 五行（T1c/T1d/T2/T4/T5）layout 抽取完整独立；gs 全页零错误。
  - **两处真实修复**：①$\Fint^{self}$ 在 T7(ii) 的 φ-松弛界中使用 4 处而从未定义——主文首现处补 $\Fint^{self}:=\Fint|_{m=0}=C_{self}$（未委托基线全视界内部流、φ:=f/C_self 的归一化因子），附录 prop:bracket 同步括注；与 sim 实现（`scenarios.py`：f_self=truth_F_int(m0,T)、phi_max=T·ln2/f_self）逐项对齐。②"endorsable"三处（T7(iv) 主文/附录重述/related_work）改论文自定义名词 **endorsability**（与 q=reversibility×transparency×endorsability 的三子指标名词形一致，消除拼写争议）。
  - **建议项采纳**：Table 2 增 X5 两闭式锚点行（连续极限 $\Agoal^\infty(\eta)=1-2\eta/(1+\eta)$＋静止间隙 $\eta(1-\eta)^2/(2(1+\eta))$ max $0.0567\le0.057$；κ 层衰减 $1/|\kappa|$，0.500→0.250 对 $|\kappa|:2\to4$）；fig:ahi 图注补"单边警报、静默非证据、双侧扩展注册未运行"句（呼应 threats (viii)）；结论补"These verdicts are internal-consistency results, not construct validation"半句（指向 §9.4）；Roberson 2006 核验在列（refs.bib＋§2.7 引用＋bbl 解析）。
  - **压缩再 pass**（R-Accept 建议 1）：四处复述改首定义＋交叉引用——§9.3(vi) 的 ebert_welsch/双推导复述（§9.2 clause three 为首定义）、§9.4 predictive validity 的证伪器句（与 §9.2 clause four 逐字重复）、limitations (xi)（与 objections (vii) 重复段收敛）、limitations (xii)（与 threats (x) 结果复述收敛）。词数 47,016→47,109（净 +93：本轮评审要求的新增内容 ≈+190 对冲压缩 ≈−100）；深度 15–20% 压缩按既有决策留待期刊定版（R8 文档 §4 清单）。
  - **artifact 再核验十条**（zzxpaper7 条件 2/3/4/5 的具体指控）：enforce nor dismiss（源码 enthrone）、Kabier（源码 Xabier）、Intellectuals（源码 Intellectica）、Scholkopf（源码 Sch{\"o}lkopf）、A_phon（源码 \hat{A}_{\mathrm{phen}}）、δ_j 缺 bar（源码 \bar\delta_j）、§2.3 标题缺换行（源码独立 \subsection）、页 7 "1" 噪声（源码无）、式 (11) [L1⊢ 括号（源码 [\text{L1+}]，抽取即评审给出的目标形）、Appendix N 截断（源码含全部四项分解）——均为评审侧抽取 artifacts；修复 fonttype 后此类误报的根因已消除。
  - 版本串 R8→R9/2026-10-22；编译 0 错误、0 未解析引用、86 页、4 处 ≤7pt overfull（均为既有）。
- 2026-10-23：**八审修订（R10paper，Accept＋条件式 Major Revision＋战略自评）**——三份新审稿意见（第四轮评审报告：**Accept**，无进一步学术修改要求，余五项投稿内务；zzxpaper8：Major Revision，以"PDF 重生成＋公式表格修复"为硬条件；战略三问：无人类实验可发性/选刊/范围收缩）逐条处置见 `docs/R10paper_审稿分析与修改方案_v1.md`。要点：
  - **审稿对象取证**：zzxpaper8.pdf 即本仓库 R9 构建——其全部页码锚点（7.2@40/8.1@43/8.8@55/T1@45/T2@46/AppN@78）与命题编号（Thm 18/Prop 23/Prop 75）与 R9 编译产物逐一吻合；其 P0 七项损坏指控（"1"填充页、式 (9)/(11)/(13) 残缺、Table 1/2 混排、重复段落、参考文献截断）经源文件＋pdftotext 双路核验**全部为评审侧提取管线 artifacts**（式 (13) 源为 `\Amin:=\Avia^{\min}`，即 A_min:=A_via^min·∏，语义正确；式 (11) 抽取与审稿人目标形式逐字一致）；小错清单 19 条逐一核验（含 Dung DOI 经 doi.org 在线复核 pqae010 正确）均无需改动。
  - **五处真实修复/采纳**：①**T7 量纲统一**（审稿人 §3.1 点中 R9 遗留混用）：簿记加速度单位约定（nats/step，视界流＝T×速率，比率定律量纲不变），$\Fint^{self}$ 定义定稿 $:=T\,C_{self}$（速率 $\Fint|_{m=0}=C_{self}$ 的视界总量，与 sim `f_self=truth_F_int(m0,T)=T·c_self`、`phi_max=T·ln2/f_self` 逐项吻合），速率等价形 $\varphi\le\ln2/C_{self}$ 并注——主文 T7(ii)＋附录 T7(i) 证明＋prop:bracket（Prop 75）四处同步；②T7 证明梗概 o(1) slack 残留改 $h(m)\le\ln2$ nats/step；③T3b Markov firing floor 加平凡界括注（g>1 时前提不可满足因 $\hat A-A^\gamma\le1$，informative range $(0,1]$；定理＋附录重述＋证明三处）；④Appendix N "M9.3 convention"（仓库内部代号泄漏，全文唯一）改自含 verdict 约定表述＋Section 8 交叉引用；⑤Table 2 detection-divergence 行补 `Prop.~\ref{prop:detection}` 交叉引用。
  - **战略自评定案**：无人类实验足以发表（体裁＝framework+benchmark，构念效度显式未确立＋验证路径已登记，双侧审稿人认可定位诚实）；首选 *Minds and Machines*、次选 *Synthese*（均 sn-jnl 就绪）；外部基底落地后 benchmark 单独成文投 NeurIPS D&B/AIES；**范围无需再收缩**——related_work 末段已有精确三基底 scoping（artificial=benchmark 实测/human=协议＋文献三角＋验证路径/animal=概念可能性非覆盖主张）。
  - 版本串 R9→R10/2026-10-23；编译 0 错误、0 未解析引用、**87 页**（+1 页为参考文献溢出，正文版式未动）、4 处 ≤7pt overfull（既有）；pdffonts 50 字体 emb+uni 全绿；逐页扫描无填充页/短页；Table 1 layout 完整；artifact 词扫描（含 M9.3）全零；md5 `69d0617e0eecb3cb06b01bf1e916d04a`。sim 零改动（122 绿记录仍有效）。
- 2026-10-23：**投稿准备**——前置信息填实并编译核验（87 页 0 错误）：作者块（Wen Hu，NUAA 电子信息工程学院＋江苏云禾峰智能科技，huwen@nuaa.edu.cn；article 版排版＋sn-jnl 切换写法已注释备妥）、Ethics 改事实性声明（无人类/动物实验；§8.8 加 `\label{sec:triangulation}` 供交叉引用）、Funding=无外部资助、Competing interests 维持 declare none、Data availability 改公开仓库 `autonomy-five-channel`（GitHub/Gitee，tag v1.0-r10）＋Zenodo DOI 预留句（替换过期哈希 8bf4f44；占位符 GHUSER/GITEEUSER 由 `tools/fill_repo_urls.sh` 填充）。发布工件在 `dist/`（gitignored）：公开快照仓库（精简范围，排除 refs/pdfs 版权 PDF 与内部文档）＋arXiv 源码包/元数据＋PhilPapers 元数据。全流程待办：`docs/投稿准备清单_v1.md`。
- 2026-10-24：**公开仓库上线**——`tools/fill_repo_urls.sh hurrywhen jiangsu-yunhefeng-intelligent` 执行（4 文件填充＋快照 PDF 重编译 87 页＋arXiv 包重建）；快照仓库 `git init`＋commit `c61d3b9`（226 文件，作者身份 Wen Hu \<huwen@nuaa.edu.cn\>）＋tag `v1.0-r10` 推送 **GitHub `hurrywhen/autonomy-five-channel`（API 确认 public）＋Gitee `jiangsu-yunhefeng-intelligent/autonomy-five-channel`** 双远端成功；开发仓库 `main.tex` 占位符同步替换为真实 URL 并重编译（87 页 0 错误，md5 `990d5ac6e3e796194690eed114cec1b4`）；清单 §0/§2/§3 台账回填。下一步：Zenodo DOI→arXiv→PhilPapers→MaM 投稿。
- 2026-10-24（续）：**Zenodo DOI 发布与全链回填**——GitHub Release（tag `v1.0-r10`）→Zenodo 自动归档：version DOI `10.5281/zenodo.23608752`／concept DOI `10.5281/zenodo.23608751`（API 核验 published；归档件 1,989,759 B，md5 `634e413d995d94a90dcb4f7dd1d0e7eb`）。`main.tex` Data availability 句升级 DOI 内联引用（删"will be minted"句），开发仓库＋快照同步重编译 87 页 0 错误；快照 README badge＋BibTeX doi 字段、CITATION.cff identifiers 块、RELEASE_NOTES DOI 台账与 tag 冻结策略；快照 commit `dc066b8` 推送 GitHub＋Gitee；**arXiv 包以 DOI 版重建**（干净目录试编译 87 页 0 错误，21 文件）。剩余待办：arXiv 提交→编号回填→PhilPapers→sn-jnl 切换→MaM 投稿。
- 2026-10-24（续 2）：**arXiv 编译版体检＋Table 1 溢出修复**——下载的 arXiv 生成 PDF（87 页）经完整性清单核验：内容锚点全在原位、公式 (9)/(11)/(13) 渲染正确、15 行表格与参考文献完整、12 个未嵌入 base-14 字体全部仅出现在第 1 页（arXiv 自身图章层注入，非源文件问题，正文 52 字体 emb+uni）；编译期报警均为良性（既有 ≤7pt overfull/underfull 等）。**但发现真实版式缺陷**：`Float too large for page by 91.7pt` → Table 1 的 C2 行页底截断、(60/60) 出线外、页码压表（此前完整性自查漏检末行，现把"末行可抽取"纳入清单）。修复：tab:main 的 caption 说明文字移为正文 `How to read Table 1` 段（内容零删减，含评审要求的 T3b/T1a 注释不动）；修复后 87 页 0 错误、无浮体警告、C2 行与 (60/60) 可抽取、页码不再压表。快照 commit `518d58b`＋修正 tag `v1.0-r10.1` 双端已推；论文 DOI 引用改 concept DOI `10.5281/zenodo.23608751`；arXiv 包重建并干净目录试编译通过（须替换 arXiv 提交）。
- 2026-10-24（续 3）：**arXiv 扫描"missing file: sn-jnl"误报处置**——权威源 `\IfFileExists{sn-jnl.cls}` 条件文档类被扫描器当硬依赖；新增 `tools/make_arxiv_package.sh`：arXiv 包内 main.tex 固定 article 文档类＋删除 sn-jnl 相关注释（仅构建配置差异，正文与权威源逐字一致），自动干净目录试编译（87 页 0 错误、无浮体警告、C2 行可抽取）；`fill_repo_urls.sh` 改走该脚本。新包 md5 `411200c05853e2a538d44e1ef36abcd8`；Review Files 页 main.bbl 勿删（arXiv 默认用之，refs.bib 保留作冗余备份）。快照 `3fe6ae5` 双端已推。
- 2026-10-26：**arXiv moderation 拒收与 MaM 双盲投稿包**——拒信明确为"需要额外评审与修订"，并指定传统期刊正式发表后凭可解析期刊 DOI/期刊网页状态走原提交 `submit/8276172` 的 appeal；不立即申诉、不新建 arXiv 投稿，Zenodo/TechRxiv 等预印本 DOI 不能替代 conventional journal DOI。主线转 *Minds and Machines*。按当日官方指南（双盲、独立 Title Page、150–250 词摘要、4–6 关键词、完整可编辑源、最多 6 位建议审稿人）新增 `tools/make_mam_submission.py`，生成 `dist/journal/minds-and-machines/`：匿名正文 106 页、摘要 212 词、6 关键词、`sn-apa` 作者—年份引文、参考文献内嵌、扁平化源包；独立 Title Page 2 页＋cover letter 1 页＋表单元数据＋审稿人候选池＋作者确认清单。期刊副本只做版式/投稿适配：Theorem 14 长表在 α 行之前分段（全行全内容保留）、T5 与两处附录公式换行、Table 1 `tabcolsep=2.5pt`、显式 Section 字样及 Type 1 bullet；权威公开源未改。最终干净构建：0 错误、0 未解析引用、0 浮体超页、0 overfull、0 Type 3、0 未嵌入字体、匿名身份扫描通过、C2/(60/60) 完整。实际投稿前仍须作者确认第二单位城市、审稿人利益冲突、生成式 AI 使用披露及 Zenodo 修正版 Release；未执行网站投稿或公开发布。
- 2026-10-27：**双作者与单位地址更新**——作者确认 Wen Hu 第一/通讯、Gong Zhang（张弓）第二，邮箱 `gzhang@nuaa.edu.cn`，二人共享 NUAA 学院＋江苏云禾峰两项单位，第二单位城市 Nanjing。开发/公开快照本地 main.tex 作者块及 sn-jnl 注释、README、CONTENT-LICENSE、论文 preferred-citation、RELEASE_NOTES、arXiv/PhilPapers 元数据与 MaM 投稿包均同步；公开线上不改动、不 commit/push。CITATION.cff 顶层 software/data creator 未因论文作者变化而擅自添加张弓，待其实际代码/数据角色确认。双作者预印本 87 页 0 错误（md5 `034da55ddcab07bca4140189421195fa`），另修复第一单位与 Gitee URL 长行；备用 arXiv 包 md5 `e45ce336070055ea1dab9ecafa38d199`。张弓贡献已确认为思路形成期共同讨论、修改期审核与讨论、最终稿责任共担，并写入 MaM Author Contributions；其投稿/利益冲突声明确认及代码/数据角色仍待办。下一公开修正版建议使用新版本标记（如 `v1.0-r10.2`），不改写已有 `v1.0-r10.1`。

- 2026-11-22：**R21 小修**——完整处置见 `docs/R21paper_复审意见处置_v1.md`。R20 复审确认四项关键修复已实质完成、无新基础理论问题；本轮闭合两项剩余缺口（检测规则/三态敏感性/估计器不变）：①高于检测限约定的复合采样区间重命名为**来源份额条件复合采样区间**（SHARE_CONDITIONAL_SAMPLING_BASIC_BOOTSTRAP＋每区间 conditioning_scope＋证书级 composite_interval_conditioning 政策；仅传播来源份额、其余通道固定为插件/结构点、非完整联合不确定度；份额自身区间保持无条件；传播数值与 R20 一致）。②**逻辑包络锚点包含与采样统计覆盖分开报告**（永不合并/跨类比较为估计器优劣）；原生表区间标记改 "SC"。③新增**联合轨迹 bootstrap 补充诊断**（每重采样重算全部通道＋复合，保留批内协方差，执行按序列分层独立重采样；工件级、非证书语义、不消除偏差）。④正文欠覆盖**双因归因**（DI 插件偏差＋条件化设计），检测表三列分列（Env.contain/SC cov./Joint cov.）＋双因解读；联合诊断量化条件化因（n=8192 RNI 14/16 胞元份额条件漏但联合覆盖、2/16 双漏；avg 11/3；NRI 联合 0/16 偏差主导）。⑤份额条件结果复现 R20。新增 37 项测试，全套 **406/406 通过**；PDF **105 页、6 图、115 引用**（用户接受 105：审稿必需新增净约+2 页，已诚实压缩约 60 行，不以格式手段虚减），0 未解析引用，最大 overfull 8.94pt。历史 R11–R20 工件只读不改写（R20 字节不变）。本轮创建不可变 tag `v1.4-r21` 与两环境冻结重放清单；version DOI 仍待 Zenodo 归档，外部执行/独立复现/selector-conditional DEL-1 未完成。
- 2026-11-22：**R20 小修至中修**——完整处置见 `docs/R20paper_复审意见处置_v1.md`。R19 复审确认跨环境重放已实质修复、核心理论问题不再作为拒稿理由；本轮闭合四项剩余缺口：①近零检测改**数据驱动可执行规则并纳入正式证书**（预声明 basic 偏差校正 bootstrap 区间三态判定；每约定 convention_status/share_interval/composite_interval/限值来源/诊断插件；真值规则降级 oracle-assisted 夹具专用；采样基线 INTERVAL 无标量、overall=报告区间 hull；0.1478374 标为诊断性插件输出）。②区间敏感性改**确认/不可判定/不可评估**三态体系，停止把相同宽区间解释为一致，中点仅描述。③真实区间传播＋区间类型区分（逻辑包络≠置信区间）。④**测试解耦**：软件正确性与预期实证结果分离，R19 实证不变量移除改快照回归（R19 工件字节不变、重放仍通过）。⑤新增预声明 16 种子×{2048,8192} 检测误判/覆盖研究（NRI 16/16 INDETERMINATE——诚实：数据不足以确认近零；误报漏报 0；包络覆盖 16/16；ABOVE 口径采样区间欠覆盖为描述性发现）。⑥主文压缩至 **103 页**（DEL-1 明细表移仓库账本、历史/重复叙述收紧，新增检测表与三态契约由压缩抵消）。新增 50 项测试，全套 **369/369 通过**；PDF **103 页、6 图、115 引用**，0 未解析引用，最大 overfull 8.94pt。历史 R11–R19 工件只读不改写。本轮创建不可变 tag `v1.3-r20` 与两环境冻结重放清单；version DOI 仍待 Zenodo 归档，外部执行/独立复现/selector-conditional DEL-1 未完成。
- 2026-11-22：**R19 中等幅度修订**——完整处置见 `docs/R19paper_复审意见处置_v1.md`。R18 复审确认无新基础数学错误，剩余问题为证书通用性、跨环境数值可复现性与近零采样误差传播。本轮闭合：①修复 R18 联合审计跨环境重放失败（开环最优输入分布非唯一→~7.5e-10 漂移＋证据哈希变化）：声明式规范化容量输入（均匀若达容量/近零，否则唯一最大熵＋确定性迭代缩放＋fail-closed 验证）、证据哈希仅绑定不可变原始输入、逐字段重放容差；失败记录 `runs/20261122_r19/REPLAY_FAILURE_R18.md` 保留不替换，两个独立干净环境验证。②证书升级 R19 层级感知 schema（`r19_guards.py`）：L0 独立内部因果归因（不强加 RNI/NRI）、通道四态 DEFINED/INTERVAL/UNKNOWN/NOT_APPLICABLE、点值/区间证书分离＋复合区间单调传播、IRL 区间模式、薄日志/零熵反思降级、零总流份额不可辨识区间语义。③修正 `state_autonomy_RNI` 仅返回资源门缺陷（改由实际五通道计算＋一致性回归）。④正文并列精确/采样各口径复合与误差（采样 NRI 0.1478 vs 精确 0.0003908，误差 0.1474>0.05）＋近零检测限区间语义＋8 独立种子偏差/覆盖率/宽度研究（百分位区间欠覆盖，精确端点仅为模型锚点）。⑤敏感性分解 order/semantic/overall，两标志独立触发；0.05 阈值改称后验冻结内部工程阈值（非结果前预注册）。⑥采样手术/解耦负控制入联合日志流程。⑦继续压缩历史/重复散文。新增 46 项测试，全套 **319/319 通过**；PDF **105 页、6 图、115 引用**（新增审稿必需内容约 2 页，历史散文压缩），0 未解析引用，最大 overfull 8.94pt。历史 R11–R18 工件只读不改写。本轮创建不可变 tag `v1.2-r19` 与两环境冻结重放清单；version DOI 仍待 Zenodo 归档，外部执行/独立复现/selector-conditional DEL-1 未完成。
- 2026-11-21：**R18 局部关键修订**——完整处置见 `docs/R18paper_复审意见处置_v1.md`。R17 复审确认 R16 核心缺陷已修复；本轮闭合剩余缺口：①最终证书升级 R18 完整剖面 schema（`r18_guards.py`），强制完整通道向量/分量状态/区间/协议版本、RNI/NRI/顺序平均/流量项/替代语义、目标点与 IRL 区间、开环视界、反思三因子与日志事件计数、权重与跨口径复合值范围，超内部阈值（0.05）强制 ORDER_SENSITIVE/MODEL_SENSITIVE＋标量警示，RNI≈1/NRI≈0 不得无警示单点出口；②R17-native 组合式夹具升级为联合日志端到端内部审计（`native_joint_audit.py`、`analysis_r18_native_joint_audit.json`，单 SCM/单日志/单批次，执行另设预承诺开环流），正文新增结果表直接报告 RNI/NRI/顺序平均复合 0.4608565/0.0003908/0.4011989 与替代语义后果；③开环零值量词改支持集相对、期末观察（0.2655022）/观察序列（0.5310044）约定分离；④权重结果统一称精确敏感性刻画；⑤外部协议 TOST（两个单侧 α=0.05⇔90% 双侧 CI）与非劣效方向精确化，摘要/结论改“工程界值已冻结、域 SESOI/功效/执行未完成”；⑥主文历史叙述压缩、版本沿革集中仓库账本、摘要去版本化。新增 22 项测试，全套 **273/273 通过**；PDF **103 页、6 图、115 引用**，0 未解析引用，最大 overfull 8.94pt。历史 R11–R17 工件只读不改写。本轮创建不可变 tag `v1.1-r18` 与冻结重放清单；version DOI 仍待 Zenodo 归档，外部执行/独立复现/selector-conditional DEL-1 未完成。
- 2026-11-03：**R13 定点数学与证据链复审**——完整处置见 `docs/R13paper_审稿合理性分析与修订记录_v1.md`。T6 仅保留上比较下的 retention margin 与 certificate-failure band，ATK-6 俘获只属精确饱和实现；C0(ii) 撤回完整外部画像相等，改非退化 L1 额外审计分离，并明确公平二值/独立信念与非退化背书反事实 TV=1 前提。二次复核另补 pointwise viability、H4$''$、M1 阈值和 T1d 的 (R-epi) 前提。T6 拆 360 实现＋60 CUSUM 描述，DEL-1 六判据账本公开，30 个 CUSUM 比值附 $t_{29}$ 敏感性。`make_report.py` 默认合并 R11 replay、缺文件 fail-closed 且不写历史根；全套 unittest **152/152 通过**，PDF **94 页**。
- 2026-11-03：**R12 定点数学复审**——完整处置记录见 `docs/R12paper_审稿合理性分析与修订记录_v1.md`。Proposition 23 改固定 \(\delta>0\)、\(\alpha\downarrow0\)，常数停止反例入附录；T7(iv) 拆结构中介与诚实/无精度损失下的无损失；T8(ii) 改逐参数方向并加入 M4-aware floor。同步修复 AHI 实际缺口口径、T1c 基线、外部 power 状态、公开版本链、route B 缩放步骤、soundness 严格条件及 Jensen 非尖锐下端。`sim/SPEC_experiments` 升 v0.8，新增 R12 反例回归；全套 unittest **141/141 通过**；独立只读复核及二次复核均确认定点问题闭合。R11 DEL-1 三件汇总材料已从 ignore 规则单独放行以便后续发布，但本轮未执行 commit/push/tag/version DOI，公开链仍未闭合。

- [ ] MaM 投稿前作者确认：两位作者 ORCID（如有）、具体贡献分工与张弓投稿/利益冲突声明确认、最多 6 位独立审稿人、AI 使用披露、Zenodo 双作者修正版 Release；详见 `dist/journal/minds-and-machines/AUTHOR_CONFIRMATION.md`
- [ ] MaM/其他传统期刊正式发表并取得可解析期刊 DOI 后，凭原 `submit/8276172` 走 arXiv appeal（不新建投稿）

## 投稿前 PDF 完整性自查（2026-10-22 起，防评审侧损坏误报；R9 加强）

```bash
cd latex
pdflatex -interaction=nonstopmode main.tex && bibtex main && \
  pdflatex -interaction=nonstopmode main.tex && pdflatex -interaction=nonstopmode main.tex
grep -c '^!' main.log                      # 期望 0
grep -i 'undefined\|multiply' main.log     # 期望空
# 全字体嵌入＋Unicode 映射（emb=$(NF-4)、uni=$(NF-2)；R9 前图区 Type 3 字体 uni=no，
# 是评审侧"图区乱码/表格错乱"抽取误报的真实根因——图必须用 fonttype=42 重生成）
pdffonts main.pdf | awk 'NR>2 && ($(NF-4)!="yes" || $(NF-2)!="yes")'   # 期望空
gs -o /dev/null -sDEVICE=nullpage main.pdf 2>&1 | grep -ci error       # 期望 0
# 逐页文本量扫描（无"1"填充页/低文本页）
for p in $(seq 1 $(pdfinfo main.pdf | awk '/^Pages/{print $2}')); do \
  t=$(pdftotext -f $p -l $p main.pdf - | tr -d '[:space:]'); \
  [ ${#t} -lt 200 ] && echo "page $p low-text: ${#t}"; done             # 期望无输出
# Table 1 行独立性 layout 抽取（页码随版式变动调整）
pdftotext -layout main.pdf - | grep -A1 "^T1c\|^T1d\|^T4 \|^T5 "       # 期望各行内容完整
# 表格末行完整性与浮体溢出（2026-10-24 新增：Table 1 的 C2 行曾被页底裁掉——
# 仅查首行/中部行会漏检；浮体超页时 LaTeX 不报错只警告）
grep -ci "float too large" main.log                                   # 期望 0
pdftotext main.pdf - | tr '\n' ' ' | grep -o "open hysteresis loop"    # 期望非空（末行 C2）
pdftotext main.pdf - | tr '\n' ' ' | grep -o "(60/60)" | head -3       # 期望 C2 verdict 可抽取
```

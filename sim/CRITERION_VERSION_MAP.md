# 论文—规约—代码—运行归档版本映射（R11–R18，更新于 2026-11-21）

## 1. 原则

- 历史运行目录 `runs/20261017_full/` 是只读证据快照；不得回写其 manifest、结果或 verdict。
- manifest 中的 `spec_version` 是运行写出器当时写入的元数据，不一定等于该 commit 实际实现的全部有效判据。必须同时记录代码 commit、SPEC 变更日志和场景内容。
- R11/R12/R13 的数学复审属于**对历史结果的重评价**，不是一次新的 4,620-run 独立实验。R14 发布必须冻结开发源 commit 与公开快照源码；公开 main 同步不等于不可变 tag/version DOI，只有全部版本链实际形成后才可声称闭合。
- R12 撤回的是 R11 的错误量词、缺失前提和单调性全称句；R13 进一步撤回 T6 上比较推出必然俘获及 C0(ii) 完整外部画像相等。R14 再撤回 T1b 漏因子、T2/T3 无条件单调性、线性—分数内点最小化、连续 $I/h$、已证比例尺度、$\Lambda$ 历史标签/退化认证例外、弱脚本前提、Via-Ind 推导和 Feng 一般排序。R15 撤回执行 n/(n+1) 错位、T2 兼容 iff/四轨充要、普遍盲性、纯随机规范自主性解释、白盒全通道点识别、C2 省 δ、Route B properness/跳步归一和当前状态=防御准备度。R16 再撤回 RNI 份额的顺序无关/唯一因果分解解释、Route B 第 6 步未缩放的中间等式、自然语言“区间非减”、NaN fail-open、完整字段自动 SCM_AUDITED、legacy 数值仅凭通道数升级及浮点逐位复核。R17 再撤回多步普通 MI 执行容量（反馈复制反例）、历史自主性仅作辅助元数据、Lambda 时间原点混用、对数份额“canonical attribution”、五权重/tau-b 作为全单纯形稳健性证明、X3 排序作为几何形式独立经验证据、T1d 有限容量来源、C1 确定性 ODE 平稳方差/AR(1)、C2 未截断吸收态，以及 exactly-five 最小必要性口吻。R18 再撤回“最终证书仅含 RNI 单点标量即满足剖面优先”的做法、R17-native 组合式夹具的笼统“端到端”表述、开环零值未限定支持集量词、观察序列容量与期末观察估计量混用、权重精确界的“稳健”概括，以及“两个单侧 95% CI 落在等价界值内”的不严格 TOST 表述。保留数值只按各自版本与收窄实现解释，不回读为被撤回命题的证据。

## 2. 历史归档 manifest 的共同事实

`runs/20261017_full/` 下 12 个 manifest（main、stress_sigma2、del1、c0_demo、c0corr、res1、force1、bb1、lh1、bb2、erosion、exec1）均记录：

- `git_commit = a6e7670`；
- `spec_version = SPEC_experiments v0.3`；
- `seed_rule = P6.2`；
- run 数：main 2880，stress_sigma2 1440，其余 10 组各 30，总计 4620。

这些 `v0.3` 字段来自 `matrix.py` 中未随后续 SPEC 升级的常量。它们是**过时的写出器元数据**，不表示 a6e7670 只实现了 v0.3。下表给出按 SPEC 变更日志和实际场景内容重建的有效映射。

## 3. 逐项有效映射

| 归档/分析 | 历史代码与原始元数据 | 按变更日志确定的有效判据 | R11 处理 |
|---|---|---|---|
| main、stress_sigma2 | a6e7670；manifest 写 v0.3 | v0.3 执行接口；v0.4 的 Aepi 精度口径与 M4 项修正；v0.5 的矩阵扩展不改变既有 ATK-1--6 主判据 | 保留历史执行记录；确定性重放不作二项 CI/功效解释 |
| del1 | a6e7670；manifest 写 v0.3 | **v0.5** DEL-1⑤⑥ direct-flow 与 \(\rho\ne1\) 臂 | 旧单-\(\varphi\) 松弛无效；R11 标 T7 为 INCONCLUSIVE，不把旧包含性当作非退化证据 |
| erosion、exec1 | a6e7670；manifest 写 v0.3 | **v0.5** 新增场景 | 保留为单平台机制演示，不称外部验证 |
| bb1、bb2 | a6e7670；manifest 写 v0.3 | v0.3 黑盒判据及后续补充 BB-2 | BB-1 被动 \(A_{exec}\) 方向仅为 ENV-0 实例；一般方向未识别 |
| c0_demo、c0corr、res1、force1、lh1 | a6e7670；manifest 写 v0.3 | v0.3 场景判据；相关精度口径按 v0.4 | 保留为定义/实现检查；T8 仅对应 R11 的直接目标/行动机制 |
| `analysis_weights_sigma.*` | a6e7670 归档的后验重算 | v0.5 权重与弹性敏感性包 | 后验模型压力分析，非独立随机试验 |
| `analysis_p3.*`（X1--X4） | a6e7670 归档的后验重算 | **v0.5**；X1/X2 有数据查看后的判据修正 | X1 原失败单列，不与主表 0 REFUTED 合并 |
| `analysis_sensitivity_arms.*`（X5） | 2026-10-22 分析代码与 `SPEC_platform v0.3` | **v0.6** | X5-a 绝对读数证伪器触发；X5-b 未触发；X5-c 未运行 |
| R11 数学反例回归与 DEL-1 修正实现 | 当前工作树；发布 commit 待冻结 | **v0.7** | `runs/20261102_r11/del1`：30 run overall 全 INCONCLUSIVE；判据 120 CONFIRMED＋60 INCONCLUSIVE；manifest 写 v0.7 和基线 `5d57b74`，但工作树含 R11 未提交修改，故该哈希不是冻结版本；不覆盖 20261017 历史归档 |
| R12 量词、T7(iv)、T8(ii) 与统计披露修正 | 当前工作树；发布 commit/tag/version DOI 均未形成 | **v0.8** | 新增 `test_l1_r12_counterexamples.py`；不新增或改写 4,620-run。ATK-6 固定-\(\alpha\) CUSUM 仅描述；FORCE-1③仅注册 \(\kappa\) 臂；独立复核后另补 \(A^0>0\)、当前-\(\mu_t\) estimand、Jensen 测试换例及旧 \(\sigma\)/C0 口径清理；公开链仍待闭合 |
| R13 T6/C0 核心命题收缩、账本与小样本敏感性 | R13 commit `f816848`；公开 tag/version DOI 未形成 | **v0.9** | 新增 `test_l1_r13_counterexamples.py`、`analysis_cusum_sensitivity.py/.json`；不改写历史 run。T6 主表拆 360 实现＋60 CUSUM 描述；DEL-1 六判据逐项 30-run 账本；C0(ii) 仅非退化 L1 额外审计分离；二次复核补 H4$''$/M1/T1d 前提及报告生成器 R11 合并与归档写保护；公开链仍待闭合 |
| R14 反例、estimand、直接文献与证据重签 | R14 开发源 `6a613086...`；公开 main `dbdf2f6f...`；不可变 tag/version DOI 未形成 | **v1.0** | 新增 R14 反例/优化/SCM 测试、`analysis_r14_math.*`、`x5c`、`x5c_stratified`、`c0cf_v2` 与失败目录；旧 `law_level_lambda` 仅 marker，新反事实仅限显式 SCM。$D_{noise}=0.089799622$ 故 MODEL_SENSITIVE。历史归档不改写 |
| R15 定义、构念、识别、证明与报告治理 | R15 开发源 `0ebbae17...`；公开 main `ec53f987...`；不可变 R15 tag/version DOI 未形成 | **v1.1** | 新增 14 个确定性负控制、`r15_guards.py`、`stats.py`、`analysis_r15_statistics.*`、`analysis_r15_x5c_paired.*`。执行改 n 行动；T2 撤 iff；L1+ N/R/I 来源分割；A_goal 结构点/IRL 区间；V_state/R_def 分账；C2/Route B 修补；tau-b 总体与分场景。旧 a_org/a_via 只作 legacy marker，历史 manifest/results/verdict 不改写，外部验证仍未完成 |
| R16 有序归因、证明缩放、证书与复核边界 | R16 开发/公开 commit 见本轮发布说明；main 同步不替代不可变 tag/version DOI | **v1.2** | RNI/NRI/Shapley 与 N/R/I 语义敏感性；OR 和 T=2 闭环独立枚举；Route B st' 缩放；IRL 区间端点序与 NaN fail-closed；注册完整≠SCM 审计；R16 schema/org/goal/readiness/hashes；浮点容差复核；Ingel/Albantakis/PID 外部协议设计冻结但未执行。R15 及更早证据只读 |
| R17 开环执行、历史形成并列、原生基准与权重界 | R17 开发/公开 commit 见本轮发布说明；main 同步不替代不可变 tag/version DOI | **v1.3** | 多步 A_exec 改预承诺开环序列干预核，反馈复制反例；当前/历史双核心输出与 Lambda 时间原点；R17-native T=3 端到端基准（真值/采样/区间/语义/负控制/证书）；权重闭单纯形对数界/半空间；X2 簿记、X3 语义示例；C1 OU、C2 截断、T1d Le Cam；外部等价/非劣效设计。R16 及更早证据只读 |
| R18 完整剖面证书、联合日志审计、输出约定与 TOST | R18 开发/公开 commit 见本轮发布说明；本轮创建不可变 tag `v1.1-r18` 与冻结重放清单，version DOI 仍待 Zenodo 归档 | **v1.4** | R18 证书强制完整通道向量/分量状态/区间/协议版本、RNI/NRI/顺序平均/流量项/替代语义、目标点与 IRL 区间、开环视界、反思三因子与事件计数、权重与复合值范围；超阈值强制 ORDER_SENSITIVE/MODEL_SENSITIVE 与标量警示。R17-native 组合式夹具升级为单 SCM/单日志模式/单联合批次的端到端内部审计（执行仍按 estimand 要求另设预承诺开环干预流）；开环零值量词改支持集相对、期末观察/观察序列测试约定分离；权重结果统一称精确敏感性刻画；外部协议 TOST 90% 双侧/两个单侧 α=0.05 与非劣效方向精确化。R17 及更早证据只读 |

## 4. 判据时间线（失败与替换不得擦除）

| 时间/版本 | 事件 | 证据地位 |
|---|---|---|
| v0.3 | 矩阵执行接口与原始主判据 | 历史注册 |
| v0.4（2026-10-15/16） | Aepi 改真值精度；ATK-4 正交诚实信号操作化曾 REFUTED，修复场景信号坐标后重跑 | 保留失败—归因—场景修复记录；不是通过调阈消除 |
| v0.5（2026-10-17） | DEL-1⑤⑥、EROSION、EXEC-1、X1--X4 加入 | 后验扩展与单平台机制演示 |
| v0.5 数据检查 | **E2-X1 原判据**“\(a_obj\leftrightarrow\bar u\) 同向且 Kendall \(\tau\ge0.8\)”在 \(\gamma\) 下失败（\(\tau=-1\)） | 原判据失败，不能计入无条件 0 REFUTED |
| v0.5 后验修订 | X1 改三态存在性描述；X2 改 log 域份额＋冻结通道归因 | 明确标 post hoc，非预注册确认 |
| v0.6（2026-10-22） | X5-a/b 执行，X5-c 保持注册 | X5-a 绝对读数证伪器触发；不得概括为全部窗口通过 |
| v0.7（2026-11-02） | 表示定理归一化、贝叶斯局部似然、T7 双误差界、被动执行方向、统计单位与外部效度主张修正 | 数学复审＋新回归；历史主表重评价为 14 CONFIRMED＋T7 INCONCLUSIVE |
| v0.8（2026-11-03） | 检测改固定 \(\delta\)、\(\alpha\downarrow0\)；T7(iv) 加诚实/无精度损失前提；T8(ii) 改逐参数方向；表示证明、soundness、copula 和全文口径修补 | R12 数学复审＋反例回归；旧 CUSUM/FORCE 数值仅按收窄场景保留，公开版本链未闭合 |
| v0.9（2026-11-03） | T6 改 certificate-failure band；C0(ii) 删除完整外部画像相等；M4 确定性口径、注册域方向、D1 归属、可比性术语、T6/T7 账本及 CP 单位修正 | R13 数学复审＋反例回归；ATK-6 俘获仅精确实现，CUSUM 只描述并补 \(t_{29}\) 敏感性，历史归档不改写 |
| v1.0（2026-11-16） | 修复 T1b/T2/T3/T4/T5、离散 $A_{ref}$、比例解释、Lemma 37、Via-Ind；$\Lambda$ 改输出律 estimand；X5-c 两噪声执行并补时分层；C0 改同环境证人；补直接文献对照；证据按类型重签 | R14 反例与 SCM 复审；历史 marker 与新反事实分账，点读数 MODEL_SENSITIVE，旧归档不改写 |
| v1.1（2026-11-17） | 修复执行索引、T2 兼容过强、L0/L1 随机来源、A_goal 识别层级、C2 与 Route B；状态/防御和强制 provenance 输出分账；补三篇直接前驱与统计报告 | R15 审稿反例与构念复审；194 项目标测试和 tau-b 只读重算；旧数值不冒充新构念验证，tag/version DOI 与外部实验未完成 |
| v1.2（2026-11-17） | RNI 改有序残差归因并强制 NRI/Shapley 与语义敏感性；OR 和 T=2 闭环精确验证；Route B 缩放、区间端点序、NaN fail-closed；证书双证据轴及 R16 schema/hash；浮点容差复核；外部协议设计冻结但未执行 | R16 复审闭合；新增 `analysis_r16_source_attribution.*`、R16 证书/闭环/复核测试。旧 R15 validation 与所有历史结果只读；不升级外部验证、tag、Release 或 version DOI |
| v1.3（2026-11-19） | 开环执行修复与反馈反例；历史形成并列输出/固定点植入/Lambda 时间原点；R17-native 端到端基准；权重闭单纯形界；X2/X3 降格；C1/C2/T1d 修正；外部等价/非劣效设计 | R17 大修；新增 `open_loop_execution.py`、`formation_audit.py`、`r17_guards.py`、`native_benchmark.py`、`analysis_r17_*` 与测试。旧 R16 validation 与所有历史结果只读；不升级外部验证、正式 Release 或 version DOI |
| v1.4（2026-11-21） | R18 完整剖面证书与强制敏感性标志；联合日志端到端内部审计；开环零值支持集量词与期末观察约定；权重术语统一为精确敏感性；TOST/非劣效方向精确化；主文压缩 | R18 局部关键修订；新增 `r18_guards.py`、`native_joint_audit.py`、`analysis_r18_native_joint_audit.*` 与 22 项测试（总 273）。R17-native 工件保持只读并被 supersede；创建不可变 tag `v1.1-r18` 与冻结重放清单；version DOI、外部执行与独立复现仍未完成 |

## 5. R11→R13 重点判据与主张 supersession 明细

| 项目 | 旧判据/主张与 verdict | 新判据/主张与 verdict | SPEC、代码与数据路径 | 数据查看与 post hoc 状态 |
|---|---|---|---|---|
| DEL-1⑤⑥ | v0.5 单-\(\varphi\) bracket；旧主表 T7 CONFIRMED | v0.7 双误差 bracket；30-run R11 replay 为 120 CONFIRMED＋60 INCONCLUSIVE、30/30 run-level INCONCLUSIVE | 历史 `a6e7670`/`runs/20261017_full/del1`；R11 工作树/`runs/20261102_r11/del1` | 2026-11-02 数学复审在查看历史结果后修正推导错误；标 superseded/post hoc，旧 CONFIRMED 不作新定理证据 |
| 检测渐近 | R11 写固定 \(\alpha\)、\(\delta\downarrow0\) 全称下界；ATK-6⑥ CONFIRMED 被用于对应叙述 | R12 定理改固定 \(\delta>0\)、\(\alpha\downarrow0\)；ATK-6⑥只保留固定 \(\alpha=10^{-3}\) CUSUM 描述，不直接检验新极限 | v0.7→v0.8；历史 `a6e7670`/`runs/20261017_full/main` 的 ATK-6 `damages_detect`；R12 工作树测试 | 2026-11-03 常数停止反例后撤回全称命题；数值本身不回写、不重标为定理证明 |
| T7(iv) | \(q=1\Rightarrow A=A_{self}\)；DEL-1④仅测 \(F_{ext}=0\) | 结构中介与全复合无损失拆分；后者需诚实、sound update、无精度损失及其他通道不变；原 \(F_{ext}\) 检查保留 | v0.8；历史/ R11 DEL-1 同一路径；新增 T-R12-T7 | 理论前提修复，无新独立实验；不得从原 \(F_{ext}\) CONFIRMED 推出全复合无损失 |
| T8(ii) | 降低 \(\theta\)、提高 \(r\) 等与 \(\delta^*\)、\(A_{min}\) 同升；FORCE-1③ 90/90 | 逐参数单调性；FORCE-1③只支持注册 \(\kappa:0.2\to0.3\) 臂，\(\theta/r\) 反例入 T-R12-T8 | v0.8；历史 `a6e7670`/`runs/20261017_full/force1`；当前 `dynamics.py` 与 R12 测试 | 2026-11-03 代数反例后收窄解释；90/90 仅是特定实现重放，不支持旧全称句 |
| CUSUM 区间 | 历史报告 \(1.951\pm0.034\)，仅写“30 seeds 95%CI” | R12 明确正态近似半宽；R13 另公开 30 个比值并补 \(t_{29}\) 半宽 \(0.034970\)，不是新样本或功效分析 | 历史数值不变；`make_report.py`、`analysis_cusum_sensitivity.py/.json` 与 v0.9 ATK-6⑥ | 只读历史重算；不改点估计、verdict 或历史文件 |
| T6 blind zone | R12 由上比较在 \(\kappa<\delta<\theta/W\) 推出 M1 不触发、M3 被超越并断言 \(D\to1\) | R13 仅保留 M3-only 正保持证书失效；\(D\equiv0\) 为合法反模型；ATK-6 的 30/30 俘获只属精确截断饱和实现 | v0.8→v0.9；主文/附录 T6、`dynamics.py`、T-R13-T6；历史 ATK-6 键名保留 | 2026-11-03 零损伤反例后收缩定理，不把实现动力学偷运进一般前提；历史数值与 verdict 不改写 |
| C0(ii) | R12 主张指定行为相同且 KG/Dung/Feng 完整画像相同而复合 \(A\) 不同 | R13 仅主张非退化 L1 中被动行为相同、\(A_{epi}:1\to0.5\) 使复合严格下降、\(\Lambda\) 额外分离；不再主张外部完整画像相等或外部映射不能区分 | v0.8→v0.9；主文/附录 C0、C0-DEMO 规约、T-R13-C0；E12.6 标记边界 | 严格映射与自身 C0(i) 冲突后收缩；C0(i) 与被动行为不可识别 corollary 独立保留；TV=1 仅解析构造，旧 $1-s(\gamma)$ 场景不冒充反事实实证 |
| T6/T7 主表账本 | T6 同一行混合 420 次 CONFIRMED 与 CUSUM 描述；T7 只报 120+60 汇总 | T6 拆 360 CONFIRMED＋60 DESCRIPTIVE；DEL-1(i)–(iv) 各 30 CONFIRMED、(v)–(vi) 各 30 INCONCLUSIVE，故 30/30 run-level INCONCLUSIVE | v0.9；论文实验节、附录 N、`runs/20261102_r11/del1` 只读复核 | 仅澄清既有计数，不重跑、不改历史或 R11 replay |
| 报告再生成链 | 旧生成器只读历史 del1，会把 T7 恢复为 180/180 CONFIRMED，并默认写 root/report.md | 历史 20261017_full 默认合并独立 R11 replay，T7=120/180 INCONCLUSIVE；默认输出 sim/reports/，缺 replay 时 fail-closed，仅显式允许才写历史根或禁用合并 | `make_report.py`、`test_report_r13.py` | 独立复核发现当前代码缺口后修复；回归确认 T6=360/360、T7=120/180、缺文件报错、默认输出及历史 report 不变 |
| T6 保持与 M1 前提 | pointwise floor 漏 $A_{via}^{min}$，$A_j^{base}=0$ 可破坏正性；M1 注册被读成无条件全域有界 | 增加 H4$''$ 非退化基线，pointwise/uniform 均含 viability；M1 保持需正常响应且 $\theta+\ell\delta$ 低于俘获阈 | 主文/附录 T6、T-R13-T6、SPEC_estimators | 二次数学复核发现后修补，不更改历史数值或窗口外 verdict |
| C0/T1d 构造前提 | situation-independent 被误当精度 0.5 充分条件，covert $\gamma$ 被误当 $\Lambda=0$ 充分条件；小 TV 被误当 Aepi 严格损失充分条件 | C0 明确公平二值真值+独立信念、非空手术史+非退化背书/反事实逐时 TV=1；T1d 显式假设任意小 TV 的 (R-epi) 退化族 | 主文/附录 C0/T1d、C0-DEMO 规约、R13 测试 | 二次数学复核发现后补齐证人前提；正交噪声反例保持 |
| Jensen 回归测试 | 首轮对称边际例中 \(A_2=1/A_1\)，实际可达到 Jensen 等号，测试反例无效 | 改用四个联合乘积全不同的双非退化边际；补零基线 T8 反例和当前-\(\mu_t\) 定义 | `sim/tests/test_l1_r12_counterexamples.py`、`SPEC_tests.md` | 独立只读复核发现后修正测试；论文的 generally non-sharp 命题不变，首轮测试通过不再被当作无误证据 |

## 6. 发布前待闭合项

1. R14 论文、SPEC、代码和数学回归测试冻结为开发源 commit，并在公开 `RELEASE_NOTES.md` 记录其与 fresh-history 公开快照的对应；不得以 R13 基线或 dirty 工作树冒充该版本。
2. R11 DEL-1 replay 与 R14 X5-c/C0-CF 的 preregistration、manifest、results、verdict table 和对应代码随公开快照发布，明确不计入原 4,620-run；后续新 DEL-1/全矩阵运行仍须另目录、另 manifest，并记录 SPEC、代码哈希、配置、独立随机单位及嵌套关系。
3. 建立新的不可变 release tag 与 version DOI；现有 `v1.0-r10.1` 和 Zenodo concept DOI 只证明历史版本，不自动覆盖 R11--R14，concept DOI 不能代替 version DOI。
4. 论文 Data availability 标明公开 main、开发源 commit 的记录位置和历史 concept DOI 边界；不可变 R14 tag/version DOI 未形成前，不得勾选“论文—代码—数据—DOI 链闭合”。
5. 外部实验仍只有 protocol outline；power analysis 必须在查看 outcome data 前冻结，不得回写为已完成。
6. selector-conditional DEL-1 估计器、非退化 bracket、独立基质外部验证和外部专家/校准对照均未完成；X5-c 仅限新 SCM，不能替代这些事项。

## 7. R14 supersession 明细

| 项目 | R13 及更早旧主张/证据 | R14 当前处理 | 证据与历史边界 |
|---|---|---|---|
| T1b | fidelity、endorsement consistency 为正即称全部活性，RES-1 60/60 被当作正性证据 | L2 另需 $\Lambda_{ref}>0$ 与有限离散非退化系综；$\Lambda_{ref}=0\Rightarrow A=0$ | T-R14-T1B；RES-1 只测闸门，不是完整正性测试 |
| T2/T3 单调性 | $F_{ext}>0$ 或离开 Fix 即严格下降，且分支未分层 | $\Fext/\Fint$ 相对基线上升、$d^1>d^0$、$A^0>0$；$\gamma$ 仅 L1+、背书复合分支仅 L2 | T-R14-ORG/GOAL；旧场景仅有利特例 |
| T4 | 凹目标被说成内点分散最优；防御证明索引矛盾；非等权代码固定 W5[0]；非增响应被误当严格可降 | 攻击者最小化，正保持域极点闭式，零保持边界允许非极点；防御另需局部严格可降 responsive 与 E>0，条件非充分；通道权重索引修复 | `analysis_r14_math` 顶点/网格/符号证书；T-R14-T4-INDEX、平坦响应/零保持反例；旧 $\varsigma\ne1$ KKT 声明撤回 |
| $A_{ref}$ | 连续变量与 k-NN $I/h$ 通用归一化 | 有限离散 Shannon 系综；高斯 $I/h=1.2374555817>1$ 排除 | T-R14-REF；旧离散表数值路径不受影响 |
| AX6a | 各通道 canonical ratio scale 已证 | 只证值域、零点、注册变换；比例解释为规范假设，幂重参数化可翻转排序 | T-R14-SCALE；表示定理仍条件成立 |
| $\Lambda$ | 历史合法性/篡改史、MI proxy、退化认证例外和 ENV-0 truth mode 混用 | 唯一实际/无手术背书输出律；$\mathcal H^{surg}$ 另列；无认证例外；marker 与新 SCM 分账 | `counterfactual.py`＋X5-c stratified；旧 ATK/β_π/A_ref/T2/T3/C0 marker 不升级 |
| T3b | AI 曲线被写成期望与触发概率界验证 | 旧曲线只列平台描述，HI 期望/概率界未执行 | 主表改 descriptive，不能据此称定理经验确认 |
| T5 脚本 | 仅知 $G,\pi$ 并控制 $B,O$ 即推出脚本 | K-full 完整状态、充分统计量与噪声受控，TV≤ν+η | T-R14-PROOF 正反控制 |
| Via-Ind | 条件独立“对应”乘法门和几何聚合 | 乘法门为独立设计；Via-Ind 不决定门权重或聚合形式 | T-R14-PROOF |
| C0/Feng | 旧环境分布也变化；首轮 c0cf 另有 AX0=0、empowerment=0、目标退化和 illustrative 因子；Feng 被称一般 rank consistent | 新 C0-CF-v2 非退化同环境全轨迹 $(E^T,O^T,A^T)$ 证人；Feng 仅描述比较，C0-CORR 无 Feng 实现 | `c0cf_v2` 实际值 0.8312378961/0.7236346187；旧 c0cf 标 SUPERSEDED，C0-DEMO 不改写；失败 `c0cf_failed_initial` 保留 |
| X5-c | R13 及旧 JSON 均 registered, not run；pooled 后 SPEC 又修改，历史 SPEC 快照不全 | R14 新 SCM 已执行；pooled preregistered＋post hoc 时分层与 SESOI=0.01 后果，点值 MODEL_SENSITIVE；common random numbers 与 arm evaluations 分账 | 旧 JSON 保持原状态；新目录独立，$D_{noise}=0.089799622$；`PROVENANCE.md` 记录缺快照、源码演进和当前 preservation copy；不是外部验证 |
| 证据总表 | 14 CONFIRMED＋T7 INCONCLUSIVE、zero-refutation 宣传汇总 | 数学状态、criterion outcome、证据类型、外部验证分列，不再给“确认理论”总数 | 历史 CONFIRMED 字段原样保留；E2-X1、ATK-4、X5-a、post hoc 与 unrun 全披露 |
| 数值边界 | 容差外负值原样返回，公开旧快照有边界失败报告 | 统一 1e-9 容差内 clipping＋warning，超容差/NaN/Inf fail-closed | T-R14-CLIP、T-REF7 更新；公开旧快照差异不冒充本工作树同一失败 |

## 8. R15 supersession 明细

| 项目 | R14 旧主张/缺陷 | R15 当前处理 | 回归与历史边界 |
|---|---|---|---|
| A_exec/T1a | $A_{t:t+n}$ 含 n+1 行动却除 n log|A|；两比特可得 2 | 改 $A_{t:t+n-1};O_{t+n}$；一般写 sup，紧有限 DMC 才 max/BA；零值含环境解耦 | T-R15-EXEC；代码 API 的 n 本来就是行动数，历史数值不回写 |
| T2 兼容性 | no surgery+mediation+honesty iff；四轨含绝对 Lambda=1 | 撤回 iff；逐分量定义和七项结构充分条件；Lambda 相对基线，Fix/其他因子不可省 | T-R15-T2 两反例；旧 ATK-4 四轨仅 legacy marker |
| T2 盲性 | o 未动即信念不变、Agoal 对 gamma/delta 普遍盲 | 行动无关环境的显式存在性证人；结构 Ueff/Fix 固定证人，IRL 不普遍盲 | 测试与附录同步，旧场景仅有利特例 |
| 随机来源 | 独立 R 驱动可在 L0 得 A=1，却称 autonomy not randomness | L0 明确 internal-causal only；L1+ R→N→I 分解，纯随机得 0 | T-R15-RANDOM；旧 a_org 不冒充 R15 点值 |
| A_goal 识别 | every channel point identified 但漏列 goal，IRL 又承认塑形自由度 | 结构读取点值与行为 IRL 集合/区间分模式；不动点定理各自前提完整 | T-R15-GOAL；ENV-0 只结构读取，未实现黑盒 IRL |
| viability | m_j=0 即使当前行为完好也令当前 A=0 | V_state/A_state 与 R_def/A_res 分离；防御零不自动状态零 | T-R15-VIA；EROSION 仅 R14 resilience legacy |
| C2 | 附录有 δ+|R|-s，主命题却只写 s>s_c | 持续攻击 s>δ+s_c；攻击移除 δ=0 才 s>s_c | T-R15-C2；历史 δ=0 数值不变 |
| Route B | 半平面线矛盾误写 properness；权和归一跳步 | 改商锥 pointedness；显式 w/s、斜率 1/s，A0 只消截距 | T-R15-PROOF；条件性表征结论不变 |
| 输出 | 高分与篡改史可共存但仅文字警告 | 强制 H_surg、Lambda、来源注册、V_state/R_def；unknown 限 LIMITED，永不称完整性证书 | T-R15-OUTPUT；不是外部验证 |
| 统计/实验报告 | 480k 被称 main contexts、C0 权重不全、tau 变体/ties 不清、SESOI 与误差近等量 | 480k cell eval/120k base draws；全权重及等权敏感性；tau-b 总体和分场景；0.01/0.0096=1.0417 仅数值判据 | `analysis_r15_statistics.json` 只读新文件，旧 JSON/结果不改写；场景 4 org-heavy 最低 0.8667，不保留统一 0.93 底线 |

## 9. R16 supersession 明细

| 项目 | R15 残留缺陷 | R16 当前处理 | 回归与证据边界 |
|---|---|---|---|
| L1+ 来源份额 | Kramer 链式和被默认读成顺序无关的客观因果份额 | RNI 是独立的有序残差归因公理；非退化 R/N 强制并列 NRI 与 I-last Shapley-style；N/R/I 语义预注册，PID 仅 comparator | OR：0.616311↔0.383689，平均 0.5；T=2 混合 XOR：1↔0，平均 0.5；N=R,A=R 时 RNI=0、NRI=1，纯随机零值不写成顺序/语义不变。链式和仍等于联合 DI，但不识别唯一来源；`analysis_r16_source_attribution.json` |
| Route B 第 6 步 | 由齐次性直接写 $\varphi(z+t')=\varphi(z)+t'/s$，漏掉 $w\cdot(t'\mathbf1)=st'$；旧测试只复述错误等式 | 改 $\varphi(z+st')=\varphi(z)+t'$，$q=st'$ 后得 $q/s$，再归一化 | 测试从 $g(u+t'\mathbf1)=g(u)+t'$ 数值推导并排除未缩放形式；最终表征不变 |
| T2 区间与非有限值 | “区间非减”未定义；NaN 与任何值或自身比较可 fail-open | 默认上下端同时非减；独立跨世界保证需 $\ell_1\ge u_0$ 或注册耦合；所有值先验有限，NaN/Inf raise | 交叉区间、NaN→NaN、±Inf 负控制；端点序不冒充 reward 逐元素配对 |
| 证书证据与 legacy 边界 | 完整字段但无 SCM 可给 SCM_AUDITED；旧 Bundle 数值可手工冒充 L1 N/R/I | registration completeness 与 mechanism evidence 分轴；无 SCM 仅 REGISTERED_COMPLETE；R16 schema/org/goal/readiness 和 L1/L2 双 hash 强制 | producer/writer 共合同，伪造字段/旧 schema/坏 hash 拒绝；hash 仅绑定工件，SCM_AUDITED 仍非外部验证 |
| 数值/状态边界追加 guard | 近退化 part-total 绝对容差可让 flow share>1；state=1/viability=0 可获审计上限 | ratio 直接检查，1e-13/1e-15 拒绝；强制 $A^{state}\le V_{state}$，0/0 可登记但正状态禁配零存续 | 新负控制使总数 228→230；首次候选 7b74ec4 被 superseded，重新冻结验收 |
| 配对与源归因复核 | 全部 JSON 叶子逐位相等，平台末位浮点差可假失败 | 状态/seed/count/hash/类型精确，float 用 $10^{-12}$ 双重容差并报最大差；源归因另有独立闭式锚 | 容差外、非有限和类型改变仍失败；X5-c 数值/verdict 不变，POST_HOC_PASS 不升级 |
| 外部协议与写作 | Ingel/Albantakis/PID 计划散见 Related Work/Conclusion；正文修订史口吻、N/A 与 UNKNOWN 表述不一致 | `EXTERNAL_VALIDATION_PROTOCOL.md` 统一设计冻结；正文保留最终定义与证据边界，历史集中本账本；UNKNOWN 才触发 LIMITED，T8 明确 A_state | 协议仍 UNEXECUTED；外部 SESOI/power、时间戳、独立基质、version DOI 和不可变 release 未完成 |

## 10. R17 supersession 明细

| 项目 | R16 残留缺陷 | R17 当前处理 | 回归与证据边界 |
|---|---|---|---|
| 多步 A_exec | 恰好 n 行动的普通 MI 仍允许反应式策略，观察→后续动作相关被计为执行能力 | 预承诺开环序列分布+干预核；后续动作不读中间观察；实际反应式策略另列 | 反馈复制旧 0.5/开环 0；控制序列上界、BSC 解析、单序列坍缩；EXEC-1/ENV-0 仅 n=1 特例 |
| 历史自主性 | 手术史/Lambda 主要作辅助元数据，固定点植入可当前剖面不变 | 当前结构 profile 与历史形成 profile 并列 top-level 输出；formation_status 不由通道推断 | U0≠U1 均 Fix、A_goal=1、F_ext=0；R17 证书双 profile/time_origin/scope 匹配 |
| Lambda 时间语义 | “移除所有注册手术”未区分审计时移除与最初植入阻止 | 默认 AUDIT_CURRENT_REMOVAL；ORIGINAL_IMPLANT_PREVENTION 另 estimand，须重算 descendants | 固定点 witness 审计时=1、最初阻止=0；证书拒绝 origin/scope 不匹配 |
| R16-native 证据 | 小型 guard 与历史 4620-run 不同量级，缺同一实例端到端 | R17-native T=3 反应式 SCM+开环执行审计，真值/采样/区间/语义/负控制/证书 | `analysis_r17_native_benchmark.json`；内部概念验证，非外部构念验证，非通用 IRL 求解 |
| 权重稳健性 | 五组权重+tau-b 被读作整体稳健 | 闭单纯形 log 上下界与半空间；22 唯一有限对比 17 权重依赖；零分量单列 | `analysis_r17_weight_regions.json`；闭单纯形为敏感性松弛，表示定理内点严格正；不冒称统计功效 |
| 聚合/归因口吻 | X2 canonical attribution、X3 排序/零歼灭作独立证据 | X2 选定几何聚合器簿记，可负/无穷；X3 语义示例；几何形式不证比例尺度/因果 | 论文摘要/讨论/结论同步；历史 JSON 不改写 |
| C1/C2/T1d | C1 确定性 ODE 写平稳方差/AR(1)；C2 D=1 吸收未截断；T1d 把 Le Cam 界归因有限容量 | C1 局部 OU 固定噪声/采样前提；C2 [0,1] 截断/投影；T1d 任意检验界，有限容量只限制可实现族 | 正文命题与附录 restatement 同步 |
| 定理层级 | T3/T5/T8 与实质定理并列营造等强度印象 | T3/T8 设计命题，T5 簿记推论，T2 任何单一通道不足；不宣称 exactly-five 最小性 | 环境/标题/交叉引用更新；证明内容不变 |
| 外部等价设计 | “较粗模型相当即否证”依赖不显著差异 | 冻结 BA/Brier 等价/非劣效界值、独立下游结局、嵌套实例级验证、独立研究者复现 | 协议仍 DESIGN_FROZEN_UNEXECUTED；界值是工程设计不是已验证域 SESOI |

## 11. R18 supersession 明细

| 项目 | R17 残留缺陷 | R18 当前处理 | 回归与证据边界 |
|---|---|---|---|
| 最终证书剖面 | `current_structural_profile` 仅存 state_autonomy/viability/defense/composite_scale；RNI 单点 0.4608565 输出，NRI/顺序平均/语义替代只留在外部 JSON | R18 schema 强制完整通道向量（值/状态/区间/协议版本）、RNI/NRI/顺序平均/各流量项/替代语义划分、目标结构点与 IRL 区间、开环视界、反思三因子与日志事件计数、权重与跨口径复合值范围；标量必须等于注册 RNI 口径复合值 | `r18_guards.py` producer/validator/writer 共合同；RNI≈1/NRI≈0 时强制 ORDER_SENSITIVE+MODEL_SENSITIVE、警示文本与 SENSITIVITY_QUALIFIED 等级；剥离任一字段 fail-closed；R17 证书仅作兼容层 |
| 顺序敏感性呈现 | 正文未直接报告 NRI≈4.38e-16 与顺序平均 0.5 的复合后果，形成事实单向呈现 | 正文新增原生基准结果表：RNI/NRI/顺序平均复合值 0.4608565/0.0003908/0.4011989，替代语义划分≈0.4608565，复合范围 [0.0003908,0.4608565]；摘要/引言/结论同步 | 精确证书锚定上述端点（独立 composite_A 复核）；采样证书另报偏差放大说明 |
| 原生基准证据含义 | R17-native 为同配置分对象组合式夹具，分对象采样，却笼统称端到端；事件级 A_ref/Lambda 载体仍列为未实现 | 单 SCM/单日志模式/单联合操作批次估计来源归因、认知、反思 fidelity/一致性/Lambda、存续/防御；执行按 estimand 要求另设同环境预承诺开环干预流（仅读期末观察）；目标仍注册结构读取+IRL 区间；全部通道进入同一 R18 证书流水线 | `native_joint_audit.py`、`analysis_r18_native_joint_audit.json`（8192 轨迹/流，日志 SHA-256 绑定，事件计数 24576/24576/8192）；R17-native 工件只读保留并被 supersede；仍为内部概念验证，非外部构念验证 |
| 开环零值量词 | “所有允许纯序列同分布”未区分容量口径与固定 Q 口径；点质量 Q 下 MI 恒零 | 容量口径：所有可被某许可 Q 赋正概率的序列核相同；固定 Q 口径：仅正概率支持集内序列核相同；点质量反例入回归 | `open_loop_zero_iff_positive_support_rows_identical`；附录与 D-exec 量词同步 |
| 期末观察/观察序列 | `memoryless_sequence_kernels` 构造整段观察序列 Kronecker 信道（p=0.1 两步得 0.5310044），与正文期末观察估计量（0.2655022）偏移 | 改名 `memoryless_observation_sequence_kernels`（保留兼容别名）并新增 `memoryless_terminal_observation_kernels`；两对象分别测试并显式标注 | R18 约定测试锚定 0.2655022 与 0.5310044；R17 旧测试注明对象为观察序列容量 |
| 权重结果术语 | 精确界/半空间仍可能在摘要/结论被概括为“稳健” | 统一称精确敏感性刻画与权重可行区域；闭单纯形（含零顶点）为敏感性松弛，表示定理与证书权重为内点严格正 | 22 唯一有限对比 17 权重依赖、5 边界 ties 非负；不冒称整体排序稳健 |
| 外部协议 TOST | “两个单侧 95% CI 完全落在 [-Δ,+Δ]”不严格（单侧区间无界）；摘要/结论仍把 equivalence margins 列为未完成 | TOST：两个单侧 α=0.05 检验均拒绝，等价于 90% 双侧 CI 落入界值；用 95% 双侧则单侧 α=0.025；NI 方向 δ_BA=BA_full−BA_reduced 上界<Δ_BA_NI、δ_Brier=Brier_full−Brier_reduced 下界>−Δ_Brier_NI；摘要/结论改“工程界值已冻结，域 SESOI/功效/外部执行未完成” | 协议仍 DESIGN_FROZEN_UNEXECUTED；界值不变，仅决策规则精确化 |
| 篇幅组织 | 103 页同时承担概念/数学/版本史/软件验证/预协议 | 主文聚焦当前定义、核心结果、关键反例与当前证据；历史判据替代/旧标记隔离/版本沿革集中于本账本与仓库；实验附录历史叙述压缩 | 本轮页数见 R18 validation；115 引用与 6 图保持 |

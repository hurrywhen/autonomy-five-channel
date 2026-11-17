# SPEC_estimators —— R3b 分量与复合指标估计规约

**版本**: v1.2（2026-11-17：R16 有序归因、闭环与证书/复核契约）｜**依据**: input v2.1 §3.3–§3.5、§5；附录 §2（数学预备）、§5（分量良构性）、§10（可辨识性与黑盒降级）。
**R16 附注**：RNI 只称有序残差归因，强制 NRI/Shapley 与语义敏感性；新增 OR 和 T=2 闭环独立枚举、Route B st' 缩放、IRL 端点序、NaN/Inf fail-closed、R16 schema/hash 和 REGISTERED_COMPLETE≠SCM_AUDITED。配对复核仅 float 叶子用容差，外部协议仅设计冻结。
**R15 附注**：执行统一为 \(A_{t:t+n-1}\) 对 \(O_{t+n}\)，恰好 n 个行动；一般非紧策略类只写 sup，紧有限 DMC 才写 max/BA。L0 的 \(A_{org}\) 仅内部因果；L1+ 按 R→N→I 链分离 \(F_{rand},F_{norm},F_{ext}\)，旧 ENV-0 聚合 S 值不冒充新 estimand。T2 撤回兼容 iff/四轨充要，盲性改显式证人。\(A_{goal}\) 分结构读取点值与 IRL 集合/区间两种模式。当前 \(V_{state}\)、防御 \(R_{def}\)、\(A^{state}\)、\(A^{res}\) 分账；强制输出手术史、Lambda、来源注册及未知证据上限。新增 `r15_guards.py`、14 个 R15 反例和 tie-aware `analysis_r15_statistics.py`；旧 R14 manifest/results/verdict 不改写。
**R14 附注**：\(A_{org}\) 仅称直接/未中介绕过抵抗，严格下降须 \(F_{ext}/F_{int}\) 相对基线上升；删除 \(A_{goal}^{hist}=\Lambda A_{goal}\)；\(A_{ref}\) 限有限离散系综；\(\Lambda\) 改唯一实际/无手术背书输出律 estimand，旧 marker 全面隔离；新增 X5-c 时分层和同环境 C0-CF；数值越界统一 fail-closed。
**R13 附注（2026-11-03）**：E10.1/E12.1 的一般 T6 上比较只给 certificate-failure band；精确饱和模拟的俘获不反推一般定理。E12.2 增加 30 个种子比值公开与 Student-\(t_{29}\) 敏感性；E10.4 不再主张外部框架完整画像相等。
**总原则**: 每个量有两条实现路径——**真值路径**（平台张量枚举，精确，用于标定与估计器验证）与**估计路径**（从日志轨迹的有限样本估计，用于测量期）；估计路径必须对照真值路径报告偏差/方差（input 风险 R2 的落地）。信息计算内部以 nats 计（log 底 e）；论文/审计若用 bit 必须显式标注并由 `nats_to_bits` 除以 ln2 转换，禁止混用单位。

---

## 1. 公共约定

- **E0.1 接口二分**：`truth_*(platform_tensors) -> exact value` 与 `estimate_*(trajectory_log) -> (point, interval, diagnostics)`。同名量的两路径签名一一对应。
- **E0.2 不确定度**：估计路径输出 `(点估计, 区间)`；区间构造法逐量登记于下文；真值路径区间退化为点。
- **E0.3 标定期先行**（input §5.2）：标定干预拟合响应函数，产出 H2 换算常数 χ、策略漂移容差 η、强度比 ρ=C_del/C_self。权重 $w_i$ 只能取等权默认、独立专家/利益相关者引出或受控单通道行为权衡协议的注册值，禁止以需要预知 F/w 的“推论 6.8 回归”充当非循环估计；全部配置化参数入日志 metadata。

## 2. A_org（来源）：DI 分解

- **E2.1 定义（R16 有序残差归因）**：L0 保留 $F_{int}=I(S^T\!\to\!A^T)$、$F_{ext}=I(I^T\!\to\!A^T\,\|\,S^T)$ 与 $A_{org}^{(0)}=F_{int}/(F_{int}+F_{ext})$，但只称内部因果份额。L1+ 注册 $N=(G,B,M)$ 与外生创新 $R$，主顺序 R→N→I 计算 $F_{rand}=I(R^T\!\to\!A^T)$、$F_{norm}=I(N^T\!\to\!A^T\|R^T)$、$F_{ext}=I(I^T\!\to\!A^T\|N^T,R^T)$，$A_{org}^{RNI}=F_{norm}/(F_{norm}+F_{rand}+F_{ext})$。这是独立的规范性强 attribution 选择，不是唯一因果分解：R 先扣除随机寄存器信息，N 其次获得规范状态中介影响，I 最后只计直接 bypass 残余。全零分母 fail-closed；统一写 $F_{src},F_{oth}$ 后严格下降判据为 $F_{oth}^1/F_{src}^1>F_{oth}^0/F_{src}^0$。历史 ENV-0 没有 N/R 分割，旧 a_org 只保留 legacy internal-causal marker。
- **E2.1a 顺序与语义敏感性（强制）**：R/N 均非退化时必须并列输出 N→R→I 的 $A_{org}^{NRI}$ 和两玩家 Shapley-style 描述量：$F_{rand}^{Sh}=\{I(R^T\to A^T)+I(R^T\to A^T\|N^T)\}/2$，$F_{norm}^{Sh}=\{I(N^T\to A^T)+I(N^T\to A^T\|R^T)\}/2$，外源仍最后条件化，$A_{org}^{Sh}=F_{norm}^{Sh}/(F_{norm}^{Sh}+F_{rand}^{Sh}+F_{ext})$。Shapley 只消除两种顺序任意性，不冒充干预识别或 PID；PID 另作外部协议 comparator。N/R/I 角色按 SCM 更新所有权、外生寄存器和外部路径在看分前预注册；合理替代语义划分另报范围，禁止通过把噪声改名规范记忆或反向重分类择高分。
- **E2.1b 非唯一性回归锚**：独立公平比特 $R,N$、$A=R\lor N$、无 I 时，以 bit 计 $I(R;A)=I(N;A)=0.311278124459$、$I(N;A|R)=I(R;A|N)=0.5$、联合 DI=$0.811278124459$；$A_{org}^{RNI}=0.616311...$、$A_{org}^{NRI}=0.383689...$、$A_{org}^{Sh}=0.5$。链式和相等不推出份额唯一。另有 $N=R,A=R$ 时 RNI 规范份额=0、NRI=1；因此纯随机的零值只限主 RNI 顺序，不得写成顺序/语义重分类不变命题。`flow_share` 必须直接检查 part/total 比率，禁止用绝对 part-total 容差让近退化分母产生 >1 份额。
- **E2.2 真值路径**：按定义逐项枚举（前缀缓存，规模约束 SPEC_platform §7）。`source_attribution.py` 另提供有限二值序列联合表的独立精确枚举；至少验证一个 $T=2$ 行动反馈闭环，分别检查纯随机、纯规范、混合策略、N 中介影响与直接 bypass，以及任意 R/N 顺序下三项和等于联合 DI。一步联合表不能替代多时刻验证。
- **E2.3 估计路径**：plug-in 估计＋偏差标注（DI 插件偏差 O(·/N)，input 风险 R2）；闭环下必须用因果条件化（禁止普通条件 MI 替代——Kramer Property 2 反例为回归测试 T-DI2）。
- **E2.4 黑盒降级（R15 单侧证书）**：随机化探针下 $F_{ext}^{obs}=I(I^T;A^T)$（引理 2.3.1：外源随机化 ⇒ MI=DI，测试 T-DI1）。bypass 语义下它是因果 $F_{ext}$ 的**下估计**，结合 $F_{src}\le F_{src}^{base}(1+\eta)$ 只给**条件认证上端** $\min(1,F_{src}^{base}(1+\eta)/[F_{src}^{base}(1+\eta)+F_{ext}^{obs}])$；L1+ 因 $F_{rand}\ge0$，舍去该项仍保守。下端永远不是认证界：L0 的 $F_{src}^{base}(1-\eta)/[F_{src}^{base}(1-\eta)+F_{ext}^{obs}]$ 只作参考；L1+ 还必须注册 $r_{max}\ge F_{rand}$ 并用 $F_{src}^{base}(1-\eta)/[F_{src}^{base}(1-\eta)+r_{max}+F_{ext}^{obs}]$，否则不显示下端。mediation/adaptive probe 不适用该证书。
- **E2.5 $F_{ext}$ 通用后验路径与调度**（第 5 步，T-COV）：按 params 调度——(i) **β_π**（旗标切换策略，SPEC_platform P4.5）：$F_{ext}=\sum_t\mathbb E_{S_t}\big[H(\bar\pi(\cdot\mid S_t))-\sum_i flag_i\,H(\pi_i(\cdot\mid S_t))\big]$（混合条件律的 Jensen 间隙；$\bar\pi=\sum_i flag_i\pi_i$，$\pi_i$ 由扁平策略张量与 flag 重建；$S_t$ 边缘精确）；(ii) **静态手术**（β_G/δ/β_Endorse，无外源 I 节点）⇒ $F_{ext}\equiv0$ 平凡成立（干预过程为空）；(iii) **α/σ/γ**：引理 7.2.1 双项零残余路径（既有）。β_π×α 复合暂不支持（显式报错；场景步按需扩展）。

## 3. A_exec（执行）：策略类 empowerment

- **E3.1 定义（R15 恰好 n 行动）**：$\mathcal E_t^\Pi=\sup_{p(a_{t:t+n-1})\in\mathrm{conv}(\Pi_t)} I(A_{t:t+n-1};O_{t+n}\mid S_t)$；$A_{exec}=\mathbb E_t[\mathcal E_t^\Pi]/(n\log|\mathcal A|)$。只有非空紧的可行输入集与固定有限信道才将 sup 写 max；BA 仅限显式离散无记忆输入—输出信道，不能自动覆盖一般闭环策略类。零值=无可用行动—结果信息，可来自策略库坍缩或环境解耦。
- **E3.2 真值路径**：表格信道容量——枚举（小字母表）或自实现 Blahut–Arimoto（不引 scipy；收敛容差入配置）。实现形态：BA 核心迭代（面内点信道）＋`channel_capacity` 循环顶点方向上升（I(q) 凹 ⇒ 坐标级精确线搜索收敛到全局最优），精度由 KKT 证书 gap=max_a D(W_a‖out)−I(q) 保证（边界最优信道不依赖迭代阈值）。
- **E3.3 分解诊断（无助鉴别器）**：同时输出 $\mathcal E^{env}$（不限策略类）与 $\mathcal E^\Pi$；无助签名=$\mathcal E^{env}$ 完好而 $\mathcal E^\Pi\to0$；真能力坍缩=两者同降（附录 §5.4）。
- **E3.4 黑盒（R11 识别边界）**：独立探针可算且 $A\perp S\Rightarrow I(A;O)\le I(A;O\mid S)$；一般被动观察方向未识别，ENV-0 的 obs>cond 仅实例描述，不作单侧界。连续动作用注册有限量化或同协议容量归一化，禁止通用 $\log Vol$ 归一化。
- **E3.5 视界剖面**：报告 $n\mapsto\mathcal E^\Pi(n)$ 饱和曲线（C0 映射中 Dung"长期规划"维度的对应物）。
- **E3.6 真值路径接口与第 4 步范围**：真值函数作用于显式信道 $W$（$|\mathcal A|\times|\mathcal O|$ 行随机矩阵）；策略类 $\Pi$ 以**输入支撑限制**表示（P3.5 的确定性策略子集 ⟺ 行动子集单纯形，$\mathrm{conv}(\Pi)$=支撑约束单纯形；温度截断族在场景步落地）。由模型内核导出 $n$ 步信道（含 $p(E_t,Z_t\mid S_t)$ 后验）与 $\mathbb E_t[\cdot]$ 期望属场景步接线（第 6/7 步）——L1 性质（命题 5.6）在显式信道上闭合。Blahut–Arimoto：初值均匀，容差默认 1e-12、最大迭代入配置。
- **E3.7 单步信道导出（第 5 步，T-COV δ 行）**：$W_s[a,o']=\sum_{e,z}p(e,z\mid s)\sum_{e'}env[e,a,z,e']\cdot obs[e',a,o']$（$p(e,z\mid s)$ 后验由 propagate 的 ESZ 联合精确提取——决策时（S 更新后）联合 $p(E_t,S_t,Z_t)$）；$\mathbb E_s[\cdot]$ 取**基线模型** $S_t$ 边缘（ceteris paribus 约定：δ 只改可行集不改环境物理）。完整 $n$ 步信道与 $\Pi_t$ 提取仍属场景步接线。

## 4. A_goal（目标）

- **E4.1 不动点**：Banach 版迭代 $U_{k+1}=\mathrm{Endorse}(U_k)$ 至 $\|U_{k+1}-U_k\|<$tol；Fix 枚举（Θ 有限）；退化预案：$\mathrm{Fix}_{\varepsilon_{min}}$＋Hausdorff 区间（E9，input §3.3）。
- **E4.2 距离与标尺**：$d$=Θ 上欧氏（canonical 参数化后）；$d_c=\max_{U\in\Theta}d(U,\mathrm{Fix})$；$A_{goal}=1-d(U_{eff},\mathrm{Fix})/d_c$。
- **E4.3 $U_{eff}$ 两种识别模式**：结构读取模式直接读取白盒注册变量 $U_{eff}$，满足非空闭 Fix、度量和 $d_c>0$ 时给点值，不调用 IRL；行为反演模式用 MaxEnt-IRL——行为律 $p(\tau)\propto e^{U(\tau)}$ 下 $U=\log p+\log Z$ 精确到常数（命题 5.5(i)），特征线性族与势函数塑形一般只给等价集合，向 $A_{goal}$ 传播区间，温度 $\alpha_{temp}$ 协议固定。只有额外识别假设使集合成为单点时才输出点值；ENV-0 使用结构读取，未实现黑盒 IRL。
- **E4.3a 区间兼容语义（R16）**：默认端点序 $[\ell_0,u_0]\preceq_{ep}[\ell_1,u_1]\iff\ell_1\ge\ell_0\land u_1\ge u_0$，由 `goal_interval_compatible` fail-closed 实现；区间须有限、含于 $[0,1]$ 且 $\ell\le u$。$[0.2,0.8]\to[0.3,0.7]$ 为反例，不能因下端上升就判兼容。端点序不是跨世界逐元素配对，也不是下端保证；若要求独立任取前后容许 reward 均非减，须另证 $\ell_1\ge u_0$，或预注册耦合 $\Pi$ 并要求 $\Pi$-a.e. 配对非减，禁止从端点序自动升级。
- **E4.4 历史分账（R14 supersession）**：删除 $A_{goal}^{hist}=\Lambda A_{goal}$。$A_{goal}$ 仅表示当前固定点对齐，$\Lambda$ 只经 L2 的 $A_{ref}$ 进入复合；手术史 $\mathcal H^{surg}$ 另列，不与 $\Lambda$ 混用。
- **E4.5 真值路径接口与退化区间约定**：真值函数输入 = $(U_{eff},\mathrm{Endorse},\Theta_{grid})$（$U_{eff}$ 容许网格外实向量，$d$ 为其到 Fix 的欧氏距离）；$U_{eff}$ 的 MaxEnt-IRL 恢复（E4.3）与 Endorse 的平台实例化（P3.2）属场景步接线。退化预案（E9）：$\mathrm{Fix}=\varnothing$ 时报 Hausdorff 区间 $\big[1-\frac{d_H+\varepsilon_{min}}{d_c},\ 1-\frac{\max(0,d_H-\varepsilon_{min})}{d_c}\big]$（$d_c$ 对 $\mathrm{Fix}_{\varepsilon_{min}}$ 重定义），区间与 $[0,1]$ 取交并在输出中标注裁剪；$d_c=0$（$\mathrm{Fix}_{\varepsilon_{min}}=\Theta$）时区间约定为 $[0,1]$（完全不定）。**数值裁剪契约（v0.6 补注，沿 E3 的 A_org 约定）**：$U_{eff}$ 为网格边缘均值 ⇒ 落在网格凸包内 ⇒ $d\le d_c$ 是数学事实；浮点残差（~1e-16，细化网格档 η=1 实测触发）致点值越出 $[0,1]$ 时，1e-9 容差内归位并记录 warning；更大越界、NaN、Inf 一律 fail-closed——测试 T-REF7/T-R14-CLIP。

## 5. A_epi（认知）：双轨（2026-10-15 精度化口径）

- **E5.1 real 轨（进复合指标；R11 公式修正）**：$A_{epi}^{real}=1-\bar D$，$\bar D=\frac1T\sum_t\mathbb E\big[TV\big(B_t,\delta_{\kappa(E_t)}\big)\big]=1-\frac1T\sum_t\mathbb E\big[B_t(\kappa(E_t))\big]$——**相对真实环境的失准**。$B_t$ 是信念分布；ENV-0 的范畴状态 $b_t$ 采用点信念 $B_t=\delta_{b_t}$，才进一步化为 $1-\frac1T\sum_tP(b_t=\kappa(E_t))$，不得把该特例写成通用“分布对象等于桶标签”。$E_t$ 为环境真值（因果日志携带）；$\kappa:\mathcal E\to\mathcal B$ 为把 $E$ 粗粒化到信念空间的协议映射，显式传入真值函数（平台侧由 `wiring.derive_bucket_map` 派生：params 含 env0 配置 ⇒ `env0.bucket_map`（与 obs 位置桶同式）；$n_E=n_B$ ⇒ 恒等映射；否则 raise 登记不可计算，不静默）。逐点恒等 $TV(B,\delta_k)=1-B(k)$。零语义：$A_{epi}=0\iff$ 信念全程对真值桶赋零概率（认识俘获=与现实完全脱节）。**基线（无干预）因观测噪声 $A_{epi}<1$——特性而非 bug**（T1c 的 D1 条件口径承认）。原"相对无干预反事实信念位移"定义（$\bar D=\frac1T\sum_t\mathbb E[TV(B_t^{(\gamma)},B_t^{(0)})]$）废止：该口径下任何诚实信息亦降 $A_{epi}$，与开放性公理矛盾（审稿意见）。
- **E5.2 rob 轨（设计对偶量）**：$A_{epi}^{rob}=1-\sup_{\|\gamma\|\le\beta}\bar D_{acc}(\gamma)$——对抗族上的最坏**精度损失**；sup 语义不变（小字母表对 γ 预算网格枚举；$\bar D_{acc}(s)$ 单调性数值核验入测试）；不进复合指标。
- **E5.3 估计路径**：ENV-0 点信念下用日志直读命中率 $\frac1T\sum_t\mathbf 1[b_t=\kappa(E_t)]$；非点信念实现须读 `belief_dist` 并累计 $B_t(\kappa(E_t))$（E14.4）；黑盒信念读出误差登记为偏差源。
- **E5.4 真值路径与对抗族**：ENV-0 点信念状态 $b_t$ 的逐步 $(E_t,b_t)$ 联合由 propagate 的 ESZ 决策时联合边缘化（对 $(G,M,R,Z)$ 求和）；$\mathrm{accuracy}_t=\sum_{e,b}P(E_t=e,b_t=b)\cdot\mathbf 1[b=\kappa(e)]=\mathbb E[B_t(\kappa(E_t))]$，$\bar D=1-\mathrm{mean}_t\,\mathrm{accuracy}_t$。γ 算子（SPEC_platform P4.4）语义=观测通道的 Blackwell 退化（garbling）；α 算子语义=外生内容经完好通道追加——精度口径下 α 的正当性判据为 $A_{epi}$ 不降（场景判据见 SPEC_experiments ATK-4）。对抗族：向常值符号核的混合族 $\gamma_s:o'=(1-s)\,o+s\cdot\delta_{o^*}$（$s\in[0,\beta]$ 网格），$\sup$ 在 $s=\beta$ 达到。零俘获见证构造：确定性 obs＋$\gamma$ 把信念钉到非真值桶（$A_{epi}^{real}=0$）。

## 6. A_ref（反思）

- **E6.1 系综构造**：$\theta_\pi$ 与 $M$ 采用时间漂移＋标定扰动形成的**有限离散**系综（连续量先注册有限量化；协议强制离散 Shannon $H(\theta_\pi)>0$；E10）。扰动族参数入配置；连续微分熵比 $I/h$ 不作为 fidelity。
- **E6.2 三因子**：保真 $I(M;\theta_\pi)/H(\theta_\pi)$（有限联合表真值/估计两路径，禁止通用连续 k-NN 比值）；背书一致性 $\Pr[\Delta G\ne0\Rightarrow$ 经 Endorse$]$（日志频率）；$\Lambda_{ref}$（§8）。
- **E6.3 退化**：$H(\theta_\pi)=0$ 不可修复时报区间 $[0,$ 后两因子之积 $]$。
- **E6.4 真值路径接口与退化区间约定**：真值函数输入 = 系综联合表 $p(\theta_\pi,M)$＋背书一致率＋$\Lambda_{ref}$（$M$ 为列、$\theta_\pi$ 为行）；系综生成（P3.3 滑窗频率估计＋时间漂移/标定扰动族）属场景步接线。$H(\theta_\pi)=0$ ⇒ 点估计不存在，报区间 $[0,f_2\cdot f_3]$（$f_2$=背书一致率、$f_3=\Lambda_{ref}$）并置 `degenerate` 标志——禁止 0/0 静默通过。

## 7. A_via（可行性）

**R16 当前存续/防御分账与证书绑定**：$V_{state}=\min\{1,\min_k s_k^{avail}/s_k^{crit}\}$，$A^{state}=V_{state}F_\varsigma(\text{channels})$；$m_j=\mathrm{clip}(\min(\kappa_j^{eff}/\kappa_j^{req},R_j^{eff}/R_j^{req}),0,1)$，$R_{def}=\min\{1,\min_jm_j\}$，可选韧性量 $A^{res}=R_{def}A^{state}$。$R_{def}=0$ 不自动推出 $A^{state}=0$；关键资源耗尽仍使 $V_{state}=A^{state}=0$。T6 的 A(t) 指状态轨，韧性下界另乘注册的 $R_{def}$ 下界。历史 `a_via` 仍是 R14 combined-resilience marker，不重标为当前状态分数。R16 输出强制携带 `channel_schema_version=R16_CHANNEL_SCHEMA_V1`、层级一致的 `org_mode`、`goal_mode`、`state_readiness_version=R15_SPLIT`、L1/L2 的 64 位小写 model/evidence hashes、$A^{state}/V_{state}/R_{def}$、手术史、Lambda 三态、registration_completeness、mechanism_evidence 和 evidence_ceiling。无 SCM 的完整注册仅为 REGISTERED_COMPLETE；只有显式 SCM_AUDITED 机制证据及哈希绑定才可给 SCM_AUDITED。UNKNOWN/字段不全 ⇒ LIMITED，L0/L1 的 N/A≠UNKNOWN。证书另强制 $0\le A^{state}\le V_{state}\le1$：零存续不得配正当前状态或 SCM_AUDITED，零-零可登记。哈希只绑定声明工件，不验证外部真值；旧 Bundle 缺/错元数据一律拒绝。现行 API 为 `produce_r16_certificate`/`write_r16_certificate`，旧 R15 名仅兼容别名。

## 7.1 u_bar（外部基线量，v0.5 新增）

$u_{bar}=\frac1T\sum_t \mathbb E[U_{\theta^*}(E_t,A_t)]$（真值路径：逐步 $(E_t,A_t)$ 联合=ESZ 决策时联合 × policy 边缘化；效用取内生背书目标 θ* 行，`env0.utility_table`）。**性质**：自主性框架之外的独立功能后果标量——不入复合、不作分量；用途=E2 外部效度分析（攻击网格上 A 与 u_bar 的序相关；等 u_bar 损失下通道剖面的归因判别力）。ENV-0 专用（fixture≠env0 的构造模型无 u_bar）。真值路径唯一（估计路径属 R3d）。

## 8. Λ（实际/无手术背书输出律；R14）

在显式 SCM 中，abduction 从事实观测恢复外生噪声，action 移除全部注册手术，prediction 在共享下游噪声下得到实际/无手术背书输出律；对两律取 TV 并在审计时点/上下文平均，$\Lambda=1-\overline{TV}$。空手术给 1；非空手术但输出不变也给 1；TV 为分布距离，不推几乎必然决策相同，不设退化背书认证例外。$\mathcal H^{surg}$ 只记录手术史，不与 $\Lambda$ 互推。旧 `law_level_lambda`/`lambda_history` 全为 legacy marker，不能支持本 estimand；R14 `counterfactual.py` 仅对独立 fixture 实现真反事实计算，X5-c 报高斯/logistic 双模型带，点值 MODEL_SENSITIVE。黑盒不可识别性采用事实输出同分布的 identity/XOR 非退化证人。

## 9. 复合指标与校准

- **E9.1 复合（R15 分账与非循环权重）**：$A^{state}=V_{state}F_\varsigma(\cdot)$，可选 $A^{res}=R_{def}A^{state}$；$\varsigma=1$ 是全公理主case，$\varsigma<1$ 仅 AX6b 松弛敏感性，$\varsigma=2$ 仅 AX5 松弛压力测试，均不得写成公理内等价格式。权重只能来自等权默认、独立专家/利益相关者引出或受控单通道行为权衡协议；$w_i=\partial\log F/\partial\log x_i$ 是导出形式后的恒等式，禁止把需要预知 F/w 的弹性回归当非循环估计。历史矩阵权重/弹性重算仅属 legacy 敏感性。
- **E9.2 H2 单位统一**：χ 把 $\varepsilon v$ 换算为损伤 nats/时间；θ/W、$\lceil(r+1)/2\rceil c_0/W$ 同样换算（附录 §7.6.1 H2）；换算常数由标定期拟合，入 metadata。
- **E9.3 敏感性**：每个报告值带 σ 带（主带 [0.5,1] 两端+中点）；T4 只在 σ=1 下作 LinLog 定理与优化证书，σ≠1 的旧重复不算 CES 内点 KKT 验证。
- **E9.4 幻觉指数**：$\mathrm{AI}_t=\hat A_{phen,t}-A_{obj,t}$；$\hat A_{phen}=f(\xi)$ 为登记证据的有界泛函（$f$ 形式入配置；T3b 假设 C2 的落地）。

## 10. 动力学与委托观测量

- **E10.1 T6 观测量**：$D_j(t)$ 轨迹（日志直读）、精确实现的俘获阈（δ 扫描二分）、κ 标定（M3 回归）、certificate-failure band 扫描（θ/W>κ 配置下 $\delta\in(\kappa,\theta/W)$ 网格）。带扫描只说明一般 M3-only 证书失效，实测俘获阈属于额外精确饱和实现。
- **E10.2 C1/C2 观测量**：EWS 三指标（恢复时间 $T_{rec}$、平稳方差、AR(1)）；标度律拟合 $(\delta_c-\delta)^{-1/2}$（最小二乘，报告 R²）；滞后回环宽度 $(\delta_{down},s_c)$ 双向报告（升程崩溃阈/降程恢复阈）。
- **E10.3 T7 观测量**：混合策略构造 $(1-m)\pi_{self}+m\pi_{del}$（$m=\lambda(1-q)$）；等强度标定 H1' 的检验与夹逼界 $\rho\in[\rho_{min},\rho_{max}]$；$w_{org}$ 作自由参数拟合。
- **E10.4 C0 演示（R14 分账）**：旧 C0-DEMO 改环境分布，仅保留历史行为/精度/marker 演示，不作同环境来源归因。新 C0-CF 两臂共享公平环境、$O=E$、均匀政策、视界与 $\kappa$，仅信念更新不同，完整 $(E,O,A)$ 张量相同而精度 1 vs 0.5；辅助 identity/XOR 背书 SCM 事实输出同分布而 $\Lambda=1/0$。只作构造性实现检查，不声称 KG/Dung/Feng 完整画像或一般 rank consistency。

## 11. 偏差源登记（对照 input §5.1 表）

DI 闭环偏差（真值标定）；empowerment 高维方差（本环境低维可控）；IRL 欠定（等价类区间化）；信念读出误差（白盒直读为零）；探针过拟合（留出标定窗）。每个估计器的 diagnostics 字段须实报上述量。

## 12. 动力学、委托与黑盒观测量（第 6 步接口）

- **E12.1 T6 动力学（R13）**：一般定理只有上比较 $\dot D\le\delta-\kappa D$；ENV-0 损伤模拟器额外采用精确饱和律 $\dot D=\delta-\kappa D$＋M1 窗登记（窗累计 ≥θ ⇒ 滞后 ℓ 复位 $D$ 与累计器）并截断到 $[0,1]$。$\delta^*:=\min\big(\theta/W,\ \chi\varepsilon v,\ \lceil(r+1)/2\rceil\,c_0/W\big)$（M4 项 2026-10-15 审稿修复：多数派接管 r 份独立副本只需腐化 $k=\lceil(r+1)/2\rceil$ 份，每窗成本 $k c_0$——原 $r c_0/W$ 高估安全边界）；$A_{min}=A_{via}^{min}\cdot\prod_j(A_j^{base}(1-\delta_j^*/\kappa_j))^{w_j}$（σ=1 几何，经 `aggregate.composite_A`）；pointwise 下界同样含 $A_{via}^{min}$，严格正性另需 H4$''$：所有适用 $A_j^{base}>0$。M1 注册域的非俘获/正保持另需正常响应且 $\theta+\ell\delta$ 低于俘获阈。在 $\theta/W>\kappa$、$\delta\in(\kappa,\theta/W)$，一般上比较只使 M3-only 正保持证书失效，$D\equiv0$ 反驳任何一般俘获结论；模拟器的零登记与 $D\to1$ 只确认精确实现。M4 使用确定性逐窗恢复前提，不写 $1-o(1)$ 概率口径；提高 $\theta$ 缩小注册域 $\{\delta:\delta\ge\theta/W\}$。显式公式逐 run 核对为 L1 义务（T-T6a），零轨迹反例见 T-R13-T6。
- **E12.2 T6c（R12 量词修正与描述臂）**：定理为 iid $N(0,\sigma_n^2)\to N(\delta,\sigma_n^2)$ 下固定 $\delta>0$、$\alpha\downarrow0$ 的 Lorden–Lai 下界 $\delta EDD\ge(1-o(1))2\sigma_n^2\log(1/\alpha)/\delta$；固定 $\alpha$、$\delta\downarrow0$ 的全称版被常数停止规则否定。ENV-0 的 LLR-CUSUM（阈 $h\approx\log(1/\alpha)$）仅在 $\alpha=10^{-3}$ 比较 $\delta=0.25,0.125$，观测量 $\delta\cdot EDD$ 与标度 $2\sigma_n^2\log(1/\alpha)/\delta$ 属该方案的描述性对照，不直接检验上述另一极限；常数因子属 overshoot 域，不做精确等式。区间按 SPEC_experiments ATK-6⑥ 的同种子比均值正态近似口径报告，并以 Student-$t_{29}$ 半宽作小样本敏感性；30 个比值和种子由 `analysis_cusum_sensitivity.json` 公开列示。
- **E12.3 T7 委托记账约定（R12 当前 selector/双误差边界）**：干预流 $I$ 为受托脚本内容；精确线性律的估计量显式定义为逐步当前 selector 条件化 $\sum_t I(S^t;A_t\mid A^{t-1},\mu_t)$ 与 $\sum_t I(I^t;A_t\mid A^{t-1},S^t,\mu_t)$，并满足等熵、脚本臂不经 $S$、$F_{ext}^{self}=0$；不得未加证明改读为完整历史 $\mu^t$ 条件化。legacy ENV-0 真值路径是未条件化流，近线性拟合只作实例描述。非 H1' 且有混合误差时用 $\varphi_0=f/C_{self}$、$\eta_\mu=h(m)/C_{self}$ 分离的双误差 bracket（DEL-1⑤⑥公式），不得把同一 $\varphi$ 只加分母吸收两类误差；退化区间报 INCONCLUSIVE。
- **E12.4 C1/C2（附录 §8.2/§8.3）**：ODE 模拟器（Euler/RK4，$dt$ 入配置）；C1 平衡公式 $D_\pm=(1\pm\sqrt{1-4\delta/\varepsilon v})/2$ 与 $T_{rec}\propto(\delta_c-\delta)^{-1/2}$ 标度；C2 双稳/滞后：$\delta_{down}=r(D_1)$、$s_c=|r(D_m)|$（$D_1,D_m$ 为 $r'=0$ 两正根，$r(D)=\varepsilon_0v\,D(1-D)(1-\gamma D$)），持续攻击下恢复须 $s>\delta+s_c$；攻击移除 $\delta=0$ 时才为 $s>s_c$（回环不闭合）。
- **E12.5 黑盒（附录 §10）**：10.2 探针 = 行动通道随机化脚本（β_π 编译，state-independent script，flag = 探针指示）；$F_{ext}^{obs}=I(\text{脚本}^T;A^T)$（引理 2.3.1：=DI，无需 S 可观测——真值路径由编译结构精确给出，采样插件路径对照）；R15 只给 bypass 语义下的条件认证上端：$F_{ext}^{obs}\le F_{ext}$ 且 $F_{src}\le F_{src}^{base}(1+\eta)$，L1+ 舍去非负 $F_{rand}$ 仍保守；参考下端不作包含性认证，L1+ 必须另注册 $r_{max}\ge F_{rand}$，否则不得显示。历史 BB-1 的区间命中只作旧 fixture 重放，η 不足与 mediation/adaptive probe 作反面控制。10.3（R11）：一般策略驱动被动观察的方向未识别，因为 $I(A;O\mid S)-I(A;O)=I(A;S\mid O)-I(A;S)$ 可正可负；ENV-0 obs>cond 只作实例描述。独立探针 $A\perp S$ ⇒ $I(A;O)\le I(A;O\mid S)$ 保留为条件方向。
- **E12.6 Λ 操作化（R14 分账）**：旧 `law_level_lambda`/`lambda_history` 与 ATK-1、β_π、T2/T3、X2 的 $\Lambda$ 相关值全部仅为 legacy marker，不能支持 AX3、$A_{ref}$ 或反事实 TV。新 `counterfactual.py` 在独立显式 SCM 上执行 abduction–action–prediction；`x5c_stratified` 每 noise×arm×t 记录 20,000 上下文，含 C1--C5、观测等价 identity/XOR 与独立共享噪声复核，$D_{noise}>0.01$ 时只报双模型带。`c0cf_v2` 记录非退化同环境、同全轨迹 $(E^T,O^T,A^T)$ 的构造证人。新证据不升级旧场景 verdict；旧 C0-DEMO 和历史 T-BB 不改写。

## 13. 验收标准（R3b done）

SPEC_tests.md §5 的 E 系列测试全绿；每个分量在至少一个合成配置上"真值=估计（容差内）"有数值记录。

---

## 14. 估计路径 v1 接口与 §13 数值记录载体（R3c 第 7d 子步）

**E14.0 落地范围**。E0.1 接口二分在 v1 的落地：五个分量有采样估计器（`estimators.py`，输入=P8.2 步级日志 `trajs`，输出 `(point, half, diagnostics)`）；**A_ref 的采样载体（defense_events 背书事件日志）与 Λ 的事件级路径 v1 无日志承载——显式登记为报告局限节条目（非静默缺口）**；复合 A 由分量估计经 E9.1 复合。数值记录由 `sim/estimator_checks.py` 产出（`runs/<矩阵>/estimator_checks.json`）。

- **E14.1** `estimate_probe_flow(trajs, n_I, n_A) -> (point, half, diag)`：10.2 探针流 $F_{ext}^{obs}=I(flag^T;A^T)$ 的采样插件估计——与真值闭式同构的插件式 $\hat f\cdot\hat H(\text{脚本})\cdot T$（$\hat f$=旗标率（`I_t["beta"]` 逐步读出）、$\hat H$=旗标步行动经验熵；state-independent 脚本约定）；真值对照 `blackbox.probe_flow_obs`（flag·H（脚本）·T 精确式）。历史 BB-1 才由 `a_org_interval(F_int^base, η, 估计值)` 重放旧区间及 fixture 命中目标 $a_{true}=F_{int}^{true}/(F_{int}^{true}+F_{ext}^{obs})$；R15 新输出只按 E2.4/E12.5 给条件认证上端，参考下端不作包含性承诺，L1+ 另需 $r_{max}$。探针流在 bypass 语义下是因果 F_ext 的**可观测下估计**，不是因果 F_ext 本身。
- **E14.2** `estimate_z_high(trajs, n_Z)`：Z 高位占时逐轨迹均值（A_via 输入；真值对照 propagate Z 边缘占时）。
- **E14.3** `estimate_g_mean(trajs, alphabet)`：S 日志 G 分量边缘均值（P9.4 $U_{eff}$ 均值读出的白盒采样对应物；E4.3 MaxEnt-IRL 黑盒恢复属报告附栏）。
- **E14.4（R11 点信念边界）** `estimate_epi_accuracy(trajs, bucket_map)`：ENV-0 点信念 $B_t=\delta_{b_t}$ 下以逐轨迹命中率 $\frac1T\sum_t\mathbf 1[b_t=\kappa(E_t)]$ 估计真实桶期望质量；$E_t$ 与 $S_t.B$ 由日志直读，κ 同真值路径。若未来支持非点信念，接口必须改为读取 `belief_dist` 的真实桶质量，不得沿用分布对象相等指示。
- **E14.5** `estimate_mi_action_obs(trajs, t, n_A, n_O)`：$I(A_t;O_{t+1})$ 黑盒观察量（10.3 obs 协议侧）采样插件；真值对照 `blackbox.a_exec_blackbox(policy_driven=True)`。
- **E14.6 区间约定**：全部估计器的 `half`=8 等分块均值的 95% 正态半宽（$1.96\,s_{块}/\sqrt8$）；插件 MI/TV 的 Miller–Madow 级正偏差 $(K-1)/2N$ 入 `diagnostics["mm_bias"]` 登记（不作为区间下限扣除——偏差方向已知为正，报告注记）。

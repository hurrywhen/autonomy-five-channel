# SPEC_estimators —— R3b 分量与复合指标估计规约

**版本**: v0.5（2026-10-17：审稿 P3 包——§7 A_via 扩展为资源∩能力包络双因子闸门（配置默认 m=1 还原旧式，v1 数值不变）；新增 §7.1 u_bar 外部基线量真值口径（E2 外部效度分析数据源））｜**依据**: input v2.1 §3.3–§3.5、§5；附录 §2（数学预备）、§5（分量良构性）、§10（可辨识性与黑盒降级）。
**总原则**: 每个量有两条实现路径——**真值路径**（平台张量枚举，精确，用于标定与估计器验证）与**估计路径**（从日志轨迹的有限样本估计，用于测量期）；估计路径必须对照真值路径报告偏差/方差（input 风险 R2 的落地）。全部信息量以 nats 计（log 底 e）。

---

## 1. 公共约定

- **E0.1 接口二分**：`truth_*(platform_tensors) -> exact value` 与 `estimate_*(trajectory_log) -> (point, interval, diagnostics)`。同名量的两路径签名一一对应。
- **E0.2 不确定度**：估计路径输出 `(点估计, 区间)`；区间构造法逐量登记于下文；真值路径区间退化为点。
- **E0.3 标定期先行**（input §5.2）：标定干预拟合响应函数，产出 H2 换算常数 χ、权 $w_i$（推论 6.8 回归）、策略漂移容差 η、强度比 ρ=C_del/C_self——全部为配置化参数，入日志 metadata。

## 2. A_org（来源）：DI 分解

- **E2.1 定义**：$F_{int}=I(S^T\!\to\!A^T)$（Massey，附录定义 2.3.A）；$F_{ext}=I(I^T\!\to\!A^T\,\|\,S^T)$（Kramer 因果条件化，定义 2.3.B）；$A_{org}=F_{int}/(F_{int}+F_{ext})$。
- **E2.2 真值路径**：按定义逐项枚举（前缀缓存，规模约束 SPEC_platform §7）。
- **E2.3 估计路径**：plug-in 估计＋偏差标注（DI 插件偏差 O(·/N)，input 风险 R2）；闭环下必须用因果条件化（禁止普通条件 MI 替代——Kramer Property 2 反例为回归测试 T-DI2）。
- **E2.4 黑盒降级**（附录 §10.2）：随机化探针下 $F_{ext}^{obs}=I(I^T;A^T)$（引理 2.3.1：外源随机化 ⇒ MI=DI，测试 T-DI1）；$A_{org}$ 报区间
  $\big[\frac{F_{int}^{base}(1-\eta)}{F_{int}^{base}(1-\eta)+F_{ext}^{obs}},\ \min\big(1,\frac{F_{int}^{base}(1+\eta)}{F_{int}^{base}(1+\eta)+F_{ext}^{obs}}\big)\big]$。
- **E2.5 $F_{ext}$ 通用后验路径与调度**（第 5 步，T-COV）：按 params 调度——(i) **β_π**（旗标切换策略，SPEC_platform P4.5）：$F_{ext}=\sum_t\mathbb E_{S_t}\big[H(\bar\pi(\cdot\mid S_t))-\sum_i flag_i\,H(\pi_i(\cdot\mid S_t))\big]$（混合条件律的 Jensen 间隙；$\bar\pi=\sum_i flag_i\pi_i$，$\pi_i$ 由扁平策略张量与 flag 重建；$S_t$ 边缘精确）；(ii) **静态手术**（β_G/δ/β_Endorse，无外源 I 节点）⇒ $F_{ext}\equiv0$ 平凡成立（干预过程为空）；(iii) **α/σ/γ**：引理 7.2.1 双项零残余路径（既有）。β_π×α 复合暂不支持（显式报错；场景步按需扩展）。

## 3. A_exec（执行）：策略类 empowerment

- **E3.1 定义**：$\mathcal E_t^\Pi=\max_{p(a_{t:t+n})\in\mathrm{conv}(\Pi_t)} I(A_{t:t+n};O_{t+n+1}\mid S_t)$；$A_{exec}=\mathbb E_t[\mathcal E_t^\Pi]/(n\log|\mathcal A|)$。
- **E3.2 真值路径**：表格信道容量——枚举（小字母表）或自实现 Blahut–Arimoto（不引 scipy；收敛容差入配置）。实现形态：BA 核心迭代（面内点信道）＋`channel_capacity` 循环顶点方向上升（I(q) 凹 ⇒ 坐标级精确线搜索收敛到全局最优），精度由 KKT 证书 gap=max_a D(W_a‖out)−I(q) 保证（边界最优信道不依赖迭代阈值）。
- **E3.3 分解诊断（无助鉴别器）**：同时输出 $\mathcal E^{env}$（不限策略类）与 $\mathcal E^\Pi$；无助签名=$\mathcal E^{env}$ 完好而 $\mathcal E^\Pi\to0$；真能力坍缩=两者同降（附录 §5.4）。
- **E3.4 黑盒**：探针化精确可算；纯观察代理 $A_{exec}^{obs}\ge A_{exec}$（单侧高估界，附录 §10.3）。
- **E3.5 视界剖面**：报告 $n\mapsto\mathcal E^\Pi(n)$ 饱和曲线（C0 映射中 Dung"长期规划"维度的对应物）。
- **E3.6 真值路径接口与第 4 步范围**：真值函数作用于显式信道 $W$（$|\mathcal A|\times|\mathcal O|$ 行随机矩阵）；策略类 $\Pi$ 以**输入支撑限制**表示（P3.5 的确定性策略子集 ⟺ 行动子集单纯形，$\mathrm{conv}(\Pi)$=支撑约束单纯形；温度截断族在场景步落地）。由模型内核导出 $n$ 步信道（含 $p(E_t,Z_t\mid S_t)$ 后验）与 $\mathbb E_t[\cdot]$ 期望属场景步接线（第 6/7 步）——L1 性质（命题 5.6）在显式信道上闭合。Blahut–Arimoto：初值均匀，容差默认 1e-12、最大迭代入配置。
- **E3.7 单步信道导出（第 5 步，T-COV δ 行）**：$W_s[a,o']=\sum_{e,z}p(e,z\mid s)\sum_{e'}env[e,a,z,e']\cdot obs[e',a,o']$（$p(e,z\mid s)$ 后验由 propagate 的 ESZ 联合精确提取——决策时（S 更新后）联合 $p(E_t,S_t,Z_t)$）；$\mathbb E_s[\cdot]$ 取**基线模型** $S_t$ 边缘（ceteris paribus 约定：δ 只改可行集不改环境物理）。完整 $n$ 步信道与 $\Pi_t$ 提取仍属场景步接线。

## 4. A_goal（目标）

- **E4.1 不动点**：Banach 版迭代 $U_{k+1}=\mathrm{Endorse}(U_k)$ 至 $\|U_{k+1}-U_k\|<$tol；Fix 枚举（Θ 有限）；退化预案：$\mathrm{Fix}_{\varepsilon_{min}}$＋Hausdorff 区间（E9，input §3.3）。
- **E4.2 距离与标尺**：$d$=Θ 上欧氏（canonical 参数化后）；$d_c=\max_{U\in\Theta}d(U,\mathrm{Fix})$；$A_{goal}=1-d(U_{eff},\mathrm{Fix})/d_c$。
- **E4.3 $U_{eff}$ 恢复**：表格 MaxEnt-IRL——行为律 $p(\tau)\propto e^{U(\tau)}$ 下 $U=\log p+\log Z$ 精确到常数（命题 5.5(i)）；特征线性族按 5.5(ii) 判等价类并报区间；温度 $\alpha_{temp}$ 协议固定（配置）。
- **E4.4 历史加权**：$A_{goal}^{hist}=\Lambda\cdot A_{goal}$（AX3 操作化，见 §8）。
- **E4.5 真值路径接口与退化区间约定**：真值函数输入 = $(U_{eff},\mathrm{Endorse},\Theta_{grid})$（$U_{eff}$ 容许网格外实向量，$d$ 为其到 Fix 的欧氏距离）；$U_{eff}$ 的 MaxEnt-IRL 恢复（E4.3）与 Endorse 的平台实例化（P3.2）属场景步接线。退化预案（E9）：$\mathrm{Fix}=\varnothing$ 时报 Hausdorff 区间 $\big[1-\frac{d_H+\varepsilon_{min}}{d_c},\ 1-\frac{\max(0,d_H-\varepsilon_{min})}{d_c}\big]$（$d_c$ 对 $\mathrm{Fix}_{\varepsilon_{min}}$ 重定义），区间与 $[0,1]$ 取交并在输出中标注裁剪；$d_c=0$（$\mathrm{Fix}_{\varepsilon_{min}}=\Theta$）时区间约定为 $[0,1]$（完全不定）。**数值裁剪契约（v0.6 补注，沿 E3 的 A_org 约定）**：$U_{eff}$ 为网格边缘均值 ⇒ 落在网格凸包内 ⇒ $d\le d_c$ 是数学事实；浮点残差（~1e-16，细化网格档 η=1 实测触发）致点值越出 $[0,1]$ 时，1e-9 容差内归位，更大越界保持原值交由调用方检出（不静默掩盖）——测试 T-REF7。

## 5. A_epi（认知）：双轨（2026-10-15 精度化口径）

- **E5.1 real 轨（进复合指标）**：$A_{epi}^{real}=1-\bar D$，$\bar D=\frac1T\sum_t\mathbb E\big[TV\big(B_t,\delta_{\kappa(E_t)}\big)\big]=1-\frac1T\sum_t P\big(B_t=\kappa(E_t)\big)$——**相对真实环境的失准**（accuracy/distortion 口径）。$E_t$ 为环境真值（因果日志携带）；$\kappa:\mathcal E\to\mathcal B$ 为把 $E$ 粗粒化到信念空间的协议映射，显式传入真值函数（平台侧由 `wiring.derive_bucket_map` 派生：params 含 env0 配置 ⇒ `env0.bucket_map`（与 obs 位置桶同式）；$n_E=n_B$ ⇒ 恒等映射；否则 raise 登记不可计算，不静默）。逐点恒等 $TV(B,\delta_k)=1-B(k)$。零语义：$A_{epi}=0\iff$ 信念全程对真值桶赋零概率（认识俘获=与现实完全脱节）。**基线（无干预）因观测噪声 $A_{epi}<1$——特性而非 bug**（T1c 的 D1 条件口径承认）。原"相对无干预反事实信念位移"定义（$\bar D=\frac1T\sum_t\mathbb E[TV(B_t^{(\gamma)},B_t^{(0)})]$）废止：该口径下任何诚实信息亦降 $A_{epi}$，与开放性公理矛盾（审稿意见）。
- **E5.2 rob 轨（设计对偶量）**：$A_{epi}^{rob}=1-\sup_{\|\gamma\|\le\beta}\bar D_{acc}(\gamma)$——对抗族上的最坏**精度损失**；sup 语义不变（小字母表对 γ 预算网格枚举；$\bar D_{acc}(s)$ 单调性数值核验入测试）；不进复合指标。
- **E5.3 估计路径**：日志直读精度——日志含 $E_t$ 与 $S_t$（$B_t$ 可解码），逐轨迹命中率 $\frac1T\sum_t\mathbf 1[B_t=\kappa(E_t)]$ 的轨迹平均（E14.4）；黑盒信念读出误差登记为偏差源（input §5.1）。
- **E5.4 真值路径与对抗族**：真值路径下逐步 $(E_t,B_t)$ 联合由 propagate 的 ESZ 决策时联合边缘化（对 $(G,M,R,Z)$ 求和）；$\mathrm{accuracy}_t=\sum_{e,b}P(E_t=e,B_t=b)\cdot\mathbf 1[b=\kappa(e)]$，$\bar D=1-\mathrm{mean}_t\,\mathrm{accuracy}_t$。γ 算子（SPEC_platform P4.4）语义=观测通道的 Blackwell 退化（garbling）；α 算子语义=外生内容经完好通道追加——精度口径下 α 的正当性判据为 $A_{epi}$ 不降（场景判据见 SPEC_experiments ATK-4）。对抗族：向常值符号核的混合族 $\gamma_s:o'=(1-s)\,o+s\cdot\delta_{o^*}$（$s\in[0,\beta]$ 网格），$\sup$ 在 $s=\beta$ 达到。零俘获见证构造：确定性 obs＋$\gamma$ 把信念钉到非真值桶（$A_{epi}^{real}=0$）。

## 6. A_ref（反思）

- **E6.1 系综构造**：$\theta_\pi$ 的时间漂移＋标定扰动族（协议强制 $H(\theta_\pi)>0$；E10）。扰动族参数入配置。
- **E6.2 三因子**：保真 $I(M;\theta_\pi)/H(\theta_\pi)$（真值/估计两路径）；背书一致性 $\Pr[\Delta G\ne0\Rightarrow$ 经 Endorse$]$（日志频率）；$\Lambda_{ref}$（§8）。
- **E6.3 退化**：$H(\theta_\pi)=0$ 不可修复时报区间 $[0,$ 后两因子之积 $]$。
- **E6.4 真值路径接口与退化区间约定**：真值函数输入 = 系综联合表 $p(\theta_\pi,M)$＋背书一致率＋$\Lambda_{ref}$（$M$ 为列、$\theta_\pi$ 为行）；系综生成（P3.3 滑窗频率估计＋时间漂移/标定扰动族）属场景步接线。$H(\theta_\pi)=0$ ⇒ 点估计不存在，报区间 $[0,f_2\cdot f_3]$（$f_2$=背书一致率、$f_3=\Lambda_{ref}$）并置 `degenerate` 标志——禁止 0/0 静默通过。

## 7. A_via（可行性）

**扩展闸门（v0.5，论文 D-via 修订落地）**：$A_{via}=\min\{1,\ \min_k s_k^{avail}/s_k^{crit},\ \min_j m_j\}$，$m_j=\mathrm{clip}(\min(\kappa_j^{eff}/\kappa_j^{req}, R_j^{eff}/R_j^{req}),0,1)$（能力包络裕度：验证-修复能力 κ 与修复预算 R 对登记需求的归一比；θ 不入闸门——双刃性）。v1 实例：单维护通道 j，κ/R 为 `Env0Config` 标量字段，默认 (1, 0.5, 1, 0.5) ⇒ m=1 ⇒ 逐点还原资源型旧式（v1 矩阵数值不变的构造性保证；回归测试 T-AVIA-ENV）。资源审计从 $Z_t$ 日志直读；κ/R 审计为白盒配置直读（黑盒降级规则不变——能力包络属 σ 类参数审计）；$A_{via}^{min}$ 随 run 记录（T6 的 $A_{min}$ 公式输入）。

## 7.1 u_bar（外部基线量，v0.5 新增）

$u_{bar}=\frac1T\sum_t \mathbb E[U_{\theta^*}(E_t,A_t)]$（真值路径：逐步 $(E_t,A_t)$ 联合=ESZ 决策时联合 × policy 边缘化；效用取内生背书目标 θ* 行，`env0.utility_table`）。**性质**：自主性框架之外的独立功能后果标量——不入复合、不作分量；用途=E2 外部效度分析（攻击网格上 A 与 u_bar 的序相关；等 u_bar 损失下通道剖面的归因判别力）。ENV-0 专用（fixture≠env0 的构造模型无 u_bar）。真值路径唯一（估计路径属 R3d）。

## 8. Λ（历史性合法性因子）

$\Lambda_T=1-I(\mathrm{Endorse}^T;I^{\beta,T})/H(\mathrm{Endorse}^T)$（无 β 时 Λ=1）；真值路径枚举；白盒可估、黑盒报 $[\Lambda_{min},1]$（$\Lambda_{min}$ 来自溯源审计参数；命题 10.4 的回归测试 T-BB 保证不可辨识性构造成立）。

## 9. 复合指标与校准

- **E9.1 复合**：$A=A_{via}\cdot F_\sigma(\cdot)$，$\sigma\in\{0.5,1\}$（公理内）＋$\{2\}$（AX5 松弛压力测试，显式标注）；权 $w_i$：标定期弹性回归（$w_i=\partial\log F/\partial\log x_i$，推论 6.8）或配置给定（矩阵内固定，入 metadata）。
- **E9.2 H2 单位统一**：χ 把 $\varepsilon v$ 换算为损伤 nats/时间；θ/W、$\lceil(r+1)/2\rceil c_0/W$ 同样换算（附录 §7.6.1 H2）；换算常数由标定期拟合，入 metadata。
- **E9.3 敏感性**：每个报告值带 σ 带（主带 [0.5,1] 两端+中点）；T4 verdict 随 σ 单列（附录 §13.3）。
- **E9.4 幻觉指数**：$\mathrm{AI}_t=\hat A_{phen,t}-A_{obj,t}$；$\hat A_{phen}=f(\xi)$ 为登记证据的有界泛函（$f$ 形式入配置；T3b 假设 C2 的落地）。

## 10. 动力学与委托观测量

- **E10.1 T6 观测量**：$D_j(t)$ 轨迹（日志直读）、实测俘获阈（δ 扫描二分）、κ 标定（M3 回归）、盲区扫描（θ/W>κ 配置下 $\delta\in(\kappa,\theta/W)$ 网格）。
- **E10.2 C1/C2 观测量**：EWS 三指标（恢复时间 $T_{rec}$、平稳方差、AR(1)）；标度律拟合 $(\delta_c-\delta)^{-1/2}$（最小二乘，报告 R²）；滞后回环宽度 $(\delta_{down},s_c)$ 双向报告（升程崩溃阈/降程恢复阈）。
- **E10.3 T7 观测量**：混合策略构造 $(1-m)\pi_{self}+m\pi_{del}$（$m=\lambda(1-q)$）；等强度标定 H1' 的检验与夹逼界 $\rho\in[\rho_{min},\rho_{max}]$；$w_{org}$ 作自由参数拟合。
- **E10.4 C0 演示**：命题 8.1.2 构造——同文指令（委托人臂）vs 隐蔽注入（γ 臂），行为分布逐点一致（TV 检验）而 $A_{epi}^{real}$、Λ 可区分。

## 11. 偏差源登记（对照 input §5.1 表）

DI 闭环偏差（真值标定）；empowerment 高维方差（本环境低维可控）；IRL 欠定（等价类区间化）；信念读出误差（白盒直读为零）；探针过拟合（留出标定窗）。每个估计器的 diagnostics 字段须实报上述量。

## 12. 动力学、委托与黑盒观测量（第 6 步接口）

- **E12.1 T6 动力学（附录 §7.6）**：损伤模拟器 $\dot D=\delta-\kappa D$＋M1 窗登记（窗累计 ≥θ ⇒ 滞后 ℓ 复位 $D$ 与累计器）；$\delta^*:=\min\big(\theta/W,\ \chi\varepsilon v,\ \lceil(r+1)/2\rceil\,c_0/W\big)$（M4 项 2026-10-15 审稿修复：多数派接管 r 份独立副本只需腐化 $k=\lceil(r+1)/2\rceil$ 份，每窗成本 $k c_0$——原 $r c_0/W$ 高估安全边界）；$A_{min}=A_{via}^{min}\cdot\prod_j(A_j^{base}(1-\delta_j^*/\kappa_j))^{w_j}$（σ=1 几何，经 `aggregate.composite_A`）。盲区判据：$\theta/W>\kappa$ 且 $\delta\in(\kappa,\theta/W)$ ⇒ 登记零触发且 $D\to1$。显式公式逐 run 核对为 L1 义务（T-T6a）。
- **E12.2 T6c（命题 7.6.5）**：LLR-CUSUM（已知漂移率 δ、噪声 $\sigma_n$，阈 $h\approx\log(1/\alpha)$）；观测量=检测时刻损伤 $\delta\cdot EDD$，标度对照 $2\sigma_n^2\log(1/\alpha)/\delta$（Lorden/Lai 下界方向；常数因子属 overshoot 域，趋势与区间为断言对象，不做精确等式）。
- **E12.3 T7 委托记账约定（附录 §7.7）**：干预流 $I$ := **受托脚本内容**（源指示 = 协议参数 $(\lambda,q)$，非影响流）；H1' 的操作化前提 = 等熵转移（自臂 $I(S;A)$ = 脚本臂逐步熵转移 $=\tilde C$），且脚本臂不经 $S$（$I(S;A\mid del)=0$）。$A_{org}=(1-m)A_{org}^{self}$ 在该记账下精确（T-T7 用同时满足字面 H1' 与该前提的构造锚定）；非 H1' 夹逼界 $\rho=C_{del}/C_{self}\in[\rho_{min},\rho_{max}]$。$F_{int}$ 由 β_π 编译模型的既有真值路径计算（源指示外源独立，熵对消后恰为自臂加权和）。
- **E12.4 C1/C2（附录 §8.2/§8.3）**：ODE 模拟器（Euler/RK4，$dt$ 入配置）；C1 平衡公式 $D_\pm=(1\pm\sqrt{1-4\delta/\varepsilon v})/2$ 与 $T_{rec}\propto(\delta_c-\delta)^{-1/2}$ 标度；C2 双稳/滞后：$\delta_{down}=r(D_1)$、$s_c=|r(D_m)|$（$D_1,D_m$ 为 $r'=0$ 两正根，$r(D)=\varepsilon_0v\,D(1-D)(1-\gamma D$)），恢复须 $s>s_c$（回环不闭合）。
- **E12.5 黑盒（附录 §10）**：10.2 探针 = 行动通道随机化脚本（β_π 编译，state-independent script，flag = 探针指示）；$F_{ext}^{obs}=I(\text{脚本}^T;A^T)$（引理 2.3.1：=DI，无需 S 可观测——真值路径由编译结构精确给出，采样插件路径对照）；区间包含真值的语义前提 = $F_{int}$ 漂移 ≤η（η 过小时不含，作反面控制）。10.3 协议前提登记：$A_{exec}^{obs}\ge A_{exec}$ 的附录方向在**策略驱动被动观察**协议下见证（状态熵混入）；独立探针协议下方向相反（$A\perp S$ ⇒ $I(A;O)\le I(A;O\mid S)$，条件化去噪）——协议标签为报告义务（登记 `R2_文献待查证事项.md` §4.7）。
- **E12.6 Λ 操作化（登记）**：本步 Λ 为**手术史标记级**（β/未登记 γ 入史 ⇒ 约定值 0.5；无 ⇒ 1.0——仅为可区分性见证的约定取值，非 Λ 的真值估计）；Endorse 事件级 Λ（附录 §4.4）随 ATK-1/ATK-5 场景步落地。T-C0/T-BB 的可区分性见证用标记级 Λ 合法。

## 13. 验收标准（R3b done）

SPEC_tests.md §5 的 E 系列测试全绿；每个分量在至少一个合成配置上"真值=估计（容差内）"有数值记录。

---

## 14. 估计路径 v1 接口与 §13 数值记录载体（R3c 第 7d 子步）

**E14.0 落地范围**。E0.1 接口二分在 v1 的落地：五个分量有采样估计器（`estimators.py`，输入=P8.2 步级日志 `trajs`，输出 `(point, half, diagnostics)`）；**A_ref 的采样载体（defense_events 背书事件日志）与 Λ 的事件级路径 v1 无日志承载——显式登记为报告局限节条目（非静默缺口）**；复合 A 由分量估计经 E9.1 复合。数值记录由 `sim/estimator_checks.py` 产出（`runs/<矩阵>/estimator_checks.json`）。

- **E14.1** `estimate_probe_flow(trajs, n_I, n_A) -> (point, half, diag)`：10.2 探针流 $F_{ext}^{obs}=I(flag^T;A^T)$ 的采样插件估计——与真值闭式同构的插件式 $\hat f\cdot\hat H(\text{脚本})\cdot T$（$\hat f$=旗标率（`I_t["beta"]` 逐步读出）、$\hat H$=旗标步行动经验熵；state-independent 脚本约定）；真值对照 `blackbox.probe_flow_obs`（flag·H（脚本）·T 精确式）。A_org 区间由 `a_org_interval(F_int^base, η, 估计值)` 合成（η=标定期漂移容差，E0.3）；区间命中目标=$a_{true}=F_{int}^{true}/(F_{int}^{true}+F_{ext}^{obs})$（E2.4 可观测重建语义，BB-1 同式——探针流是外部流的**可观测上界代理**，非因果 F_ext 本身）。
- **E14.2** `estimate_z_high(trajs, n_Z)`：Z 高位占时逐轨迹均值（A_via 输入；真值对照 propagate Z 边缘占时）。
- **E14.3** `estimate_g_mean(trajs, alphabet)`：S 日志 G 分量边缘均值（P9.4 $U_{eff}$ 均值读出的白盒采样对应物；E4.3 MaxEnt-IRL 黑盒恢复属报告附栏）。
- **E14.4** `estimate_epi_accuracy(trajs, bucket_map)`：$A_{epi}^{real}$ 的日志直读精度估计（2026-10-15 精度化口径，取代原两臂 B 边缘经验 TV 估计器 `estimate_b_tv`）——逐轨迹命中率 $\frac1T\sum_t\mathbf 1[B_t=\kappa(E_t)]$（$E_t$ 与 $S_t.B$ 由 P8.2 日志直读，κ 同真值路径）的轨迹平均；真值对照 `components.truth_A_epi_real`（同 κ）。
- **E14.5** `estimate_mi_action_obs(trajs, t, n_A, n_O)`：$I(A_t;O_{t+1})$ 黑盒观察量（10.3 obs 协议侧）采样插件；真值对照 `blackbox.a_exec_blackbox(policy_driven=True)`。
- **E14.6 区间约定**：全部估计器的 `half`=8 等分块均值的 95% 正态半宽（$1.96\,s_{块}/\sqrt8$）；插件 MI/TV 的 Miller–Madow 级正偏差 $(K-1)/2N$ 入 `diagnostics["mm_bias"]` 登记（不作为区间下限扣除——偏差方向已知为正，报告注记）。

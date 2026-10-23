# WFF 能力边界与知识层修复计划

- 日期: 2026-10-24
- 状态: 待用户确认（决策表见 §6，回复"全部默认"即放行）
- 负责侧: skill 侧 agent（P2 §4 平台传导按分工只出清单不改平台代码）
- 依据: 2026-10-23 两轮深度对话（能力边界重验 + 错误归因复盘），证据落盘 `~/unpack-audit/`

---

## 1. 背景与证据基线

2026-10-23 晚解包审计实锤：

1. 上游 google/watchface 规范现有 **v1–v5 五版本**（v5 = PR#113, 2026-08-13 上线）；本仓库 08-24 vendor 只入了 v1 树（`vendor/google-watchface/SOURCE.md`），而知识层蒸馏的却是 v5（`data/wff_inventory_v5.json`）——**知识 v5 / 校验树 v1 / 运行声明 v1，三分裂从未对账**。
2. **Rush-Hour-Reply**（复刻 Pixel Watch 4 Rush Hour 的开源 WFF 成品，WatchFaceStudio-1.9.5 导出，`unpack-audit/rush-hour-reply/`）声明 `format.version=2`：**37 个 `<Transform>` 全部表达式驱动**（如 `value="144 + ([SECOND_MILLISECOND] * 6)"`），零帧序列 / 零 BitmapFont / 零 Animation 时间线 → 规则层"动效铁律：WOS6 只渲染帧序列（R53/R54）"被第三方成品证伪（一般形式）。
3. **AboutTime-Wear**（`unpack-audit/abouttime/`）README 明确目标 = Wear OS 6 / API 36 / WFF4，770 个系统 `<Font>` 渲染中文；utility-wff 声明 version=4。
4. 本仓库 builder 的 Manifest 一直声明 `format.version=1`（08-15 以"WFF v1 对应 minSdk=33"拍板，"版本声明门控什么特性"从未被审查；P2 阶段曾为编辑器按钮问题试过 wff_version=2，"对那个 bug 无效"被泛化成"版本不是变量"）。

**错误归因**（10-23 复盘终判）：H3 起源（未经审视的默认值 + 实验缺关键变量 + 已识别的验证任务从不执行）+ H2 固化（铁律式规则语言，无置信标注/推翻条件，跨会话自我复制，外部 agent 三回合反复修改同病根）+ H4 跨会话碎片化（反证与结论分居两文档两会话从未同框）为主因；H1 模型能力仅贡献一步过度概括；另补 H5 单一神谕（只有负向自测，无正向成品对照）。

**污染范围实测**（10-24 grep）：错误结论**未泄漏进 api/ 或 frontend/**（CDM 提示词干净），仅存在于 skill 目录（references/tests/SKILL.md）、`docs/ROADMAP.md`、`docs/ACCEPTANCE_v0.3.0.md`、`wff_builder.py` 注释层——修复范围收敛。

## 2. 问题清单

| # | 问题 | 层级 | 修复阶段 |
|---|---|---|---|
| P-01 | R53"只渲染帧序列"被证伪；R54/R61 存在未排除的版本混淆变量 | 内容 | P1 |
| P-02 | builder 声明 version=1；vendor 只入 v1，上游已 v1-v5 | 数据源 | P3 |
| P-03 | 规则层"铁律"式语言、无证据类型/适用范围/推翻条件，误导生成与诊断 agent | 知识层 | P2 |
| P-04 | 反证与结论跨会话不同框；决策被记成规则而非"带假设的决策" | 流程 | P4/P6 |
| P-05 | 验证体系单一神谕：无正向成品对照 | 流程 | P4 |
| P-06 | 美学路径未落地：3 个通用 Web 向 skill 契合度不够，需 WFF 域特化 | 产品 | P5 |
| P-07 | 记忆/文档中历史结论的过度自信表述需要结构化修订 | 记忆 | P6 |

## 3. 阶段总览

| 阶段 | 内容 | 依赖 | 工作量 | 状态 |
|---|---|---|---|---|
| P0 | 解包审计 + 记忆清理 + 需求对齐 | — | — | ✅ 完成（10-23） |
| P1 | version×construct 真机矩阵复测 → 边界定稿 | 用户真机一轮 | 我方 ~2h + 用户 ~20min | 待确认即启 |
| P2 | 规则层修订（置信标注 + 终判 + 全库一致性） | P1 结果 | 1-2 天 | 排队 |
| P3 | 数据源升级（vendor v1-v5 + 上游监控脚本） | 无，可并行 | 2-3h | 可立即 |
| P4 | 解包语料库 + 自动矛盾扫描（正向神谕常态化） | 无，可并行 | 1 天 | 可立即 |
| P5 | WFF 域特化美学 skill 蒸馏 | P1/P2 定稿（骨架可并行） | 3-5 天 | 排队 |
| P6 | 记忆/流程结构修复（决策带假设、结论带不确定性） | 无，可并行 | 2-3h | 可立即 |

## 4. 各阶段详情

### P1 真机矩阵复测（边界定稿）

**目标**: R53/R54/R61 从"version=1 下我们的构造不渲染"升级为"version×construct 全格真机实证"。

构造 × 版本矩阵（minSdk 恒定 33 隔离变量；"v1↔minSdk33 不要混用 v4"的旧配对本身未经实证，矩阵后退役）：

| 构造 | 内容 |
|---|---|
| C1 | 表达式驱动 Transform（[SECOND_MILLISECOND] 秒针环，Rush-Hour 原构造照抄） |
| C2 | Transform+Animation 时间线（R53 原构造，duration/fps/interpolation） |
| C3 | Gyro（官方 gyroElements.xsd 示例表达式，转腕验证） |
| C4 | BitmapFont 最小数字 |
| C5 | 帧序列动画（正控制，R55 已实证） |

交付 3 个探针 APK（M1/M2/M4，每个包含全部 5 探针、空间分区布局，单 APK 内构造互不依赖）+ **Rush-Hour-Reply 原版 APK（正向对照，排除我方代码风险）**。用户安装 4 个，短反馈（"1动/2不动"式）。

**验收**: 15 格 + RHR 对照全部带证据标注的边界表；R53/R54/R61 终判（维持/推翻/版本门控）落盘。

**分支预案**: 若 V2/V4 下 C1 不动而 RHR 原版正常动 → 问题在我方构造与第三方构造差异，转构造逐字段 diff；若 RHR 原版也不动 → "WOS6 渲染器缺口"修正版复活，转帧序列+表达式混合路线并重评美学策略（解包对标方法论不变）。

### P2 规则层修订

范围: `skills/wff-watchface-dev/references/`（pitfalls/styles/elements/recipes）+ `tests/blindtest/`（BT-09 卡与 criteria.json）+ SKILL.md + `docs/ROADMAP.md` + `docs/ACCEPTANCE_v0.3.0.md` + `wff_builder.py` 注释。

1. R53/R54/R61 按 P1 终判重写：实测构造、版本上下文、证据类型（真机实证/成品实证/推断/未验/被推翻）、**推翻条件**（什么观察会翻案）。
2. R 系列全量规则挂证据类型与适用范围；"铁律/不渲染/不支持/废弃"式无条件表述改为带范围表述。
3. 新增规则：版本门控语义、表达式 Transform 构造参考（引 Rush-Hour XML 样例）、[SECOND_MILLISECOND] 平滑秒针。
4. 平台侧传导：10-24 grep 证实错误结论未入 api/frontend；P2 完成后在 CHANGELOG 记录规则语义变更，按 `docs/API_CONTRACT.md` 通知平台 agent（平台无代码改动需求）。

**验收**: grep 扫描负面断言零"无标注"；validate 16/16 PASS；BT-01/09 盲测卡冒烟重跑；CHANGELOG 同步。

### P3 数据源升级

1. vendor 重取：上游（d1cdafa9，已在 `unpack-audit/google-watchface-upstream`）v1/v2/v4/v5 全入 + SOURCE.md 更新钉定 commit/日期；校验器按声明版本选 XSD 树（v1/v5 双树 → 四树矩阵）。
2. `tools/check-upstream.sh`：比对 GitHub API 上游 HEAD vs SOURCE.md 钉定值——边界相关会话必跑，落位 skill 三触发器流程。
3. 查上游 wff-validator.jar 是否有 >1.7.0 的 release：有则升，无则记。

**验收**: demo 构建 21KB 签名 PASS；本机 148+1 全绿；四版本 XSD 树编译通过。

### P4 解包语料库 + 自动矛盾扫描（正向神谕）

1. `tools/unpack-audit.py`：APK → 分类（WFF: res/raw/watchface.xml 明文 / WFS/Canvas: 其他）→ 抽 watchface.xml + 解析二进制 manifest 的 format.version + 元素/数据源清单 → JSON 语料条目（含 license/来源标注，GPL 只看不抄，素材不复用）。
2. 语料回填：rush-hour-reply（v2）、abouttime（v4）、utility-wff（v4）、concentric（MIT）+ 用户 adb 拉取的商店标杆 2-5 个。
3. **矛盾扫描**：语料元素清单 × 规则层负面断言交叉——"第三方用了我们判定不可能的构造"即红牌。规则修订后、语料新增后必跑。直接堵死 09-22 型失败（反证躺库一个月无人对照）。

**验收**: 脚本对 4 个存量语料 e2e 跑通；矛盾扫描报告输出且当前零红牌（R53 修订后）。

### P5 WFF 域特化美学 skill 蒸馏

数据源: 解包语料（Rush-Hour 的 108 PartDraw 矢量构造 / ColorConfiguration 调色 / 57 个 AOD Variant 组织 / HsbFilter 着色语法）+ 官方 samples + 11 个已核验仓库 + S1 Material-Refresh 成功案例。

蒸馏目标（设计 token 化）: 圆屏内接圆布局数学、调色系统、系统字 12 weight × 9 width 字体策略、信息密度模式、双态（active/AOD）设计、动画帧预算。

结构约束: 上下文预算按已测数据控制（两套全载 59-72K 过重 → 分阶段挂载）。

**验收**: 同提示词 A/B 盲测（旧 skill 配置 vs 新配置）→ 用户真机评判 + 结构指标（内接圆违规数/资源合法性）；提升不显著则降级为"语料直进 recipes 案例库"路线。

### P6 记忆/流程结构修复

1. 承重决策（版本声明、minSdk、vendor 范围）在记忆中改写为"决策 + 假设 + 重开条件"三段式，不再记成规则。
2. 实证结论入记忆必须带证据类型 + 适用范围；09-13 历史条目保留原文（历史不篡改），10-23 新条目已注明重验覆盖关系。
3. 归因复盘方法论沉淀（10-23 daily 已记）。

## 5. 用户参与点

- P1: 安装 4 个 APK + 短反馈（唯一硬参与，~20 分钟）
- P4: 可选 adb 拉商店标杆 APK 2-5 个（不拉则开源语料先行，不阻塞）
- P5: 美学盲测评判轮（后期）

## 6. 决策表（分歧点 + 默认方案）

| # | 分歧点 | 默认 | 备选 |
|---|---|---|---|
| D1 | 矩阵规模 | 3 探针包 + Rush-Hour 原版 = 4 个安装 | 15 个独立 APK（更准、装机量大） |
| D2 | 矩阵通过后的默认版本 | 切到全构造通过的最高版本（对齐第三方） | 保守留 v1 |
| D3 | 规则审计范围 | R 系列全量 + 被引用最多的正规则挂范围 | 仅负面断言 |
| D4 | vendor 版本树 | v1+v2+v4+v5 全入 | 只加 v5 |
| D5 | 美学 skill 启动时机 | 骨架+语料整理立即并行，蒸馏等 P1/P2 定稿 | 全串行 |
| D6 | 上游监控 | 手动 check-upstream 脚本挂 skill 触发器流程 | cron 每日自动 |
| D7 | 平台侧传导 | 只出发现清单走契约文档（守分工） | 直接改平台代码 |

## 7. 风险与降级预案

| 风险 | 概率 | 降级预案 |
|---|---|---|
| V2/V4 探针在 WOS6 不动（R53 修正版复活） | 中 | Rush-Hour 原版行为是分水岭；转帧序列+表达式混合路线，美学策略重评但解包对标方法论不变 |
| 商店 APK adb 拉取不顺 | 中 | 开源语料（4 个）先行，商店标杆延后不阻塞 |
| 全量规则审计工作量超预期 | 低 | R 系列先行分批，其余滚动 |
| 美学蒸馏盲测无显著提升 | 中 | 语料直进 recipes/案例库（检索路线兜底） |
| 其他会话在途改动（api/services/quota.py 未提交） | — | 本计划单独提交文档，绝不碰在途代码 |

## 8. 执行顺序

确认后并行启动：**P1 构建（~2h，交付 4 APK 等真机反馈）+ P3 vendor 升级 + P4 语料脚本 + P6 记忆格式**。真机反馈回来 → **P2 规则终修** → **P5 美学蒸馏** → 回归主轨道（届时再做系统级产品规划）。

## 9. 总验收判据

**结构性**（同类错误不可再以同样方式发生）:
1. 规则层负面断言 100% 挂证据类型 + 推翻条件
2. 矛盾扫描在环（语料 × 规则自动对照）
3. 承重决策带假设、可重开
4. 正向神谕（成品对照）常态化

**内容性**: R53/R54/R61 终判落盘；builder 默认版本对齐第三方实证；盲测回归全绿。

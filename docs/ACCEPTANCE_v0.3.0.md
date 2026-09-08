# WatchFace-Forge WFF Skill v0.3.0 盲测验收报告

- 项目：WatchFace-Forge（GitHub: FDFxiaoyugan/WatchFace-Forge）
- 验收对象：`skills/wff-watchface-dev/`（教任意 AI agent 开发 WFF 表盘的 Agent Skill）
- 阶段：Phase 4C 盲测循环收官
- 日期：2026-09-08
- 验收环境：Galaxy Watch6 / One UI 8.0 / Android 16（WOS6）
- 主持人（评分方）：本仓库维护 agent；被测对象：fresh agent 会话（无历史知识）

---

## 1. 执行摘要

**结论：v0.3.0 通过盲测验收。** 四轮盲测（BT-03 / BT-02 / BT-04 / BT-05）全部 PASS，交付物均通过三层评分（静态检查 + 双级 validate + 签名 APK 构建）与真机验收。

核心质量指标：

| 指标 | 结果 |
|------|------|
| 盲测轮次 | 4 轮，4 张需求卡，全部 PASS |
| XML 首轮通过双级校验 | Round 2 起 3/3 轮零修复 |
| 静态检查累计 | 4 轮全过（38 项检查点） |
| validate 累计 | 0 error（Round 4 唯一 warning 为评分工具误报，已修） |
| 签名 APK | 4 枚（32.6KB / 128.9KB / 16.6KB / 24.6KB） |
| 真机验收 | 4 轮全过（含条件变色、ambient 双态两个高难场景） |
| 知识层缺陷趋势 | 11 处 → 7 处 → 1 处（规范级）→ 0 处（XML 结构层面） |

**v0.3.0 发布**（2026-09-08，提交 `23222db`）：规则 21 条（R01-R32 中生效 21 条）、环境自查清单、inventory attributeGroup 修复、R13 数据源白名单 XSD 全集、商务风配方、PartDraw 整层 Variant 范式。

---

## 2. 盲测方法论

### 2.1 设计目标

验证「fresh agent 仅凭 skill 就能从一行需求交付可安装、真机渲染正确的表盘」。这是对 skill 知识层完备性的黑盒测试——不测实现，只测结果。

### 2.2 流程

1. **需求卡**（cards/BT-xx）：一段用户原话需求 + 资源约束，agent 看不到卡之外的任何验收标准
2. **fresh agent 会话**：新开无历史会话，唯一知识源 = skill 目录；禁止读 docs/、runs/、记忆文件；禁止提问
3. **三层评分**（score_blindtest.py）：
   - static：criteria.json 正则查语义（验语义不验实现路径）
   - validate：builder 21 规则初筛 + 官方 wff-validator.jar v5 终审（双级）
   - build：可安装签名 APK + sha256
4. **真机验收**：用户实机装 APK + 短句反馈（每条都是精准诊断线索）
5. **评分回灌**：agent 的 ASSUMPTIONS.md 反馈逐条核实 → 修 skill / 修评分工具 → 回归测试 → 版本发布

### 2.3 kickoff 前预审（Round 3 起强制）

每轮开测前精读未抽卡的知识层章节 + criteria：Round 3 实证抓出 Condition 三处规范错误（无 expression 属性 / Compare 按 name 引用 / 运算符无 `<` `<=` 只能反转写 `20 > [SRC]`）——若非预审，该轮盲测必挂。知识层新示例必须先过 wff-validator 再入库。

### 2.4 卡池

| 卡 | 场景 | 状态 |
|----|------|------|
| BT-01 | 极简数字表盘 | 降级为发布前冒烟卡（功能点被 BT-03/04 覆盖） |
| BT-02 | 模拟三针表盘 | Round 2 PASS |
| BT-03 | Complication 复杂功能 | Round 1 PASS |
| BT-04 | 低电量条件变色 | Round 3 PASS |
| BT-05 | Ambient 双态场景 | Round 4 PASS |

---

## 3. 四轮结果

| 轮 | 卡 | 日期 | validate 修复轮 | 真机验收 | 回灌量 |
|----|----|------|----------------|----------|--------|
| R1 | BT-03 | 08-27 | 4 | complication 心率渲染 OK | 11 处知识层大修 → v0.2.0 |
| R2 | BT-02 | 09-06 | **0** | 秒针像素级错位 1 轮自修 | 7 处（配方坐标/R31/工具） |
| R3 | BT-04 | 09-08 | **0** | 电量 19% 红色分支实证 | R32 规范级大修 + 环境类 5 处 |
| R4 | BT-05 | 09-08 | **0** | active 全彩 + 熄屏只剩细体暗色时间 | 6 处（全工具/文档） |

**收敛分析**：validate 修复轮 4→0→0→0。Round 1 的 4 轮修复全部源自 v0.1.0 知识层缺陷（嵌套方向反转、HH:mm 非法、Complication 属性集错误）；v0.2.0 之后 agent 交付的 XML 一次通过双级校验。Round 3/4 的回灌全部是环境清单、builder 白名单、inventory 解析器、配方丰富度——XML 结构层面缺陷已收敛到零。

**两个高难场景真机实证**：
- 条件渲染（BT-04）：`20 > [BATTERY_PERCENT]` 反转条件在真机正确求值切分支（截图电量 19% → 数字变红）
- Ambient 双态（BT-05）：抬腕全彩三元素（时间/日期/步数+金装饰），熄屏只剩细体暗色时间——Variant 整层隐藏策略真机有效

---

## 4. 真机验证记录

| 轮 | 真机反馈 | 处置 |
|----|----------|------|
| R1 | 心率 complication 渲染成功（约 1 秒/次刷新为三星健康 provider 行为） | R26 空 Complication / R28 局部坐标修正被验证有效 |
| R2 | 三针渲染成功但秒针旋转轴不过圆心（0.163px alpha 质心偏移） | 盲测 agent 自主像素级修复（PIL inclusive 右边界 → alpha 质心校验），回灌 R31 指针对称规则 |
| R3 | 电池 19% 时数字变红，时间/日期/布局正常 | R32 官方 Condition 结构真机验证通过 |
| R4 | 熄屏后只剩细体暗色时间，active 全彩无渲染异常 | 双 TimeText 交换 + Variant 隐藏范式真机验证通过 |

历史真机复盘（2026-08-31，三轮）：R26-R30（空 Complication / cornerRadiusX-Y / BoundingShape 局部坐标 / Template 强制 Parameter / displayName 资源化）已并入 v0.2.2。

---

## 5. 知识层演进

| 版本 | 日期 | 驱动事件 | 变化 |
|------|------|----------|------|
| v0.1.0 | 08-24 | Phase 4B 首版 | 90 元素 / 29 枚举 XSD 蒸馏 + 3 配方 + 16 规则 |
| v0.2.0 | 08-27 | Round 1 评分回灌 | 知识层大修 11 处 + 两级验证工作流 + R17-R25 |
| v0.2.2 | 08-31 | 真机三轮复盘 | R26-R30 + 规则 20 条（真机验证闭环） |
| v0.3.0 | 09-08 | 盲测四轮收官 | R31-R32 + 环境自查清单 + inventory attributeGroup 修复 + R13 白名单 XSD 全集 + 商务配方 + PartDraw Variant 范式（规则 21 条） |

四轮回灌账本（全部核实属实，零误报）：

- **R1（11 处）**：嵌套方向反转 / HH:mm 非法 / Complication 属性集 / 列表空格分隔 / BoundingShape 抽象
- **R2（7 处）**：配方三针旋转中心 bug / R31 alpha 对称 / builder yaml 列表解析 / 评分正则锁实现路径（A5/A6）
- **R3（5 处，环境类）**：SDK 兜底路径 / JDK 获取 / build-tools zip 结构 / aapt2 ARM 限制 / AOD Condition 语义空白
- **R4（6 处，工具/文档）**：R13 白名单失同步 / inventory attributeGroup 缺失 / 形状属性表 / PartDraw Variant 范式 / 商务配方 / preview 镜像要点

---

## 6. 已知限制与遗留

| 项 | 状态 | 说明 |
|----|------|------|
| P2 编辑器自定义按钮 | 归档待修 | 用户对照实验证实官方表盘有自定义按钮 → 锁定表盘缺编辑器识别项；最大嫌疑 UserConfigurations 缺失 → 由颜色包（v0.4.0）验证 |
| test_build_digital 存量失败 | 已记录 | CDM 编译链路环境问题，干净 HEAD 同样失败，与 skill 无关 |
| ARM 兜底模板单槽位 | 已写明 | aapt2 x86_64 only；ARM 走预编译模板只注册 preview——多图盘必须 x86_64 构建 |
| AOD 下 Condition 求值语义 | 未验证 | agent 保守处理（条件始终求值 + alpha 降亮度）active 态验证通过；AOD 态待真机 |
| BT-01 | 降级 | 冒烟卡用途：skill 升级后直接跑端到端确认无回归 |

---

## 7. 下一阶段：三个能力包

### 7.1 排序与依据

| 包 | 版本 | 范围（XSD 权威结构） | 真机验证点 | 盲测卡 | 依赖 |
|----|------|---------------------|-----------|--------|------|
| 自定义颜色包 | v0.4.0 | ColorConfiguration / ColorOption（id + PartElementGroup/Group 引用）/ [CONFIGURATION.X] 表达式 / @string displayName 资源化（R30） | One UI 编辑器出现自定义按钮 + 颜色切换生效；**顺带验证 P2 bug 修复** | BT-07 | 无（XSD 已就绪） |
| 自定义组件包 | v0.5.0 | ListConfiguration / BooleanConfiguration / ComplicationSlot 自定义 provider 选择 | 编辑器内换 complication provider、切换列表选项 | BT-08 | 颜色包的 UserConfigurations 基础 |
| 动画能力包 | v0.6.0 | AnimatedImage / AnimatedImages / PartAnimatedImage / SequenceImages / AnimationController / Animation / Gyro 视差 | AOD 下动画行为（帧率/burn-in）、SequenceImages 资源体积、触发语义 | BT-09 | **建议等平台 CI 真机工具链联调**（动画需要高频真机反馈） |

### 7.2 各包交付标准

每个能力包走完整闭环：XSD 精读 → 知识层章节 + 配方 → wff-validator 验证 → 真机验证 → 盲测卡一轮 → 评分回灌 → 版本发布。

- **颜色包**关键风险：ColorOption 内部是 PartElementGroup/Group 引用（每选项定义一整组渲染），非简单换色——配方必须教「按 [CONFIGURATION.id] 表达式切换渲染组」的正确范式；displayName 必须 @string 资源化（R30 真机教训）
- **组件包**关键风险：ComplicationSlot 编辑器自定义入口与 UserConfigurations 的联动语义；R26/R28 真机经验复用
- **动画包**关键风险：全 WFF 最容易真机翻车的区域（AOD 帧率限制、burn-in 保护、帧序列体积）；预审要精读 animatedImage + transform 两个 XSD 分支

---

## 8. 结论

Phase 4C 盲测循环收官：四轮全 PASS，质量收敛曲线明确（validate 修复轮 4→0，知识层缺陷收敛至零），skill v0.3.0 具备「fresh agent 一次通过双级校验 + 真机渲染正确」的可复现能力。

下一阶段按颜色包（v0.4.0）→ 组件包（v0.5.0）→ 动画包（v0.6.0）推进，颜色包与 P2 编辑器 bug 验证联动。

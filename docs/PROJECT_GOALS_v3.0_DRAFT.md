# AI 驱动的 Wear OS 表盘生成与分发平台 — 项目目标文档 v3.0 修订草案

> **文档版本:** v3.0-draft.1
> **创建日期:** 2026-08-23
> **状态:** 修订草案，待用户审阅批准。批准前不得作为开发依据；现行有效版本仍为 PROJECT_GOALS.md v2.2
> **审阅重点:** §0 变更对照表、§10 待拍板清单
> **生效流程:** 用户批准后，按 §0 变更对照表将本文档内容合并进 `docs/PROJECT_GOALS.md` 并升版为 v3.0，本草案文件保留作决策存档

---

## 0. 修订摘要 — v2.2 → v3.0 变更对照表

| # | v2.2 | v3.0 | 变更类型 |
|---|------|------|----------|
| 1 | 愿景：让**任何人**通过一句话 + 可视化编辑器获得表盘 | 愿景：让**任何 agent**（以及通过 CDM 通道的普通用户）产出高质量表盘，质量由平台 CI 保证 | 修订 §0 |
| 2 | 一期核心交付物含完整 WYSIWYG 编辑器（Phase 3 已交付子集） | **编辑器方向冻结**。复杂表盘的表达路径改为 agent 直写 WFF XML | 重大转向 |
| 3 | 二期 Phase 4 = Apple Watch 编译器（CDM 多端统一） | 二期 Phase 4 = **WFF 直通管线 + Agent Skill**。Apple Watch 改走 agent-skill 路线，CDM 多端统一叙事退役 | 重排 |
| 4 | CDM 是前后端唯一桥梁，前端永远不直接生成 WFF XML（红线） | **双通道数据模型**：CDM 通道（普通用户，安全子集）+ WFF 直通通道（agent，全功能，平台校验把关）。原红线继续适用于 CDM 通道编辑器代码 | 红线修订 |
| 5 | 无 skill / agent 生态概念 | 新增 **Agent Skill 规格**（§5）与**分工协作机制**（§8） | 新增 |
| 6 | 官方 google/watchface 仓库仅作 XSD 校验器引用 | 升级为**官方工具链全量集成**：XSD 知识蒸馏、wff-validator、内存评估器、优化器（§4.4） | 增强 |
| 7 | 风险登记册 R01-R07 | 新增 R08-R14（§9），R05/R06 部分失效 | 增量 |
| 8 | 未提及章节（管理后台 §6、部署架构 §7、非功能性 §8、隐形问题清单 §9A、代码规范 §10.5-10.6、附录） | **全部继承 v2.2 原文，仅按需微调**（见附录 A） | 继承 |

---

## 1. 转向决策记录

### 1.1 触发背景

2026-08-22 用户提出：完整好用的 WFF 编辑器难度远超预期——做编辑器等于做解释器，需要完整理解 WFF 的全部语言特性；且美观、动画复杂的表盘用编辑器拼装本身就不现实。提议改为：**做一个 skill 教任意 agent 开发 WFF 表盘，网站承担测试、验证、预览、打包**。

### 1.2 决策依据

**① 编辑器与渲染器成本不对称。**

| 组件 | 方向 | 成本 |
|------|------|------|
| 预览渲染器 | XML → 画面（只读，单向） | 可控，是编辑器成本的零头 |
| WYSIWYG 编辑器 | XML ⇌ 画布（双向往返） | 需完整建模每个元素/属性/表达式 + 表达式编辑 UI + 动画时间线，等价于重造 Samsung Watch Face Studio（专职团队多年投入） |

**② 一期已实际撞到这堵墙。** ARCHITECTURE.md 偏差 #1 记录：CDM 被迫收窄为 7 个功能域的结构化子集，Phase 3 编辑器只能表达该子集——复杂动画、多场景、条件渲染天然做不了。这是路线问题，不是实现问题。

**③ Agent 是写受约束声明式 XML 的最强选手。** 项目已有的 16 条校验规则 + XSD 结构化错误输出，恰好构成 agent 自我修复循环（validate → fix → re-validate）所需的反馈信号。平台已经天然是个 oracle，此前没有把它当主角。

**④ 赛道验证（2026-08-23 调研）：**

| 调研项 | 结果 |
|--------|------|
| Watch Face Studio MCP / API / AI 集成 | 无，纯 GUI 工具，无开放迹象 |
| GitHub 全站 watch face 相关 MCP 服务器 | 0 个 |
| 各 skill 市场 WFF / 表盘开发 skill | 0 个 |
| 最接近类比 | lens-studio-mcp（Snap AR 特效，证明"AI+官方格式+验证闭环"模式成立） |
| 潜在需求信号 | Reddit 常年有"不懂代码如何做 WFF 表盘"求助（Wear OS 5 后 Facer/WatchMaker 失效） |
| 官方地基 | google/watchface（Apache-2.0，活跃维护）提供 XSD 规范、官方校验器、内存评估器、优化器 |

**结论：第一个做"agent 表盘 CI 平台"，且踩在官方地基上，而非自建地基。**

### 1.3 定位变化（明说）

"人人 30 秒做表盘" → "任何 agent 30 秒做出高质量表盘 + 普通用户一句话快速生成（CDM 通道）"。2026 年 agent 使用门槛趋近于零，但定位确实变了，需用户认可（§10-1）。

---

## 2. 新愿景与产品形态

### 2.1 愿景（v3.0）

让任何 agent 通过平台 skill 与 CI 管线，在分钟级产出通过官方校验、可直接安装到真机的 Wear OS 表盘；普通用户仍可通过一句话快速生成（CDM 通道）。平台是表盘质量的裁判和分发枢纽，不苛求自己是表盘的作者。

### 2.2 双引擎产品形态

```
┌────────────────────────────────────────────────────────────┐
│ 引擎 A（主）：Agent CI 平台                                  │
│                                                            │
│   任意 agent + wff-watchface-dev skill                      │
│     → 写 watchface.xml (+素材)                              │
│     → POST /api/v1/wff/validate   (XSD + 官方validator+lint)│
│     → POST /api/v1/wff/preview    (多时间点/ambient 静态帧)  │
│     → 迭代修复（agent 自修复循环）                            │
│     → POST /api/v1/wff/build      (APK + 校验和；二维码为辅助) │
│     → 真机安装验证（无线 ADB / Play 测试轨道抽查）             │
└────────────────────────────────────────────────────────────┘
┌────────────────────────────────────────────────────────────┐
│ 引擎 B（辅）：CDM 快速通道（一期已建成，维持现状）              │
│                                                            │
│   普通用户一句话 → LLM → CDM JSON（7 功能域安全子集）          │
│     → 模板微调 → compile → APK                              │
└────────────────────────────────────────────────────────────┘
```

两引擎共享：APK 构建管线、图像处理服务、存储/CDN、管理后台、安装引导。

### 2.3 目标用户变化

| v2.2 | v3.0 |
|------|------|
| 主要：手表爱好者（无开发能力） | 主要：**agent 及其背后的人类操作者**（开发者/爱好者/设计师） |
| 次要：独立设计师 | 次要：普通用户（CDM 通道，一句话生成） |

---

## 3. 核心原则修订

### 3.1 保留的原则（原文不动）

- 只走 WFF（hasCode=false，纯资源 APK）
- AI 外包，本地不做推理
- 编译器可插拔（WFF 直通管线不经过 CDM，但 CDM 编译器接口保留）
- 客户端可裁剪
- 许可证合规（严禁 Copyleft）
- 三次熔断

### 3.2 修订：数据与视图分离 → 双通道数据模型

| 通道 | 数据形态 | 用户 | 表达能力 | 质量把关 |
|------|----------|------|----------|----------|
| CDM 通道 | CDM JSON（7 功能域结构化子集） | 网站普通用户、编辑器（冻结态） | 安全子集 | 编译期校验 |
| WFF 直通通道 | WFF XML（agent 直写，全功能） | agent | 完整 WFF 特性 | 平台 CI：XSD + 官方 validator + 16 规则 lint + 预览 + 真机抽查 |

**原红线"前端永远不直接生成 WFF XML"继续适用于 CDM 通道的编辑器前端代码。** WFF 直通通道的 XML 由 agent 产出，但**必须通过平台 validate 才能进入 build 与分发**——平台校验是唯一放行关口，这条是新的硬约束。

### 3.3 红线规则 v3.0

| 规则 | 说明 |
|------|------|
| 只走 WFF | 不变 |
| AI 外包 | 不变 |
| 许可证合规 | 不变 |
| 双通道数据模型 | CDM 通道不接触 XML；直通通道 XML 未经平台 validate 不得 build/分发 |
| 三次熔断 | 不变 |
| **预览非真相** | 预览渲染器只做结构正确性与大致视觉检查，**最终裁判永远是真机**。此边界必须写进 skill 并在平台 UI 标注 |

---

## 4. 新架构 — WFF 直通管线（Agent CI）

### 4.1 管线总览

```
agent（任意机器，持有 skill + API key）
   │  multipart: watchface.xml + assets[]
   ↓
/api/v1/wff/validate ──→ 三层校验合并输出（结构化错误 + 修复提示）
   ↓ 通过
/api/v1/wff/preview  ──→ 静态帧 PNG（active×N 时间点 + ambient）
   ↓ agent 自查视觉（可用 VLM）
（循环：修改 XML → 重新 validate/preview，直到满意）
   ↓
/api/v1/wff/build    ──→ 签名 APK + 下载 URL + 校验和（二维码为手机辅助入口）
   ↓
真机安装（无线 ADB / Wear Installer / Play 测试轨道）→ 显示效果反馈回 pitfalls 知识库
```

### 4.2 API 契约 v0.1

> 详细契约在 Phase 4 开工时固化为 `docs/API_CONTRACT.md`（版本化，双方唯一协调产物）。以下为 v0.1 摘要，字段级变更走 §8.2 契约变更流程。

**通用**

- 鉴权：`X-API-Key` 头（平台签发，管理后台管理）
- 限流：令牌桶，按 key 配额（建议初始：validate 60 次/h、preview 20 次/h、build 10 次/h，待定）
- 错误格式：`{"error": {"code": "RATE_LIMITED", "message": "..."}}`
- 请求格式：`multipart/form-data`（XML 文本 + 二进制素材）

**POST /api/v1/wff/validate**

```
请求字段:
  xml       (必填) watchface.xml 内容
  assets[]  (可选) 素材文件

响应 200:
{
  "valid": false,
  "errors": [
    {
      "source": "xsd | official_validator | lint",   // 三层来源
      "rule": "WFF-R07",                              // lint 规则编号
      "severity": "error | warning",
      "element": "/WatchFace/Scene/Group[2]/PartText[1]",
      "line": 42,
      "message": "...",
      "hint": "修复建议（lint 层必填，agent 自修复的关键字段）"
    }
  ],
  "stats": {
    "elements": 23, "images": 5, "fonts": 1,
    "total_asset_kb": 214, "estimated_memory_kb": 812
  }
}
```

三层校验（全跑，错误合并，按 severity 排序）：
1. **XSD**（lxml + 官方 XSD）——结构合法性
2. **官方 wff-validator.jar**（服务器侧 Java 调用）——官方语义规则
3. **平台 lint**（现有 16 条规则扩展）——项目踩坑规则 + 修复 hint

**POST /api/v1/wff/preview**

```
请求字段:
  xml, assets[]          同上
  times[]    (默认 ["10:09"])  预览时间点，如 ["10:09","23:59"]
  modes[]    (默认 ["active"]) ["active","ambient"]
  shape      (默认 "round")    round | square
  size       (默认 384)        输出边长像素

响应 200:
{
  "frames": [
    {"time": "10:09", "mode": "active", "format": "png", "data_base64": "..."},
    {"time": "23:59", "mode": "ambient", "format": "png", "data_base64": "..."}
  ],
  "renderer": "pillow-v0",
  "warnings": ["动画渲染为关键帧状态，不代表真机连续动画"]
}
```

**POST /api/v1/wff/build**

```
请求字段:
  xml, assets[]   同上
  name            (必填) 表盘名
  package_name    (可选，默认平台分配)
  version_code    (可选，默认 1)

响应 200:
{
  "build_id": "b_20260823_xxxx",
  "apk": {"url": "https://.../xx.apk", "size_bytes": 398123, "sha256": "..."},
  "qr_url": "https://.../qr.png",
  "warnings": [...]
}
```

同步接口（构建 <10s）；后续量大时升级 202 + 轮询，契约预留 `status` 字段。

### 4.3 预览渲染器

| 版本 | 形态 | 用途 | 说明 |
|------|------|------|------|
| v0 | 服务端 Pillow 静态帧（WFF XML → PNG） | agent 视觉自查（配合 VLM） | 唯一新增的核心工程；**建议由 skill 负责人实现参考版**（WFF 语义密集，与知识层同源），平台侧负责服务化（§8.1 备注） |
| v1 | 浏览器 Canvas + 时间轴 scrub + ambient 切换 | 人类用户在网站上看效果 | 复用一期 Fabric.js 组件（LayerPanel 等）；二期按需排期 |

**渲染边界（写入 skill 与 UI）**：表达式按给定时间点求值；动画渲染为关键帧状态；字体 kerning、抗锯齿与真机存在容差。预览是结构正确性检查，不是像素级模拟。

### 4.4 官方工具链集成（google/watchface，Apache-2.0）

| 组件 | 用途 | 集成位置 | 备注 |
|------|------|----------|------|
| WFF XSD 规范（v1+v2，machine-readable） | skill 知识层蒸馏的**数据源** | `third_party_specs/google-watchface/`（vendor，保留 LICENSE/NOTICE） | 一次性解决"不知道语言特性"问题 |
| wff-validator.jar | validate 端点第二层 | ARM 计算节点（已有 JRE，apksigner 同源依赖） | `java -jar wff-validator.jar 5 watchface.xml` |
| 内存占用评估器 | validate 的 stats 输出 | validate 端点 | Play 上架前置检查，差异化能力 |
| WFF 优化器 | build 管线增值步骤（可选开关） | build 端点 | 降运行时内存 |

许可证结论：Apache-2.0 属宽松许可，**合规**，满足无 Copyleft 红线。仓库活跃维护，列入 skill 更新监控清单（§5.5）。

### 4.5 MCP Wrapper（展望，Phase 5）

HTTP API 稳定后，加一层 MCP server wrapper（~百行代码），暴露 validate/preview/build 三个 tool。skill（知识）+ MCP（工具）组合，任何支持 MCP 的 agent 即插即用。不阻塞 Phase 4。

---

## 5. Agent Skill 规格（wff-watchface-dev）

### 5.1 目录结构

```
skills/wff-watchface-dev/
├── SKILL.md                # 触发条件、工作循环、快速上手（≤300行，按渐进披露原则）
├── references/
│   ├── elements.md         # 元素+属性全参考（XSD 蒸馏 + 实验补充，覆盖率标注）
│   ├── expressions.md      # 数据源/运算符/条件表达式（[MONTH] 方括号语法等）
│   ├── recipes.md          # 配方：数字/指针/混合/ambient/complication/多场景
│   ├── pitfalls.md         # 16 条规则 + NOTES.md 蒸馏 + 真机已知差异，持续增补
│   └── assets.md           # 素材规范：尺寸/格式/单图≤100KB/内存预算
├── examples/               # 已真机验证的完整项目（xml + 素材 + README）
│   ├── minimal-digital/    # 迁移自现有 3 模板 + 1 个复杂示例
│   ├── analog-hands/
│   └── hybrid-complication/
├── client/
│   ├── wff_api.py          # 薄客户端：validate/preview/build 三命令
│   │                       #   双后端: remote(HTTP) | local(subprocess 调 wff-builder)
│   └── config.example.json # base_url / api_key / 后端选择
├── tests/
│   └── blindtest/          # 盲测需求卡片 + 自动评分脚本（§7 Phase 4C）
├── SKILL_MAINTENANCE.md    # 更新手册：触发器、知识层再生成流程、交接须知
└── CHANGELOG.md            # 版本化更新记录（任何 agent 可据此接手）
```

与现有 `wff-builder/SKILL.md` 的关系：**吸收并取代**（旧文件是文档说明，非可分发 skill；迁移后旧文件指向新位置）。

### 5.2 知识层与来源

| 知识文件 | 主数据源 | 增补来源 |
|----------|----------|----------|
| elements.md | 官方 XSD 枚举（4B 首个任务即 XSD 盘点） | 官方文档、真机实验 |
| expressions.md | 官方文档 + XSD | 一期编译器已实现的表达式集 |
| pitfalls.md | 项目 16 条规则 + NOTES.md 全部踩坑 | 真机验证差异、盲测失败案例回灌 |
| recipes.md | examples 归纳 | 盲测沉淀 |

诚实边界：v1 不承诺 100% 覆盖 XSD 全部元素。知识文件对每个元素标注 `已验证 / 文档级 / 未验证` 三档，未验证元素在 skill 中明确提示 agent 谨慎使用并反馈。

### 5.3 工作循环（SKILL.md 核心内容）

```
1. 理解需求 → 选 recipe 起点（复制对应 example）
2. 写/改 watchface.xml + 准备素材（遵守 assets.md 约束）
3. validate → 有 error 按 hint 修复 → 循环（建议上限 5 轮，超限提醒需求可能超出现有能力）
4. preview → （可选）VLM 自查视觉：布局溢出、重叠、ambient 可读性
5. build → 拿到 APK + SHA-256；二维码仅供手机快速打开下载页
6. 真机安装（人类环节）→ 效果反馈记录进 pitfalls.md
```

### 5.4 分发形态

- **remote 模式**（目标形态）：任意机器的任意 agent，只需 skill 目录 + 平台公网地址 + API key。依赖公网入口（阿里云），过渡期不阻塞——
- **local 模式**（开发/测试/过渡期）：本仓库检出环境下，client 直接 subprocess 调 `wff-builder/wff_builder.py`（validate/build 可用，preview 依赖 4A 进度）

### 5.5 版本与更新机制（skill 负任人承诺的维护协议）

| 触发器 | 动作 | 检测方式 |
|--------|------|----------|
| google/watchface 仓库变更（XSD 版本更新） | 知识层 diff → elements/expressions 增补 → 跑回归 examples → 发版 | 可设定时任务周期检查（用户批准后配置） |
| API_CONTRACT.md 版本升级 | client/wff_api.py 适配 → 发版 | 契约变更流程（§8.2）通知 |
| 盲测/真机/用户反馈失败案例 | pitfalls.md 增补（含最小复现） | 反馈渠道 |
| 素材规范/内存预算变化 | assets.md 更新 | 官方评估器输出变化 |

每次更新：git commit + CHANGELOG.md 记录 + SKILL_MAINTENANCE.md 同步。**skill 目录自包含**，任何 agent 可凭 CHANGELOG + 维护手册接手（满足项目交接标准）。

---

## 6. 一期资产处置表

| 一期资产 | 处置 | 新角色 |
|----------|------|--------|
| wff-builder（16 规则 + APK 管线，真机已验证） | ✅ 存活，升为核心 | `/api/v1/wff/build` 后端 + local 模式执行器 |
| XSD 校验 + lint | ✅ 存活 | validate 端点第 1、3 层 |
| FastAPI 骨架 / AI gateway / Pillow 图像管线 | ✅ 存活 | 素材生成+抠图服务（skill 与 CDM 通道共用） |
| APK 下载 + 无线 ADB / Wear Installer 安装链路 | ✅ 存活 | 真机验证闭环；二维码降为手机辅助入口 |
| CDM + /api/compile + 3 模板前端 | 🔧 保留降级 | CDM 快速通道（普通用户一句话生成），不再作为多端统一核心 |
| preview_renderer（CDM→PNG） | 🔧 重写 | WFF XML→静态帧渲染器（4A/4B 协作，见 §4.3） |
| Fabric.js 编辑器（Phase 3） | ❄️ 冻结 | 代码留档不再投入；LayerPanel 等组件可被预览 v1 复用 |
| Celery 异步队列 | ✅ 存活 | build/preview 重任务的异步化（沿用一期踩坑结论） |

---

## 7. 二期开发阶段重排

> 一期（Phase 1-3）已完成并通过验收（2026-08-20），状态不变。二期重新定义如下。

### Phase 4 — WFF 直通管线 + Agent Skill v1

**目标：** 任意 agent 仅凭 skill + 平台 API，盲测产出可通过全流程的表盘。

#### Phase 4A 平台侧（负责人：平台 agent）

| ID | 需求 | 优先级 | 验收标准 |
|----|------|--------|----------|
| P4A-F01 | /api/v1/wff/validate 端点（三层校验合并） | P0 | §4.2 契约符合；非法输入 4xx 结构化错误 |
| P4A-F02 | /api/v1/wff/build 端点（复用 wff-builder） | P0 | 同步构建 <10s；含 sha256 + 直接下载；二维码为非阻塞辅助项 |
| P4A-F03 | 预览渲染器 v0 服务化（/api/v1/wff/preview） | P0 | 常规表盘 3 帧 <5s；渲染边界 warning 输出 |
| P4A-F04 | API key 签发 + 限流 | P0 | 令牌桶生效，超限 429 |
| P4A-F05 | API_CONTRACT.md 固化（v0.1 → v1.0） | P0 | 契约文档含错误码全表 + 示例请求/响应 |
| P4A-F06 | 官方工具链 vendor + 集成 | P1 | wff-validator.jar 跑通于 ARM 节点；内存评估进 stats |

#### Phase 4B Skill 侧（负责人：skill agent，不依赖 4A 进度，立即可开工）

| ID | 需求 | 优先级 | 验收标准 |
|----|------|--------|----------|
| P4B-F01 | XSD 盘点 + elements/expressions v0 | P0 | 覆盖率报告：常用元素全集 + 三档验证标注 |
| P4B-F02 | skill 骨架 + SKILL.md + pitfalls.md（一期知识全量蒸馏） | P0 | 16 规则 + NOTES.md 踩坑全部收录 |
| P4B-F03 | examples：3 现有模板迁移 + 1 个复杂示例（含动画/条件） | P0 | 每个示例 validate+build 通过；1 个经真机复验 |
| P4B-F04 | client 双后端（remote/local） | P0 | local 模式立即可用；remote 待 4A 联调 |
| P4B-F05 | 预览渲染器 v0 参考实现（Pillow） | P0 | 与 4A 共享实现；examples 全集渲染通过 |
| P4B-F06 | 盲测框架（需求卡片 + 评分脚本） | P1 | 自动评 validate/build，视觉项人工/VLM |

#### Phase 4C 集成与盲测（双方联合，4A/4B 完成后）

| ID | 需求 | 验收标准 |
|----|------|----------|
| P4C-T01 | skill ↔ 平台 API 联调（remote 模式全流程） | 三端点全通 |
| P4C-T02 | 盲测首轮 | ≥5 张需求卡片，见下方标准 |

**盲测定义：** 从未接触本仓库的 agent（fresh context），仅获得 skill 目录 + API 地址/key，按随机需求卡独立完成表盘。

**盲测需求卡示例：** ①极简数字 + 日期 + 电池 ②三针模拟 + 秒针 ③混合表盘 + 心率 complication ④含条件渲染（如低电量变色）⑤含 ambient 独立场景。

**盲测通过标准（Phase 4 总验收）：**

| 指标 | 标准 |
|------|------|
| validate 一次通过率 | ≥ 60%（5 张卡中 ≥3 张） |
| 修复循环 | 平均 ≤3 轮达到全绿 |
| build 成功率 | 100%（通过 validate 的必过 build，否则属平台 bug） |
| 真机显示 | 用户抽查 ≥2 张，显示正确、无元素缺失 |
| 知识回灌 | 盲测暴露的每个坑 48h 内进 pitfalls.md |

**工作量估计：** 4A、4B 并行，各 5-8 个工作日；4C 集成 2-3 个工作日。

### Phase 5 — 生态扩展（菜单，按价值排序，待用户排期确认）

| 序 | 项 | 说明 | 依赖 |
|----|-----|------|------|
| 1 | 预览渲染器 v1（浏览器 Canvas） | 时间轴 scrub、ambient 切换，复用 Fabric 组件 | Phase 4 |
| 2 | MCP server wrapper | validate/preview/build 三 tool，skill+MCP 组合 | Phase 4 契约稳定 |
| 3 | 表盘广场 / 社区分发 | agent 产出物的展示、分享、安装统计 | Phase 4 |
| 4 | Apple Watch（agent-skill 路线） | 新 skill（apple-watchface-dev）+ 平台 CI 复用；**不再做 CDM 多端编译器** | Phase 4 验证模式跑通 |
| 5 | 微信小程序（消费端） | 降级为纯浏览/分享/安装引导客户端（v2.2 §5 缩减版） | Phase 5-3 |
| 6 | 多 agent 协作模板 | skill 进阶：人机协作工作流（设计师出图 → agent 组装） | 社区反馈 |

---

## 8. 分工与协作机制

### 8.1 角色分工

| 角色 | 范围 | 交付物 |
|------|------|--------|
| **skill agent**（本 agent 承接） | §5 skill 全部：知识层、examples、client、预览渲染器 v0 参考实现、盲测框架、skill 持续更新 | `skills/wff-watchface-dev/` + CHANGELOG |
| **平台 agent** | §4.2 三端点服务化、鉴权限流、官方工具链集成部署、网站 CI 页面（提交/日志/产物展示）、预览 v1 | `api/` 扩展 + `web/` 扩展 + API_CONTRACT.md 服务端实现 |
| **用户** | 资源决策（阿里云购买、域名/备案）、真机安装抽查（盲测与发版抽验）、方向拍板（§10） | 决策 + 真机反馈 |

**唯一人工环节：真机安装验证**（优先无线 ADB 或 Play 测试轨道，Wear Installer 可选）。validate/preview/build 及 agent 自修复循环全自动。

**备注（§4.3 呼应）：** 预览渲染器 v0 的参考实现放在 skill 侧，理由是 WFF 语义密集、与知识层同源，减少跨 agent 知识转移；平台侧负责其服务化与性能化。若用户不同意此切分，可整体划归平台 agent，skill 侧仅提供语义测试用例集（§10-4）。

### 8.2 接口契约与变更流程

- `docs/API_CONTRACT.md` 是 skill 侧与平台侧的**唯一协调产物**，语义化版本号
- 变更流程：提案（issue/文档批注）→ 双方确认 → 版本升级 → skill client 适配 + 平台实现 → CHANGELOG 双写
- 破坏性变更提前一个 minor 版本公告，skill client 兼容窗口 ≥2 周

### 8.3 交接标准（沿用用户既有要求）

任何一方产出的文档 + 代码必须做到**新 agent 无需人类补充上下文即可开发**：
- skill 侧：SKILL_MAINTENANCE.md + CHANGELOG.md 保证可接手
- 平台侧：API_CONTRACT.md + 部署文档（继承 v2.2 §7 与 DEVELOPMENT.md）
- 双方以 git commit + 文档落盘传递状态，禁用口头/会话内约定

---

## 9. 风险登记册（v3.0 增量，v2.2 R01-R07 中 R05/R06 失效）

| ID | 风险 | 影响 | 概率 | 缓解策略 |
|----|------|------|------|----------|
| R08 | WFF 规范演进（google/watchface 活跃维护，XSD v2/v3） | 知识层与校验器过期 | 中 | §5.5 更新触发器；XSD 版本锁定 vendor，升级走回归 |
| R09 | 预览保真度不足导致 agent 误判 | 视觉缺陷漏到真机环节 | 高 | "预览非真相"红线；preview warnings 必返；真机抽查兜底 |
| R10 | 公网端点缺失，"任意 agent"承诺不成立 | remote 模式不可用 | 中 | 阿里云入口列为 Phase 4 前置项（§10-2）；过渡期 local 模式自用 |
| R11 | API 滥用（validate/preview/build 均消耗计算） | 成本与服务不稳 | 中 | API key + 令牌桶 + 管理后台用量看板（继承 §6） |
| R12 | skill 知识层覆盖率不足，盲测通过率低 | 核心价值不达 | 中 | 三档标注诚实边界；盲测失败案例回灌机制；三次熔断适用于知识生成策略 |
| R13 | agent 生态迁移（skill → MCP 为主流交互） | skill 形态边缘化 | 低 | skill 知识层与工具层解耦，MCP wrapper 平移复用（§4.5） |
| R14 | Java 环境约束（wff-validator.jar） | validate 第二层缺失 | 低 | ARM 节点已有 JRE（apksigner 同源）；容器内置 headless JRE |

---

## 10. 待用户拍板清单

| # | 决策点 | 选项与建议 |
|---|--------|-----------|
| 1 | 本草案批准（定位变化：编辑器冻结、agent CI 为主引擎） | 批准后按 §0 合并升版 v3.0 |
| 2 | 阿里云购买与域名备案启动时间 | 建议 Phase 4A 开工前启动（备案 1-2 周与开发并行）；备案期间用日本 VPS IP 过渡 |
| 3 | Phase 5 排期（§7 菜单 1-6 序确认或调整） | 建议 1→2→3 优先 |
| 4 | 预览渲染器 v0 实现归属 | 建议 skill 侧参考实现 + 平台侧服务化（§8.1 备注）；或整体平台侧 |
| 5 | API 免费配额策略（§4.2 建议值） | 影响成本模型，可后置到 Phase 4 末 |

---

## 附录 A: v2.2 章节继承声明

以下 v2.2 章节**全文继承，仅按需微调**，升版时并入 v3.0 正式文档：

- §6 管理后台（微调：增加 API key 管理与 agent 用量看板）
- §7 部署架构与资源规划（微调：validate/preview/build 端点部署于 ARM 计算节点，阿里云仅入口反代；wff-validator.jar 依赖 JRE 已满足）
- §8 非功能性需求（微调：新增 agent API 指标——validate P95 <2s、preview 3帧 P95 <5s、build P95 <10s）
- §9A 隐形问题清单（历史存档，其中 P1-01/02/05/06/08 等行动项继续有效）
- §10.1-10.6 红线/熔断/图像处理/APK 构建/代码规范/环境配置（红线按 §3.3 修订版为准）
- 附录 A/B 参考资料与合规清单（增量：github.com/google/watchface 仓库主链接）

## 附录 B: 参考资料（增量）

| 资料 | 链接 |
|------|------|
| google/watchface 官方仓库（XSD/validator/评估器/优化器） | https://github.com/google/watchface |
| Watch Face Format 官方文档 | https://developer.android.com/training/wearables/wff |
| lens-studio-mcp（模式参照） | https://github.com/dhravya/lens-studio-mcp |

---

> **文档维护说明:** 本草案批准后合并入 PROJECT_GOALS.md 升版 v3.0 并存档。重大决策与分工确认通过 `edit_memory` 记录到长期记忆。

# 表盘多平台生态调研 · 开源 WFF 案例清单

> 调研日期：2026-09-22 ｜ 调研人：skill 侧 agent
> 目的：回答三个问题——①下一个表盘生成管线做哪个厂商/系统最容易、效果最好、用户最多；②除官方 samples 外，社区有哪些高质量开源 WFF 表盘可借鉴；③给出可直接执行的下一步计划。

---

## 0. 结论速览

| 排序 | 平台 | 管线难度 | 效果上限 | 用户量 | 变现能力 | 综合判定 |
|---|---|---|---|---|---|---|
| **①主推** | **华为 HarmonyOS（Theme Studio + 表盘市场）** | 低-中（模板化图层+配置导出，与 WFF 声明式思路同构） | 高（成熟商业设计师生态，付费表盘） | 中国第一、全球前三 | **强**（付费表盘+设计师分成，头部案例 1300 万 RMB） | ★★★★★ |
| ②备选 | Zepp OS / Amazfit（Watch Face Maker） | **最低**（官方 JSON 格式+文档全+上架通道开放） | 中（受设备屏幕档位限制） | 全球前五（性价比线，估 3-5%） | 弱-中 | ★★★★ |
| ③长线 | Garmin Connect IQ（Monkey C） | 高（生成代码而非声明式 XML） | 很高（运动数据深度整合+付费生态） | 全球 ~8%（高净值运动人群） | 强（IQ Store premium $4.99 起） | ★★★ |
| ✗排除 | 小米 HyperOS | 中（社区逆向 .bin） | 中 | 大 | — | **无官方第三方表盘通道**，依赖 Shizuku 破解安装，商用随时可被封 |
| ✗排除 | Apple watchOS | —（无第三方表盘 API） | — | 最大 | — | 完全封闭，仅 complication 可定制 |
| 已覆盖 | Samsung（WFS） | — | — | — | — | Galaxy Watch4+ 全部 Wear OS，WFS 输出即 WFF → 与现有管线同一目标市场 |

**一句话结论：主推华为鸿蒙表盘管线；若自动化实测受阻，退守 Zepp OS；Garmin 留作代码生成能力升级后的长线目标。**

华为与现管线的同构性超预期：Theme Studio 的核心约束是**功耗校验**（背景白色像素过多/饱和度亮度过高 → 禁止导出），与 WFF「省电纯黑」是同一套设计哲学，知识层迁移成本低。且与 09-18 毕设迁移候选「鸿蒙表盘域」直接咬合（商业与学术双成立）。

---

## 1. 市场盘子（2025 全年，Counterpoint 及二手引用，口径有差异）

| 厂商/系统 | 全球出货份额（2025） | 备注 |
|---|---|---|
| Apple watchOS | ~23%（Counterpoint）/ 34%（另一口径） | 表盘完全封闭，份额参考意义仅在于盘子大小 |
| 华为 HarmonyOS | **9%~17%（口径差异大，取区间）** | 中国市场 HarmonyOS 手表出货份额 2024 估 **61%**；2025 华为是增长引擎之一 |
| 小米 | ~9% | 第三方表盘无官方支持 |
| Samsung（Wear OS） | ~7-8%，2025 出货 **-12%** | 逆风，但存量+Pixel+其他品牌撑起 Wear OS 基本盘 |
| Garmin | ~8% | 高客单价运动人群 |
| Amazfit/Zepp | 估 3-5% | 出货量大、付费能力弱 |

大盘：2025 全球智能表出货 **+4% YoY**（2024 下滑后转正，Apple/Huawei 驱动）。
Wear OS 基本盘：Google 未公布活跃设备数；WFF 是 Google 官方主推方向（2025-08 Android Developers 博客报道 amoledwatchfaces 商业迁移案例）。

---

## 2. 候选平台逐个评估

### 2.1 华为 HarmonyOS — Theme Studio + 表盘市场（主推）

- **工具链**：Theme Studio（官方表盘设计工具，GUI），工程 = 图层 + 配置 + 资源图，导出表盘包后提交「华为主题设计师平台」审核上架。社区教程证明工程文件结构可解析（JSON+图层）。
- **上架通道**：个人可申请「华为主题设计师」入驻（consumer.huawei.com），实名认证制。
- **市场规模**：表盘市场 2019 年随 WATCH GT 2 推出；付费表盘+分成模式成熟。**头部案例：太空液晶表盘收入 1300 万 RMB**（余承东 2021 HDC 披露）；腰部案例：铁路职工唐义文 385 款表盘、单品下载近 20 万次。
- **功耗校验**（官方文档原文精神）：背景避免白色像素过多、饱和度/亮度过高，否则耗电快——**Theme Studio 强制校验，过亮不可导出**。与 WFF 省电约束同构。
- **风险**：①Theme Studio 是 GUI 工具，无 XSD/官方 validator/命令行构建三件套，自动化管线需逆向工程文件格式或半自动导入；②上架走审核，AI 生成内容过审标准未知；③格式无官方公开 schema，知识层要从社区教程+导出包逆向蒸馏（比 WFF 规范蒸馏难一档）。
- **关键文档入口**（搜索引擎仅返回域名，站内定位方式已注明）：
  - Theme Studio 使用指南（表盘主题开发教程）：https://developer.huawei.com （文档中心搜「Theme Studio 使用指南」，含制作实例/颜色自定义/功耗校验）
  - 设计师入驻：https://consumer.huawei.com （搜「设计师如何申请入驻华为主题」）
  - 社区教程：《华为表盘设计简明教程 - 余以为》 https://www.cnblogs.com （站内搜标题，2022，工程结构参考）

### 2.2 Zepp OS / Amazfit — Watch Face Maker（备选：最容易）

- **工具链**：官方 Watch Face Maker（Zepp Health 出品，Web 工具）+ 完整开发者文档；表盘格式 JSON+图片资源，文档化程度高，**自动化管线友好度全场最高**。
- **上架通道**：Watch Face Maker 内完成开发者注册 → 上传预览图 → 提审 → Zepp 应用商店分发。个人开发者全流程开放。
- **效果**：中——设备屏幕档位低于旗舰，但组件模型（指针/组件/自定义颜色）够用。
- **用户量**：全球前五出货，但付费转化弱（性价比用户群）。
- **风险**：变现天花板低；AI 生成表盘的价值主张更偏「量」而非「质」。
- **关键文档入口**：
  - 官方 Create a Watchface 教程：https://docs.zepp.com （开发者文档站，导航 Guides → Watchface）
  - Watch Face Maker 介绍：https://docs.huami.com （老域名文档站，搜「Watch Face Maker」）
  - 第三方编辑器（参考其交互设计）：Watch Face Editor (ZeppOS)（Microsoft Store 应用）、Amazfit Watchface Editor（paolo4c，Google Play）

### 2.3 Garmin Connect IQ — Monkey C（长线）

- **工具链**：CIQ SDK + VS Code Monkey C 扩展；工程 = manifest.xml + resources + Monkey C 源码（类 Java）。**代码生成难度比声明式 XML 高一档**，但有官方模拟器可闭环验证。
- **上架通道**：apps.garmin.com（Connect IQ Store），2024-08 起开放 premium 付费购买（$4.99 起），变现能力强。
- **效果**：很高——运动数据深度整合（心率区间/训练负荷）是表盘差异化能力。
- **用户量**：全球 ~8%，高客单价、付费意愿最强的用户群。
- **风险**：①Monkey C 是新语言栈，LLM 代码生成质量需验证；②watch face data fields 官方限制 5 个；③IQ Store 低质量 spam 泛滥（说明门槛低、能赚钱、竞争激烈）。
- **关键文档入口**：
  - SDK 安装：https://developer.garmin.com/connect-iq/sdk/
  - 商店：https://apps.garmin.com/
  - 开发者论坛：https://forums.garmin.com/developer/connect-iq/
  - 社区入门教程：https://www.ottorinobruni.com （Monkey C + VS Code 入门）

### 2.4 排除项依据

- **小米 HyperOS**：官方无第三方表盘支持；社区方案 = bandbbs「表盘自定义工具」v6.5.1（逆向 .bin 格式 + Shizuku 读小米运动健康日志拿通信密钥直传手表，https://www.bandbbs.cn ）。工具活跃（2026-09 仍在更新）但属灰色地带，商用随时可被封。
- **Apple watchOS**：无第三方表盘 API。.watchface 文件仅被逆向分析过（banjun/WatchFaceDumper，63★）但无法安装自定义表盘。
- **Samsung**：Galaxy Watch4 起全部 Wear OS；官方工具 Watch Face Studio（WFS）本质是 WFF 的可视化编辑器，导出即 WFF APK → 现有管线已覆盖，不算新系统。WFS 入口：https://developer.samsung.com （搜「Watch Face Studio」，多预设单工程等高级用法可参考）。

---

## 3. 推荐路线（结合现有资产与毕设叙事）

```
Phase A（1 周级）: 华为管线 Spike
  1. 装 Theme Studio，手工复刻现有 S1-Refresh 表盘导出包
  2. 解剖导出包/工程文件结构（对照 2022 社区教程）
  3. 判定点：工程文件是否可脚本化生成？
     ├── 可 → 正式立项鸿蒙管线（规范蒸馏方法论复用）
     └── 不可 → 切换 Zepp OS（官方 JSON 格式，自动化无障碍）
Phase B（立项后）: 知识层蒸馏（SKILL-spec-to-skill 方法论复用）
Phase C: 鸿蒙表盘走华为主题设计师入驻 + 上架实测
毕设联动: 「鸿蒙表盘域迁移」候选获商业数据背书（61% 中国份额 + 付费表盘生态）
```

与 WFF 的能力复用清单：规范蒸馏方法论 / 生成-校验-构建管线骨架 / 62 规则+案例库（RAG 语料跨域复用）/ 盲测评估框架。需新建：Theme Studio 工程格式逆向知识层、华为功耗校验规则（映射自现有省电规则）。

---

## 4. 开源 WFF 表盘清单（本次调研核心交付）

> 已逐仓库核验 star/许可证/最后活跃时间（2026-09-22 实测）。
> ⚠️ 许可证合规红线：无 LICENSE 标注 = 默认版权保留（只看结构不抄代码）；GPL = Copyleft（借鉴思路，禁抄实现）。

### A 组：高质量 WFF 表盘（重点借鉴对象）

| # | 仓库 | ★ | 许可 | 最后活跃 | 内容与借鉴点 |
|---|---|---|---|---|---|
| 1 | https://github.com/lukakilic/concentric-watch-face | 64 | **MIT ✅** | 2026-07 | Pixel Watch Concentric 同款复刻（WFF）；环形布局/指针系统/AOD 双态的标杆实现 |
| 2 | https://github.com/amoledwatchfaces/Pixel-Minimal-Watch-Face | 9 | 未标注 ⚠️ | 2026-05 | **商业团队 amoledwatchfaces 的 WFF2 完整 Gradle 工程**（Google 官方博客迁移案例）；极简信息布局+双电池（表+手机 complication 联动）+Preview 组织方式 |
| 3 | https://github.com/PizzaRom/Rush-Hour-Reply | 16 | 未标注 ⚠️ | 2026-03 | Pixel Watch 4 Rush Hour 复刻（WFF）；**流畅动画 + AOD 优化**；仓库即成品 APK——可用我们现有 unzip 流程直接抽 `res/raw/watchface.xml` 学习，无需 license 顾虑之外还省去构建 |
| 4 | https://github.com/SamakaCD/utility-wff | 1 | **MIT ✅** | 2026-08 | Pixel Watch 4 Utility 复刻（WFF）；大号 next-event 日历行实现（WFF4 日历数据源用法） |
| 5 | https://github.com/Praepes/AboutTime-Wear | 2 | **MIT ✅** | 2026-08 | **中式「松弛时间」表盘（WFF4 / WOS6）**，Garmin About Time 启发；中文本地化+非精确时间表达的孤品案例 |
| 6 | https://github.com/hms-douglas/dsh008v2 | 1 | 未标注 ⚠️ | 2026-01 | 日历表盘 v2（WFF/WOS5）；含照片背景配置 |

### B 组：管线与工具链参考

| # | 仓库 | ★ | 许可 | 借鉴点 |
|---|---|---|---|---|
| 7 | https://github.com/Splitties/WffDsl | 21 | **Apache-2.0 ✅** | Kotlin DSL → WFF XML 生成器；「结构化生成 WFF」与我们 builder 同方向，API 设计可参考 |
| 8 | https://github.com/gondwanasoft/wff-boilerplate | 4 | **MIT ✅** | WFF 工程模板（构建配置/资源组织规范化） |
| 9 | https://github.com/android/codelab-watch-face-format | 2 | **Apache-2.0 ✅** | 官方 codelab（2025-12 更新）；官方推荐工程范式 |
| 10 | https://github.com/google/watchface | 71 | **Apache-2.0 ✅** | 官方 XSD 仓库（已入库依赖，2026-09 仍活跃） |
| 11 | https://github.com/android/wear-os-samples | — | Apache-2.0 ✅ | 官方 samples（WatchFaceFormat 目录，已知） |

### C 组：⚠️ Copyleft 警示（只可观摩，禁止抄代码/文件）

| 仓库 | ★ | 许可 | 说明 |
|---|---|---|---|
| https://github.com/amoledwatchfaces/Complications-Suite-Wear-OS | 128 | GPL-3.0 ❌ | complication 套件（交互设计可观摩） |
| https://github.com/gondwanasoft/xml-preprocessor | 4 | GPL-3.0 ❌ | WFF XML 预处理（思路：Python 表达式消重） |
| https://github.com/Eamo5/MinimalWatchFace | 2 | GPL-2.0 ❌ | 极简 WFF 表盘 |
| 旧 Canvas 时代经典（**非 WFF，仅美学灵感**）：ClusterM/wear-os-hex-editor (58★ GPL-3.0)、LayoutXML/Twelveish (52★ GPL-3.0)、lanrat/minimalin (20★ GPL-3.0)、AChep/horlogo (19★ GPL-3.0) | | | 全部 GPL，全部非 WFF |

### D 组：辅助学习资源（非 GitHub）

| 资源 | URL | 价值 |
|---|---|---|
| Google 官方博客：amoledwatchfaces 迁移 WFF 案例 | https://android-developers.googleblog.com/（2025-08-27 「Migrating to the Watch Face Format – Amoledwatchfaces」，站内搜标题） | 商业团队 WFF 迁移的一手经验（定制能力+续航提升） |
| Samsung 开发者博客：Building a Watch Face with WFF | https://developer.samsung.com/（2025-08-14，站内搜标题） | 官方工程转换范式 |
| watch-go.com 「What is WFF?」 | https://watch-go.com | WFF 社区站点（WFS vs 手工打包对比） |
| XDA：WFF vs WFS 兼容性讨论 | https://xdaforums.com/（搜「Watch Face Format vs Watch Face Studio」） | 真机兼容性民间经验 |
| Android 官方 WFF 文档 | https://developer.android.com/training/wearables/wff/watch-face | 权威文档（已知） |

### 使用建议（下次借鉴学习时的姿势）

1. **首选 A 组 1/4/5（MIT）**：可直接 diff 学习 XML 结构，进案例库前先过 wff-validator（SKILL-spec-to-skill 既有纪律）。
2. **Rush-Hour-Reply（#3）**：APK 抽 XML 流程现成——`unzip com.round.rushhour.apk res/raw/watchface.xml`，正好当「官方级动画写法」样本（它有流畅动画+AOD 优化，补我们动画样本不足的短板）。
3. **amoledwatchfaces（#2）**：无 LICENSE，**只读结构不复制代码**；它家的 Preview 图片组织和 complication 联动设计值得看。
4. 入库时逐条记录 star/活跃度快照（本表数据 2026-09-22 实测）。

---

## 5. 下一步建议（按优先级）

1. **华为 Theme Studio Spike（1 周级）**——判定鸿蒙管线可行性，成败标准就一条：工程文件能否脚本化生成。
2. **Rush-Hour-Reply APK 解包**——半小时级，抽取动画 XML 进案例库，补动画样本短板。
3. Zepp OS 文档精读作为 Plan B 预案（不阻塞主线）。
4. 毕设侧：若导师原话拿到且指向「适用面小」，本次调研的鸿蒙商业数据（61% 中国份额/付费生态/1300 万案例）可直接用于迁移论证。

---

*数据来源：Counterpoint（2026-02 全年报告及二手引用）、Garmin 官方新闻室、华为开发者大会披露、GitHub API 实测（2026-09-22）。市场数据存在口径差异，已标注区间。*

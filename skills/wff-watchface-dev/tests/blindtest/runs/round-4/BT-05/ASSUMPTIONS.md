# ASSUMPTIONS — BT-05 商务风格表盘

> 盲测轮次：round-4 / BT-05
> 需求原话："商务风格的表盘：抬腕看的时候全彩显示——时间、日期、步数都要；常亮模式（ambient）下要省电，只保留时间显示，其他内容全部隐藏或变暗，整体风格保持一致。"

## 一、总体设计决策

| 决策项 | 取值 | 理由 |
|--------|------|------|
| 画布尺寸 | 450×450 | 覆盖 Pixel Watch 2 / Galaxy Watch 6+ 等主流 Wear OS 机型；SKILL 中 384 仅限 PW1 |
| WFF 版本 | v1（wff_version: 1） | SKILL 各配方与规则均以 v1 验证为主；minSdk 33（Wear OS 4+） |
| CLOCK_TYPE | DIGITAL | 商务场景要求信息清晰、一目了然；数字表盘对时间/日期/步数布局更可控 |
| 包名 | com.wffforge.executive | 语义化命名，符合 Java 包名规范 |
| 表盘名 | Executive | 商务定位的简洁命名 |
| 素材策略 | 纯矢量/文本，零位图 | 盲测资源约束；唯一位图是构建必需的 preview.png |
| PREVIEW_TIME | 10:08:32 | 手表选择器预览惯例时间 |

## 二、布局坐标（450×450，圆心 225,225）

| 元素 | 定位 | 说明 |
|------|------|------|
| 外环 + 金色断弧 | PartDraw 全屏；Arc centerX/Y=225，width/height=428 | 细环（#ff1E2A3A，t=2）作边框；两段金色断弧（#ffD4AF37，t=4）：顶部 WFF 300°→360°、底部 120°→180°，180° 旋转对称，商务"精工"点缀 |
| 时间 | DigitalClock 内 TimeText x=0 y=120 w=450 h=130，size=100 | Active：SEMI_BOLD #ffF2F5F8（近白）；AMBIENT：THIN #ff7E878F（暗灰） |
| 日期 | PartText x=0 y=262 w=450 h=44，size=30 | 格式 `%s, %s %s` = 周几短名, 月短名 日（如 "TUE, SEP 08"），色 #ffB9C2CE |
| 分隔金线 | Line startX=185 startY=322 endX=265 endY=322，t=2 | 金色细分隔（#ffD4AF37），把"时间/日期"与"步数"分区 |
| 步数标签 | PartText x=0 y=342 w=450 h=26，size=18 | 静态文本 "STEPS"，letterSpacing=6，色 #ff7E8B9B |
| 步数值 | PartText x=0 y=370 w=450 h=56，size=42 | Template `%s` + `[STEP_COUNT]`，SEMI_BOLD #ffF2F5F8 |

颜色取值（8 位 ARGB）：
- 场景背景 `#ff0A0F17`（深海军蓝黑，Active 与 AMBIENT 一致——深底本身省电）
- 主文本近白 `#ffF2F5F8`、次要文本钢灰 `#ffB9C2CE`、弱标签 `#ff7E8B9B`
- 金色强调 `#ffD4AF37`（商务经典金），暗环 `#ff1E2A3A`

## 三、AMBIENT 策略（省电核心）

- **只保留时间**：日期、步数标签、步数值、外环装饰全部通过各自元素上的
  `<Variant mode="AMBIENT" target="alpha" value="0"/>` 在常亮模式下隐藏（比"变暗"
  更省电，符合需求"其他内容全部隐藏或变暗"）。
- **时间变暗**：Ambient 用独立 TimeText（默认 alpha=0 + AMBIENT→255），
  THIN 字重 + 暗灰 #ff7E878F，低对比低功耗，与 Active 同位置同字号，保证
  切换时布局不跳变（"整体风格保持一致"）。
- 背景保持深色不变量（Scene backgroundColor 固定），无动画、无秒针，
  常亮模式刷新负担最小。

## 四、其他假设与说明

1. 步数不用 ComplicationSlot，直接用 `[STEP_COUNT]` 数据源绑定 PartText ——
   数据源在模板内实时刷新，避免 complication 槽位（supportedTypes/BoundingShape/
   displayName 资源引用）带来的真机兼容风险，也符合"步数都要"的诉求。
2. 日期用 `[DAY_OF_WEEK_S]` + `[MONTH_S]` + `[DAY_Z]`，短名英文布局（预览图
   按 2026-09-08 周二渲染 "TUE, SEP 08"；真机随系统语言/时区变化）。
3. 预览图 preview.png（450×450）由 Pillow 按 watchface.xml 设计逐元素镜像绘制
   （PIL 角度映射：PIL = WFF − 90°），时间 10:08、步数静态示例 8642。
4. 时间 format 只用小写 `hh:mm`（R18），12/24 小时制交由 `hourFormat="SYNC_TO_DEVICE"`。
5. 未使用位图素材、未使用 complication、未使用用户自定义配置——全部满足盲测
   资源约束；minSdk 跟随 wff_version: 1 → 33。

## validate 修复轮数

共执行 **1 轮**即全绿：

- 初筛（builder validate，21 规则）第 1 次执行：**20/21 PASS，0 errors，1 warning**
  （warning 为 R13 对 `[STEP_COUNT]` 的误报——expressions.md 明确收录该数据源，
  官方校验也通过，无需修复）。
- 官方校验（wff-validator.jar v5）第 1 次执行：**PASSED**（valid against v5）。
- 无需任何修复轮；两级校验首轮通过后直接进入构建。

## skill 知识层反馈

**实际用到的 skill 文件：**
- `SKILL.md` — 工作循环、validate/build 命令、环境前置、两级校验流程
- `references/pitfalls.md` — R01-R32 全部 MUST/SHOULD 规则（本任务直接命中 R01-R05、
  R08、R09、R18、R19、R23、R24、R26-R29 等）
- `references/recipes.md` — 布局模板（minimal-digital / hybrid）与 AMBIENT 变体写法
- `references/elements.md` — 元素树、PartDraw 形状嵌套方向、Font/颜色规范
- `references/expressions.md` — 数据源清单（[STEP_COUNT] [DAY_OF_WEEK_S] 等）
- `data/wff_inventory_v5.md` + `wff_inventory_v5.json` — 补充查证 Line/Rectangle/
  Arc/Stroke 的精确属性与必填项
- `examples/minimal-digital/watchface.xml` — 双 TimeText 双模式骨架参照

**想找但 skill 里没有/找不到的信息：**
1. **Arc 的 startAngle/endAngle 未进 inventory**：`wff_inventory_v5.json` 中 Arc
   只列了 centerX/centerY/width/height/direction，没有 startAngle/endAngle；
   而 elements.md/recipes.md 使用了这两个属性。同一 skill 内部不一致，我只能以
   官方 validator 结果为准（通过）。建议把 startAngle/endAngle 补进 inventory。
2. **Line 元素属性缺失**：elements.md 只提了 Line 名字，没有 startX/startY/
   endX/endY 定义；要翻 data/wff_inventory_v5.md 才拿到。建议在 elements.md 补全
   五种矢量形状的属性表。
3. **builder 内置数据源清单与 expressions.md 不同步**：R13 初筛把官方规范收录的
   `[STEP_COUNT]` 报为"未知数据源"（warning）。建议 builder 的 R13 名单同步
   expressions.md（或反向：把初筛白名单来源写进 SKILL，避免误导）。
4. **无"预览图与 XML 一致性"指引**：R24 只说"Pillow 自绘兜底"，但没有预览图应
   如何与 watchface.xml 布局/颜色/角度对齐的说明（PIL 弧线角度与 WFF 角度的映射
   关系是 180° 级别易错的坑）。建议补一小节"preview.png 镜像渲染要点"。
5. **装饰层整体隐藏没有现成范式**：recipes 的 AMBIENT 变体都写在单个部件上；
   把 `<Variant mode="AMBIENT">` 直接挂在 PartDraw（含多个形状）上整体隐藏装饰层
   的做法没有示例。经验证官方 XSD 合法、有效，建议补进配方。
6. **商务/风格化布局没有设计配方**：SKILL 只给了"看时间/指针/信息密集"三种功能
   型配方，没有面向视觉风格（商务、极简、运动等）的排版建议（字号层级、留白、
   强调色用法）。本轮字号层级与坐标完全自研，建议沉淀。

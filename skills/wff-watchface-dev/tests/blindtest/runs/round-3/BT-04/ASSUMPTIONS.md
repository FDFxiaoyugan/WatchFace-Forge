# ASSUMPTIONS.md — BT-04

> 盲测任务：表盘显示电池百分比，正常白色、低于 20% 变红提醒充电，其余简洁即可。
> 本文记录全部假设与决策，以及 validate 轮数统计与 skill 知识层反馈。

## 一、需求理解

用户核心诉求是**电池百分比数字的颜色条件变化**：

- 电池 ≥ 20%：数字为白色（`#ffffffff`）
- 电池 < 20%：数字变为红色（`#ffff4444`），以此作为"提醒我充电"的手段
- "其他内容你自己看着办，简洁就好" → 采用极简数字表盘：大字时间 + 日期 + 电池，无多余装饰

## 二、布局与画布（决策）

| 项 | 决策 | 依据 |
|----|------|------|
| 画布尺寸 | 450×450 | skill 常见画布：450 = Pixel Watch 2 / Galaxy Watch 6+（pitfalls R01）；minimal-digital 配方同尺寸 |
| 时钟类型 | DIGITAL | 数字表盘，与需求场景匹配 |
| 时间 | `hh:mm`，y=120, h=120, size=100, BOLD，白色 | minimal-digital 配方位置（y=120），颜色改为纯白 `#ffffffff` |
| 日期 | `MONTH/DAY`，y=258, h=50, size=30，灰色 `#ffAAAAAA` | minimal-digital 配方（y=260）微调，与电池区拉开间距 |
| 电池数字 | y=322, h=64, size=46, BOLD | 核心信息，字号大于日期；两分支（Compare/Default）坐标完全一致，仅颜色不同，避免切换时跳动 |

## 三、颜色取值（决策）

| 元素 | Active 颜色 | AMBIENT 处理 |
|------|------------|--------------|
| 时间（Active） | `#ffffffff` 纯白 | 隐藏，切换至暗色 `#ff888888` THIN 细字（配方惯例） |
| 日期 | `#ffAAAAAA` 灰 | `alpha=0` 隐藏（配方惯例，省电） |
| 电池 ≥20% | `#ffffffff` 纯白（用户要求"白色"） | `alpha=80` 变暗保底（核心信息，AOD 下仍可见） |
| 电池 <20% | `#ffff4444` 红色（用户要求"红色"） | `alpha=80` 变暗保底 |

颜色全部为 8 位 ARGB（R08）。

## 四、条件表达式写法（依据 R32）

"电池低于 20%" 在 WFF 中**没有 `<` 运算符**（XSD `_operatorType` 仅 `>` `>=` `==`，
且 `<` 是 XML 非法字符），必须反转写。依据 pitfalls.md R32 与 recipes.md
"条件渲染（低电量变色）"配方：

```xml
<Condition>
    <Expressions>
        <Expression name="battery_low">20 > [BATTERY_PERCENT]</Expression>
    </Expressions>
    <Compare expression="battery_low">  <!-- 红色分支 -->
        ...
    </Compare>
    <Default>                             <!-- 白色分支 -->
        ...
    </Default>
</Condition>
```

要点（全部来自 skill 知识层）：
- 算式写在 `Expressions/Expression` 的**文本内容**，`Compare/@expression` 是**按 name 引用**（R32）
- 数据源必须用方括号 `[BATTERY_PERCENT]`（R05）
- Compare 首个命中即渲染，否则走 Default（白色兜底）

## 五、文本与数据绑定写法

- 电池文本用 `<Template>%s%%` + `<Parameter expression="[BATTERY_PERCENT]"/>`，
  `%%` 转义百分号（recipes.md 已验证写法），输出如 `85%`
- 日期用 `<Template>%s/%s` + `[MONTH]` `[DAY]`（minimal-digital 配方）
- 时间用 `DigitalClock + TimeText format="hh:mm"`（R09/R18：仅小写，`hourFormat="SYNC_TO_DEVICE"`）

## 六、其他假设

1. **包名/表盘名**：`com.example.batterywatch` / `Battery Watch`（盲测未指定，取直观名；包名合法）
2. **wff_version = 1**（Wear OS 4，minSdk 33）：与 skill 示例一致，兼容面最广
3. **PREVIEW_TIME = 10:08:32**：配方惯例
4. **低电量"提醒"仅通过数字变红实现**：不加 "LOW"/"充电" 等附加文字，保持最简洁，严格贴合用户原话"数字变成红色"
5. **AMBIENT（AOD）**：时间切暗色细字、日期隐藏、电池降 alpha=80——按 R10 SHOULD 规则降亮度，同时保留核心电池信息
6. **preview.png**：R24 要求 build 必须有 preview.png；用 Pillow 自绘 450×450 黑底预览图（10:08 / 9/7 / 85%）
7. **project.yaml 无任何注释**（R23：行内注释会泄漏进 manifest 字符串；整行注释一并清除以求最稳）
8. **环境补齐**：宿主缺 Java 17（仅 11）与 Android SDK，为通过官方校验和构建，下载 OpenJDK 17.0.1 至 `~/tools/jdk-17.0.1`、Android build-tools 34.0.0 + platform-34 至 `~/tools/android-sdk`（构建时设 `ANDROID_HOME`）。未修改 skill 目录任何内容

## 七、构建与验证结果

| 步骤 | 结果 |
|------|------|
| 初筛 validate（20 规则） | 21/21 PASS，0 error 0 warning（首次即过） |
| 官方 XSD 校验 `wff-validator.jar 5` | `✅ PASSED ... valid against watch face format version #5`（首次即过；首次调用因宿主仅 Java 11 报 UnsupportedClassVersionError，补装 JDK 17 后通过） |
| build | APK 打包成功，resources.arsc STORED + 对齐，签名 Verified: PASS (v1+v2+v3) |
| 独立复核（apksigner verify / zip 解包） | `Verifies`；res/xml/watch_face_info.xml 为二进制 AXML（magic 03000800）；res/raw/watchface.xml 保留原始文本且含 battery_low 表达式；无独立 res/values/ 目录 |

产物：`watchface.xml`、`project.yaml`、`preview.png`、`batterywatch-watchface.apk`

---

## validate 修复轮数

从首次 validate 到全绿共 **1 轮**（XML 零修复）：

- 初筛（20 规则）：执行 **1 次**，21/21 全绿（0 errors 0 warnings）。
- 官方 XSD 校验：**调用 2 次**——第 1 次因宿主环境缺 Java 17 报
  `UnsupportedClassVersionError`（环境失败，非 XML 问题），补装 JDK 17 后
  第 2 次调用即 `PASSED`。同一 XML 首次通过，无任何 XML 修复轮。
- 结论：**1 轮**（含两级；环境补齐不计入 XML 修复轮数）。

---

## skill 知识层反馈

### 实际用到的 skill 文件

- `SKILL.md` — 工作流（Quick Start、Work Loop、Build Constraints、Data Sources）
- `references/pitfalls.md` — R01/R05/R08/R09/R18/R22/R23/R24/R26-R29/R32 规则
- `references/expressions.md` — 数据源表、运算符、低电量变红配方
- `references/recipes.md` — 配方 1（minimal-digital）+ 条件渲染（低电量变色）配方
- `references/elements.md` — PartText/Font/Template/Condition/Compare/Default/Variant 结构
- `examples/minimal-digital/watchface.xml` — 可直接复用的已验证骨架

### 想找但 skill 里没有/找不到的信息

1. **Android SDK 的精确查找路径与兜底顺序**：SKILL.md Environment 只写了
   `ANDROID_HOME: /home/z/my-project/tools/android-sdk`；实际 build 报错暴露了
   builder 还会兜底查 `/opt/android-sdk/build-tools/34.0.0/apksigner` 并支持
   `APKSIGNER` 环境变量。知识层未说明"缺 SDK 时 agent 应如何补齐/最小需要哪些组件"。
2. **Java 版本缺失的应对**：SKILL.md 说需要 Java 17+，但未说明宿主只有旧版 Java
   时该从何处获取（下载 tarball 到用户目录）——环境前置章节缺"自查与补齐清单"。
3. **build-tools zip 解压结构**：`build-tools_r34-linux.zip` 解压后顶层目录是
   内部代号 `android-14`（需改名 `34.0.0`）、`platform-34` 的正确 zip 文件名是
   `platform-34-ext7_r02.zip`（`platform-34_r02.zip` 404）——这类环境细节知识层完全空白，
   盲测 agent 需要反复试错（我各探测了一次）。
4. **aapt2 不可用时的兜底行为**：构建日志出现 `aapt2 unavailable: using verified
   precompiled ARM template`，知识层未说明该兜底逻辑的存在与适用条件（x86_64 宿主
   上补装 aapt2 后实际走的是真 aapt2，模板路径未被使用）。
5. **AMBIENT 下 Condition 分支元素的行为**（AOD 中条件求值是否继续、Variant alpha
   与 Compare/Default 分支的组合语义）：knowledge layer 无直接说明，我按
   "条件始终求值 + alpha 仅降亮度"的保守假设处理（见上文第五节）。

# ASSUMPTIONS.md — BT-08 表盘开发假设与决策记录

## 项目概述

- **需求**：可自定义的 Wear OS 表盘——时钟样式切换（细/粗）、"显示秒"开关、左右各一个 complication 槽、主题颜色 2-3 个选项，长按表盘进编辑器可改。
- **交付物**：`watchface.xml`（WFF v1）+ `project.yaml` + 签名 APK（`bt08-watchface.apk`）+ 本文件。
- **知识来源**：仅 `skills/wff-watchface-dev/` 下 SKILL.md 及其引用文件 + 任务 prompt（未读取任何被禁目录）。

---

## 一、需求 → 实现映射

| 用户需求 | 实现 |
|---|---|
| 时钟样式切换（≥2 种：细字体/粗字体） | `ListConfiguration id="clockStyle"`：选项 0=THIN 细体、1=BOLD 粗体（渲染版双 TimeText，active 主题色 / AMBIENT 灰白） |
| 底部"显示秒"开关 | `BooleanConfiguration id="showSeconds"`（默认 FALSE 省电）；渲染版只放 TRUE 选项，内含 `TimeText format="ss"`，关闭=不渲染（R37 官方 showHr 模式） |
| 左右各一个 complication 槽 | `ComplicationSlot slotId="0"`（左，默认 HEART_RATE 心率）+ `slotId="1"`（右，默认 STEP_COUNT 步数），`supportedTypes="SHORT_TEXT EMPTY"`，`isCustomizable="TRUE"` |
| 主题颜色 2-3 个选项 | `ColorConfiguration id="themeColor"`：3 个 ColorOption（Cyan / Gold / Red），元素颜色绑定 `[CONFIGURATION.themeColor.0]` |
| 长按表盘进编辑页可改 | `res/xml/watch_face_info.xml` 含 `<Editable value="true"/>`（R33）+ 容器版 UserConfigurations 提供选项内容 |

---

## 二、假设与决策明细

### 1. 画布尺寸
- **450×450**（Pixel Watch 2 / Galaxy Watch 6+ 世代，skill 推荐现代尺寸），`wff_version: 1`（Wear OS 4+，minSdk 33，兼容面最广）。

### 2. 布局坐标（450×450，圆屏安全区 y≈25..425，内切圆中心 (225,225) 半径 225）
| 元素 | 坐标 | 说明 |
|---|---|---|
| 日期（周几, 月 日） | PartText (105,52,240,36)，size 26 灰 #ff9aa5b1 | 模板 `%s, %s %s` = [DAY_OF_WEEK_S][MONTH_S][DAY]，AMBIENT 隐藏 |
| 主时间 hh:mm | TimeText (0,150,450,115)，size 92，hourFormat=SYNC_TO_DEVICE | 12/24 制跟随设备；THIN/BOLD 由 clockStyle 切换；AMBIENT 版灰白与 active 坐标完全重合 |
| 秒 ss | TimeText (0,315,450,55)，size 40 主题色 | 仅 showSeconds=TRUE 渲染；AMBIENT 隐藏（AOD 不刷秒，省电） |
| 左槽 | ComplicationSlot (65,290,90,90)，slotId=0 | 圆心 (110,335)，距画布中心 ≈174px < 225，圆内安全 |
| 右槽 | ComplicationSlot (295,290,90,90)，slotId=1 | 圆心 (340,335)，距画布中心 ≈223px < 225，圆内安全 |
| 槽位底板 | Scene 层 PartDraw (65,290/295,290,90,90) 椭圆描边 | 放 slot 外部恒显示（R26 推荐），不随 provider 数据消失；颜色随主题；AMBIENT alpha=40 |

### 3. 颜色取值
- 背景 `#ff0a0d12`（深蓝黑，商务风基调）
- 主题色三选：Cyan `#ff00E5FF` / Gold `#ffFFC940` / Red `#ffFF5555`（对比度充足的经典三色）
- 日期灰 `#ff9aa5b1`；AMBIENT 时间灰白 `#ff9aa5b1`；EMPTY 占位灰 `#ff7E93A8`
- 颜色全部 8 位 ARGB（R08）

### 4. 配置项结构选择
- 容器版（UserConfigurations，Scene 前）只做编辑器元数据：ColorConfiguration / ListConfiguration / BooleanConfiguration，`displayName` 一律**裸资源名**（R30），对应字符串放 `res/values/strings.xml`（builder 合并进 arsc）。
- 渲染版（Scene 内）只写 id，与容器版 id 一一对应（R37）。
- `BooleanConfiguration` 渲染版**只放 TRUE**（FALSE=不渲染），默认值 FALSE——贴合用户"平时关掉省电"习惯。
- ListOption 不设 `icon`（约束：不使用位图素材，风格切换全矢量/文本实现；icon 非必填）。

### 5. Complication 类型选择
- `supportedTypes="SHORT_TEXT EMPTY"`：SHORT_TEXT 是系统 provider 兼容面最广的类型（elements.md 保守策略），EMPTY 做无数据占位（"--"）。
- 默认 provider：左 HEART_RATE（用户点名心率）、右 STEP_COUNT（"其他小工具"）。
- `BoundingOval` 用**局部坐标**（0,0 起，尺寸=slot 尺寸）（R28）；slotId 从 0 起（R38）。
- 槽内文本绑定 `[COMPLICATION.TEXT]`（R26：Complication 内必须有渲染内容），`tintColor` 绑定主题色随用户切换。
- 槽位圆框底板移到 Scene 层独立 PartDraw：保证 EMPTY/无数据时边框仍显示（R26 建议），同时消除初版"底板画在 SHORT_TEXT 分支内、EMPTY 时消失"的缺陷。

### 6. AMBIENT（AOD）策略
- 主时间：双 TimeText 交换（active 255→0 / ambient 0→255），ambient 版灰白细字，坐标与 active 完全重合（风格一致）。
- 日期、秒：AMBIENT 整体隐藏（省电）。
- 槽位：整体 alpha 40（保留弱可见边框）。
- CLOCK_TYPE=DIGITAL，PREVIEW_TIME=10:08:32（预览秒数 32 与秒显示功能呼应）。

### 7. 其他
- 包名 `com.wfftest.bt08`、版本 1.0、表盘名 "Forge Play"（自定，无冲突风险）。
- project.yaml 无任何注释（R23）。
- 预览图 preview.png 由 Pillow 自绘（450×450），布局/颜色/文本与 XML 对齐（含模拟 complication 数据 72/8450 展示开启态效果；实际默认 showSeconds=FALSE）。

---

## 三、验证结果

| 验证项 | 结果 |
|---|---|
| builder validate 初筛（27 规则） | 26/27 PASSED，0 errors，1 warning |
| 官方 XSD v5 校验（wff-validator.jar） | **PASSED**（两次构建均通过） |
| APK 构建 | 成功，25,155 bytes |
| 签名 | apksigner verify PASS（v1+v2+v3，test.keystore 开发密钥） |
| APK 内部独立核验 | watch_face_info.xml 为二进制 AXML（头 0x03000800）含 Editable+Preview；res/raw/watchface.xml 为原始 XML 且与源文件逐字节一致；resources.arsc STORED |

**剩余 1 个 WARN（R34）为检查器误报**：R34 圆屏裁剪检查把 Complication 内部**局部坐标** PartText (0,0,90,90) 当作全局坐标计算四角距中心，得 318px > 225px。实际该元素位于 slot 内，slot 全局坐标 (65,290)/(295,290)，四角距圆心均 < 225，真机无裁剪风险。官方 XSD 校验通过，且该 WARN 无法通过合法 XML 写法消除（Complication 内部必须用 0,0 起始的局部坐标，R28），故保留并记录。

---

## validate 修复轮数

- **27 规则初筛**：共执行 **2** 次。
  - 第 1 次：25/27 PASSED，2 WARN —— R34（局部坐标误报）+ R33（项目未自带 watch_face_info.xml）。修复：将槽位底板由 Complication 内部移到 Scene 层独立 PartDraw（顺带消除初版"EMPTY 时边框消失"缺陷）；项目自带含 `<Editable value="true"/>` 的 `res/xml/watch_face_info.xml`。
  - 第 2 次：26/27 PASSED，0 errors，仅剩 R34 误报（无法消除，见上）。
- **官方 XSD 校验**：共执行 **2** 次，均 PASSED（初版与终版 watchface.xml 各 1 次）。
- 两级合计 validate 执行 **4** 次。未出现 error 级失败，无需规则修复轮。

---

## skill 知识层反馈

### 实际用到的 skill 文件
- `SKILL.md`（工作流、环境前置、速记规则）
- `references/pitfalls.md`（R01-R40 全部规则，重点 R26/R28/R30/R33/R37/R38/R39）
- `references/recipes.md`（配方 4 组件包表盘骨架——List/Boolean/双槽位/Color 全链路）
- `references/elements.md`（UserConfigurations/Complication 属性、局部坐标、数据源）
- `references/expressions.md`（[COMPLICATION.TEXT]、[CONFIGURATION.x.0]、格式）
- `examples/minimal-digital/`（watchface.xml 参考双 TimeText AMBIENT 模式）

### 想找但 skill 里没有/找不到的信息（对 skill 改进）
1. **BoundingOval 坐标属性矛盾**：`elements.md` 写 `<BoundingOval centerX centerY width height/>`，`recipes.md` 配方 4 用 `<BoundingOval x="0" y="0" width height/>`（标称 v5 PASSED）。两者冲突，最终按配方 4 写法并通过官方 XSD 校验。建议知识层统一（XSD 实证 x/y 合法，elements.md 该行需更正或注明两种写法）。
2. **Windows 宿主构建适配缺失**：SKILL.md 环境前置只覆盖 Linux（`/opt/android-sdk`、aapt2 无扩展名路径）。Windows 上 builder 探测不到 `aapt2`/`apksigner`（需要 `.exe`/`.bat` 后缀），报错信息提示可通过 `AAPT2`/`APKSIGNER` 环境变量指定完整路径——该平台适配信息 skill 未记载，首轮构建因此失败一次（通过报错信息自愈）。建议环境自查清单增加 Windows 分支。
3. **R34 对局部坐标的误报**：R34 检查器不识别 Complication 内部的局部坐标系，把 (0,0,90,90) 当全局坐标导致必然 WARN。建议 R34 实现跳过 Complication 子元素，或在文档中注明"Complication 内部局部坐标元素的 R34 报错为误报，可忽略"。
4. **icon 属性的资源依赖**：配方 4 的 ListOption 写了 `icon="style_thin_icon"`，但约束要求不使用位图素材，且文档未说明 icon 缺失时的构建/编辑器行为（本次选择省略 icon，构建与校验均通过，编辑器用文本标签显示选项）。

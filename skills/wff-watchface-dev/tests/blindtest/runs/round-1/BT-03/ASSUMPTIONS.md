# ASSUMPTIONS.md — BT-03 / Velocity Sport

> 盲测交付记录：所有设计假设、决策依据、validate 轮数、skill 知识层反馈。

## 需求解读

用户原话："运动风格的表盘：数字时间要大，另外加一个数据格子显示心率，用户可以自己换数据源的那种（就是 complication 插槽）。背景做个深色渐变，看起来有速度感。"

拆解为 4 个可执行需求：
1. 大数字时间（Active 亮色 + Ambient 省电双模式）
2. 心率数据格 = Complication 插槽，默认 provider HEART_RATE，`isCustomizable="TRUE"` 让用户长按换数据源
3. 深色渐变背景 = LinearGradient 对角渐变
4. 速度感 = 角落斜向拖尾光痕（streak），方向统一、透明度渐变

## 画布与项目

| 项 | 取值 | 依据 |
|---|---|---|
| 画布 | 450×450 | pitfalls R01：Pixel Watch 2 / Galaxy Watch 6+ 主流运动表尺寸；450 比 384 更适配"大时间" |
| wff_version | 1（minSdk 33, Wear OS 4+） | recipes project.yaml 配方；未用 v2+ 特性，取最大兼容 |
| package | `com.example.velocitysport` | 沿用 skill 示例命名惯例 `com.example.*` |
| 名称 | Velocity Sport | 运动风格命名（速度主题，与视觉语言一致） |
| keystore | skill 自带测试签名（alias wfftest） | SKILL.md Environment 节 |

## 设计决策

### 颜色
- 渐变：`#ff03050B → #ff071629 → #ff0E2C55`（左上→右下对角）。近黑深蓝→藏青→钢蓝，右下渐亮制造"向前冲"的纵深；三档都在深色区间，符合"深色渐变"。
- 主强调色：电光青 `#ff00E5FF`（时间、光痕、插槽 tint、tile 描边）。运动/科技感惯例色，与深蓝底对比强。
- 次强调色：荧光黄绿 `#ffC8FF2E`（两条 streak 点缀）。运动品牌常见 volt 色，少量使用避免噪。
- 文本：日期 `#ffB8C4D4`、电池 `#ff7E93A8`（低饱和冷灰，不与主信息抢焦点）。

### 字体
- 全部 `family="SYNC_TO_DEVICE"`（R07：无需自带字体文件，设备默认无衬线恰好是运动风）。
- 时间 `size=130 BOLD`——按字宽 ~0.55em 估算 "hh:mm" ≈ 320px，450 画布内可容纳的最大舒适字号；Active 用 `#ff00E5FF`，Ambient 用 `THIN #ff8A9BA8`（细笔画少点亮像素，AOD 省电防烧屏）。
- 日期 26px、电池 22px。

### 布局坐标（450×450，圆形屏安全区校验过）
| 元素 | 区域 | 说明 |
|---|---|---|
| 电池 BAT %s%% | y=58..90，居中 | 顶部小字，模板 `BAT %s%%` + `[BATTERY_PERCENT]` |
| 大时间 | y=140..270，居中 | 视觉中心略偏上，为底部数据格留空间 |
| 日期 %s %s/%s | y=284..318 | `[DAY_OF_WEEK_S] [MONTH] [DAY]` → "WED 8/27" |
| 数据格 | x=140..310, y=328..416 | 170×88 圆角矩形（r=14），半透明填充 `#80102A4C` + 2px 青色描边 `#B300E5FF`（70% 不透明度）。y=416 处圆屏半宽 ≈120px，tile 右缘 310 < 345，在安全区内 |
| 速度光痕 ×7 | 左上×3 青、右上×1 荧光绿、左下×1 荧光绿、右下×2 青 | 全部落在时间/日期/tile 之外的角落空区；每条两端点到圆心距离 ≤ ~217px，不被圆屏裁掉 |

### Complication 插槽（核心需求）
- `slotId="0" supportedTypes="SHORT_TEXT"`：HEART_RATE 系统 provider 的 SHORT_TEXT 是跨版本最稳妥的类型（RANGED_VALUE 兼容矩阵 skill 里查不到，未敢用，见反馈 #11）。
- `DefaultProviderPolicy defaultSystemProvider="HEART_RATE" defaultSystemProviderType="SHORT_TEXT"`：默认显示心率（"显示心率"需求）。
- `isCustomizable="TRUE"`（注意 booleanType 枚举是大写 TRUE，不是 true）：用户可在手表上长按表盘更换该插槽数据源（"用户可以自己换数据源"需求）。
- `tintColor="#ff00E5FF"`：系统渲染的心率图标/文字统一染成主题青色。
- `BoundingRoundBox x=140 y=328 w=170 h=88 cornerRadius=14 outlinePadding=2`：与 tile 底板几何一致。
- 渲染：不写自定义 `<Complication>` 内的 Group，交给系统默认渲染（图标+数值+短标题），保证换任何 provider 都有合理显示。

### 速度光痕实现
- 每条 = `<Line>` + `<Stroke>`（含厚度、cap 默认）+ `<LinearGradient>` 沿线两端做透明度渐变（如 `#0000E5FF → #ff00E5FF`）：起点透明、角端最亮，形成"拖尾"。
- 方向统一沿副对角线（左下→右上），与主对角渐变交叉，制造速度张力。
- 亮度分级：主拖尾 t=5、副 t=3、细点缀 t=2~2.5。

### Ambient（常显）模式
- 背景渐变 alpha→30；全部光痕/底板/日期/电池 alpha→0；时间切换为暗灰细体；Complication alpha→30（沿用 recipes 配方 3 的模式）。保证 AOD 低功耗、低烧屏风险。

### preview.png
- 本地模式没有预览渲染器（CHANGELOG 已知限制），用 Pillow 手绘 384×384 近似帧：按 384/450 等比缩放全部元素，显示 PREVIEW_TIME 10:08:32、日期 THU 8/27、BAT 87%、♥72 BPM，圆形蒙版。字体用环境 DejaVu Sans（近似 SYNC_TO_DEVICE 效果）。

### 时间格式
- `format="hh:mm"`（小写）+ `hourFormat="SYNC_TO_DEVICE"`。注意：skill 示例/skeleton 用的 `HH:mm` 过不了官方 v5 XSD 校验（timeFormatType pattern 只收小写 h/m/s），真机可能宽容但规范不允许，详见反馈 #2。

## validate 修复轮数

**共 4 轮**（`wff_builder.py validate` 16 规则 ×4 + 官方 `wff-validator.jar` v5 XSD ×4；修复 3 处，第 4 轮双验证全绿）：

| 轮 | wff_builder 16 规则 | 官方 XSD v5 | 修复内容 |
|---|---|---|---|
| 1 | 16/16 PASS | ❌ colorListType 不接受逗号分隔 | —（首次发现 16 规则查不出 XSD 错误） |
| 2 | 16/16 PASS | ❌ timeFormatType 拒绝 `HH:mm` | 渐变 colors/positions 逗号 → 空格分隔 |
| 3 | 16/16 PASS | ❌ BoundingShape 是抽象元素不可实例化 | `HH:mm` → `hh:mm` |
| 4 | 16/16 PASS | ✅ **PASSED** | `<BoundingShape><BoundingBox/></BoundingShape>` → 直接写 `<BoundingRoundBox .../>`（substitution group 成员，几何属性必填） |

附注（非 validate 轮）：build 阶段两次环境问题——缺 preview.png（init 不生成，需自备）、缺 apksigner（按 SKILL.md 环境节路径 `/home/z/my-project/tools/android-sdk` 下载安装 build-tools 34.0.0 解决）。

## skill 知识层反馈

### 实际用到的文件
- `SKILL.md`：工作流、环境（keystore/ANDROID_HOME）、数据源速查表
- `references/pitfalls.md`：16 条 MUST 规则（R01 尺寸、R05 方括号、R07 字体、R09 模板不自动刷新等）、官方验证器命令、XSD 规范位置
- `references/elements.md`：元素树结构、PartDraw 形状/样式概览
- `references/expressions.md`：`[BATTERY_PERCENT]`、`[DAY_OF_WEEK_S]` 等数据源
- `references/recipes.md`：配方 3（Complication 布局、Ambient alpha 模式）、project.yaml 字段
- `examples/minimal-digital/`：已验证基线（双 TimeText Active/Ambient 切换、Template/Parameter 写法）
- `data/wff_inventory_v5.json`：LinearGradient/Fill/Stroke/ComplicationSlot/DefaultProviderPolicy 的属性与 cardinality、booleanType=TRUE/FALSE 枚举、defaultProviderType 枚举（确认含 HEART_RATE）
- `CHANGELOG.md`：已知限制（本地无预览渲染器、配方 2/3 未验证——这个警告很有用，让我对配方 3 的写法保持怀疑并回查了 inventory）

### 想找但 skill 里没有 / 与规范冲突的信息（按严重度排序）

1. **【高】Stroke/Fill 与形状的嵌套方向，文档写反了**：elements.md 和 recipes.md 全部示例都是 `<Stroke><Arc/></Stroke>`（样式包形状），但 XSD 实际是 `<Arc><Stroke/></Arc>`（形状包样式，Line/Rectangle/RoundRectangle/Circle 同理）。照抄 skill 文档的写法过不了官方校验。我是靠 inventory JSON 的 children cardinality 反推 + 官方验证器实测才确定的。
2. **【高】`HH:mm` 时间格式非法**：examples/minimal-digital（标注"真机验证通过"）、wff_builder init 生成的 skeleton、recipes 配方 1 全都用 `format="HH:mm"`，但 XSD v5 timeFormatType pattern 只接受小写 `h/m/s` 组合（`hh:mm` 合法）。真机宽容、规范不容，知识层自相矛盾，盲测 agent 无所适从。
3. **【高】wff_builder validate 的 16 规则查不出任何 XSD 级错误**：本轮 3 个真实错误全部 16/16 通过。skill 只在 pitfalls.md 顺带提了一句官方验证器命令，SKILL.md 工作流里没有把它列为必跑步骤。建议 Quick Start 改成 "validate（16 规则）→ 官方 XSD 验证 → build" 三步，否则盲测 agent 会带着非法 XML 直接出包。
4. **【中】列表分隔符无文档**：colorListType/floatListType 是空格分隔（XSD `xs:list`），recipes 里没有任何一个渐变实例展示列表写法，我第一版猜了逗号直接翻车。elements.md 提到 LinearGradient 属性但没给 colors/positions 的格式示例。
5. **【中】BoundingShape 抽象 + substitution group 无文档**：inventory 只列出它是 ComplicationSlot 必填子元素，没说明它不可直接实例化、需用 BoundingBox/BoundingRoundBox/BoundingOval/BoundingArc 之一替换、且这些成员自带必填的 x/y/width/height。recipes 配方 3 的 ComplicationSlot 干脆没写 bounding 元素（照抄会缺必填项）。
6. **【中】配方 3 的 Complication 属性集与 XSD 不符**：`defaultProvider/primaryDataStyle/primaryDataSource/fallbackBehavior` 这些属性在 XSD 的 Complication 元素上不存在（Complication 只有 `@type`），默认数据源语义属于 DefaultProviderPolicy。配方 3 本身过不了官方校验。
7. **【低】booleanType 枚举 TRUE/FALSE**：只在 inventory JSON 里能查到，文档/示例均未出现 `isCustomizable` 用法，大小写写错（true/false）不会得到任何提示。
8. **【低】init 不生成 preview.png，但 build 硬性要求它**：CHANGELOG 承认本地预览渲染器缺失，但没有给出"agent 如何自产 preview.png"的指引（尺寸要求 384×384 只出现在 init 的输出文本里）。建议 skill 提供一个 Pillow 预览生成配方或让 build 可选跳过 preview。
9. **【低】系统 provider 与 complication 类型的兼容矩阵缺失**：HEART_RATE 能供 SHORT_TEXT 还是 RANGED_VALUE？inventory 只有枚举值列表，没有 provider×type 兼容表，只能保守选 SHORT_TEXT。
10. **【低】SKILL.md 环境节的 ANDROID_HOME 路径在本机不存在**：新环境需自行下载 build-tools 34.0.0（apksigner/aapt2），skill 未给出获取方式；另外 build 日志显示 project.yaml 行内注释会被解析进 manifest 字符串（`wff_version: 1  # 注释` 泄漏），建议在 SKILL.md 提醒"project.yaml 不要写行内注释"。
11. **【低】TimeText 的 `align` 属性在 inventory 里缺失**（所有示例都在用、XSD 有），再次说明 inventory 解析器会丢继承属性——inventory 不能盲信"属性不存在"，只能信"存在的属性"。这一条同样适用于 DigitalClock/ComplicationSlot 的 x/y/width/height。

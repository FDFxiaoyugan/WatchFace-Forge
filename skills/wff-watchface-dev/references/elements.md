# WFF 元素参考

> WFF v5 完整元素树，从 google/watchface 官方 XSD 规范蒸馏。
> 完整属性/文档见 `data/wff_inventory_v5.json`（90 元素，29 枚举，99 XSD 文件）。

---

## 文档结构

```
<WatchFace>                    根元素
├── <Metadata>×N               表盘元信息（CLOCK_TYPE, PREVIEW_TIME, ...）
├── <UserConfigurations>       用户自定义配置（可选）
├── <BitmapFonts>              位图字体定义（可选）
└── <Scene>                    场景树（所有可见内容）
    ├── <Group>×N              分组（active/ambient 变体）
    │   └── <Part>×N          部件
    │       ├── <PartImage>    图片
    │       ├── <PartText>     文本
    │       ├── <PartDraw>     矢量绘制
    │       ├── <AnalogClock>  模拟时钟
    │       └── <DigitalClock> 数字时钟
    └── <ComplicationSlot>×N  Complication 插槽
```

---

## 根元素

### `<WatchFace>`

| 属性 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `width` | int | ✅ | 画布宽度 |
| `height` | int | ✅ | 画布高度 |
| `clipShape` | enum | v2+ | `NONE`/`CIRCLE`/`RECTANGLE`（v1 不可用） |

常见尺寸：384（PW1）、450（PW2/GW6+）

### `<Metadata>`

| 属性 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `key` | string | ✅ | 键名 |
| `value` | string | ✅ | 值 |

必填 Metadata：`CLOCK_TYPE`（`DIGITAL`/`ANALOG`）、`PREVIEW_TIME`（如 `10:08:32`）

---

## 场景

### `<Scene>`

| 属性 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `backgroundColor` | color | ⚠️ | 背景色 `#ffRRGGBB` |

Scene 是所有可见元素的容器，直接子元素为 `Group` 和 `ComplicationSlot`

### `<Group>`

| 属性 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | ✅ | 组名 |
| `x` `y` | int | | 位置偏移 |
| `width` `height` | int | | 尺寸 |
| `drawMode` | enum | | `ACTIVE`/`AMBIENT`（默认 ACTIVE） |

Group 用于组织部件并应用变体。典型模式：一个 ACTIVE Group + 一个 AMBIENT Group

---

## 部件

### `<PartText>` — 文本

```xml
<PartText x="0" y="260" width="450" height="50">
    <Text align="CENTER">
        <Font family="SYNC_TO_DEVICE" size="32" weight="NORMAL" color="#ffAAAAAA">
            <Template>%s/%s
                <Parameter expression="[MONTH]"/>
                <Parameter expression="[DAY]"/>
            </Template>
        </Font>
    </Text>
</PartText>
```

| 子元素 | 说明 |
|--------|------|
| `<Text>` | 静态/模板文本 |
| `<Text.`/`Text.DECIMAL`> | 十进制数 |
| `<Text.`/`Text.CURRENT_DATE`> | 当前日期 |
| `<Font>` | 字体定义 |
| `<Template>` | 模板字符串（`%s` 占位 + `<Parameter>`） |
| `<Variant>` | 变体（mode=AMBIENT 等） |
| `<Gyro>` | 陀螺仪响应 |
| `<Transform>` | 动态变换 |
| `<Condition>` | 条件渲染 |

### `<PartImage>` — 图片

```xml
<PartImage x="0" y="0" width="450" height="450">
    <Image resource="background"/>
    <Variant mode="AMBIENT" target="alpha" value="0"/>
</PartImage>
```

| 子元素 | 说明 |
|--------|------|
| `<Image>` | 图片引用（仅 `resource` 属性） |
| `<ImageFilters>` | 滤镜容器（内含 `<HsbFilter>`） |
| `<Variant>` | 变体 |
| `<Gyro>` | 陀螺仪 |
| `<Transform>` | 动态变换 |
| `<Condition>` | 条件渲染 |

### `<PartDraw>` — 矢量绘制

> ⚠️ **嵌套方向（易错）**：形状在外、样式在内 —— `<Arc><Stroke/></Arc>`，
> 不是 `<Stroke><Arc/></Stroke>`。Stroke/Fill 是形状的子元素（XSD 权威结构）。

```xml
<PartDraw x="0" y="0" width="450" height="450">
    <Arc centerX="225" centerY="225" width="400" height="400"
         direction="CLOCKWISE" startAngle="0" endAngle="180">
        <Stroke color="#ff00F5FF" thickness="4">
            <LinearGradient startX="0" startY="0" endX="450" endY="450"
                            colors="#ff00E5FF #ff071629"
                            positions="0.0 1.0"/>
        </Stroke>
    </Arc>
    <Ellipse x="25" y="25" width="400" height="400">
        <Fill color="#ff00F5FF"/>
    </Ellipse>
</PartDraw>
```

**Arc 角度**：`startAngle` + `endAngle`（必填，度，0 = 12 点方向，顺时针为正）。
**没有 `sweepAngle` 属性**；且角度只支持静态值——动态进度环用
ComplicationSlot `type="RANGED_VALUE"`（系统渲染），不要试图给 Arc 写表达式角度。

> ⚠️ **Arc 角度语义速查（R36，ArcLab 像素级实证 2026-09-09）**：
> 0°=12点、**顺时针**为正、**负角度合法**。
> 上半拱 `-90→90`（开口朝下）；`180→360` 是左半弧 C 形（开口朝右，不是上半拱）；
> 官方电量环 `-150→150` 缺口朝下。`cap="ROUND"` 官方 sample 在用。
>
> ⚠️ **Arc 几何是 PartDraw 局部坐标（R35，斜线悬案实证 2026-09-10）**：
> centerX/centerY 相对**父容器**（0,0=容器左上角），椭圆 bbox 溢出容器的弧段
> 被直接裁剪。居中写法：`centerX = 容器width/2, centerY = 容器height/2`。

**形状**（PartDraw 直接子元素）：`<Arc>` `<Ellipse>` `<Line>` `<Rectangle>` `<RoundRectangle>`
> ⚠️ **没有 `<Circle>` 和 `<Path>`**——画圆用 Ellipse（width=height），x/y/width/height 定包围盒。

五种形状的属性（粗体=必填；`**` 标注来自 XSD attributeGroup，与 inventory v5 同步）：

| 形状 | 属性 |
|------|------|
| `<Arc>` | **centerX** **centerY** **width** **height** **startAngle** **endAngle**（角度制，0=12点方向）, direction=`CLOCKWISE`/`COUNTER_CLOCKWISE`（默认 CW） |
| `<Ellipse>` | **x** **y** **width** **height**（x/y=包围盒左上角） |
| `<Line>` | **startX** **startY** **endX** **endY**（线段两端坐标） |
| `<Rectangle>` | **x** **y** **width** **height** |
| `<RoundRectangle>` | **x** **y** **width** **height** **cornerRadiusX** **cornerRadiusY**（R27：无单一 cornerRadius） |

> Arc 的 startAngle/endAngle 也可用表达式（angleExpressionAttributeGroupRequired，
> 如动态进度环 `endAngle="[SECOND]*6"`——但真机验证仅静态值可靠，动态环建议
> ComplicationSlot type="RANGED_VALUE"）。

**Variant 可整体挂在 PartDraw 上**：装饰层（多个形状）需在 AMBIENT 一次隐藏时，
不必逐形状写 Variant，直接挂父 PartDraw（官方 XSD 合法、BT-05 真机验证有效）：

```xml
<PartDraw x="0" y="0" width="450" height="450">
    <Variant mode="AMBIENT" target="alpha" value="0"/>  <!-- 整层隐藏 -->
    <Arc ...><Stroke .../></Arc>
    <Line .../>
</PartDraw>
```

**样式**（形状的子元素，必选其一）：`<Fill>` `<Stroke>`

**渐变**（Fill/Stroke 的子元素）：`<LinearGradient>` `<RadialGradient>` `<SweepGradient>`

> 📌 **列表属性分隔符是空格，不是逗号**：`colors="#ff03050B #ff071629 #ff0E2C55"`、
> `positions="0.0 0.5 1.0"`（XSD `xs:list` 语义）。逗号分隔过不了官方校验。

### `<AnalogClock>` — 模拟时钟

> ⚠️ **三针全部基于图片资源**：HourHand/MinuteHand/SecondHand 的 `resource`
> 属性**必填**（指向 drawable），**没有 `color` 属性**（只有 `tintColor` 给图片染色）。
> 纯矢量画指针不可行——针的 PNG 需自备（Pillow 生成：细长矩形+透明底，指向 12 点方向）。

> 📐 **旋转中心公式（盲测 Round 2 修正 2026-09-06）**：旋转中心 =
> `(x + pivotX·width, y + pivotY·height)`，**必须精确等于表盘圆心**（如 450 画布
> = (225,225)）。针放错位置时指针绕非圆心转，真机上三针不交汇于一点。
> 12 点竖直针：`x = 圆心x − 宽/2`，`y = 圆心y − 针长`。

```xml
<AnalogClock x="0" y="0" width="450" height="450">
    <!-- 旋转中心 (214+11, 110+115)=(225,225) = 圆心 ✓ -->
    <HourHand resource="hand_hour" x="214" y="110" width="22" height="115"
             pivotX="0.5" pivotY="1.0"/>
    <!-- 旋转中心 (217+8, 60+165)=(225,225) ✓ -->
    <MinuteHand resource="hand_minute" x="217" y="60" width="16" height="165"
                pivotX="0.5" pivotY="1.0"/>
    <!-- 秒针（细+红；Sweep 平滑扫秒；AMBIENT 隐藏）。
         带配重尾部：图高 235 = 针长 195 + 尾部 40，pivotY = 195/235 ≈ 0.8298
         （pivot 不在图片边缘时按占比推算），旋转中心仍精确 (225,225) -->
    <SecondHand resource="hand_second" x="221" y="30" width="8" height="235"
                pivotX="0.5" pivotY="0.8298" tintColor="#ffff3b30" alpha="255">
        <Variant mode="AMBIENT" target="alpha" value="0"/>
        <Sweep frequency="10"/>
    </SecondHand>
</AnalogClock>
```

| 子元素 | 说明 |
|--------|------|
| `<HourHand>` | 时针（resource 必填） |
| `<MinuteHand>` | 分针（resource 必填） |
| `<SecondHand>` | 秒针（resource 必填；Sweep/Tick 可选） |

Hand 属性：`resource`（必填）`x y width height`（必填）`pivotX pivotY`（旋转中心，**归一化 0~1**，相对针自身包围盒；12 点方向竖直针的 pivot 在底端中心 = `0.5, 1.0`）`alpha` `tintColor`

### `<DigitalClock>` — 数字时钟

```xml
<DigitalClock x="0" y="0" width="450" height="450">
    <TimeText format="hh:mm" hourFormat="SYNC_TO_DEVICE" align="CENTER"
              x="0" y="120" width="450" height="120">
        <Font family="SYNC_TO_DEVICE" size="100" weight="BOLD" color="#ff00F5FF"/>
        <Variant mode="AMBIENT" target="alpha" value="0"/>
    </TimeText>
</DigitalClock>
```

| 子元素 | 说明 |
|--------|------|
| `<TimeText>` | 时间文本（自动刷新） |
| `<Text>` | 附加文本 |

> ⚠️ **format 只接受小写 h/m/s**（XSD `timeFormatType` pattern：`h{1,2}:m{1,2}(:s{1,2})?` 等
> 小写组合）。`HH:mm` 过不了官方校验（真机可能宽容，但规范非法）。12/24 小时制由
> `hourFormat`（`12`/`24`/`SYNC_TO_DEVICE`）控制，与 format 无关。
>
> ⚠️ **TimeText 的 Font 是精简内联版**（XSD 局部定义，纯属性）——**不能内嵌任何子元素**
> （Outline/Shadow/Transform 等都不行），描边等装饰只有 `PartText > Font`（全局版，
> 支持 TextComponentGroup 装饰子元素）才有。TimeText 要描边就叠一层 PartDraw 圈线视觉替代。

---

## 变体与条件

### `<Variant>` — 变体

```xml
<Variant mode="AMBIENT" target="alpha" value="0"/>
```

| 属性 | 类型 | 说明 |
|------|------|------|
| `mode` | enum | `AMBIENT`（常用） |
| `target` | string | 变体目标属性名（`alpha`/`color`/`size` 等） |
| `value` | string | 变体值 |

### `<Condition>` — 条件渲染

> ⚠️ **Condition 元素本身没有 `expression` 属性**（R32，官方 XSD 实证 2026-09-07）。
> 条件算式定义在子元素 `<Expressions>/<Expression name="...">` 的**文本内容**里，
> `<Compare expression="...">` 通过 name **引用**（XSD keyref 强制）。
> 比较运算符只有 `>` `>=` `==`（**没有 `<` `<=`**——`<` 在 XML 里非法，官方设计
> 就是用反转写法）：`[BATTERY_PERCENT] < 20` 必须写成 `20 > [BATTERY_PERCENT]`。
> 首个命中的 Compare 渲染，其余不渲染；都没命中走 `<Default>`（可选）。

```xml
<Condition>
    <Expressions>
        <Expression name="battery_low">20 > [BATTERY_PERCENT]</Expression>
    </Expressions>
    <Compare expression="battery_low">
        <PartText x="45" y="300" width="360" height="48">
            <Text align="CENTER"><Font family="SYNC_TO_DEVICE" size="28" color="#ffFF4444">[BATTERY_PERCENT]% LOW</Font></Text>
        </PartText>
    </Compare>
    <Default>
        <PartText x="45" y="300" width="360" height="48">
            <Text align="CENTER"><Font family="SYNC_TO_DEVICE" size="28" color="#ffededf2">[BATTERY_PERCENT]%</Font></Text>
        </PartText>
    </Default>
</Condition>
```

| 子元素 | 说明 |
|--------|------|
| `<Expressions>` | **必填**，≥1 个 `<Expression name="...">`，算式写在元素文本 |
| `<Compare expression="引用名">` | **必填** ≥1 个；expression 必须引用 Expressions 里定义的 name |
| `<Default>` | 可选；所有 Compare 都不命中时渲染 |

### `<Transform>` — 属性驱动变换

> ⚠️ **没有 `rotate()`/`translate()`/`scale()` 这类变换函数**（旧知识层虚构）。
> Transform 的机制是：`target` 指定要修改的**宿主属性名**，`value` 给出该属性的新值（算术表达式）。

```xml
<!-- 官方 samples 实例：把 Arc 的 endAngle 变成动态值 -->
<Transform target="endAngle"
           value="-150 + (clamp([COMPLICATION.GOAL_PROGRESS_VALUE], 0,
                 [COMPLICATION.GOAL_PROGRESS_TARGET_VALUE])
                 / [COMPLICATION.GOAL_PROGRESS_TARGET_VALUE]) * 300"/>
```

| 属性 | 必填 | 说明 |
|------|------|------|
| `target` | ✅ | 宿主属性名（如 `angle` `x` `y` `alpha` `endAngle` `startAngle` `scaleX`） |
| `value` | ✅ | 算术表达式，结果写入 target 属性 |
| `mode` | | `TO`（默认，设为该值）/ `BY`（在原值上累加） |

- 挂载点：形状（Arc/Ellipse/Rectangle/RoundRectangle/Line）、Stroke、渐变、Part、Group、TextCircular 内部
- **动画**：内嵌一个 `<Animation>` 子元素（见下方动画章节），`value` 里用 `[ANIMATION_VALUE]` 引用动画进度值

### `<Gyro>` — 陀螺仪响应

```xml
<Gyro x="(5/90) * clamp([ACCELEROMETER_ANGLE_X], -90, 90)"
     y="(5/90) * clamp([ACCELEROMETER_ANGLE_Y], -90, 90)"/>
```

支持 `x y scaleX scaleY angle alpha` 六个响应属性（全部为表达式类型）。

- 挂载点：**Group 或 Part 内部**（直接子元素），调整的是**父 Group/Part** 的对应属性
- 数据源：`[ACCELEROMETER_ANGLE_X]` `[ACCELEROMETER_ANGLE_Y]`（XSD sensorSourceType 白名单）
- 表达式建议用 `clamp()` 限幅，复杂式可用 CDATA 包裹（官方注释建议）
- 腕部倾斜 ±90° → 表达式输出控制父元素位移/旋转/透明度 → 视差效果

---

## Complication

### `<ComplicationSlot>`

```xml
<ComplicationSlot x="140" y="328" width="170" height="88"
                  slotId="1" supportedTypes="SHORT_TEXT EMPTY"
                  displayName="@string/complication_slot_display"
                  isCustomizable="TRUE" tintColor="#ff00E5FF">
    <!-- 可选：默认数据源（不写则用户手动选） -->
    <DefaultProviderPolicy defaultSystemProvider="HEART_RATE"
                           defaultSystemProviderType="SHORT_TEXT"/>
    <!-- 必填①：边界形状（BoundingShape 是抽象头，必须用具体替换组成员）
         ⚠️ R28: 局部坐标（0,0 = slot 左上角），覆盖 slot 自身尺寸；写全局坐标
         会让槽位落到画布外——不渲染 + 编辑器不出现自定义入口（真机实证 2026-08-31） -->
    <BoundingRoundBox x="0" y="0" width="170" height="88"
                      cornerRadius="14" outlinePadding="2"/>
    <!-- 必填②：Complication 渲染定义（每个 supportedType 一个） -->
    <Complication type="SHORT_TEXT">
        <!-- ⚠️ R26: 内部必须有 Part 组件，否则真机渲染为空 -->
        <!-- 坐标是 slot 的局部坐标系：0,0 = slot 左上角 -->
        <PartText x="0" y="0" width="170" height="88">
            <Text align="CENTER">
                <Font family="SYNC_TO_DEVICE" size="40" weight="BOLD" color="#ff00E5FF">
                    <Template>%s
                        <Parameter expression="[COMPLICATION.TEXT]"/>
                    </Template>
                </Font>
            </Text>
        </PartText>
    </Complication>
    <!-- 可选但强烈建议：EMPTY 占位（无数据/用户选"无"时兜底，格子不空白） -->
    <Complication type="EMPTY">
        <PartText x="0" y="26" width="170" height="36">
            <Text align="CENTER">
                <Font family="SYNC_TO_DEVICE" size="24" weight="NORMAL" color="#ff7E93A8">--</Font>
            </Text>
        </PartText>
    </Complication>
</ComplicationSlot>
```

> ⚠️ **空 `<Complication type="..."/>` 真机渲染为空**（真机实证 2026-08-31，R26）：
> XSD 允许空 Complication（choice minOccurs=0），但没有任何 Part 就什么都不画——
> 16 规则和官方 XSD 校验都抓不住这种"合法但空白"的错。Complication 内部必须放
> PartText/PartImage/PartDraw，用 **`[COMPLICATION.*]` 特殊数据源**绑定 provider 数据。

> ⚠️ **数据格底板放 slot 外面**（真机实证 2026-08-31）：Complication 内容是
> type-gated 的——provider 无数据时整个 `<Complication type="SHORT_TEXT">` 不渲染，
> 里面的静态底板也会消失。想要边框永远可见，把底板写成 Scene 里独立的 PartDraw
> （紧挨 ComplicationSlot 之前），配自己的 AMBIENT Variant。

> ⚠️ **`<Template>` 至少含一个 `<Parameter>`**（XSD 强制）；静态文本直接写在
> `<Font>` 里（mixed=true），不要用无参 Template。

**`COMPLICATION.*` 数据源**（仅 Complication 内部可用，按 type 取用）：

| 字段 | 适用类型 | 内容 |
|---|---|---|
| `COMPLICATION.TEXT` | SHORT_TEXT/LONG_TEXT | 主文本（如心率值 "72"） |
| `COMPLICATION.TITLE` | SHORT_TEXT/LONG_TEXT | 短标题（如 "bpm"） |
| `COMPLICATION.MONOCHROMATIC_IMAGE` / `_AMBIENT` | SHORT_TEXT/LONG_TEXT | 单色图标 |
| `COMPLICATION.SMALL_IMAGE` / `_AMBIENT`、`COMPLICATION.IMAGE_STYLE` | SMALL_IMAGE | 小图（PHOTO=1/ICON=2） |
| `COMPLICATION.PHOTO_IMAGE` | PHOTO_IMAGE | 照片 |
| `COMPLICATION.RANGED_VALUE_VALUE/MIN/MAX/COLORS/COLORS_INTERPOLATE` | RANGED_VALUE | 区间值 |
| `COMPLICATION.GOAL_PROGRESS_*` | GOAL_PROGRESS | 目标进度（值/目标/颜色） |
| `COMPLICATION.WEIGHTED_ELEMENTS_*` | WEIGHTED_ELEMENTS | 加权元素 |

用法：文本走 `<Template>%s<Parameter expression="[COMPLICATION.TEXT]"/></Template>`；
图片走 `<Image resource="[COMPLICATION.SMALL_IMAGE]"/>`。

> ⚠️ **BoundingShape 不可直接实例化**：它是 XSD substitution group 抽象头，
> 必须写具体成员之一：`<BoundingBox x y width height/>`（直角）、
> `<BoundingRoundBox x y width height cornerRadius outlinePadding/>`（圆角矩形，最常用）、
> `<BoundingOval x y width height outlinePadding/>`（椭圆；几何属性是
> **x/y** 包围盒左上角——XSD `geometricAttributesRequired`，不是 centerX/centerY，
> BT-08 盲测实证 validator 通过）、`<BoundingArc .../>`。
> 成员的几何属性（x/y/width/height 等）**必填**。
> 注意：BoundingShape 只是点击/碰撞区域，**不渲染任何视觉内容**——边框底板要自己在
> Complication 里用 PartDraw 画。

> ⚠️ **Complication 元素只有 `@type` 一个属性**。`defaultProvider`/`primaryDataStyle`/
> `primaryDataSource` 等属性在 XSD 中不存在——默认数据源语义属于
> `<DefaultProviderPolicy>` 子元素。

> 📌 **booleanType 枚举是大写 `TRUE`/`FALSE`**（`isCustomizable="TRUE"`），小写
> `true` 不合法（XSD `booleanType` 自定义枚举，非 xs:boolean）。

> ⚠️ **`displayName` 用裸资源名**（R30 反转版，真机复测 2026-09-09）：`displayName="slot_heart_rate"`
> 与 `res/values/strings.xml` 中资源名一致。res/raw 与 res/xml 不经 aapt2 编译，`@string/`
> 前缀在这些文件里是字面量，WFF 库按名自查 arsc。
> `slotId` 官方 samples 从 **0** 开始（Flavors/Complications 一致），XSD `xs:unique`
> 强制全局唯一；Scene 内 ComplicationSlot **上限 8 个**（R38）。
> `BoundingOval` 支持 `outlinePadding`（编辑器选中外框内边距，官方 sample 在用）。

Complication 类型：`SHORT_TEXT` `LONG_TEXT` `MONOCHROMATIC_IMAGE` `SMALL_IMAGE` `PHOTO_IMAGE` `RANGED_VALUE` `GOAL_PROGRESS` `WEIGHTED_ELEMENTS` `EMPTY`

DefaultProvider：`APP_SHORTCUT` `DATE` `DAY_OF_WEEK` `FAVORITE_CONTACT` `NEXT_EVENT` `STEP_COUNT` `SUNRISE_SUNSET` `TIME_AND_DATE` `UNREAD_NOTIFICATION_COUNT` `WATCH_BATTERY` `WORLD_CLOCK` `HEART_RATE` `EMPTY`

> 📌 provider×type 兼容矩阵规范未给出。保守策略：系统 provider 用 `SHORT_TEXT`
> （跨 provider 兼容面最广）。RANGED_VALUE 仅在确认 provider 支持时使用。

---

## 用户配置

### `<UserConfigurations>`（容器版——编辑器 UI 元数据，挂在 Scene 前）

```xml
<UserConfigurations>
    <ColorConfiguration id="themeColor" displayName="theme_color" defaultValue="0">
        <ColorOption id="0" displayName="color_zero" colors="#ff00E5FF #ff071629"/>
    </ColorConfiguration>
    <ListConfiguration id="clockStyle" displayName="clock_style" defaultValue="0">
        <ListOption id="0" displayName="style_thin" icon="style_thin_icon"/>
        <ListOption id="1" displayName="style_bold" icon="style_bold_icon"/>
    </ListConfiguration>
    <BooleanConfiguration id="showSeconds" displayName="show_seconds" defaultValue="TRUE"/>
    <PhotosConfiguration id="bg" displayName="bg_label" defaultValue="..."
                         configType="SINGLE" highlight="highlight_icon"/>
    <Flavors>
        <Flavor id="flavorOne" displayName="flavor_one_label" icon="flavor_one_icon">
            <Configuration id="themeColor" optionId="1"/>
            <Configuration id="showSeconds" optionId="FALSE"/>
            <ComplicationSlot slotId="0">
                <DefaultProviderPolicy defaultSystemProvider="SUNRISE_SUNSET"
                                       defaultSystemProviderType="EMPTY"/>
            </ComplicationSlot>
        </Flavor>
    </Flavors>
</UserConfigurations>
```

- **没有 `<UserConfiguration>` 这个元素**（旧知识层写法是错的，XSD v5 无此元素）；
  五种配置各是独立元素：`ColorConfiguration` `ListConfiguration` `BooleanConfiguration`
  `PhotosConfiguration` `Flavors`
- **icon 属性可省**（BT-08 盲测实证）：省略时构建/校验不受影响，编辑器用文本
  标签显示选项——纯矢量/无位图素材约束下的推荐做法
- `ListConfiguration` 必填 id/displayName/defaultValue；`ListOption` 纯属性
  （id + displayName/icon/`complicationSlotIds`/`childSettingIds`——空格分隔多值）
- `BooleanConfiguration` 容器版**纯属性无子元素**（defaultValue 取 TRUE/FALSE）
- `PhotosConfiguration` configType 枚举 `SINGLE`/`MULTIPLE`；`Flavors/Flavor` 是
  预设组合（Configuration optionId + ComplicationSlot 预设 provider）
- `displayName` 一律裸资源名（R30）

### List/Boolean **渲染版**（Scene/Group/指针内——每选项的渲染内容，R37）

```xml
<!-- Scene 内; id 与容器版一致 -->
<ListConfiguration id="clockStyle">
    <ListOption id="0"><DigitalClock>…细体时间…</DigitalClock></ListOption>
    <ListOption id="1"><DigitalClock>…粗体时间…</DigitalClock></ListOption>
</ListConfiguration>

<BooleanConfiguration id="showSeconds">
    <BooleanOption id="TRUE"><PartText>…秒…</PartText></BooleanOption>
    <!-- 可只放 TRUE: FALSE 状态=该处不渲染 (官方 showHr 模式) -->
</BooleanConfiguration>
```

BooleanOption/ListOption 内嵌单个部件：PartElementGroup / Group / Condition /
AnalogClock / DigitalClock。渲染版可挂在 HourHand/MinuteHand/SecondHand 内
（多套指针样式切换）。

### 引用方式

- 无索引：`[CONFIGURATION.themeColor]`（单色 ColorOption，P2 真机实证）
- **色位索引**：`[CONFIGURATION.themeColor.0]`（多色 colors 取第 0 位，官方 sample）
- 数据有无判断：`[CONFIGURATION.x] != null`；三元 `[A] != null ? [A] : "--"`
- 复杂表达式（含 `&&`）用 CDATA 包裹（R39）

---

## 位图字体

```xml
<BitmapFonts>
    <BitmapFont name="custom_digits">
        <Character name="0" file="digits/0.png"/>
        <Character name="1" file="digits/1.png"/>
        <Word name="AM" file="am.png"/>
    </BitmapFont>
</BitmapFonts>
```

用 `family="custom_digits"` 引用

---

## 字体

### `<Font>`

| 属性 | 类型 | 说明 |
|------|------|------|
| `family` | string | `SYNC_TO_DEVICE`（推荐）或自定义位图字体名 |
| `size` | int | 字号 |
| `weight` | enum | `THIN` `ULTRA_LIGHT` `EXTRA_LIGHT` `LIGHT` `NORMAL` `MEDIUM` `SEMI_BOLD` `BOLD` |
| `slant` | enum | `NORMAL` `ITALIC` |
| `color` | color | 8 位 ARGB |
| `letterSpacing` | float | 字间距 |
| `scaleX` `scaleY` | float | 缩放 |

---

## 图片 / 动画

### 图片滤镜 `<ImageFilters>`

挂 `PartImage` 内（不是独立元素；旧知识层的 `<ImageFilter>` + `NONE/GRAYSCALE/DIMMED/TINTED` 枚举是虚构的）：

```xml
<PartImage x="0" y="0" width="450" height="450">
    <Image resource="background"/>
    <ImageFilters>
        <HsbFilter saturate="1.5" brightness="0.8"/>
    </ImageFilters>
</PartImage>
```

`<HsbFilter>`：`hueRotate`（角度）`saturate` `brightness`（归一化值，默认 1）。

### 动画总览

WFF 动画分三类（**v1 / Wear OS 4 起全部可用**，无版本障碍）：

| 类别 | 元素组合 | 效果 |
|------|---------|------|
| 帧序列动画 | `PartAnimatedImage > AnimationController + SequenceImages > Image×N` | 多张 PNG 逐帧播放 |
| 动图 | `PartAnimatedImage > AnimationController + AnimatedImage` | AGIF / 动态 WEBP 单文件播放 |
| 属性动画 | `Part/Group/形状 > Transform(target,value) > Animation` | 矢量属性随时间插值变化 |
| 陀螺仪响应 | `Group/Part > Gyro` | 属性随腕部倾斜实时变化 |

### `<PartAnimatedImage>` — 动画 Part 容器

与 `PartImage`/`PartDraw` 平级（Group 内直接引用）。**三件套缺一不可**：

```xml
<PartAnimatedImage x="90" y="330" width="90" height="90" name="seq">
    <AnimationController play="ON_VISIBLE" repeat="TRUE"/>
    <SequenceImages>
        <Image resource="seq_0"/>
        <Image resource="seq_1"/>
        <Image resource="seq_2"/>
        <Image resource="seq_3"/>
    </SequenceImages>
</PartAnimatedImage>
```

| 子元素 | 必填 | 说明 |
|--------|------|------|
| `<AnimationController>` | ✅ 1 个 | 播放控制器（见下） |
| `<SequenceImages>` 或 `<AnimatedImage>` 或 `<AnimatedImages>` | ✅ 1 个 | 动画内容 |
| `<Thumbnail>` | | 静态占位图资源名 |

### `<AnimationController>` — 播放控制

| 属性 | 必填 | 类型/默认 | 说明 |
|------|------|----------|------|
| `play` | ✅ | 事件列表 | 触发播放的事件（见下表） |
| `delayPlay` | | float, 0 | 触发后延迟秒数 |
| `delayRepeat` | | float, 0 | 重复之间的延迟秒数 |
| `repeat` | | bool, FALSE | **TRUE = 无限循环**（不是 loopCount=-1！） |
| `loopCount` | | int ≥0, 1 | 播放轮数（v5 不允许负数；无限循环用 repeat） |
| `resumePlayBack` | | bool, FALSE | 中断后恢复播放（而非重头） |
| `beforePlaying` | | DO_NOTHING(默认) | 播放前显示：`DO_NOTHING` `FIRST_FRAME` `THUMBNAIL` `HIDE` |
| `afterPlaying` | | DO_NOTHING(默认) | 播放结束后显示：同上四个值 |

`play` 事件值域（eventTriggerType，空格分隔可多值）：

| 值 | 触发时机 |
|---|---------|
| `ON_VISIBLE` | 元素变为可见（表盘进入视野，最常用） |
| `TAP` | 用户点击元素 |
| `ON_NEXT_SECOND` | 下一秒 |
| `ON_NEXT_MINUTE` | 下一分钟 |
| `ON_NEXT_HOUR` | 下一小时 |

### `<SequenceImages>` — 帧序列

| 属性 | 类型/默认 | 说明 |
|------|----------|------|
| `loopCount` | int ≥1, 1 | 播放轮数（v5 为 positiveInteger） |
| `thumbnail` | string | 静态占位图资源名 |
| `frameRate` | 1-60, 15 | ⚠️ **WFF 2+ 才支持**，v1 表盘禁用 |

子元素：多个 `<Image>`（**只有 `resource` 属性**，没有 width/height——尺寸由外层 PartAnimatedImage 决定）。

### `<AnimatedImage>` — 动图

| 属性 | 必填 | 说明 |
|------|------|------|
| `resource` | ✅ | drawable 资源名（AGIF/WEBP 文件） |
| `format` | ✅ | `AGIF`（动图 GIF）或 `WEBP`（动图 WebP）；`IMAGE` 为静态图 |
| `thumbnail` | | 静态占位图资源名 |

> ⚠️ 没有 `file`/`playback` 属性（旧知识层虚构）；播放控制全部在 AnimationController。
> 播放控制（循环/触发/结束行为）写在 `<AnimationController>`，不写在 AnimatedImage 上。

### `<AnimatedImages>` — 多内容切换

动画内容多态容器（点击等事件切换子项）：

```xml
<PartAnimatedImage x="0" y="0" width="90" height="90">
    <AnimationController play="ON_VISIBLE"/>
    <AnimatedImages change="TAP">
        <AnimatedImage resource="state_a" format="AGIF"/>
        <AnimatedImage resource="state_b" format="AGIF"/>
    </AnimatedImages>
</PartAnimatedImage>
```

| 属性 | 默认 | 说明 |
|------|------|------|
| `change` | TAP | 切换到下一子项的事件（eventTriggerType） |
| `changeDirection` | FORWARD | `FORWARD`/`BACKWARD`/`RANDOM`（⚠️ WFF 2+） |

### `<Animation>` — 属性动画（Transform 内嵌）

挂在 `<Transform>` 内，让 `value` 表达式中的 `[ANIMATION_VALUE]` 随时间插值（0→1）：

```xml
<PartDraw x="165" y="165" width="120" height="120">
    <Transform target="alpha" value="[ANIMATION_VALUE] * 0.7">
        <Animation duration="2.0" repeat="-1" interpolation="EASE_IN_OUT"/>
    </Transform>
    <Ellipse x="0" y="0" width="120" height="120">
        <Stroke color="#ff2ec4b6" thickness="2"/>
    </Ellipse>
</PartDraw>
```

| 属性 | 必填 | 类型/默认 | 说明 |
|------|------|----------|------|
| `duration` | ✅ | float ≥0 | 时长（秒） |
| `repeat` | | int ≥-1, 0 | **0=不重复，-1=无限循环**（注意与 AnimationController.repeat 的 bool 语义不同！） |
| `interpolation` | | LINEAR | `LINEAR` `EASE_IN` `EASE_OUT` `EASE_IN_OUT` `OVERSHOOT` `CUBIC_BEZIER` |
| `controls` | | "0.5 0.5 0.5 0.5" | CUBIC_BEZIER 控制点（4 个浮点空格分隔） |
| `angleDirection` | | NONE | `NONE` `CLOCKWISE` `COUNTER_CLOCKWISE`（角度插值方向） |
| `fps` | | int, 15 | 帧率 |

### `<ImageFilter>` — 滤镜（速查）

实际结构是 `<ImageFilters>` 容器 + `<HsbFilter>`（见图片滤镜节）。

---

## 完整元素清单

| 分类 | 元素 |
|------|------|
| 根 | WatchFace |
| 元信息 | Metadata |
| 场景 | Scene |
| 分组 | Group, Part |
| 时钟 | AnalogClock, DigitalClock, HourHand, MinuteHand, SecondHand, TimeText |
| 文本 | PartText, Text, Text.DECIMAL, Text.CURRENT_DATE, Template, Parameter, Font |
| 图片 | PartImage, Image, ImageFilters, HsbFilter |
| **动画** | PartAnimatedImage, AnimationController, AnimatedImage, AnimatedImages, SequenceImages, Animation |
| 绘制 | PartDraw, Stroke, Fill, Arc, Ellipse, Line, Rectangle, RoundRectangle(cornerRadiusX/Y) |
| 渐变 | LinearGradient, RadialGradient, SweepGradient |
| 变体 | Variant |
| 条件 | Condition, Compare, Default |
| 变换 | Transform(target/value/mode) |
| 陀螺仪 | Gyro |
| Complication | ComplicationSlot, Complication, DefaultProviderPolicy |
| 用户配置 | UserConfigurations, UserConfiguration, ListOption, BooleanOption, ColorOption, PhotosOption, FlavorsOption |
| 位图字体 | BitmapFonts, BitmapFont, Character, Word |
| 其他 | ScreenReader, Reference, WeightedElements, Thumbnail, OutGlow, Outline, Shadow, Underline, StrikeThrough |

> 完整属性列表（含文档、类型、枚举）见 `data/wff_inventory_v5.md`

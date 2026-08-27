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
| `<Image>` | 图片引用 |
| `<ImageFilter>` | 滤镜 |
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

**形状**（PartDraw 直接子元素）：`<Arc>` `<Ellipse>` `<Line>` `<Rectangle>` `<RoundRectangle>`
> ⚠️ **没有 `<Circle>` 和 `<Path>`**——画圆用 Ellipse（width=height），x/y/width/height 定包围盒。

**样式**（形状的子元素，必选其一）：`<Fill>` `<Stroke>`

**渐变**（Fill/Stroke 的子元素）：`<LinearGradient>` `<RadialGradient>` `<SweepGradient>`

> 📌 **列表属性分隔符是空格，不是逗号**：`colors="#ff03050B #ff071629 #ff0E2C55"`、
> `positions="0.0 0.5 1.0"`（XSD `xs:list` 语义）。逗号分隔过不了官方校验。

### `<AnalogClock>` — 模拟时钟

> ⚠️ **三针全部基于图片资源**：HourHand/MinuteHand/SecondHand 的 `resource`
> 属性**必填**（指向 drawable），**没有 `color` 属性**（只有 `tintColor` 给图片染色）。
> 纯矢量画指针不可行——针的 PNG 需自备（Pillow 生成：细长矩形+透明底，指向 12 点方向）。

```xml
<AnalogClock x="0" y="0" width="450" height="450">
    <HourHand resource="hand_hour" x="215" y="100" width="20" height="200"
             pivotX="0.5" pivotY="1.0"/>
    <MinuteHand resource="hand_minute" x="218" y="60" width="14" height="240"
                pivotX="0.5" pivotY="1.0"/>
    <!-- 秒针：可加 Sweep（平滑扫秒，频率 2/5/10/15Hz）或 Tick（跳动动画） -->
    <SecondHand resource="hand_second" x="221" y="40" width="8" height="280"
                pivotX="0.5" pivotY="1.0" alpha="255">
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

```xml
<Condition expression="[BATTERY_PERCENT] < 20">
    <Compare expression="1">
        <PartText>...</PartText>
    </Compare>
    <Default>
        <PartText>...</PartText>
    </Default>
</Condition>
```

### `<Transform>` — 动态变换

```xml
<Transform value="rotate([SECOND] / 60 * 360)"/>
```

支持 `rotate()` `translate()` `scale()` 等变换函数，参数为表达式

### `<Gyro>` — 陀螺仪响应

```xml
<Gyro x="(5/90) * clamp([ACCELEROMETER_ANGLE_X], -90, 90)"
     y="(5/90) * clamp([ACCELEROMETER_ANGLE_Y], -90, 90)"/>
```

支持 `x y scaleX scaleY angle alpha` 六轴响应

---

## Complication

### `<ComplicationSlot>`

```xml
<ComplicationSlot x="140" y="328" width="170" height="88"
                  slotId="0" supportedTypes="SHORT_TEXT"
                  displayName="DATA" isCustomizable="TRUE" tintColor="#ff00E5FF">
    <!-- 必填①：边界形状（BoundingShape 是抽象头，必须用具体替换组成员） -->
    <BoundingRoundBox x="140" y="328" width="170" height="88"
                      cornerRadius="14" outlinePadding="2"/>
    <!-- 可选：默认数据源（不写则用户手动选） -->
    <DefaultProviderPolicy defaultSystemProvider="HEART_RATE"
                           defaultSystemProviderType="SHORT_TEXT"/>
    <!-- 必填②：Complication 渲染定义（至少 1 个；自定义渲染太复杂时可用最小结构占位） -->
    <Complication type="SHORT_TEXT" .../>
</ComplicationSlot>
```

> ⚠️ **BoundingShape 不可直接实例化**：它是 XSD substitution group 抽象头，
> 必须写具体成员之一：`<BoundingBox x y width height/>`（直角）、
> `<BoundingRoundBox x y width height cornerRadius outlinePadding/>`（圆角矩形，最常用）、
> `<BoundingOval centerX centerY width height/>`、`<BoundingArc .../>`。
> 成员的几何属性（x/y/width/height 等）**必填**。

> ⚠️ **Complication 元素只有 `@type` 一个属性**。`defaultProvider`/`primaryDataStyle`/
> `primaryDataSource` 等属性在 XSD 中不存在——默认数据源语义属于
> `<DefaultProviderPolicy>` 子元素。

> 📌 **booleanType 枚举是大写 `TRUE`/`FALSE`**（`isCustomizable="TRUE"`），小写
> `true` 不合法（XSD `booleanType` 自定义枚举，非 xs:boolean）。

Complication 类型：`SHORT_TEXT` `LONG_TEXT` `MONOCHROMATIC_IMAGE` `SMALL_IMAGE` `PHOTO_IMAGE` `RANGED_VALUE` `GOAL_PROGRESS` `WEIGHTED_ELEMENTS` `EMPTY`

DefaultProvider：`APP_SHORTCUT` `DATE` `DAY_OF_WEEK` `FAVORITE_CONTACT` `NEXT_EVENT` `STEP_COUNT` `SUNRISE_SUNSET` `TIME_AND_DATE` `UNREAD_NOTIFICATION_COUNT` `WATCH_BATTERY` `WORLD_CLOCK` `HEART_RATE` `EMPTY`

> 📌 provider×type 兼容矩阵规范未给出。保守策略：系统 provider 用 `SHORT_TEXT`
> （跨 provider 兼容面最广）。RANGED_VALUE 仅在确认 provider 支持时使用。

---

## 用户配置

### `<UserConfigurations>`

```xml
<UserConfigurations>
    <UserConfiguration id="color_theme" ...>
        <ListOption displayName="Blue" value="blue"/>
        <ListOption displayName="Red" value="red"/>
    </UserConfiguration>
    <UserConfiguration id="show_seconds" type="Boolean" .../>
    <UserConfiguration id="bg_photo" type="Photos" .../>
</UserConfigurations>
```

配置类型：`List`（下拉选择）、`Boolean`（开关）、`Color`（颜色选择器）、`Photos`（用户照片）、`Flavors`（预设风格）

引用方式：`[CONFIGURATION.color_theme]`

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

## 图片/动画

### `<AnimatedImage>`

```xml
<AnimatedImage file="anim.gif" playback="LOOP">
    <Variant mode="AMBIENT" target="alpha" value="0"/>
</AnimatedImage>
```

`playback`: `ONE_SHOT` `LOOP`

`frameOption`: `DO_NOTHING` `FIRST_FRAME` `THUMBNAIL` `HIDE`（ambient 时的处理）

### `<ImageFilter>`

滤镜类型：`NONE` `GRAYSCALE` `DIMMED` `TINTED`

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
| 图片 | PartImage, Image, AnimatedImage, ImageFilter |
| 绘制 | PartDraw, Stroke, Fill, Arc, Circle, Ellipse, Line, Rectangle, RoundRectangle, Path |
| 渐变 | LinearGradient, RadialGradient, SweepGradient |
| 变体 | Variant |
| 条件 | Condition, Compare, Default |
| 变换 | Transform |
| 陀螺仪 | Gyro |
| Complication | ComplicationSlot, Complication, DefaultProviderPolicy |
| 用户配置 | UserConfigurations, UserConfiguration, ListOption, BooleanOption, ColorOption, PhotosOption, FlavorsOption |
| 位图字体 | BitmapFonts, BitmapFont, Character, Word |
| 其他 | ScreenReader, Reference, WeightedElements |

> 完整属性列表（含文档、类型、枚举）见 `data/wff_inventory_v5.md`

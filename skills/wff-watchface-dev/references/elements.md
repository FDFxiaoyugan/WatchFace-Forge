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

```xml
<PartDraw x="0" y="0" width="450" height="450">
    <Stroke color="#ff00F5FF" thickness="4">
        <Arc centerX="225" centerY="225" width="400" height="400" 
             direction="CLOCKWISE" sweepAngle="180"/>
    </Stroke>
    <Fill color="#ff00F5FF">
        <Circle centerX="225" centerY="225" radius="200"/>
    </Fill>
</PartDraw>
```

**形状子元素**（Draw 下）：`<Arc>` `<Circle>` `<Ellipse>` `<Line>` `<Rectangle>` `<RoundRectangle>` `<Path>`

**样式子元素**：`<Fill>` `<Stroke>`

**渐变**：`<LinearGradient>` `<RadialGradient>` `<SweepGradient>`

### `<AnalogClock>` — 模拟时钟

```xml
<AnalogClock x="50" y="50" width="350" height="350">
    <HourHand x="175" y="50" width="50" height="200"
             color="#ffFFFFFF" offsetX="175" offsetY="225"/>
    <MinuteHand .../>
    <SecondHand .../>
</AnalogClock>
```

| 子元素 | 说明 |
|--------|------|
| `<HourHand>` | 时针 |
| `<MinuteHand>` | 分针 |
| `<SecondHand>` | 秒针 |

Hand 属性：`x y width height color offsetX offsetY`

### `<DigitalClock>` — 数字时钟

```xml
<DigitalClock x="0" y="0" width="450" height="450">
    <TimeText format="HH:mm" hourFormat="SYNC_TO_DEVICE" align="CENTER"
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

`TimeText.format` 支持的占位符：`H` `HH` `m` `mm` `s` `ss` `a`（AM/PM）等

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
<ComplicationSlot slotId="0" x="150" y="150" width="150" height="150">
    <Complication type="SHORT_TEXT" .../>
</ComplicationSlot>
```

Complication 类型：`SHORT_TEXT` `LONG_TEXT` `MONOCHROMATIC_IMAGE` `SMALL_IMAGE` `PHOTO_IMAGE` `RANGED_VALUE` `GOAL_PROGRESS` `WEIGHTED_ELEMENTS` `EMPTY`

DefaultProvider：`APP_SHORTCUT` `DATE` `DAY_OF_WEEK` `FAVORITE_CONTACT` `NEXT_EVENT` `STEP_COUNT` `SUNRISE_SUNSET` `TIME_AND_DATE` `UNREAD_NOTIFICATION_COUNT` `WATCH_BATTERY` `WORLD_CLOCK` `HEART_RATE` `EMPTY`

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

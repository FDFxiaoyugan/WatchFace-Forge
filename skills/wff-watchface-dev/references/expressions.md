# WFF 表达式与数据源参考

> WFF 的算术/条件表达式是表盘动态效果的核心。数据源用方括号 `[NAME]` 引用，支持运算符和函数组合。
> 数据来源：google/watchface XSD v5 `common/simpleTypes/` 枚举（官方规范）

---

## 数据源（Data Sources）

数据源在表达式中用**方括号**引用：`[SOURCE_NAME]`

### 时间

| 数据源 | 说明 | 示例值 |
|--------|------|--------|
| `[MILLISECOND]` | 毫秒 (0-999) | `530` |
| `[SECOND]` | 秒 (0-59)，无前导零 | `8` |
| `[SECOND_Z]` | 秒 (00-59)，前导零 | `08` |
| `[MINUTE]` | 分 (0-59) | `7` |
| `[MINUTE_Z]` | 分 (00-59) | `07` |
| `[HOUR_0_11]` | 12 小时制 (0-11) | `9` |
| `[HOUR_0_11_Z]` | 12 小时制 (00-11) | `09` |
| `[HOUR_1_12]` | 12 小时制 (1-12) | `10` |
| `[HOUR_1_12_Z]` | 12 小时制 (01-12) | `10` |
| `[HOUR_0_23]` | 24 小时制 (0-23) | `14` |
| `[HOUR_0_23_Z]` | 24 小时制 (00-23) | `14` |
| `[HOUR_1_24]` | 24 小时制 (1-24) | `14` |
| `[HOUR_1_24_Z]` | 24 小时制 (01-24) | `14` |
| `[AMPM_STATE]` | 0=AM, 1=PM | `0` |
| `[SECONDS_IN_DAY]` | 当天已过秒数 | `37812` |
| `[SECONDS_SINCE_EPOCH]` | Unix 时间戳 | `1724567890` |
| `[UTC_TIMESTAMP]` | UTC 时间戳 | `1724567890` |

> ⚠️ `_Z` 后缀 = 前导零版本。表盘显示时间推荐用 `DigitalClock` + `TimeText format="hh:mm"`，**不要**用 `Text` + `[HOUR]` 手动拼接（模板不自动刷新）。

### 日期

| 数据源 | 说明 | 示例值 |
|--------|------|--------|
| `[DAY]` | 日 (1-31) | `8` |
| `[DAY_Z]` | 日 (01-31) | `08` |
| `[DAY_OF_WEEK]` | 周几 (1-7) | `2` |
| `[DAY_OF_WEEK_S]` | 周几短名 | `Mon` |
| `[DAY_OF_WEEK_F]` | 周几全名 | `Monday` |
| `[DAYS_IN_MONTH]` | 当月天数 | `31` |
| `[MONTH]` | 月 (1-12) | `3` |
| `[MONTH_Z]` | 月 (01-12) | `03` |
| `[MONTH_S]` | 月名短 | `Mar` |
| `[MONTH_F]` | 月名全 | `March` |
| `[YEAR]` | 年 (4 位) | `2026` |
| `[YEAR_S]` | 年 (2 位) | `26` |

### 电池

| 数据源 | 说明 |
|--------|------|
| `[BATTERY_PERCENT]` | 电池百分比 (0-100) |
| `[BATTERY_CHARGING_STATUS]` | 充电状态 (0/1) |
| `[BATTERY_IS_LOW]` | 低电量警告 (0/1) |
| `[BATTERY_TEMPERATURE_CELSIUS]` | 电池温度 (摄氏) |
| `[BATTERY_TEMPERATURE_FAHRENHEIT]` | 电池温度 (华氏) |

### 健康

| 数据源 | 说明 |
|--------|------|
| `[STEP_COUNT]` | 今日步数 |
| `[STEP_GOAL]` | 步数目标 |
| `[STEP_PERCENT]` | 目标完成百分比 (0-100) |
| `[HEART_RATE]` | 心率 (BPM) |
| `[HEART_RATE_Z]` | 心率 (前导零) |

### 天气

| 数据源 | 说明 |
|--------|------|
| `[WEATHER.IS_AVAILABLE]` | 天气数据是否可用 (0/1) |
| `[WEATHER.IS_ERROR]` | 天气数据是否出错 (0/1) |
| `[WEATHER.CONDITION]` | 天气状况代码 |
| `[WEATHER.CONDITION_NAME]` | 天气状况名称 |
| `[WEATHER.IS_DAY]` | 白天/夜晚 (0/1) |
| `[WEATHER.TEMPERATURE]` | 温度 |
| `[WEATHER.TEMPERATURE_UNIT]` | 温度单位 |
| `[WEATHER.TEMPERATURE_LOW]` | 最低温度 |
| `[WEATHER.TEMPERATURE_HIGH]` | 最高温度 |
| `[WEATHER.CHANCE_OF_PRECIPITATION]` | 降水概率 |
| `[WEATHER.UV_INDEX]` | 紫外线指数 |
| `[WEATHER.LAST_UPDATED]` | 最后更新时间 |

### 传感器

| 数据源 | 说明 |
|--------|------|
| `[ACCELEROMETER_IS_SUPPORTED]` | 加速度计是否可用 (0/1) |
| `[ACCELEROMETER_X]` | X 轴加速度 |
| `[ACCELEROMETER_Y]` | Y 轴加速度 |
| `[ACCELEROMETER_Z]` | Z 轴加速度 |
| `[ACCELEROMETER_ANGLE_X]` | X 轴角度 (-90~90) |
| `[ACCELEROMETER_ANGLE_Y]` | Y 轴角度 |
| `[ACCELEROMETER_ANGLE_Z]` | Z 轴角度 |
| `[ACCELEROMETER_ANGLE_XY]` | XY 合成角度 |

### 月相

| 数据源 | 说明 |
|--------|------|
| `[MOON_PHASE_POSITION]` | 月相位置 (0.0-1.0) |
| `[MOON_PHASE_TYPE]` | 月相类型代码 |
| `[MOON_PHASE_TYPE_STRING]` | 月相名称 |

### 通知

| 数据源 | 说明 |
|--------|------|
| `[UNREAD_NOTIFICATION_COUNT]` | 未读通知数 |

### 语言/区域

| 数据源 | 说明 |
|--------|------|
| `[LANGUAGE_CODE]` | 语言代码 (en/zh) |
| `[LANGUAGE_COUNTRY_CODE]` | 国家代码 (CN/US) |
| `[LANGUAGE_LOCALE_NAME]` | 区域名称 |
| `[LANGUAGE_TEXT_DIRECTION]` | 文字方向 (0=LTR, 1=RTL) |

### 用户配置

| 数据源 | 说明 |
|--------|------|
| `[CONFIGURATION.<id>]` | 引用用户配置项的当前值 |

### Complication

> ⚠️ **只在 `<Complication>` 元素内部可用**（slot 上下文隐含，**不带 slotId**）。
> 官方写法是 `[COMPLICATION.TEXT]`，不是 `[COMPLICATION.0.TEXT]`。
> 这不是普通数据源——它由系统 complication provider 动态注入。

| 数据源 | 适用 type | 说明 |
|--------|------|------|
| `[COMPLICATION.TEXT]` | SHORT_TEXT / LONG_TEXT | 主文本（如心率值 "72"） |
| `[COMPLICATION.TITLE]` | SHORT_TEXT / LONG_TEXT | 短标题（如 "bpm"） |
| `[COMPLICATION.MONOCHROMATIC_IMAGE]` / `[COMPLICATION.MONOCHROMATIC_IMAGE_AMBIENT]` | SHORT_TEXT / LONG_TEXT | 单色图标（可作 Image 的 resource） |
| `[COMPLICATION.SMALL_IMAGE]` / `[COMPLICATION.SMALL_IMAGE_AMBIENT]` | SMALL_IMAGE | 小图（可作 Image 的 resource） |
| `[COMPLICATION.IMAGE_STYLE]` | SMALL_IMAGE | 图片样式（PHOTO=1 / ICON=2） |
| `[COMPLICATION.PHOTO_IMAGE]` | PHOTO_IMAGE | 照片 |
| `[COMPLICATION.RANGED_VALUE_VALUE]` | RANGED_VALUE | 当前值 |
| `[COMPLICATION.RANGED_VALUE_MIN]` / `[COMPLICATION.RANGED_VALUE_MAX]` | RANGED_VALUE | 区间上下限 |
| `[COMPLICATION.RANGED_VALUE_COLORS]` / `[COMPLICATION.RANGED_VALUE_COLORS_INTERPOLATE]` | RANGED_VALUE | 颜色列表 / 是否插值 |
| `[COMPLICATION.GOAL_PROGRESS_VALUE]` | GOAL_PROGRESS | 当前进度 |
| `[COMPLICATION.GOAL_PROGRESS_TARGET_VALUE]` | GOAL_PROGRESS | 目标值 |
| `[COMPLICATION.GOAL_PROGRESS_COLORS]` / `[COMPLICATION.GOAL_PROGRESS_COLORS_INTERPOLATE]` | GOAL_PROGRESS | 颜色列表 / 是否插值 |
| `[COMPLICATION.WEIGHTED_ELEMENTS_*]` | WEIGHTED_ELEMENTS | 加权元素（权重/颜色/背景色） |

用法示例：

```xml
<Complication type="SHORT_TEXT">
    <PartText x="0" y="0" width="150" height="80">
        <Text align="CENTER">
            <Font family="SYNC_TO_DEVICE" size="36" weight="BOLD" color="#ff00F5FF">
                <Template>%s
                    <Parameter expression="[COMPLICATION.TEXT]"/>
                </Template>
            </Font>
        </Text>
    </PartText>
</Complication>
```

### 预定义 Metadata

| 数据源 | 说明 |
|--------|------|
| `[PREVIEW_TIME]` | 预览时间（Metadata 中设置） |
| `[CLOCK_TYPE]` | 表盘类型 (DIGITAL/ANALOG) |
| `[STEP_GOAL]` | 步数目标（Metadata 可覆盖） |

---

## 运算符

| 运算符 | 说明 | 示例 |
|--------|------|------|
| `+` `-` `*` `/` | 算术 | `[BATTERY_PERCENT] / 100` |
| `%` | 取模 | `[SECOND] % 2` |
| `~` | 按位取反 | |
| `!` | 逻辑非 | `![BATTERY_IS_LOW]` |
| `\|` | 按位或 | |
| `\|\|` | 逻辑或 | `[BATTERY_IS_LOW] \|\| [BATTERY_PERCENT] < 15` |
| `&` | 按位与 | |
| `&&` | 逻辑与 | `[WEATHER.IS_AVAILABLE] && [WEATHER.IS_DAY]` |
| `>` `>=` `<` `<=` | 比较 | `[BATTERY_PERCENT] >= 80` |
| `==` | 等于 | `[AMPM_STATE] == 1` |
| `? :` | 三元条件 | `[AMPM_STATE] == 1 ? "PM" : "AM"` |
| `(` `)` | 分组 | `([HOUR_0_23] * 15) + ([MINUTE] / 4)` |

---

## 函数

| 函数 | 说明 | 示例 |
|------|------|------|
| `round(x)` | 四舍五入 | `round([BATTERY_PERCENT] / 100 * 360)` |
| `floor(x)` | 向下取整 | `floor([SECOND] / 10) * 10` |
| `ceil(x)` | 向上取整 | |
| `fract(x)` | 小数部分 | |
| `sin(x)` | 正弦（角度） | `sin([SECOND] / 60 * 360)` |
| `cos(x)` | 余弦（角度） | `cos([ACCELEROMETER_ANGLE_X])` |
| `tan(x)` | 正切 | |
| `asin(x)` `acos(x)` `atan(x)` | 反三角 | |
| `abs(x)` | 绝对值 | `abs([ACCELEROMETER_ANGLE_X])` |
| `clamp(x, min, max)` | 钳制范围 | `clamp([BATTERY_PERCENT], 0, 100)` |
| `rand(min, max)` | 随机数 | |
| `log(x)` `log2(x)` `log10(x)` | 对数 | |
| `sqrt(x)` | 平方根 | |
| `cbrt(x)` | 立方根 | |
| `exp(x)` | 指数 | |
| `expm1(x)` | e^x - 1 | |

---

## 表达式使用位置

表达式可用于以下属性（类型为 `arithmeticExpressionType` 的属性）：

- `Transform/@value` — 动态变换（位置/旋转/缩放/透明度）
- `Condition/@expression` — 条件渲染
- `Compare/@expression` — 条件分支
- `Parameter/@expression` — 模板参数
- `Variant/@value` — 变体值
- `Gyro/@x` `@y` `@scaleX` `@scaleY` `@angle` `@alpha` — 陀螺仪响应
- `ScreenReader/@expression` — 无障碍描述
- `Reference/@defaultValue` — 引用默认值

---

## 典型表达式配方

```xml
<!-- 电池百分比文本（真机验证过的写法：Template %s 占位 + Parameter 注入） -->
<PartText x="0" y="400" width="450" height="40">
    <Text align="CENTER">
        <Font family="SYNC_TO_DEVICE" size="28" weight="NORMAL" color="#ff00F5FF">
            <Template>BAT %s%%
                <Parameter expression="[BATTERY_PERCENT]"/>
            </Template>
        </Font>
    </Text>
</PartText>

<!-- 注意：矢量 Arc 的 startAngle/endAngle 只支持静态值，
     动态进度环用 ComplicationSlot type="RANGED_VALUE"（系统渲染） -->

<!-- 低电量变红 -->
<Condition expression="[BATTERY_PERCENT] < 20">
    <Compare expression="1">
        <PartText><Text><Font color="#ffFF4444">低电量</Font></Text></PartText>
    </Compare>
    <Default>
        <PartText><Text><Font color="#ff00F5FF">正常</Font></Text></PartText>
    </Default>
</Condition>

<!-- 12/24 小时自适应 -->
<TimeText format="hh:mm" hourFormat="SYNC_TO_DEVICE" ...>

<!-- 陀螺仪视差 -->
<Gyro x="(5/90) * clamp([ACCELEROMETER_ANGLE_X], -90, 90)" .../>
```

---

## 参考

- 完整数据源枚举见 `data/wff_inventory_v5.json` (`enums` 字段)
- 运算符/函数定义见 XSD `common/simpleTypes/` 下的 `_operatorType` 和 `_functionType`

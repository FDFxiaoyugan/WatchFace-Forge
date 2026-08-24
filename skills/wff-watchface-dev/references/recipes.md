# WFF 表盘配方

> 三种典型表盘的完整 XML 模板。每配方可独立构建。复制 → 改参数 → 构建即用。

---

## 配方 1：极简数字表盘（minimal-digital）

**特征**：大字时间 + 日期 + 电池，Active/AMBIENT 双模式

```xml
<?xml version="1.0"?>
<WatchFace width="450" height="450">
    <Metadata key="CLOCK_TYPE" value="DIGITAL"/>
    <Metadata key="PREVIEW_TIME" value="10:08:32"/>
    <Scene backgroundColor="#ff000000">
        <!-- 数字时钟 -->
        <DigitalClock x="0" y="0" width="450" height="450">
            <!-- Active 模式：亮色大字 -->
            <TimeText format="HH:mm" hourFormat="SYNC_TO_DEVICE"
                      align="CENTER" x="0" y="120" width="450" height="120" alpha="255">
                <Variant mode="AMBIENT" target="alpha" value="0"/>
                <Font family="SYNC_TO_DEVICE" size="100" weight="BOLD" color="#ff00F5FF"/>
            </TimeText>
            <!-- AMBIENT 模式：暗色细字 -->
            <TimeText format="HH:mm" hourFormat="SYNC_TO_DEVICE"
                      align="CENTER" x="0" y="120" width="450" height="120" alpha="0">
                <Variant mode="AMBIENT" target="alpha" value="255"/>
                <Font family="SYNC_TO_DEVICE" size="100" weight="THIN" color="#ff888888"/>
            </TimeText>
        </DigitalClock>

        <!-- 日期 -->
        <PartText x="0" y="260" width="450" height="50">
            <Variant mode="AMBIENT" target="alpha" value="0"/>
            <Text align="CENTER">
                <Font family="SYNC_TO_DEVICE" size="32" weight="NORMAL" color="#ffAAAAAA">
                    <Template>%s/%s
                        <Parameter expression="[MONTH]"/>
                        <Parameter expression="[DAY]"/>
                    </Template>
                </Font>
            </Text>
        </PartText>

        <!-- 电池 -->
        <PartText x="0" y="320" width="450" height="50">
            <Variant mode="AMBIENT" target="alpha" value="0"/>
            <Text align="CENTER">
                <Font family="SYNC_TO_DEVICE" size="28" weight="NORMAL" color="#ffFF6B6B">
                    <Template>BAT %s%%
                        <Parameter expression="[BATTERY_PERCENT]"/>
                    </Template>
                </Font>
            </Text>
        </PartText>
    </Scene>
</WatchFace>
```

---

## 配方 2：模拟指针表盘（analog-hands）

**特征**：时针/分针/秒针 + 刻度环 + AMBIENT 隐藏秒针

```xml
<?xml version="1.0"?>
<WatchFace width="450" height="450">
    <Metadata key="CLOCK_TYPE" value="ANALOG"/>
    <Metadata key="PREVIEW_TIME" value="10:08:32"/>
    <Scene backgroundColor="#ff000000">
        <!-- 表盘背景图 -->
        <PartImage x="0" y="0" width="450" height="450">
            <Image resource="dial_bg"/>
            <Variant mode="AMBIENT" target="alpha" value="40"/>
        </PartImage>

        <!-- 模拟时钟 -->
        <AnalogClock x="0" y="0" width="450" height="450">
            <!-- 时针 -->
            <HourHand x="215" y="100" width="20" height="200"
                      color="#ffFFFFFF" offsetX="225" offsetY="225"/>
            <!-- 分针 -->
            <MinuteHand x="218" y="60" width="14" height="240"
                        color="#ff00F5FF" offsetX="225" offsetY="225"/>
            <!-- 秒针（AMBIENT 隐藏） -->
            <SecondHand x="221" y="40" width="8" height="280"
                         color="#ffFF6B6B" offsetX="225" offsetY="225" alpha="255">
                <Variant mode="AMBIENT" target="alpha" value="0"/>
            </SecondHand>
        </AnalogClock>

        <!-- 中心圆点 -->
        <PartDraw x="0" y="0" width="450" height="450">
            <Fill color="#ff00F5FF">
                <Circle centerX="225" centerY="225" radius="6"/>
            </Fill>
            <Variant mode="AMBIENT" target="alpha" value="0"/>
        </PartDraw>
    </Scene>
</WatchFace>
```

> Hand 的 `offsetX/offsetY` 是旋转中心点。画布 450×450 时中心在 (225, 225)。

---

## 配方 3：混合表盘 + Complication（hybrid-complication）

**特征**：数字时间 + 指针 + 电池弧 + 步数 Complication

```xml
<?xml version="1.0"?>
<WatchFace width="450" height="450">
    <Metadata key="CLOCK_TYPE" value="DIGITAL"/>
    <Metadata key="PREVIEW_TIME" value="10:08:32"/>
    <Scene backgroundColor="#ff111111">
        <!-- 电池弧形进度条 -->
        <PartDraw x="0" y="0" width="450" height="450">
            <Stroke color="#ff333333" thickness="6">
                <Arc centerX="225" centerY="225" width="420" height="420"
                     direction="CLOCKWISE" sweepAngle="360"/>
            </Stroke>
            <Stroke color="#ff00F5FF" thickness="6">
                <Arc centerX="225" centerY="225" width="420" height="420"
                     direction="CLOCKWISE"
                     sweepAngle="round([BATTERY_PERCENT] / 100 * 360)"/>
            </Stroke>
            <Variant mode="AMBIENT" target="alpha" value="30"/>
        </PartDraw>

        <!-- 数字时间 -->
        <DigitalClock x="0" y="0" width="450" height="450">
            <TimeText format="HH:mm" hourFormat="SYNC_TO_DEVICE"
                      align="CENTER" x="0" y="150" width="450" height="100" alpha="255">
                <Variant mode="AMBIENT" target="alpha" value="0"/>
                <Font family="SYNC_TO_DEVICE" size="80" weight="BOLD" color="#ffFFFFFF"/>
            </TimeText>
            <TimeText format="HH:mm" hourFormat="SYNC_TO_DEVICE"
                      align="CENTER" x="0" y="150" width="450" height="100" alpha="0">
                <Variant mode="AMBIENT" target="alpha" value="255"/>
                <Font family="SYNC_TO_DEVICE" size="80" weight="THIN" color="#ff888888"/>
            </TimeText>
        </DigitalClock>

        <!-- 日期 -->
        <PartText x="0" y="250" width="450" height="40">
            <Variant mode="AMBIENT" target="alpha" value="0"/>
            <Text align="CENTER">
                <Font family="SYNC_TO_DEVICE" size="24" weight="NORMAL" color="#ffAAAAAA">
                    <Template>%s, %s %s
                        <Parameter expression="[DAY_OF_WEEK_S]"/>
                        <Parameter expression="[MONTH_S]"/>
                        <Parameter expression="[DAY]"/>
                    </Template>
                </Font>
            </Text>
        </PartText>

        <!-- 步数 Complication -->
        <ComplicationSlot slotId="0" x="150" y="320" width="150" height="80">
            <Complication type="SHORT_TEXT"
                          defaultProvider="STEP_COUNT"
                          primaryDataStyle="ICON_AND_TEXT"
                          primaryDataSource="STEP_COUNT"
                          fallbackBehavior="EMPTY"/>
            <Variant mode="AMBIENT" target="alpha" value="30"/>
        </ComplicationSlot>
    </Scene>
</WatchFace>
```

---

## 配方变体速查

### 添加 AOD（息屏）模式

每个可见元素加一个 AMBIENT 变体控制显隐/透明度：

```xml
<!-- Active 元素：AMBIENT 时隐藏 -->
<PartText alpha="255">
    <Variant mode="AMBIENT" target="alpha" value="0"/>
</PartText>

<!-- Ambient 元素：AMBIENT 时显示 -->
<PartText alpha="0">
    <Variant mode="AMBIENT" target="alpha" value="255"/>
</PartText>
```

### 添加陀螺仪视差

```xml
<PartImage x="0" y="0" width="450" height="450">
    <Image resource="bg"/>
    <Gyro x="(10/90) * clamp([ACCELEROMETER_ANGLE_X], -90, 90)"
          y="(10/90) * clamp([ACCELEROMETER_ANGLE_Y], -90, 90)"/>
</PartImage>
```

### 条件渲染（低电量变色）

```xml
<Condition expression="[BATTERY_PERCENT] < 20">
    <Compare expression="1">
        <Font color="#ffFF4444">低电量</Font>
    </Compare>
    <Default>
        <Font color="#ff00F5FF">正常</Font>
    </Default>
</Condition>
```

### 用户自定义颜色

```xml
<!-- 在 UserConfigurations 中定义 -->
<UserConfiguration id="accent_color" type="Color" displayName="强调色"/>

<!-- 在元素中引用 -->
<Font color="[CONFIGURATION.accent_color]">10:08</Font>
```

### 动态旋转（秒针平滑动画）

```xml
<SecondHand x="221" y="40" width="8" height="280" 
            color="#ffFF6B6B" offsetX="225" offsetY="225">
    <Transform value="rotate(([SECOND] + [MILLISECOND]/1000) / 60 * 360)"/>
    <Sweep frequency="SYNC_TO_DEVICE"/>
</SecondHand>
```

---

## project.yaml 配套配置

```yaml
package_name: com.example.mywatchface
version_code: 1
version_name: "1.0"
watch_face_name: My Watch Face
wff_version: 1              # 1=Wear OS 4 (minSdk 33), 2+=Wear OS 5+ (minSdk 34)
```

## 构建流程

```bash
# 初始化项目
python wff-builder/wff_builder.py init projects/my_watch

# 验证 (16 条规则 + XSD)
python wff-builder/wff_builder.py validate projects/my_watch

# 构建 APK
python wff-builder/wff_builder.py build projects/my_watch

# 或通过平台 API（需要平台就绪）
python skills/wff-watchface-dev/client/wff_api.py build projects/my_watch
```

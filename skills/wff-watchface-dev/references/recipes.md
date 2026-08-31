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
            <TimeText format="hh:mm" hourFormat="SYNC_TO_DEVICE"
                      align="CENTER" x="0" y="120" width="450" height="120" alpha="255">
                <Variant mode="AMBIENT" target="alpha" value="0"/>
                <Font family="SYNC_TO_DEVICE" size="100" weight="BOLD" color="#ff00F5FF"/>
            </TimeText>
            <!-- AMBIENT 模式：暗色细字 -->
            <TimeText format="hh:mm" hourFormat="SYNC_TO_DEVICE"
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

**特征**：时针/分针/秒针 + AMBIENT 隐藏秒针
**前置**：三针各需一张 PNG（Pillow 生成：细长矩形+透明底，指针指向 12 点，
pivot 画在针的旋转中心）。`resource` 指向 res/drawable 下的图片名（不带扩展名）。

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

        <!-- 模拟时钟（三针必须 resource 引用图片，无 color 属性；tintColor 染色可选） -->
        <AnalogClock x="0" y="0" width="450" height="450">
            <!-- 时针 -->
            <HourHand resource="hand_hour" x="215" y="100" width="20" height="200"
                      pivotX="0.5" pivotY="1.0" tintColor="#ffffffff"/>
            <!-- 分针 -->
            <MinuteHand resource="hand_minute" x="218" y="60" width="14" height="240"
                        pivotX="0.5" pivotY="1.0" tintColor="#ff00F5FF"/>
            <!-- 秒针（10Hz 平滑扫秒；AMBIENT 隐藏） -->
            <SecondHand resource="hand_second" x="221" y="40" width="8" height="280"
                        pivotX="0.5" pivotY="1.0" tintColor="#ffFF6B6B" alpha="255">
                <Variant mode="AMBIENT" target="alpha" value="0"/>
                <Sweep frequency="10"/>
            </SecondHand>
        </AnalogClock>

        <!-- 中心圆点（矢量，形状包住样式） -->
        <PartDraw x="0" y="0" width="450" height="450">
            <Ellipse x="219" y="219" width="12" height="12">
                <Fill color="#ff00F5FF"/>
            </Ellipse>
            <Variant mode="AMBIENT" target="alpha" value="0"/>
        </PartDraw>
    </Scene>
</WatchFace>
```

> Hand 的 `pivotX/pivotY` 是旋转中心（归一化 0~1，相对针自身包围盒）。
> 12 点方向竖直针的 pivot 在底端中心：`pivotX="0.5" pivotY="1.0"`。

---

## 配方 3：混合表盘 + Complication（hybrid-complication）

**特征**：数字时间 + 指针 + 电池弧 + 步数 Complication

```xml
<?xml version="1.0"?>
<WatchFace width="450" height="450">
    <Metadata key="CLOCK_TYPE" value="DIGITAL"/>
    <Metadata key="PREVIEW_TIME" value="10:08:32"/>
    <Scene backgroundColor="#ff111111">
        <!-- 装饰环（静态矢量弧；动态进度环用 ComplicationSlot RANGED_VALUE，Arc 角度不支持表达式） -->
        <PartDraw x="0" y="0" width="450" height="450">
            <Arc centerX="225" centerY="225" width="420" height="420"
                 direction="CLOCKWISE" startAngle="0" endAngle="360">
                <Stroke color="#ff333333" thickness="6"/>
            </Arc>
            <Arc centerX="225" centerY="225" width="420" height="420"
                 direction="CLOCKWISE" startAngle="0" endAngle="180">
                <Stroke color="#ff00F5FF" thickness="6"/>
            </Arc>
            <Variant mode="AMBIENT" target="alpha" value="30"/>
        </PartDraw>

        <!-- 数字时间 -->
        <DigitalClock x="0" y="0" width="450" height="450">
            <TimeText format="hh:mm" hourFormat="SYNC_TO_DEVICE"
                      align="CENTER" x="0" y="150" width="450" height="100" alpha="255">
                <Variant mode="AMBIENT" target="alpha" value="0"/>
                <Font family="SYNC_TO_DEVICE" size="80" weight="BOLD" color="#ffFFFFFF"/>
            </TimeText>
            <TimeText format="hh:mm" hourFormat="SYNC_TO_DEVICE"
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

        <!-- 步数 Complication（supportedTypes 必填 + BoundingShape 必填 + DefaultProviderPolicy 设默认源） -->
        <!-- ⚠️ Complication 内必须有 Part 渲染组件 + [COMPLICATION.*] 数据绑定，空元素真机不渲染（R26） -->
        <ComplicationSlot x="150" y="320" width="150" height="80"
                          slotId="0" supportedTypes="SHORT_TEXT"
                          isCustomizable="TRUE">
            <BoundingRoundBox x="150" y="320" width="150" height="80"
                              cornerRadius="10" outlinePadding="2"/>
            <DefaultProviderPolicy defaultSystemProvider="STEP_COUNT"
                                   defaultSystemProviderType="SHORT_TEXT"/>
            <Complication type="SHORT_TEXT">
                <!-- 局部坐标：0,0 = slot 左上角 -->
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

### 动态旋转（指针平滑动画）

秒针本体已自动随时间旋转，**不要**再叠加 rotate Transform（会双倍旋转）。
平滑扫秒用 Sweep：

```xml
<SecondHand resource="hand_second" x="221" y="40" width="8" height="280"
            pivotX="0.5" pivotY="1.0" tintColor="#ffFF6B6B">
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

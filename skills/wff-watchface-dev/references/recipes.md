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

        <!-- 模拟时钟（三针必须 resource 引用图片，无 color 属性；tintColor 染色可选）
             📐 旋转中心 = (x+pivotX·w, y+pivotY·h) 必须精确等于圆心 (225,225)
             （盲测 Round 2 修正 2026-09-06：旧配方坐标反推旋转中心在 (225,300)，错误） -->
        <AnalogClock x="0" y="0" width="450" height="450">
            <!-- 时针：中心 (214+11, 110+115) = (225,225) ✓ -->
            <HourHand resource="hand_hour" x="214" y="110" width="22" height="115"
                      pivotX="0.5" pivotY="1.0" tintColor="#ffffffff"/>
            <!-- 分针：中心 (217+8, 60+165) = (225,225) ✓ -->
            <MinuteHand resource="hand_minute" x="217" y="60" width="16" height="165"
                        pivotX="0.5" pivotY="1.0" tintColor="#ffededf2"/>
            <!-- 秒针：细+红，带配重尾部（图高 235 = 针长 195 + 尾 40，
                 pivotY = 195/235 ≈ 0.8298）；10Hz 平滑扫秒；AMBIENT 隐藏 -->
            <SecondHand resource="hand_second" x="221" y="30" width="8" height="235"
                        pivotX="0.5" pivotY="0.8298" tintColor="#ffff3b30" alpha="255">
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
>
> 📐 **旋转中心必须精确落在表盘圆心**：`(x + pivotX·w, y + pivotY·h) = (圆心x, 圆心y)`。
> 12 点竖直针：`x = 圆心x − w/2`，`y = 圆心y − 针长`。
> 带配重尾部（尾悬在旋转中心下方）：`pivotY = 针长 / 图片总高`。
>
> ⚠️ **指针 PNG 左右 alpha 必须对称（R31）**：PIL `ImageDraw` 在偶数宽度画布上
> inclusive 右边界导致抗锯齿不对称（+0.16px 质心偏移），细秒针肉眼可见错位。
> 修复：奇数宽度画布或精确光栅化（半开区间）。交付前校验：
> `alpha 质心 x == width/2`（`sum(x·a)/sum(a)`，逐像素算）。
> 指针素材生成脚本参考 BT-02 交付（4× 超采样 + 扫描线精确光栅化）。

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

        <!-- 步数 Complication（supportedTypes 必填 + BoundingShape 局部坐标必填 + DefaultProviderPolicy 设默认源） -->
        <!-- ⚠️ R26: Complication 内必须有 Part 渲染组件 + [COMPLICATION.*] 数据绑定，空元素真机不渲染 -->
        <!-- ⚠️ R28: BoundingRoundBox 用 slot 局部坐标（0,0 起），不是全局画布坐标 -->
        <ComplicationSlot x="150" y="320" width="150" height="80"
                          slotId="1" supportedTypes="SHORT_TEXT EMPTY"
                          displayName="@string/complication_slot_display"
                          isCustomizable="TRUE">
            <BoundingRoundBox x="0" y="0" width="150" height="80"
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
            <Complication type="EMPTY">
                <PartText x="0" y="24" width="150" height="32">
                    <Text align="CENTER">
                        <Font family="SYNC_TO_DEVICE" size="20" weight="NORMAL" color="#ff7E93A8">--</Font>
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
<!-- R32: 算式在 Expression 文本 + Compare 按 name 引用；
     "低于 20" 反转写 20 > [BATTERY_PERCENT]（无 < 运算符） -->
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
            <Text align="CENTER"><Font family="SYNC_TO_DEVICE" size="28" color="#ff00F5FF">[BATTERY_PERCENT]%</Font></Text>
        </PartText>
    </Default>
</Condition>
```


### 商务风（business）——BT-05 真机验证交付沉淀

适用：抬腕全彩信息 + AOD 极简。核心是**字号层级 + 金色点缀 + 大留白**：

- 布局骨架：时间 size 84-100 BOLD（y≈110）→ 日期 size 28-30 灰（y≈240）→
  数据（步数等）size 44-52 BOLD（y≈310）→ 底部装饰细线
- 配色：黑底 `#ff0a0d12` 系 + 白字 `#ffededf2` + 点缀金 `#ffFFC940`（唯一彩色，
  只用于装饰线/标签，不用在大面积元素上）
- AMBIENT 策略：双 TimeText 交换（active 时间 alpha=255→0，ambient 时间 0→255，
  ambient 版变灰）；日期/数据/装饰整体 `Variant value="0"` 隐藏（挂 PartDraw 更简洁）
- AOD 只留时间 = 省电核心；风格一致靠 ambient 时间坐标与 active 完全重合

### preview.png 镜像渲染要点（Pillow 自绘时）

> R24 说"Pillow 自绘兜底"，但预览图与 XML **布局/颜色/角度对齐**有坑：

1. **弧线角度坐标系**：WFF `startAngle` 0°=12 点方向顺时针；PIL `arc()` 的
   start/end 是数学角度（0°=3 点方向逆时针）。映射：`pil_start = wff_angle - 90`
   （再注意 PIL 逆时针 vs WFF CLOCKWISE 的方向反转）。BT-05 用
   `end=start+arc_deg` 画进度弧对齐成功
2. **字体渲染**：Pillow 默认字体无 BOLD——用 `ImageFont.truetype` 加粗体字库
   （如 NotoSansSC-Bold），否则预览图比真机细一圈
3. **逐元素镜像**：按 XML 的 x/y/width/height + align 逐个画；CENTER 对齐的
   文本要 measure 后居中，别用默认 anchor
4. 预览图是静态印象分——与真机渲染有亚像素差异是正常的，但**大方向（角度/
   布局/配色）必须一致**，否则用户预期错位

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

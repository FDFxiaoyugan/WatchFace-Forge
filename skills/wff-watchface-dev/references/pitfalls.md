# WFF 踩坑大全

> 一期 16 条规则（2026-08-15 真机验证）+ 盲测/真机复盘扩充至 32 条（R17-R32）。
> **每条规则都是用真机安装失败换来的。写 WFF XML 前必读。**

---

## 🔴 MUST 规则（违反 = 构建失败 / 真机不显示）

### R01: WatchFace 根元素必须有 width + height

```xml
<!-- ❌ -->
<WatchFace>
<!-- ✅ -->
<WatchFace width="450" height="450">
```

常见画布尺寸：384×384（Pixel Watch 1）、450×450（Pixel Watch 2/Galaxy Watch 6+）

### R02: 必须有 Metadata CLOCK_TYPE

```xml
<Metadata key="CLOCK_TYPE" value="DIGITAL"/>
<!-- 或 value="ANALOG" -->
```

### R03: 必须有 Metadata PREVIEW_TIME

```xml
<Metadata key="PREVIEW_TIME" value="10:08:32"/>
```

预览时间影响表盘在手表选择器中的截图。

### R05: 数据源表达式必须用方括号

```xml
<!-- ❌ 编译不报错，但运行时不显示 -->
<Parameter expression="MONTH"/>
<Parameter expression="BATTERY_PERCENT"/>

<!-- ✅ -->
<Parameter expression="[MONTH]"/>
<Parameter expression="[BATTERY_PERCENT]"/>
```

### R06: WFF v1 不支持 clipShape

```xml
<!-- ❌ WFF v1 报错 -->
<WatchFace width="450" height="450" clipShape="CIRCLE">

<!-- ✅ 不写 clipShape，系统默认圆形裁剪 -->
<WatchFace width="450" height="450">
```

> 注意：XSD v5 中 `clipShape` 有 `NONE/CIRCLE/RECTANGLE` 枚举，但 WFF v1 运行时不支持。v2+ 可用。

### R08: 颜色必须用 8 位 ARGB

```xml
<!-- ❌ 6 位在部分设备渲染为透明 -->
<Font color="#00F5FF">
<Stroke color="#FF6B6B">

<!-- ✅ 8 位 ARGB，前两位 = alpha -->
<Font color="#ff00F5FF">
<Stroke color="#ffFF6B6B">
```

格式：`#AARRGGBB`，`ff` = 不透明，`00` = 全透明

### R09: 时间显示必须用 DigitalClock + TimeText

```xml
<!-- ❌ Text + Template 不自动刷新时间 -->
<PartText><Text><Template>%s:%s<Parameter expression="[HOUR]"/>...</Template></Text></PartText>

<!-- ✅ DigitalClock + TimeText 自动刷新 -->
<DigitalClock x="0" y="0" width="450" height="450">
    <TimeText format="hh:mm" hourFormat="SYNC_TO_DEVICE" align="CENTER" 
              x="0" y="120" width="450" height="120">
        <Font family="SYNC_TO_DEVICE" size="100" weight="BOLD" color="#ff00F5FF"/>
    </TimeText>
</DigitalClock>
```

### R11: 用 expression= 而非 source=

```xml
<!-- ❌ -->
<Parameter source="MONTH"/>
<!-- ✅ -->
<Parameter expression="[MONTH]"/>
```

### R12: Parameter 必须用 expression=

```xml
<!-- ❌ -->
<Parameter source="BATTERY_PERCENT"/>
<!-- ✅ -->
<Parameter expression="[BATTERY_PERCENT]"/>
```

### R14: Template 中 %s 数量必须与 Parameter 数量匹配

```xml
<!-- ❌ 2 个 %s 但只有 1 个 Parameter -->
<Template>%s/%s<Parameter expression="[MONTH]"/></Template>

<!-- ✅ -->
<Template>%s/%s<Parameter expression="[MONTH]"/><Parameter expression="[DAY]"/></Template>
```

### R16: 不需要 WatchFaceService 声明

```xml
<!-- ❌ WFF APK 是纯资源包，hasCode=false，不含代码 -->
<service android:name=".WatchFaceService">
    <intent-filter>
        <action android:name="android.service.wallpaper.WallpaperService"/>
    </intent-filter>
</service>

<!-- ✅ 什么都不写，AndroidManifest.xml 只需 meta-data -->
```

---

## 🟡 SHOULD 规则（违反 = 警告，但可构建）

### R04: Scene 应有 backgroundColor

```xml
<!-- ⚠️ 缺省时背景可能透明 -->
<Scene>

<!-- ✅ -->
<Scene backgroundColor="#ff000000">
```

### R07: 字体 family 应为 SYNC_TO_DEVICE

```xml
<!-- ⚠️ Roboto 在部分设备可能缺失 -->
<Font family="Roboto" size="100"/>

<!-- ✅ -->
<Font family="SYNC_TO_DEVICE" size="100"/>
```

### R10: 应有 ambient Variant

表盘在 AOD（Always-On Display）模式下应降低亮度和刷新率：

```xml
<TimeText format="hh:mm" ... alpha="255">
    <!-- Active 模式：alpha=255, AMBIENT 时变 0 -->
    <Variant mode="AMBIENT" target="alpha" value="0"/>
    <Font family="SYNC_TO_DEVICE" size="100" weight="BOLD" color="#ff00F5FF"/>
</TimeText>

<!-- Ambient 版本：平时 alpha=0, AMBIENT 时变 255 -->
<TimeText format="hh:mm" ... alpha="0">
    <Variant mode="AMBIENT" target="alpha" value="255"/>
    <Font family="SYNC_TO_DEVICE" size="100" weight="THIN" color="#ff888888"/>
</TimeText>
```

### R13: 使用已知数据源名称

完整数据源列表见 [expressions.md](./expressions.md)。常用：`[HOUR_0_23_Z]` `[MINUTE_Z]` `[SECOND_Z]` `[BATTERY_PERCENT]` `[STEP_COUNT]` `[HEART_RATE]` `[MONTH]` `[DAY_Z]`

### R15: 数字时间优先用 DigitalClock

见 R09。

### R17: 形状包住样式，不是样式包住形状（盲测 BT-03 实证）

正确：`<Arc><Stroke color="..." thickness="..."/></Arc>`（Stroke/Fill 是形状的**子元素**）。
错误：`<Stroke><Arc/></Stroke>`。后者真机可能宽容渲染，但过不了官方 XSD 校验。

### R18: TimeText format 只接受小写 h/m/s（盲测 BT-03 实证）

XSD `timeFormatType` pattern 只匹配小写组合（`h`/`hh`/`m`/`mm`/`s`/`ss`）。
`HH:mm` 非法（真机宽容，官方校验拒绝）。12/24 小时制由 `hourFormat` 属性控制。

### R19: 列表属性用空格分隔，不用逗号（盲测 BT-03 实证）

`colors="#ff03050B #ff071629 #ff0E2C55"`、`positions="0.0 0.5 1.0"`、
`supportedTypes="SHORT_TEXT RANGED_VALUE"` —— 全部空格分隔（XSD `xs:list`）。

### R20: BoundingShape 不可直接写，必须用具体替换组成员（盲测 BT-03 实证）

`<BoundingShape>` 是抽象头。用 `<BoundingBox>` `<BoundingRoundBox>`（最常用）
`<BoundingOval>` `<BoundingArc>`，且几何属性必填。ComplicationSlot 的
`supportedTypes` 必填；`<Complication>` 子元素至少 1 个。

### R21: booleanType 枚举是大写 TRUE/FALSE

`isCustomizable="TRUE"` 合法，`"true"` 非法。XSD 自定义枚举，不是 xs:boolean。

### R22: 16 规则 validate ≠ XSD 合法，官方校验才是终审（盲测 BT-03 实证）

wff_builder 规则抓不住 XSD 级错误（嵌套方向/枚举值/pattern 全漏）。
**交付前必须跑官方 validator**（见 SKILL.md 工作流第 3 步），内置规则只当初筛。

### R23: project.yaml 不要写行内注释

`wff_version: 1  # 注释` 会被 yaml 解析器把注释内容泄漏进 manifest 字符串。

### R24: build 需要 preview.png，init 不自动生成

无位图素材时用 Pillow 自绘一张 384×384 PNG 兜底（尺寸要求见 init 输出文本）。

### R25: 三针必须图片资源，无 color 属性（文档纠错）

HourHand/MinuteHand/SecondHand 的 `resource` 必填（指向 res/drawable 图片），
只有 `tintColor`（染色）没有 `color`。纯矢量指针不可行——用 Pillow 生成针形 PNG
（细长矩形、透明底、指向 12 点）。秒针可选 `<Sweep frequency="2|5|10|15"/>`
平滑扫秒或 `<Tick strength duration/>` 跳动动画。

### R26: 空 `<Complication/>` 合法但真机渲染为空（真机实证 2026-08-31，BT-03 复盘）

XSD 允许 `<Complication type="SHORT_TEXT"/>` 空元素（choice minOccurs=0），官方
validator 也放行——但没有任何 Part 组件就**什么都不画**。三级验证（16 规则 +
XSD + build）全部抓不住这种"合法但空白"。正确写法：

- Complication 内放 PartText/PartImage/PartDraw（坐标为 slot 局部系，0,0=slot 左上角）
- provider 数据用特殊数据源绑定：`[COMPLICATION.TEXT]` `[COMPLICATION.TITLE]`
  `[COMPLICATION.MONOCHROMATIC_IMAGE]` 等（完整表见 elements.md）
- BoundingShape 只是点击区域，不渲染视觉内容；边框底板要自己用 PartDraw 画
- 文本绑定官方写法：`<Template>%s<Parameter expression="[COMPLICATION.TEXT]"/></Template>`

### R27: 矢量 RoundRectangle 用 cornerRadiusX/cornerRadiusY（真机实证 2026-08-31）

`<RoundRectangle cornerRadiusX="14" cornerRadiusY="14"/>` 两属性**必填**；
单一 `cornerRadius` 是 BoundingRoundBox（complication 边界）的属性，矢量圆角矩形
没有——两处易混。

### R28: BoundingShape 用 slot 局部坐标，写全局坐标槽位整体消失（真机实证 2026-08-31 第二轮）

官方示例：slot `x="100" y="100"` 的 BoundingOval 写 `x="0" y="0"`——边界形状
坐标系是 **slot 左上角原点**，不是画布原点。把 slot 的全局坐标抄进 BoundingShape
（如 slot 140,328 + Bounding 140,328）会让边界区域落到画布外，症状：
- 槽位不渲染（内容画的坐标是对的，但边界在画布外被裁/剔除）
- **长按表盘不出现自定义入口**（编辑器认为无可编辑槽位）
- 表盘选择器预览图正常（那是静态 preview.png，与实时渲染无关）

正确写法：`<BoundingRoundBox x="0" y="0" width="{slot宽}" height="{slot高}"/>`。
注意 Complication 子元素同样是局部坐标（这个 v0.2.1 文档写对了，BoundingShape 抄错了）。

### R29: Template 至少一个 Parameter；静态文本直接放 Font（XSD 强制）

`<Template>--</Template>` 无 Parameter 非法（官方 XSD: content of 'Template' is
not complete）。EMPTY 占位等静态文本直接写 `<Font ...>--</Font>`（Font 是
mixed=true）——**但 Font 必须在 `<Text>` 内**（R39：`PartText > Text > Font`
三层，直挂 PartText 被 validator 拒）。无数据兜底还可以用
`<Complication type="EMPTY">` 渲染占位符（supportedTypes 加 EMPTY）。

### R30: ComplicationSlot displayName 用**裸资源名**，不是 @string/ 引用（R30 结论反转，真机复测 2026-09-09）

> ⚠️ 本条曾写"必须是 @string/ 资源引用"（2026-08-31 第一版），方向反了。
> 2026-09-09 P2 四轮单变量迭代复测证明 @string/ 无效，裸资源名才对。

`res/raw/watch_face.xml` 与 `res/xml/watch_face_info.xml` **不经 aapt2 编译**，
`@string/xxx` 在这些文件里只是字面量字符串，WFF 运行库按资源名自查 arsc——
所以 displayName 直接写裸名 `theme_color`：

```xml
<!-- ✅ 正确: 裸资源名, WFF 库按名自查 -->
<ColorConfiguration id="themeColor" displayName="theme_color" ...>
<ComplicationSlot ... displayName="slot_heart_rate" ...>
<!-- ❌ 错误: res/raw|xml 里 @string/ 是字面量, 查不到 -->
<ColorConfiguration id="themeColor" displayName="@string/theme_color" ...>
```

配套修复（维持有效）：
- 字符串资源仍放项目 `res/values/strings.xml`（builder 合并进 arsc），元素
  `displayName` 值与资源名一致
- `slotId` 官方 samples 从 **0** 开始（Flavors/Complications 一致；类型 xs:string 无
  数值约束，从 1 也合法）；XSD `xs:unique` 强制全局唯一。配套：Slot 数量上限 **8**
  （Scene maxOccurs=8，R38）
- 官方教程与 samples（android/wear-os-samples/WatchFaceFormat）全部实证裸名写法

### R31: 指针 PNG 左右 alpha 必须对称（真机实证 2026-09-06，盲测 Round 2）

PIL `ImageDraw` 的 `rectangle/polygon` 右边界是 inclusive——偶数宽度画布上画细线，
右侧多占 1 个超采样像素，LANCZOS 缩放放大不对称 → alpha 质心偏移 +0.163px。
`pivotX=0.5` 绕图片几何中心旋转，但视觉轴线在质心处——秒针旋转后不经过表盘圆心，
细秒针上肉眼可见错位（时针分针主体粗处对称，只在尖端细处偏 +0.5px，不易察觉）。

修复（任选一）：
- 奇数宽度画布（宽度中心落在整数像素上）
- 精确光栅化：半开区间 `[x0, x1)` + 像素中心采样 + 扫描线算法 + BOX 降采样

交付前校验：`质心x = sum(x·alpha)/sum(alpha) == width/2`，逐行 alpha 序列左右对称。
参考实现：BT-02 交付（4× 超采样 + 扫描线，hand_second 8 宽行 alpha [0,0,127,255,255,127,0,0] 完全对称）。


### R32: Condition 无 expression 属性；算式在 Expression 文本、Compare 按 name 引用；无 `<` 运算符（XSD 实证 2026-09-07）

官方 XSD（v5 `common/conditionElement.xsd` + keyref）真实结构：

```xml
<Condition>
  <Expressions>
    <Expression name="battery_low">20 > [BATTERY_PERCENT]</Expression>
  </Expressions>
  <Compare expression="battery_low">…Part…</Compare>
  <Default>…Part…</Default>   <!-- 可选兜底 -->
</Condition>
```

三个易错点（旧知识层三处全错，盲测 Round 3 前修正）：
1. `Condition` **没有** `expression` 属性——算式只能定义在 `Expressions/Expression` 的文本内容
2. `Compare/@expression` 是对 `Expression/@name` 的**引用**（XSD keyref 强制校验），不是算式本身
3. 运算符枚举只有 `>` `>=` `==`（XSD `_operatorType`：+ - * / % ~ ! | || & && ( ) > >= ? : ==）
   ——**没有 `<` `<=`**。"<20" 必须反转写 `20 > [BATTERY_PERCENT]`（`<` 也是 XML 非法字符）
首个命中的 Compare 渲染，其余不渲染；全不命中走 Default。已验证示例过 wff-validator v5。

### R33: watch_face_info.xml 必须含 `<Editable value="true"/>`——编辑器自定义按钮总开关（真机实证 2026-09-09 P2 破案）

One UI 表盘编辑器「自定义」按钮的**唯一开关**是 `res/xml/watch_face_info.xml` 里的：

```xml
<WatchFaceInfo>
    <Preview value="@drawable/preview" />
    <Editable value="true" />
</WatchFaceInfo>
```

关键行为（P2 悬案四轮单变量迭代定位：wff_version=2 无效 → displayName 裸名无效 →
watch_face_info.xml 加 Editable **破案**）：
- 缺失 Editable：表盘渲染/选择/安装全正常，**仅编辑器不出现自定义入口**——
  之前所有悬案（R30 无效、UserConfigurations 无效、wff_version 无效）的真正根因
- 有 Editable 无 UserConfigurations：按钮出现但编辑页无选项（ArcLab 实证）——
  按钮由 Editable 决定，**选项内容由 UserConfigurations 决定**
- 有 Editable + ColorConfiguration：按钮出现 + 颜色三选 + 选中全局变色（P2 终版实证）

builder `build` 自动生成含 Editable 的 watch_face_info（v0.4.0 起模板内置）；
`validate` 的 R33 检查项目自带文件：文件存在但缺 Editable = error，无文件 = warn。
官方 samples：`android/wear-os-samples/WatchFaceFormat`。

### R34: 圆屏只显示画布内切圆——顶层元素贴边会被切（真机实证 2026-09-10，P2 拱顶被切数像素）

450×450 画布映射圆屏后，可见区域是**内切圆**（中心 225,225，半径 225）。
四角区域完全不可见；竖直方向顶部 y<25 / 底部 y>425 的水平窄条也基本被切
（弦长公式：距边缘 dy 的水平可用宽度 = 2·√(225² − (225−dy)²)）。

| 元素位置 | 是否被切 | 判断 |
|---|---|---|
| 顶部窄条 (0,0,450,80) | ❌ 四角全灭 | 角到中心距离 √(225²+145²)=267 > 225 |
| 顶部居中 (105,8,240,72) | ⚠️ 角溢出 23px | √(120²+217²)=248 > 225（P2 真机现象） |
| 中央 (105,189,240,72) | ✅ | 262 ≤ 225×安全系数… 角距 137 |

校验：`wff_builder validate` R34 自动检查 Scene 直接子元素 bbox 四角到中心距离。
设计准则：贴顶/贴底元素压在 y=25..425 内并收窄宽度；弧线/圆环沿内切圆布置天然安全。

### R35: Arc 的 centerX/centerY 是 PartDraw 局部坐标——椭圆溢出容器被裁成"斜线"（真机实证 2026-09-10 斜线悬案）

Arc 椭圆几何（centerX/centerY/width/height）是**父 PartDraw 的局部坐标系**，
(0,0) = 容器左上角。椭圆 bbox 超出容器边界的弧段**直接被裁剪**——真机表现为
"弧度很小、像一条斜线"（实际是上半拱的左半段，右半段溢出被裁）。

```xml
<!-- ❌ 斜线悬案原版: 椭圆中心 (225,30) 偏离容器中心 (160,22), 右半拱溢出 320 宽容器 -->
<PartDraw x="65" y="8" width="320" height="44">
    <Arc centerX="225" centerY="30" width="320" height="44" startAngle="-90" endAngle="90"/>

<!-- ✅ 居中椭圆: centerX=容器宽/2, centerY=容器高/2 -->
<PartDraw x="105" y="8" width="240" height="72">
    <Arc centerX="120" centerY="36" width="240" height="72" startAngle="-90" endAngle="90"/>
```

校验：`wff_builder validate` R35 自动比对每对 (PartDraw 容器, 内部 Arc bbox)。
同族坑（R28 BoundingShape 局部坐标）：WFF 的子元素坐标一律相对最近容器， Complication 子元素同理。

### R36: Arc 角度语义——0°=12点方向，顺时针为正，负角度合法（像素级五发全中实证 2026-09-09 ArcLab）

XSD 只说 startAngle/endAngle 是角度数值，语义靠实验锁定（ArcLab 对照表盘，
像素聚类分析每道弧的实际象限）：

| XML 参数 | 渲染弧段 | 开口朝向 |
|---|---|---|
| `0 → 90` | 12点 → 3点（右上四分之一） | 左下 |
| `90 → 180` | 3点 → 6点（右下四分之一） | 左上 |
| `180 → 270` | 6点 → 9点（左下四分之一） | 右上 |
| `270 → 360` | 9点 → 12点（左上四分之一） | 右下 |
| **`-90 → 90`** | **上半拱（跨 0°，12点对称）** | **下** ✓ |
| `180 → 360` | 左半弧（C 形） | 右 |

三个要点：
1. **0° = 12 点方向**（不是数学惯用的 3 点/右方向），**顺时针为正**
2. **负角度合法**——`startAngle="-90" endAngle="90"` 跨 0° 画上半拱，官方电量环
   用 `-150 → 150` 缺口朝下
3. `cap="ROUND"`（圆头端点）官方 sample 在用，安全

易错：想要"时间上方拱形"写成 `180→360`（得到 C 形左半弧）——上半拱是 `-90→90`。

### R37: List/Boolean 配置有**两套模式**，id 两边必须对应（XSD 引用链 + Flavors sample 实证 2026-09-10）

XSD 引用链实证：主 schema include 的 `userConfigurationsElement.xsd`（容器版）
与 Scene/Group/指针 include 的 `booleanConfigurationElement.xsd`/
`listConfigurationElement.xsd`（渲染版）**两套并存**——这与 Color 不同
（Color 的独立 element 版是废弃的，Boolean/List 的渲染版是活跃的）：

| | 容器版（UserConfigurations 内） | 渲染版（Scene/Group/Hand 内） |
|---|---|---|
| 职责 | **编辑器 UI 元数据** | **每选项的渲染内容** |
| ListConfiguration | 必填 id/displayName/defaultValue；ListOption 纯属性（id + displayName/icon/complicationSlotIds/childSettingIds） | 只写 id；ListOption id + **内嵌完整部件**（Part/Group/Condition/Clock） |
| BooleanConfiguration | 纯属性（id/displayName/defaultValue/icon），**无子元素** | 只写 id；BooleanOption id="TRUE\|FALSE" + 内嵌部件 |
| 数量 | 每配置一次 | 同 id 的配置可在多处挂（每处渲染自己的内容） |

三个易错点：
1. **id 必须两边一致**——容器版定义选项列表（编辑器显示），渲染版按 id 匹配
   选项渲染内容。渲染版出现容器版没有的 ListOption id = 无效
2. **Boolean 渲染版可以只放 TRUE 一个 BooleanOption**（官方 Flavors sample 的
   showHr 即此）——FALSE 状态=该处不渲染，天然"开关显隐"
3. ListOption 的 `complicationSlotIds` 属性（容器版）：选中该选项时才启用对应
   complication 槽位——风格联动槽位显隐的官方机制

完整示例（过 wff-validator v5）见 recipes.md §4 组件包配方。

### R38: ComplicationSlot 上限 8 个、slotId 全局唯一、slotId 从 0 开始（XSD 实证 2026-09-10）

- Scene 内 `ComplicationSlot` **maxOccurs=8**（sceneElement.xsd）
- `slotId` 是 `xs:string`（无数值约束），XSD `xs:unique` 强制唯一
- 官方 samples（Flavors/Complications）slotId 全部从 **0** 开始——旧说法
  "从 1 开始（官方示例惯例）"是错的，已修正
- `BoundingOval/RoundBox` 支持 `outlinePadding`（编辑器选中描边内边距）

### R39: PartText 文本是三层结构 `PartText > Text > Font`（XSD v1/v5 一致，validator 强制）

```xml
<!-- ✅ 正确: Text 是 TextElement 的具体替换成员 -->
<PartText x="0" y="0" width="90" height="90" tintColor="[CONFIGURATION.themeColor.0]">
    <Text align="CENTER" ellipsis="TRUE">
        <Font family="SYNC_TO_DEVICE" size="24">
            <Template><![CDATA[%s]]>
                <Parameter expression="[COMPLICATION.TEXT]"/>
            </Template>
        </Font>
    </Text>
</PartText>
<!-- ❌ Font 直挂 PartText: 渲染器可能宽容, 但 wff-validator 拒绝 -->
```

- `PartText` 可用 `tintColor` 绑 `[CONFIGURATION.x]`（官方 Complications sample）
- **颜色位索引语法**：`[CONFIGURATION.themeColor.0]` 取 ColorOption 第 0 色
  （ColorOption colors 可多色空格分隔）；单色时无索引引用（P2 真机实证）也可
- 表达式含 `&&`/`!= null` 等时用 **CDATA** 包裹（`<![CDATA[[X] != null && [Y] != null]]>`）
- 高级：Font 内可挂 `<Outline color width>` 描边（color 可绑配置色）

### R40: Complication 数据有无的分支渲染用 Condition + null 判断（官方 Complications sample 模式）

provider 无数据时整个 `<Complication type="...">` 不渲染（R26），但**有部分字段**
（如只有 TEXT 无 TITLE/图标）时需要分支布局——官方模式：

```xml
<Condition>
    <Expressions>
        <Expression name="imgAndTitle"><![CDATA[[COMPLICATION.MONOCHROMATIC_IMAGE] != null && [COMPLICATION.TITLE] != null]]></Expression>
        <Expression name="imgOnly"><![CDATA[[COMPLICATION.MONOCHROMATIC_IMAGE] != null]]></Expression>
    </Expressions>
    <Compare expression="imgAndTitle">…图标+标题布局…</Compare>
    <Compare expression="imgOnly">…仅图标布局…</Compare>
    <Default>…兜底…</Default>
</Condition>
```

三元兜底同样常用（Flavors sample）：`[HEART_RATE] != null ? [HEART_RATE] : "--"`
（字符串字面量在 XML 属性里用 `&quot;--&quot;` 转义）。

---

## 🎬 动画包（v0.6.0 前置知识，2026-09-12 XSD 精读 + validator 实证）

> 来源：XSD v1/v5 逐文件精读 + 正解 XML 过 wff-validator（v1/v5 双过）+ builder 全链路。
> 官方 samples（wear-os-samples）**零动画实例**——只有 Transform 静态用法（Complications 弧），
> 动画知识全部以 XSD 为权威，正解 XML 是唯一实证来源。

### R41: 帧动画是三件套 `PartAnimatedImage > AnimationController + 内容`，缺一不可

XSD `xs:all`：AnimationController（1 个，必填）+ AnimatableImageElement（SequenceImages /
AnimatedImage / AnimatedImages 三选一，必填）。裸 `<SequenceImages>` 直接挂 Group 里
= validator 报错。AnimationController 不写 = 报错。

### R42: 无限循环用 `AnimationController repeat="TRUE"`，不是 loopCount="-1"

v5 XSD：`loopCount` 是 nonNegativeInteger（SequenceImages 更是 positiveInteger），
**写 -1 直接被 validator 拒**（v1 XSD 宽容 xs:int，但别赌真机）。无限循环语义在
`repeat` 布尔属性上。注意两套 repeat 语义完全不同：
- `AnimationController repeat` = **bool**（TRUE = 无限循环）
- `Animation repeat` = **int**（0 = 不重复，**-1 = 无限循环**）
写反必炸。

### R43: SequenceImages 的帧 `<Image>` 只有 resource 属性

帧尺寸由外层 `PartAnimatedImage` 的 width/height 决定；给帧 Image 写
width/height = validator 拒（cvc-complex-type.3.2.2）。跟 PartImage>Image（有
resource/tintColor/资源引用语义）同名不同形，别混。

### R44: `frameRate`（SequenceImages）和 `changeDirection`（AnimatedImages）是 WFF 2+ 属性

v1 表盘（minSdk 33 / Wear OS 4）禁用。默认帧率 15fps 已够用；真机可能限帧
（XSD 注释：设备限 15fps 时 frameRate=30 会跳帧播放保速度）。

### R45: `Transform` 没有 rotate()/translate() 变换函数（旧知识层虚构）

正解是 `target`（宿主属性名字符串，必填）+ `value`（算术表达式，必填）+ `mode`
（TO/BY）。把"旋转 30 度"写成 `<Transform target="angle" value="30"/>`；
不是 `value="rotate(30)"`。官方 samples 全部是 target="endAngle"/"angle" 模式。

### R46: 属性动画 = `Transform > Animation`，value 里用 `[ANIMATION_VALUE]`

`[ANIMATION_VALUE]` 是 0→1 的插值进度，只在与 `<Animation>` 同一 Transform 的
value 表达式里可用。duration（秒）必填。呼吸效果样板：
`<Transform target="alpha" value="[ANIMATION_VALUE] * 0.7"><Animation duration="2.0" repeat="-1" interpolation="EASE_IN_OUT"/></Transform>`
注意 repeat=-1（Animation 是 int 语义，见 R42）。

### R47: `AnimatedImage` 没有 file/playback 属性（旧知识层虚构）

正解：`resource`（drawable 名）+ `format`（AGIF/WEBP/IMAGE）+ 可选 thumbnail。
播放控制（循环/触发/结束行为）全在 `<AnimationController>` 上，包括"ambient 时
显示什么"——用 `afterPlaying`/`beforePlaying`（DO_NOTHING/FIRST_FRAME/THUMBNAIL/HIDE）
或干脆用 `<Variant mode="AMBIENT">` 挂在 PartAnimatedImage 上。

### R48: 图片滤镜是 `PartImage > ImageFilters > HsbFilter`（旧知识层 `<ImageFilter>` 枚举虚构）

没有独立 ImageFilter 元素，没有 NONE/GRAYSCALE/DIMMED/TINTED 枚举。滤镜是
HsbFilter 数值参数（hueRotate/saturate/brightness，默认 1）。

### R49: Gyro 调整的是父 Group/Part 的属性（非独立变换节点）

`<Gyro>` 挂 Group/Part 内部，表达式算出的值直接改**父元素**的 x/y/angle/alpha/
scaleX/scaleY。想做"背景层视差"就把 Gyro 挂在背景 Group 里（内容物不动，Group
整体微移）。数据源 `[ACCELEROMETER_ANGLE_X]`/`[ACCELEROMETER_ANGLE_Y]`（XSD
sensorSourceType 白名单），官方示例模式：`(8/90) * clamp([ACCELEROMETER_ANGLE_X], -90, 90)`。

### R50: TimeText 的 Font 是精简内联版，无任何子元素

`DigitalClock > TimeText > Font` 是 XSD 局部定义（family/size/color/slant/width/
weight 纯属性），**不支持 Outline/Shadow/Transform 等子元素**——validator 报
"No child element is expected"。装饰只有 `PartText > Font`（全局版）才有。
另外 `Font > Outline` 的宽度属性叫 **width**（Stroke 的才叫 thickness）。

### R61: TimeText 内放 BitmapFont 会导致时间整体消失（真机实证 2026-09-15）

v3 教训: DigitalClock>TimeText>BitmapFont 结构 wff-validator 双版本全过, 但真机
渲染器不执行 → **时间完全不显示**。XSD 允许 ≠ 渲染器支持（TimeText 只认 Font
子元素）。位图时间正解 = PartText>Text>BitmapFont+Template 拼接:
`floor([HOUR_1_12_Z])` + `floor([MINUTE_Z])`（_Z 后缀=补零字符串源, 时间源
全浮点必须 floor; 12/24h 切换需 [IS_24_HOUR_MODE]+Condition, 简单场景固定制式）。
表达式驱动刷新已实证可行（BT-04 [SECOND] 变色）。AMBIENT 层保留
DigitalClock>TimeText>Font 系统字（省电+稳定双保险）。

**矩阵终判 (2026-09-15 真机 A/B/C/D 四方案并存实测)**: A=TimeText+Font ✓
B=PartText+Font+Template floor ✓ **C=PartText+BitmapFont+字符串源 ✗
D=PartText+BitmapFont+floor 数值源 ✗**——BitmapFont 在 WOS6 渲染链路
**全面不可用**（TimeText 通道 R61 前证, PartText 通道本次证）。自定义时间
字体正解 = B 通道: `<Font family="SYNC_TO_DEVICE" size weight="BOLD">` +
`floor([HOUR_1_12])`/`floor([MINUTE])`。位图字模方案在 WOS6 上废弃。

### R62: builder 资源同步"存在即跳过"——项目资源更新永远不进包（真机实证 2026-09-15）

wff_builder.py 旧逻辑 `if not dst.exists(): copy2(...)` 导致 _build/res/drawable
里 09-13 的旧图标快照永远占位, 后续 v2-v5 四轮图标替换全部静默失效（真机
"图标没变"的真正根因, 而非渲染问题）。修复 (2026-09-15): 始终覆盖复制 +
清理 stale 文件。**教训**: ① 交付含图片资源的 APK 必须字节级核验包内资源
（unzip 提取 + 尺寸/IoU 对比）, "构建成功"不代表"资源更新"; ② 用户反馈
"没有变化"时优先怀疑构建缓存/增量同步, 而不是先怀疑渲染器; ③ One UI 表盘
渲染有缓存, 复测需切走再切回表盘。

### R59: [已被 R61 推翻] 位图字体 Text 内用法曾验证可行（真机实证 2026-09-14）

> ⚠️ 本条结论已被 R61 推翻（2026-09-15 矩阵测试）：BitmapFont 在 WOS6 渲染
> 链路**全面不可用**（TimeText 与 PartText 通道均不渲染）。保留本条仅作历史
> 演变记录。当前结论：**位图字体整体废弃**，个性化字体用系统字
> SYNC_TO_DEVICE weight/width 变体（12 weight × 9 width）。

`<Font family="位图族名"/>` 引用 BitmapFonts 无效——渲染器不认 Font 引用位图族,
静默回退系统默认字体（真机表现"字体没变"）。正确用法（官方 Weather sample）:
`<Text><BitmapFont family="materialDigits" size="72"><Template>...</Template></BitmapFont></Text>`
—— **BitmapFont 是独立元素**, 不是 Font 的属性引用。BitmapFonts 声明挂 WatchFace
直接子级, Character name/resource/width/height 必填。字模 PNG 颜色固定 → 多主题
配"深胶囊+白字模"最稳。

### R60: 日期源的浮点陷阱与中式日期组装（真机实证 2026-09-14）

[MONTH_DAY]/[MONTH] 是浮点数（含当天时刻进度小数, 真机显示"9.433"）——
**Template 参数必须 floor() 包裹**: `floor([MONTH_DAY])`。中式日期
"9月14日 周一": `<Template><![CDATA[%s月%s日 %s]]>` + floor([MONTH]) +
floor([MONTH_DAY]) + [DAY_OF_WEEK_S]（星期源随系统语言本地化, 中文系统
输出"周一"）。官方 Weather sample 还用 `<Localization calendar="GREGORIAN"
timeZone="SYNC_TO_DEVICE"/>` 控制日历/时区语义。

### R56: Text 没有 letterSpacing 属性（validator 实证 2026-09-13）

Text 元素合法属性仅 ellipsis/maxLines。字距效果用空格分隔文本（"F L O W"）
实现；styles 文档早期版本的 letterSpacing=1.2px 是虚构写法。

### R57: Parameter 是 Template 的子元素, 不是同级（validator 实证 2026-09-13）

正确结构: `<Font><Template><![CDATA[%s]]><Parameter expression="[X]"/></Template></Font>`
——Parameter 包在 Template **内部**。写成同级（Font 下 Template+Parameter 并列）
报 "content of Template is not complete"。

### R58: 电池数据源是 [BATTERY_PERCENT], 日期三源 [DAY_OF_WEEK_S]+[MONTH]+[MONTH_DAY]（真机实证 2026-09-13）

BATTERY_PERCENTAGE 不存在（S1 首版右下组件只渲染出 "%%" 字面量）。
统一日期格式 "周日 9.13": Template 三参数 %s %s.%s。圆屏矩形元素四角须验算
落在内接圆内（450 盘: 角点距心 <215px）, 上下 1/3 区域宽度按 √(225²-dy²)
收窄——S1 首版底部胶囊被圆边切割实证。

### R53: One UI 8 Watch (WOS6) 渲染器不执行 Transform+Animation 属性动画（真机实证 2026-09-13）

XSD 合法、wff-validator v1/v5 双 PASS 的 `<Transform target=...>+<Animation
duration/repeat/interpolation/fps>` 在 One UI 8 Watch (WOS6/Android 16) 真机上
**完全不被执行**。红点探针实验（Transform target="x" 几何平移，最简表达式+
fps=30+EASE_IN_OUT）静止不动——与 target 类型（alpha/几何）、表达式复杂度、
fps 缺省全部无关，是渲染器整体缺口。**帧序列（PartAnimatedImage）是唯一可用
动画通道**；呼吸等慢动效必须把变化烘进帧像素（R55）。

### R54: One UI 8 Watch (WOS6) 渲染器不渲染 Gyro 视差（真机实证 2026-09-13）

官方 gyroElements.xsd 文档**原样示例表达式**（双向 clamp 分段式）挂 Group/Part
在 WOS6 真机无任何反应（背景刻度不随转腕轻移）。与挂载层级、clamp 写法无关。
WFF 规范定义了 Gyro 但 One UI 8 Watch 未实现渲染——视差需求在 WOS6 上无法交付，
需求卡里把"陀螺仪视差"列为可选加分项而非必选项。

### R55: 慢动效（呼吸）用帧序列 alpha 烘帧实现（WOS6 实证方案）

呼吸动画 = 把 alpha 曲线烘进 N 帧 PNG（PartAnimatedImage + repeat=TRUE 循环）。
要点：① alpha 曲线首尾同值（三角波/整周期贝塞尔）保证循环无缝；② 柔光素材
可缩至 160px 省体积（30 帧×160²≈460KB）；③ AnimationController 记得
beforePlaying/afterPlaying="FIRST_FRAME"；④ 官方 memory-footprint.jar 会验
总解码内存，30+45 帧双序列实测 PASS。

### R52: Metadata 只能挂 WatchFace 级, 不能放 Scene 里（平台 CI 实证 2026-09-13）

`<Metadata>` 是 `<WatchFace>` 的直接子元素（在 `<Scene>` **之前**）；Scene 的
xs:all 不含 Metadata。放错位置官方 wff-validator 直接拒（v1/v5 同拒）。配方 §5
曾中招——本地 builder 只查"Metadata 存在性"不查层级, 修 XML 后必须**回归官方
validator**（教训: 正解 XML 每次修改后全链路重验, 不能只跑 builder）。平台 CI
的 lxml XSD 校验层抓到过这个 bug——三级校验有真实拦截价值。

### R51: v5 XSD 对 Group 强制 name + 全套几何属性

validator 5 模式下 `Group` 必须写 `name` + `x y width height`（v1 宽容但不代表
真机宽容）。xsd unique 约束：同名兄弟 Group 不合法。clipShape 属性在 WFF v1
真机不支持（builder R06 拒），validator 宽容——**builder 规则比 validator 严，
以 builder 为准**。

---


## 🔧 构建约束（APK 打包层面）

### BC1: minSdkVersion

| WFF 版本 | minSdk | Wear OS |
|----------|--------|---------|
| v1 | 33 | Wear OS 4+ |
| v2 | 34 | Wear OS 5+ |
| v3+ | 34+ | Wear OS 5+ |

### BC2: resources.arsc 必须 STORED + 4 字节对齐

- `resources.arsc` 在 APK 中必须**不压缩**（`ZIP_STORED`）
- 必须在 ZIP 中 **4 字节对齐**（APK Signature Scheme v2 要求）
- DEFLATED 压缩会报 `error -124`

### BC3: res/xml/ 必须是二进制 AXML

- `res/xml/watch_face_info.xml` 在 APK 中必须是 **aapt2 编译后的二进制 AXML**（文件头 `0x0300`）
- 不能放原始文本 XML
- aapt2 只有 x86_64 二进制，ARM64 需要 Docker 构建

### BC4: res/values/ 不独立出现在 APK 中

- `res/values/strings.xml` 等已编译进 `resources.arsc`
- APK 中不应有独立的 `res/values/` 目录

### BC5: res/raw/ 保持原始文本

- `res/raw/watchface.xml` 是 WFF 主文件，**不编译**，保持原始文本 XML

### BC6: 签名必须 v1+v2+v3 全签

- 开发密钥：`test.keystore`（pass: `wfftest123`, alias: `wfftest`）
- 上线前必须换正式密钥，keystore 不提交公开仓库

---

## ⚡ XSD v5 与一期规则的差异

通过对比官方 XSD v5 规范与一期 16 条规则，以下差异需注意：

| 项 | 一期规则 | XSD v5 实际 | 说明 |
|----|----------|-------------|------|
| clipShape | R06: v1 不支持 | v5 定义了 NONE/CIRCLE/RECTANGLE | v2+ 可用，v1 仍不支持 |
| Font weight | 8 档 | THIN/ULTRA_LIGHT/EXTRA_LIGHT/LIGHT/NORMAL/MEDIUM/SEMI_BOLD/BOLD | 匹配 |
| Font width | 未提及 | 8 档 (ULTRA_CONDENSED...EXTRA_EXPANDED) | 可用 |
| Sweep | 未提及 | frequency: 2/5/10/15/SYNC_TO_DEVICE | 秒针平滑度控制 |
| BlendMode | 未提及 | 20 种混合模式 | 可做特效 |
| Photos | 未提及 | 用户照片表盘 | 可做照片表盘 |
| Complication | 简单引用 | 9 种类型 + DefaultProviderPolicy | 一期未覆盖，agent 可用全功能 |
| UserConfiguration | 未提及 | List/Boolean/Color/Photos/Flavors | 可做用户自定义表盘 |
| Gyro | 未提及 | 6 轴响应表达式 | 可做陀螺仪视差 |
| Condition | 未提及 | Compare/Default 多分支条件 | 可做条件渲染 |
| Reference | 未提及 | 发布属性供其他元素引用 | 可做动态联动 |

---

## 📋 已知限制

1. **rembg/onnxruntime 不可用**：~500MB 依赖在 ARM 环境装不上。用 Pillow flood-fill 阈值抠图替代，纯色背景素材够用，复杂照片背景效果有限
2. **aapt2 仅 x86_64**：ARM64 服务器需 Docker 构建（一期已解决）
3. **npm 重依赖超时**：低配 VM 装 fabric 等大包频繁 504，用 `--registry=https://registry.npmmirror.com`
4. **预览渲染器是近似值**：平台 preview 端点用 Pillow 静态帧渲染，复杂动画/状态机可能与真机有差异。**最终判据永远是真机安装**
5. **WFF 规范演进**：google/watchface 仓库活跃维护（2026-08-22 最后更新），XSD 版本 v1→v5，新版本可能引入破坏性变更

---

## 参考

- 一期踩坑原文：`docs/NOTES.md` §1-5
- 完整 16 规则代码实现：`wff-builder/wff_builder.py` validate 命令
- 官方 XSD 规范：`tools/google-watchface/watchface/third_party/wff/specification/documents/5/`
- 官方验证器：`java -jar wff-validator.jar 5 watchface.xml`

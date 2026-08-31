# WFF 踩坑大全

> 一期 16 条规则（2026-08-15 真机验证）+ 盲测/真机复盘扩充至 29 条（R17-R29）。
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
mixed=true）。无数据兜底还可以用 `<Complication type="EMPTY">` 渲染占位符
（supportedTypes 加 EMPTY）。

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

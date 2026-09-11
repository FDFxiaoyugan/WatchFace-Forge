# WFF Watch Face Development Skill

> Agent Skill: 教任意 AI agent 开发 Wear OS Watch Face Format (WFF) 表盘。
> 从一行需求到可安装 APK，全流程 agent 自主完成。

**版本 v0.5.0**（2026-09-11）— 组件包（可定制配置全链路）。版本史：
- v0.1.0（2026-08-24）首版端到端验证
- v0.2.0（2026-08-27）Round 1 回灌：知识层大修 11 处（嵌套方向/HH:mm/Complication 属性集）
- v0.2.2（2026-08-31）真机三轮复盘：R26-R30 + 规则 20 条
- v0.3.0（2026-09-08）盲测四轮收官：R31-R32、环境自查清单、inventory attributeGroup
  修复、R13 白名单 XSD 全集、商务风配方、PartDraw 整层 Variant 范式、规则 21 条
- v0.4.0（2026-09-10）P2 大满贯日：R33 Editable（编辑器自定义按钮总开关）+ R30
  反转（displayName 裸资源名）+ R34/R35 圆屏溢出与 Arc 容器溢出校验 + R36 Arc
  角度语义（ArcLab 像素级实证）、颜色包 UserConfigurations 全链路真机验证、规则 24 条
- v0.5.0（2026-09-11）组件包闭环：List/Boolean 两套模式（R37）+ slotId 0 起/上限 8
  （R38）+ PartText>Text>Font 三层（R39）+ Condition null 分支（R40）+ 配方 §4 +
  Windows 宿主适配 + R34 嵌套误报修复 + BoundingOval x/y 修正；五轮盲测全 PASS
  （BT-08 真机四项自定义全正常）、规则 27 条

---


## 环境前置（宿主机一次性，含自查与补齐清单）

**自查**（构建前逐项确认，缺什么补什么）：

| 组件 | 检查 | 缺失时的补齐 |
|------|------|--------------|
| Java 17+ | `java -version` | apt 装 openjdk-21，或 tarball 解压到用户目录后设 JAVA_HOME |
| aapt2 | `$ANDROID_HOME/build-tools/34.0.0/aapt2 -h` | 下载 build-tools_r34-linux.zip；**解压后顶层目录是 android-14，需改名 34.0.0** |
| apksigner | 同目录 `apksigner --version` | 同上（build-tools 内含） |
| android.jar | `$ANDROID_HOME/platforms/android-34/android.jar` | 下载 `platform-34-ext7_r02.zip`（**不是** platform-34_r02.zip，那个 404）解压到 platforms/android-34 |

**路径探测顺序**：builder 先读 `ANDROID_HOME` 环境变量；未设置时兜底查
`/opt/android-sdk`。SDK 组件装到任意位置后 `export ANDROID_HOME=<路径>` 即可。

**⚠️ ARM64 宿主限制**：aapt2 官方 Linux 构建是 x86_64 only。ARM 宿主上 builder
走"预编译模板"兜底——该模板**只注册了 drawable/preview 一个资源槽位**，
多 drawable 表盘（指针 PNG/dial 背景等）会丢图。ARM 上构建多图盘必须在
x86_64 机器（或 Docker x86_64）上进行。

**⚠️ Windows 宿主**（BT-08 盲测实证）：工具名带 `.exe`/`.bat` 后缀，SDK 路径
探测可能失败。用环境变量指定完整路径：
`AAPT2=<SDK>\build-tools\34.0.0\aapt2.exe`、`APKSIGNER=<SDK>\build-tools\34.0.0\apksigner.bat`
（builder 报错信息里有此提示；java 用 `java -version` 同查）。

## When to Use

- 用户想"做一个 Wear OS 表盘"
- 用户想"生成/构建/验证 watch face"
- 需要写 WFF XML
- 需要 validate/preview/build watchface APK

## Quick Start

```bash
# 1. 初始化项目（生成 project.yaml + watchface.xml 骨架）
python wff-builder/wff_builder.py init projects/my_watch

# 2. 写 watchface.xml（参考 recipes.md 配方）
# 3. 验证（27 条规则 + XSD）
python wff-builder/wff_builder.py validate projects/my_watch

# 4. 构建 APK
python wff-builder/wff_builder.py build projects/my_watch

# 或通过平台 API（需要平台就绪）
python client/wff_api.py build projects/my_watch
```

## Knowledge Layer

| 参考 | 内容 | 何时读 |
|------|------|--------|
| [elements.md](./references/elements.md) | WFF v5 全量元素树 + 属性 | 需要查"某个元素叫什么/有什么属性"时 |
| [expressions.md](./references/expressions.md) | 数据源 + 运算符 + 函数 | 需要写动态表达式时 |
| [pitfalls.md](./references/pitfalls.md) | 40 条规则 + 踩坑 + 构建约束 | 写 WFF XML 前必读 |
| [recipes.md](./references/recipes.md) | 3 种典型表盘完整模板 | 开始一个新表盘时 |

## WFF XML Skeleton

```xml
<?xml version="1.0"?>
<WatchFace width="450" height="450">
    <Metadata key="CLOCK_TYPE" value="DIGITAL"/>
    <Metadata key="PREVIEW_TIME" value="10:08:32"/>
    <Scene backgroundColor="#ff000000">
        <!-- Active 模式内容 -->
        <DigitalClock x="0" y="0" width="450" height="450">
            <TimeText format="hh:mm" hourFormat="SYNC_TO_DEVICE"
                      align="CENTER" x="0" y="120" width="450" height="120">
                <Variant mode="AMBIENT" target="alpha" value="0"/>
                <Font family="SYNC_TO_DEVICE" size="100" weight="BOLD" color="#ff00F5FF"/>
            </TimeText>
        </DigitalClock>
        <!-- AMBIENT 模式内容 -->
        <DigitalClock x="0" y="0" width="450" height="450">
            <TimeText format="hh:mm" hourFormat="SYNC_TO_DEVICE"
                      align="CENTER" x="0" y="120" width="450" height="120" alpha="0">
                <Variant mode="AMBIENT" target="alpha" value="255"/>
                <Font family="SYNC_TO_DEVICE" size="100" weight="THIN" color="#ff888888"/>
            </TimeText>
        </DigitalClock>
    </Scene>
</WatchFace>
```

## Work Loop

### 1. 理解需求

从用户描述提取：
- 表盘类型：数字 / 指针 / 混合
- 核心信息：时间、日期、电池、步数、心率、天气...
- 画布尺寸：384（PW1）或 450（PW2+）
- 风格：极简 / 信息密集 / 动画
- 是否需要 AOD（息屏）模式
- 是否需要用户自定义（颜色/照片）

### 2. 选配方

| 需求 | 配方 | 文件 |
|------|------|------|
| 只看时间 | minimal-digital | `examples/minimal-digital/` |
| 指针表盘 | analog-hands | `recipes.md` §2 |
| 信息密集 | hybrid-complication | `recipes.md` §3 |
| 可定制组件 | configurable-components | `recipes.md` §4 |

### 3. 写 WFF XML

**必读 [pitfalls.md](./references/pitfalls.md) 的 MUST 规则（R01-R36）**

关键规则速记：
- 颜色 8 位 ARGB：`#ffRRGGBB`（不是 `#RRGGBB`）
- 数据源用方括号：`[MONTH]` 不是 `MONTH`
- 时间用 DigitalClock + TimeText（不用 Text + Template），format 只用小写 `hh:mm`
- 字体用 `family="SYNC_TO_DEVICE"`（不用 `Roboto`）
- AMBIENT 模式用 `<Variant>` 控制
- **形状包住样式**：`<Arc><Stroke/></Arc>`，不是 `<Stroke><Arc/></Stroke>`
- **Complication 必须写渲染内容**：空 `<Complication/>` 真机渲染为空（R26），
  内部放 PartText/PartImage + `[COMPLICATION.TEXT]` 等数据绑定
- 矢量圆角矩形用 `cornerRadiusX/cornerRadiusY`（R27），BoundingRoundBox 才是 `cornerRadius`
- **ComplicationSlot 的 BoundingShape 用局部坐标**（0,0 起，尺寸=slot 尺寸），
  写全局坐标槽位整体消失且编辑器无自定义入口（R28）
- Template 至少一个 Parameter，静态文本直接写 `<Font>text</Font>`（R29）
- **displayName 用裸资源名**（R30 反转版，2026-09-09 实证）：`displayName="theme_color"`
  不是 `@string/theme_color`——res/raw 与 res/xml 不经 aapt2 编译，@string/ 是字面量
- **指针三坐标公式**（R31 前置）：旋转中心 `(x+pivotX·w, y+pivotY·h)` 必须等于圆心；
  12 点竖直针 `y=圆心y−针长`；带配重尾 `pivotY=针长/图高`
- **指针 PNG 左右 alpha 对称**（R31）：偶数宽 PIL 细线抗锯齿不对称 → 秒针错位；
  奇数宽画布或精确光栅化；交付前校验质心 `== width/2`
- **Condition 正确结构**（R32）：算式在 `<Expressions><Expression name>` 文本，
  `<Compare expression="引用名">`；运算符只有 `>` `>=` `==`——"低于X"写成 `X > [SRC]`
- **编辑器自定义入口两件套**（R33）：`res/xml/watch_face_info.xml` 含
  `<Editable value="true"/>`（按钮开关）+ watchface.xml 内 `<UserConfigurations>`
  （选项内容）。缺 Editable：一切正常但无自定义按钮；有 Editable 无配置：按钮在但空
- **圆屏 = 画布内切圆**（R34）：贴顶/贴底元素四角超内切圆被切；450 画布顶部元素
  压 y≥25 且收窄宽度；validate R34 自动查
- **Arc 几何是 PartDraw 局部坐标**（R35）：centerX/centerY 相对父容器，椭圆溢出
  容器弧段被裁成"斜线"；居中写 `centerX=容器宽/2`
- **Arc 角度 0°=12点、顺时针正、负角合法**（R36）：上半拱 `-90→90`；`180→360`
  是左半弧 C 形（开口朝右）
- **List/Boolean 两套模式，id 两边对应**（R37）：容器版（UserConfigurations 内）
  = 编辑器 UI 元数据；渲染版（Scene/Group 内）= Option id + 内嵌部件。Boolean
  渲染版可只放 TRUE（FALSE=不渲染）。ListOption `complicationSlotIds` 联动槽位显隐
- **ComplicationSlot 上限 8、slotId 唯一、从 0 起**（R38）
- **PartText > Text > Font 三层**（R39）：Font 直挂 PartText 被 validator 拒
  （渲染器宽容也不行）；`[CONFIGURATION.<id>.<N>]` 取多色 ColorOption 第 N 色位；
  表达式含 `&&` 用 CDATA
- 列表属性空格分隔：`colors="#ffAABBCC #ff112233"`
- 布尔枚举大写：`isCustomizable="TRUE"`
- project.yaml 不写行内注释

### 4. 验证（两级，都要过）

```bash
# 初筛：20 条结构规则（快）
python wff-builder/wff_builder.py validate projects/my_watch

# 终审：官方 XSD 校验（必跑！初筛抓不住 XSD 级错误）
java -jar vendor/google-watchface/tools/wff-validator.jar 5 projects/my_watch/watchface.xml
```

两级都通过 → 进入步骤 5
失败 → 读错误信息 → 修复 → 重新验证（最多 3 轮）

> R22：初筛全绿 ≠ XSD 合法。嵌套方向、枚举值、format pattern 等 XSD 级错误
> 只有官方 validator 抓得住。

### 5. 构建

```bash
python wff-builder/wff_builder.py build projects/my_watch
```

构建成功 → 交付 APK
构建失败 → 读 [pitfalls.md](./references/pitfalls.md) 构建约束 → 修复

### 6. （可选）平台 API

如果平台就绪（阿里云入口可用），可用 HTTP API：

```bash
python client/wff_api.py validate projects/my_watch
python client/wff_api.py preview projects/my_watch --times "10:08,23:59"
python client/wff_api.py build projects/my_watch
```

## Project Structure

```
my_watch/
├── project.yaml          # 包名、版本、WFF 版本
├── watchface.xml         # WFF XML 设计
├── preview.png           # 384×384 或 450×450 预览图
└── res/                  # 资源目录（可选）
    ├── drawable/         # 图片
    ├── font/             # 字体
    └── xml/
        └── watch_face_info.xml  # 含 <Editable value="true"/> (R33, builder 自动生成)
```

## project.yaml

```yaml
package_name: com.example.mywatchface
version_code: 1
version_name: "1.0"
watch_face_name: My Watch Face
wff_version: 1              # 1=Wear OS 4, 2+=Wear OS 5+
```

## Build Constraints

- `minSdk`: WFF v1=33 (Wear OS 4), v2+=34 (Wear OS 5+)
- `resources.arsc`: 必须 STORED + 4 字节对齐
- `res/xml/`: 二进制 AXML (aapt2 编译, Docker x86_64)
- `res/values/`: 不独立出现 (编译进 resources.arsc)
- `res/raw/`: 原始文本 (watchface.xml 不编译)
- 签名: v1+v2+v3 (开发密钥 test.keystore, 上线前换正式密钥)

## Environment

- ANDROID_HOME: /home/z/my-project/tools/android-sdk
- Build-Tools: 34.0.0 (x86_64, Docker on ARM64)
- Keystore: wff-builder/keystore/test.keystore (pass: wfftest123, alias: wfftest)

## Data Sources (Quick)

| 数据源 | 说明 |
|--------|------|
| `[HOUR_0_23_Z]` | 24h 前导零 |
| `[MINUTE_Z]` | 分前导零 |
| `[SECOND_Z]` | 秒前导零 |
| `[BATTERY_PERCENT]` | 电池百分比 0-100 |
| `[STEP_COUNT]` | 步数 |
| `[HEART_RATE]` | 心率 |
| `[MONTH]` `[DAY_Z]` `[DAY_OF_WEEK_S]` `[MONTH_S]` | 日期 |
| `[WEATHER_CURRENT_TEMPERATURE]` | 天气温度 |

> 完整列表见 [expressions.md](./references/expressions.md)

## Version & Updates

- 当前版本：v0.5.0（2026-09-11）
- 知识来源：google/watchface XSD v5 + 官方 samples + 一期真机验证 + 盲测四轮 +
  P2 颜色包真机迭代（Editable/displayName 裸名/ArcLab 角度语义像素级实证）
- 更新触发：XSD 规范变更 / 平台 API 契约变更 / 盲测反馈 / 真机复盘
- 更新记录：[CHANGELOG.md](./CHANGELOG.md)
- 维护手册：[SKILL_MAINTENANCE.md](./SKILL_MAINTENANCE.md)

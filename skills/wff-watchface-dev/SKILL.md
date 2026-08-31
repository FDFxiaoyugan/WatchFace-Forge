# WFF Watch Face Development Skill

> Agent Skill: 教任意 AI agent 开发 Wear OS Watch Face Format (WFF) 表盘。
> 从一行需求到可安装 APK，全流程 agent 自主完成。

---

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
# 3. 验证（20 条规则 + XSD）
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
| [pitfalls.md](./references/pitfalls.md) | 29 条规则 + 踩坑 + 构建约束 | 写 WFF XML 前必读 |
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

### 3. 写 WFF XML

**必读 [pitfalls.md](./references/pitfalls.md) 的 MUST 规则（R01-R29）**

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
- **ComplicationSlot 的 `displayName` 用 `@string/` 资源引用**（R30）：字符串放项目
  `res/values/strings.xml`（builder 自动合并）；slotId 从 1 开始
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
    └── font/             # 字体
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

- 当前版本：v0.1.0（Phase 4B 开发中）
- 知识来源：google/watchface XSD v5 + 一期 16 规则真机验证 + BT-03 真机复盘
- 更新触发：XSD 规范变更 / 平台 API 契约变更 / 盲测反馈
- 更新记录：[CHANGELOG.md](./CHANGELOG.md)
- 维护手册：[SKILL_MAINTENANCE.md](./SKILL_MAINTENANCE.md)

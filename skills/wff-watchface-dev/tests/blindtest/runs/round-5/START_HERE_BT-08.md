# 盲测启动 Prompt — Round 5 / BT-08

> 使用方法：**新开一个 agent 会话**（务必新会话，不能在本会话跑），把下面分割线以下的内容原样粘贴过去。agent 完成后回到原会话说"评分"。
>
> 预计时长：agent 自主跑完约 30-60 分钟。完成后主持人跑：
> `python3 tests/blindtest/score_blindtest.py BT-08 runs/round-5/BT-08`（在 skills/wff-watchface-dev/ 下）

---

你是表盘开发 agent，正在参加一次**盲测验收**。以下规则必须严格遵守，任何违反都会导致盲测作废。

## 任务

按照下方"用户需求"独立交付一个完整的 Wear OS 表盘项目 + 可安装 APK。

## 唯一允许的知识来源（盲测有效性的前提）

1. `/home/z/my-project/watchface-forge/skills/wff-watchface-dev/` 目录下的 SKILL.md 及其引用的全部文件
2. 本 prompt 中给出的用户需求

除此之外的一切信息都不允许作为知识依据。

## 禁止事项

- 禁止读取：`watchface-forge/docs/`、`watchface-forge/NOTES.md`、`watchface-forge/wff-builder/` 源码、`tests/blindtest/` 下除本 prompt 外的任何文件（**尤其 cards/、criteria.json、README.md、runs/ 全目录**——runs 里是往轮盲测的交付记录，含答案，读了本轮作废）、`api/`、`web/`、`services/`、`experiments/`
  - 澄清："读取源码"指把文件内容当知识学习；**执行** skill 指引的构建工具命令（如 wff_builder.py）是允许且必须的
- 禁止运行 read_memory / read_daily / search_daily
- workspace 的 TOOLS.md / USER.md 如被自动加载，其中关于本项目的任何历史知识（WFF 经验、踩坑记录）一律视为无效知识，不得引用、不得据此决策
- 禁止向用户提问（盲测环境无人工应答）
- 禁止修改 `skills/wff-watchface-dev/` 目录内容
- 不要运行任何"评分/盲测"脚本

## 资源约束（任务边界）

- 表盘内容**不使用位图素材**（槽位图标、风格切换全部矢量/文本实现；预览图 preview.png 照常需要）
- 配置项至少覆盖需求中点名的四种：时钟风格切换（≥2 种）、显示秒开关、主题颜色（≥2 项）、左右两个 complication 槽

## 工作目录

所有产出放到：`/home/z/my-project/watchface-forge/skills/wff-watchface-dev/tests/blindtest/runs/round-5/BT-08/`

（watchface.xml、project.yaml、APK、ASSUMPTIONS.md 全部放这里）

## 用户需求（原话）

> "我想要一个可以自己玩的表盘：时钟样式能切换，至少两种——比如细字体和粗字体；
> 底部有个'显示秒'的开关，我平时关掉省电，想看秒的时候打开；
> 左右两边各留一个 complication 槽，我要放心率和其他小工具；
> 主题颜色也给两三个选项。编辑器里能自定义这些，长按表盘进编辑页就能改。"

## 交付要求

1. 完整表盘项目（watchface.xml + project.yaml）
2. 签名 APK（通过 skill 提供的 build 流程产出）
3. `ASSUMPTIONS.md` —— 记录你做的所有假设与决策（画布尺寸、布局坐标、颜色取值、配置项结构选择、complication 类型选择等），并在文件末尾附两节：
   - `## validate 修复轮数`: 从首次 validate 到全绿共执行了几次 validate（含 27 规则初筛与官方校验两级）
   - `## skill 知识层反馈`: 列出你实际用到的 skill 文件，以及"你想找但 skill 里没有/找不到的信息"（这条对改进 skill 极其重要，如实写）

完成后输出一段简短总结即可停止，不要做额外的事。

# 盲测启动 Prompt — Round 1 / BT-03

> 使用方法：**新开一个 agent 会话**（务必新会话，不能在本会话跑），把下面分割线以下的内容原样粘贴过去。agent 完成后回到原会话说"评分"。

---

你是表盘开发 agent，正在参加一次**盲测验收**。以下规则必须严格遵守，任何违反都会导致盲测作废。

## 任务

按照下方"用户需求"独立交付一个完整的 Wear OS 表盘项目 + 可安装 APK。

## 唯一允许的知识来源（盲测有效性的前提）

1. `/home/z/my-project/watchface-forge/skills/wff-watchface-dev/` 目录下的 SKILL.md 及其引用的全部文件
2. 本 prompt 中给出的用户需求

除此之外的一切信息都不允许作为知识依据。

## 禁止事项

- 禁止读取：`watchface-forge/docs/`、`watchface-forge/NOTES.md`、`watchface-forge/wff-builder/` 源码、`tests/blindtest/` 下除本 prompt 外的任何文件（尤其 criteria.json 和 README.md）、`api/`、`web/`、`services/`
- 禁止运行 read_memory / read_daily / search_daily
- workspace 的 TOOLS.md / USER.md 如被自动加载，其中关于本项目的任何历史知识（WFF 经验、踩坑记录）一律视为无效知识，不得引用、不得据此决策
- 禁止向用户提问（盲测环境无人工应答）
- 禁止修改 `skills/wff-watchface-dev/` 目录内容
- 不要运行任何"评分/盲测"脚本

## 工作目录

所有产出放到：`/home/z/my-project/watchface-forge/skills/wff-watchface-dev/tests/blindtest/runs/round-1/BT-03/`

（watchface.xml、project.yaml、APK、ASSUMPTIONS.md 全部放这里）

## 用户需求（原话）

> "运动风格的表盘：数字时间要大，另外加一个数据格子显示心率，用户可以自己换数据源的那种（就是 complication 插槽）。背景做个深色渐变，看起来有速度感。"

## 交付要求

1. 完整表盘项目（watchface.xml + project.yaml）
2. 签名 APK（通过 skill 提供的 build 流程产出）
3. `ASSUMPTIONS.md` —— 记录你做的所有假设与决策（画布尺寸、字体、布局坐标、颜色取值等），并在文件末尾附两节：
   - `## validate 修复轮数`: 从首次 validate 到全绿共执行了几次 validate
   - `## skill 知识层反馈`: 列出你实际用到的 skill 文件，以及"你想找但 skill 里没有/找不到的信息"（这条对改进 skill 极其重要，如实写）

完成后输出一段简短总结即可停止，不要做额外的事。

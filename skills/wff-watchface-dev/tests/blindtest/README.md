# 盲测执行手册（Phase 4C / P4B-F06）

> 主持人（人类或监督 agent）必读。被测 agent **只能**获得 `cards/` 中的需求卡 + skill 目录，
> 不能看本文件和 `criteria.json`（评分标准保密，防止应试优化）。

---

## 1. 盲测定义（v3.0 §7）

从未接触本仓库的 agent（fresh context），仅获得 skill 目录 + API 地址/key，
按随机需求卡独立完成表盘。

## 2. 环境准备

| 项 | 说明 |
|----|------|
| 被测 agent | 新会话，无本项目记忆 |
| 提供物 ① | `skills/wff-watchface-dev/` 完整目录（含 SKILL.md） |
| 提供物 ② | 一张需求卡（`cards/BT-0X_*.md`），随机抽取 |
| 提供物 ③ | API 地址/key（平台就绪时）；未就绪则告知用 local 模式 |
| 产出位置 | 约定目录，如 `runs/BT-01/`（项目本体） |
| 记录 | 会话日志（用于统计修复轮数） |

## 3. 执行流程

```
1. 开新 agent 会话，发需求卡（原样粘贴，不加任何提示）
2. agent 自主工作：读 skill → 写 XML → validate → build
3. 主持人记录：validate 首次结果 + 每轮修复（rounds = 首次 validate 到全绿的尝试次数）
4. agent 交付后，运行评分脚本（见下）
5. 视觉项（布局溢出/重叠/ambient 可读性）人工或 VLM 抽查
6. 真机安装：用户抽查 ≥2 张
```

## 4. 评分

```bash
# 单卡
python3 tests/blindtest/score_blindtest.py BT-01 runs/BT-01 --rounds 2

# 全卡汇总（目录约定 runs/BT-01..BT-05）
# 可选 runs/runs.json: {"BT-01": {"rounds": 2}, "BT-02": {"rounds": 1}, ...}
python3 tests/blindtest/score_blindtest.py --all runs --markdown report.md
```

评分三层：
1. **static** — 需求验收的 XML 静态检查（criteria.json，保密）
2. **validate** — wff-builder 16 规则
3. **build** — APK 产出 + 签名 + sha256

**不评**（人工/VLM）：视觉布局、真机显示。

## 5. 通过标准（Phase 4 总验收）

| 指标 | 标准 | 来源 |
|------|------|------|
| validate 一次通过率 | ≥ 60%（5 张卡中 ≥3 张） | 脚本（rounds==1） |
| 修复循环 | 平均 ≤ 3 轮全绿 | 脚本（runs.json） |
| build 成功率 | 100%（过 validate 必过 build，否则平台 bug） | 脚本 |
| 静态需求满足 | 每卡 static 检查全过 | 脚本 |
| 真机显示 | 用户抽查 ≥2 张，无元素缺失 | 人工 |
| 知识回灌 | 暴露的坑 48h 内进 pitfalls.md | CHANGELOG 记录 |

## 6. 结果回灌

每个失败项按根因归档：

| 根因 | 动作 |
|------|------|
| 知识层缺失（agent 不知道某元素/数据源） | 补 references/elements.md 或 expressions.md |
| 踩坑未记录 | 补 references/pitfalls.md |
| 卡片歧义（需求描述导致误解） | 修卡片措辞 |
| 工具缺陷（wff-builder/skill client bug） | 修代码 + 记 ISSUE |

回灌记录进 `CHANGELOG.md`（格式：`blind-test fix (BT-0X): ...`）。

## 7. 卡片清单

| 卡 | 主题 | 考点 |
|----|------|------|
| BT-01 | 极简数字 + 日期 + 电池 | 基础：DigitalClock/TimeText、数据源、颜色 |
| BT-02 | 三针模拟 + 秒针 | AnalogClock、三针元素、矢量绘制 |
| BT-03 | 混合 + 心率 complication | ComplicationSlot、混合布局 |
| BT-04 | 低电量条件变色 | Condition 表达式、分支渲染 |
| BT-05 | Ambient 独立场景 | Variant mode=AMBIENT、多模式设计 |
| BT-08 | 可定制组件 | List/Boolean 双模式、ComplicationSlot、编辑器自定义全链路 |

难度梯度：BT-01 < BT-02 ≈ BT-05 < BT-03 ≈ BT-04（后两张考 skill 知识层覆盖面）。

## 8. 快速冒烟（评分脚本自检）

```bash
# demo 项目应过 BT-01
python3 tests/blindtest/score_blindtest.py BT-01 wff-builder/projects/demo
# demo 项目应挂 BT-02（区分度检查）
python3 tests/blindtest/score_blindtest.py BT-02 wff-builder/projects/demo
```

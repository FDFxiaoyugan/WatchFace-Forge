# Skill Maintenance Guide

> 维护者必读。定义更新触发器、流程和交接标准。

---

## Update Triggers

### Trigger 1: WFF Spec Evolution

**监控源**: `google/watchface` 仓库 `third_party/wff/specification/documents/`

**检查方式**:
```bash
cd tools/google-watchface/watchface && git fetch origin && git log --oneline origin/main -5
```

**当 XSD 变更时**:
1. `git pull` 更新本地 XSD
2. 重新运行 `tools/google-watchface/parse_xsd.py` 生成新的 `data/wff_inventory_v5.json`
3. 对比新旧 inventory，找出新增/删除/变更的元素和属性
4. 更新 `references/elements.md` 和 `references/expressions.md`
5. 在 `CHANGELOG.md` 记录变更
6. 如果有破坏性变更，更新 `references/pitfalls.md`

### Trigger 2: Platform API Contract Change

**监控源**: `docs/API_CONTRACT.md` 版本号

**当契约变更时**:
1. 读取新版 `docs/API_CONTRACT.md`
2. 更新 `client/wff_api.py` 的请求/响应处理
3. 更新 `client/config.example.json` 如有新配置项
4. 在 `CHANGELOG.md` 记录变更

### Trigger 3: Blind-Test Failure Feedback

**来源**: Phase 4C 盲测用例 + 用户反馈

**当盲测失败时**:
1. 分析失败根因（validate 错误 / build 失败 / 真机不显示）
2. 如果是知识层缺失 → 补充 `references/elements.md` 或 `expressions.md`
3. 如果是踩坑未记录 → 补充 `references/pitfalls.md`
4. 在 `CHANGELOG.md` 记录："blind-test fix: ..."
5. 考虑是否需要更新 `examples/` 中的模板

---

## Handover Standard

后续 agent 接手时需读取以下文件即可继续工作:

1. `SKILL.md` — 入口，工作循环
2. `CHANGELOG.md` — 版本历史
3. `data/wff_inventory_v5.json` — 完整元素/属性数据
4. `references/pitfalls.md` — 构建规则
5. 本文件 (`SKILL_MAINTENANCE.md`) — 维护流程
6. `tools/google-watchface/parse_xsd.py` — XSD 解析脚本

---

## Versioning

- 版本号: `vMAJOR.MINOR.PATCH`
- 知识层新增元素/数据源 → MINOR
- 踩坑修复/示例更新 → PATCH
- XSD 大版本变更 (v5→v6) → MAJOR

---

## Quality Checklist

发布前检查:
- [ ] `data/wff_inventory_v5.json` 与最新 XSD 一致
- [ ] `references/elements.md` 覆盖所有常用元素
- [ ] `references/pitfalls.md` 的 16 条规则仍然有效
- [ ] `examples/` 中的表盘能通过 validate + build
- [ ] `client/wff_api.py` local 模式可运行
- [ ] `CHANGELOG.md` 已更新

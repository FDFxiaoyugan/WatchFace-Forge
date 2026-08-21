# AGENTS.md — AI Agent 开发指引

> 本项目预期由 AI Agent 持续开发与维护。本文档定义工作规则，动手前必读。

## 文档阅读顺序

1. `README.md` — 项目全貌与 API 清单
2. `docs/ARCHITECTURE.md` — **实际架构与规划的偏差**（最关键，规划文档与实现不一致时以它为准）
3. `docs/DEVELOPMENT.md` — 环境搭建与服务启动顺序
4. `docs/NOTES.md` — 踩坑记录（改构建器/编译器/Celery 前必读）
5. `docs/PROJECT_GOALS.md` — 背景规划（注意：是 2026-08-12 的规划蓝图，不是实现记录）
6. `wff-builder/SKILL.md` — APK 构建引擎使用指南

## 硬性红线

1. **许可证红线**：严禁引入 GPL / AGPL / LGPL 组件（如 MinIO、pngquant）。加新依赖前先查许可证
2. **密钥红线**：API Key 走环境变量，不硬编码；`test.keystore` 仅限开发，不新增密钥文件入库
3. **CDM 单一定义**：CDM 结构只改 `schema/cdm/models.py`，改完必须重新导出 `v1.0.json` 并跑全量测试
4. **不要重构 WFF 字节流逻辑**：`wff-builder/` 的手动 ZIP 构造是 16 条规则换来的，除非有真机验证条件，否则只加不改
5. **Celery 启动命令**：`celery -A api.tasks worker`（详见 NOTES.md §2，改错会 KeyError）

## 工作流要求

### 改动前

- `git status` + `git diff` 确认工作区状态，不覆盖他人改动
- 涉及 CDM / 编译器 / 构建器的改动，先读 `docs/NOTES.md` 对应小节

### 改动后（缺一不可）

```bash
python3 -m pytest tests/ -v          # 36 个测试全绿
python3 -c "import ast; ast.parse(open('改动的.py').read())"  # 语法兜底
```

- 改 API 路由：起 uvicorn 后 curl 实测端点（不要只信测试）
- 改前端：`cd web && npx tsc --noEmit` 零错误 + `next build` 成功
- 改 Celery：必须实测异步链路（提交 → 轮询 → SUCCESS），参考 `docs/DEVELOPMENT.md` 的启动顺序

### 提交规范

```
feat|fix|docs|refactor: 简述（中英文均可）
```

- 一次提交一个逻辑单元；bug 修复在正文里写根因（root cause），方便后来者搜索
- 提交前更新 `docs/NOTES.md`：新踩的坑按章节归档，标注日期

## 测试环境事实（2026-08-20）

- DevSpace（华为云 8vCPU ARM64）已部署全栈：uvicorn :8000 + celery worker + redis + next :3000
- 已验证：异步图像管线端到端（200×200 绿底 → 113×113 透明 PNG）、/editor 页面 200
- 未验证：编辑器画布浏览器端交互（拖拽/缩放/撤销栈）——Fabric.js 是纯客户端行为，需要开端口隧道后浏览器实测

## Phase 4-5（二期）扩展指引

见 `docs/ARCHITECTURE.md` §5 预留的扩展点。新编译器（Apple Watch）按 `compiler/wff/` 的纯函数模式实现，API 层按 platform 参数路由。

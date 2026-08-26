# WatchFace Forge

AI 驱动的 Wear OS 表盘生成与分发平台：用户一句话描述 → AI 生成 CDM → 可视化编辑 → 编译签名 APK → 扫码安装到手表。

> **状态：** Phase 1-3 一期工程已完成并端到端验证（2026-08-20）。
> 规划文档见 `docs/PROJECT_GOALS.md`，实际架构见 `docs/ARCHITECTURE.md`（含规划与实现的偏差说明）。

## 核心链路

```
用户提示词 ──→ AI Gateway (z-ai SDK) ──→ CDM JSON (Pydantic 校验+自动修复)
                                              │
              ┌───────────────────────────────┤
              ↓                               ↓
        Web 编辑器 (Fabric.js)          WFF 编译器 (CDM → WFF XML)
              │                               ↓
              │                    APK 构建 (纯 Python: zip+对齐+签名)
              ↓                               ↓
        Celery 异步队列  ←──────────────  签名 APK
        (image/build 双队列)                    ↓
                                     二维码扫码下载 → Wear Installer 安装
```

## 项目结构

```
watchface-forge/
├── docs/
│   ├── PROJECT_GOALS.md     # 项目规划文档 v2.2 (2026-08-12, 供背景参考)
│   ├── ARCHITECTURE.md      # 实际实现架构 + 与规划的偏差 ⭐ 必读
│   ├── DEVELOPMENT.md       # 开发环境搭建与服务启动
│   └── NOTES.md             # 踩坑记录 (WFF 16 规则 + Celery + DevSpace)
├── schema/cdm/              # CDM 数据模型 (Pydantic)
│   ├── models.py            #   WatchFaceCDM 等 18 个模型
│   └── v1.0.json            #   导出的 JSON Schema
├── compiler/wff/            # WFF 编译器 (CDM → WFF XML)
├── services/
│   ├── ai_gateway/          # AI 调用网关 (z-ai 默认 / OpenAI 可选, 限流 10次/h)
│   └── cdm_generator/       # 提示词工程 + CDM 自动修复层
├── api/
│   ├── app.py               # FastAPI 入口
│   ├── routes/              # 路由: templates/compile/build/generate/editor...
│   ├── services/image/      # Pillow 图像管线 (抠图/裁剪/压缩, 替代 rembg)
│   ├── models/              # API 请求/响应模型
│   └── tasks/               # Celery 异步任务 (image/build 双队列 + 死信)
├── web/                     # Next.js 前端
│   └── src/
│       ├── app/             #   / (生成) /editor (可视化编辑器)
│       ├── components/      #   editor/ (画布/图层/属性/数据绑定面板)
│       └── stores/          #   editorStore.ts (Zustand, 撤销/重做 50 步)
├── wff-builder/             # WFF APK 构建引擎 (16 条校验规则, 独立可用)
│   └── SKILL.md             #   构建引擎使用指南
├── tests/                   # 36 个测试 (core + api + phase2)
└── AGENTS.md                # AI Agent 开发指引 ⭐ agent 必读
```

## Phase 进度

- [x] **Phase 1 — MVP**：WFF 构建引擎 + CDM 模型 + 编译器 + FastAPI + Next.js + 二维码下载。真机验证通过 (2026-08-15)
- [x] **Phase 2 — AI 接入**：AI Gateway + 提示词工程 + CDM 自动修复 + WebSocket 进度推送。端到端验证 ("霓虹蓝赛博朋克" → 37KB APK)
- [x] **Phase 3 — 完整体验**：Fabric.js v6 可视化编辑器 + Pillow 图像管线 + Celery 双队列 + CDM 实时校验。异步链路端到端 SUCCESS (2026-08-20)
- [x] **Phase 4A — WFF Agent CI 基础设施**：直通 validate/preview/build API、API Key 限流、Google 官方 XSD/validator/内存评估（2026-08-25）
- [ ] Phase 4C — Agent CI 工作台与自修复反馈（Skill 开发按当前计划跳过）
- [ ] Phase 5 — 微信小程序（二期）

访问 `/ci` 使用 Agent CI 工作台：可直接提交 WFF XML/素材，查看 XSD、
Google validator 与 lint 三层日志，生成多时刻预览，并下载带 SHA-256 和
官方内存报告的签名 APK。

## API 端点（20 个）

| Method | Path | Phase | 说明 |
|--------|------|-------|------|
| GET | `/` | 1 | 根信息 |
| GET | `/api/health` | 1 | 健康检查 |
| GET | `/api/templates` | 1 | 模板列表（3 个固定模板） |
| GET | `/api/templates/{id}` | 1 | 模板详情 |
| POST | `/api/compile` | 1 | CDM → WFF XML（含校验） |
| POST | `/api/build` | 1 | CDM → 签名 APK 全流程 |
| GET | `/api/download/{filename}` | 1 | 下载 APK |
| GET | `/api/qrcode/{filename}` | 1 | APK 下载二维码 |
| POST | `/api/generate` | 2 | 提示词 → CDM（AI 生成，异步） |
| WS | `/api/ws/{task_id}` | 2 | 生成进度推送 |
| POST | `/api/editor/image/process` | 3 | 图片异步处理（抠图/裁剪，Celery） |
| POST | `/api/editor/image/upload` | 3 | 图片同步处理（multipart 上传） |
| GET | `/api/editor/task/{task_id}` | 3 | 异步任务结果查询 |
| GET | `/api/editor/queue/info` | 3 | 队列拓扑信息 |
| GET | `/api/editor/cdm/{task_id}` | 3 | 取回 AI 生成的 CDM |
| POST | `/api/editor/cdm/validate` | 3 | CDM 实时校验（结构+语义） |
| POST | `/api/v1/wff/validate` | 4A | WFF XML：官方 XSD + validator + lint 三层校验 |
| POST | `/api/v1/wff/preview` | 4A | WFF XML 多时间/Active/Ambient 近似预览 |
| POST | `/api/v1/wff/build` | 4A | WFF XML → 签名 APK + SHA-256 + 官方内存报告 |
| GET | `/api/v1/wff/builds/{filename}` | 4A | 下载直通 API 构建产物 |

## 快速开始

### 本地开发

```bash
# 0. Python 依赖
pip install -r requirements.txt

# 1. 启动 redis (Celery broker, 必须先于 API 启动)
redis-server --daemonize yes

# 2. 启动 API
uvicorn api.app:app --host 0.0.0.0 --port 8000

# 3. 启动 Celery worker (⚠️ 必须 -A api.tasks, 见 DEVELOPMENT.md 的坑)
python3 -m celery -A api.tasks worker -Q image,default -c 2 --loglevel WARNING

# 4. 启动前端
cd web && npm install && npx next dev -p 3000
```

### 测试

```bash
python3 -m pytest tests/ -v   # 42 个测试
```

### WFF Builder 独立使用

```bash
cd wff-builder
python wff_builder.py init projects/my_watch
python wff_builder.py validate projects/my_watch
python wff_builder.py build projects/my_watch
```

## 技术栈（全部宽松许可证，无 Copyleft）

| 层 | 技术 | 许可证 |
|---|---|---|
| 后端 | FastAPI + Pydantic + Celery | MIT / BSD |
| 前端 | Next.js 15 + Tailwind CSS 4 + Fabric.js 6 + Zustand | MIT |
| 图像处理 | Pillow（flood-fill 抠图，替代 rembg） | MIT-CMU |
| APK 构建 | 纯 Python zipfile + pyzipalign + apksigner | Apache 2.0 |
| AI | z-ai SDK（默认）/ OpenAI（可选） | — |

> ⚠️ 红线：严禁引入 GPL/AGPL/LGPL 组件（如 MinIO、pngquant）。完整清单见 PROJECT_GOALS.md §4.4。

## 已知约束

- 签名密钥 `wff-builder/keystore/test.keystore` 为开发用（pass: wfftest123），上线前必须更换
- AI 生成限流 10 次/小时（内存令牌桶，重启失效）
- 抠图为阈值 flood-fill，适合纯色背景素材；复杂照片背景效果有限
- APK 构建的 aapt2 预编译模板在 Docker 构建时生成（x86_64），运行时纯 Python 跨平台

# WatchFace Forge

AI 驱动的 Wear OS 表盘生成与分发平台。

## 项目结构

```
watchface-forge/
├── docs/                        # 项目文档
│   ├── PROJECT_GOALS.md         # 项目目标文档 v2.2
│   └── NOTES.md                 # 开发笔记
├── schema/cdm/                  # CDM 数据模型
│   ├── models.py                # Pydantic 模型
│   └── v1.0.json                # JSON Schema
├── compiler/wff/                # WFF 编译器
│   └── compiler.py              # CDM → WFF XML
├── api/                         # FastAPI 后端
│   ├── app.py                   # 应用入口
│   ├── routes/                  # 路由
│   │   ├── health.py            # 健康检查
│   │   ├── templates.py         # 模板列表/详情
│   │   ├── compile.py           # CDM → WFF XML
│   │   ├── build.py             # CDM → APK 全流程
│   │   └── qrcode.py            # APK 下载二维码
│   └── services/                # 业务逻辑
│       └── templates.py         # 3 个固定模板
├── web/                         # Next.js 前端
│   └── src/
│       ├── app/                 # 页面
│       └── components/          # 组件
├── wff-builder/                 # WFF APK 构建引擎
│   ├── wff_builder.py           # 核心引擎 + 16 条校验规则
│   ├── SKILL.md                 # Agent 使用指南
│   └── keystore/                # 签名密钥
└── docker-compose.yml           # 开发环境
```

## Phase 1 进度

- [x] WFF APK 构建引擎 (wff-builder, 16 条校验规则)
- [x] 真机验证通过 (2026-08-15)
- [x] CDM 数据模型 + JSON Schema
- [x] WFF 编译器 (CDM → WFF XML)
- [x] FastAPI 后端 (7 个端点)
- [x] Next.js 前端 (模板选择 + 预览 + 下载)
- [x] APK 二维码下载
- [x] Docker Compose 开发环境
- [ ] 自定义编辑器 (Phase 3)
- [ ] AI 自然语言生成 (Phase 2)

## API 端点

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/health` | 健康检查 |
| GET | `/api/templates` | 模板列表 |
| GET | `/api/templates/{id}` | 模板详情 |
| POST | `/api/compile` | CDM → WFF XML |
| POST | `/api/build` | CDM → APK |
| GET | `/api/download/{filename}` | 下载 APK |
| GET | `/api/qrcode/{filename}` | APK 二维码 |

## 快速开始

### 本地开发

```bash
# 1. 启动后端
cd api
pip install -r requirements.txt
cd .. && uvicorn api.app:app --host 0.0.0.0 --port 8000

# 2. 启动前端
cd web
npm install
npx next dev -p 3000

# 3. 打开浏览器
# http://localhost:3000
```

### Docker

```bash
docker compose up -d
# API: http://localhost:8000
# Web: http://localhost:3000
```

### WFF Builder 单独使用

```bash
cd wff-builder
python wff_builder.py init projects/my_watch
python wff_builder.py validate projects/my_watch
python wff_builder.py build projects/my_watch
```

## 技术栈

| 层 | 技术 | 许可证 |
|---|---|---|
| 后端 | FastAPI + Pydantic | MIT |
| 前端 | Next.js 15 + Tailwind CSS | MIT |
| 构建 | aapt2 + apksigner (Android SDK) | Apache 2.0 |
| 签名 | Java JRE + keytool | GPL+CE |
| 二维码 | qrcode (Python) | MIT/BSD |

## 开发踩坑总结

详见 `docs/NOTES.md` — 16 条 WFF 规则，覆盖 Manifest 配置、构建管线、表达式语法三个层级。

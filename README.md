# WatchFace Forge

AI 驱动的 Wear OS 表盘生成与分发平台。

## 项目结构

```
watchface-forge/
├── docs/                    # 项目文档
│   ├── PROJECT_GOALS.md     # 项目目标文档 v2.2
│   └── NOTES.md             # 开发笔记
├── wff-builder/             # WFF APK 构建引擎 (已验证)
│   ├── wff_builder.py       # 核心构建器 + 16 条校验规则
│   ├── SKILL.md             # Agent 使用指南
│   ├── projects/            # 表盘项目
│   │   └── demo/            # 示例表盘
│   └── keystore/            # 签名密钥
├── schema/                  # CDM JSON Schema (Phase 1)
├── compiler/                # 编译器模块 (Phase 1)
├── api/                     # FastAPI 后端 (Phase 1)
├── web/                     # Next.js 前端 (Phase 1)
└── docker-compose.yml       # 开发环境
```

## Phase 1 进度

- [x] WFF APK 构建引擎 (wff-builder)
- [x] 16 条 WFF 校验规则
- [x] 真机验证通过 (2026-08-15)
- [ ] CDM JSON Schema
- [ ] WFF 编译器 (CDM → WFF XML)
- [ ] FastAPI 后端服务
- [ ] Next.js 前端 (3 个固定模板)
- [ ] APK 下载端点
- [ ] 安装引导页
- [ ] Docker Compose 开发环境

## 开发命令

```bash
# WFF Builder
cd wff-builder
python wff_builder.py init projects/my_watch
python wff_builder.py validate projects/my_watch
python wff_builder.py build projects/my_watch
```

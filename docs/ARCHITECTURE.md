# 架构文档 — 实际实现 (Phase 1-3)

> **本文档描述实际实现的架构。** 规划文档 `PROJECT_GOALS.md` (v2.2, 2026-08-12) 是设计时点的蓝图，
> 实现过程中有若干关键决策变更，**以本文档为准**。新 agent 开发前必读本文档的「与规划的偏差」一节。

## 1. 与规划的偏差（重要 ⭐）

| # | 规划 (PROJECT_GOALS.md) | 实际实现 | 原因 |
|---|------------------------|---------|------|
| 1 | CDM 为通用 **layers 数组**模型（background/image/text/pointer + transform + dataBinding） | CDM 为**结构化功能域**模型：`clock_type` + `background` + `digital_time` + `analog_time` + `date_display` + `info_line` + `complications[]` | WFF XML 本身是结构化声明式格式，结构化 CDM 与 WFF 元素一一对应，编译器简单可靠；通用 layers 模型需要复杂的类型推断和映射，一期无必要。**改 CDM 结构前先读 `schema/cdm/models.py`** |
| 2 | AI 用 GPT-4o Structured Outputs | 用 **z-ai SDK**（默认），OpenAI 兼容接口可选 | 国内网络环境 + 成本。网关层已抽象 provider，`services/ai_gateway/` 可切换 |
| 3 | 图像抠图用 **Rembg + onnxruntime** | 用 **Pillow flood-fill 阈值抠图** | onnxruntime ~500MB，DevSpace/低配环境装不上。阈值法对表盘场景（纯色背景素材）够用。接口已抽象 `ProcessOptions`，后续可换 |
| 4 | 消息代理用 **Valkey** | 用 **redis-server** (yum/apt 直装) | DevSpace 环境限制。接口兼容，上线时可无感切换 Valkey（broker_url 配置项） |
| 5 | 存储 S3/OSS + CDN | 本地磁盘 `outputs/` 目录 | 一期无公网入口。下载端点读本地目录，抽象了 filename 白名单校验 |
| 6 | 数据库 PostgreSQL + SQLAlchemy | 无数据库，状态在 redis（Celery result backend） | 一期无用户体系。CDM/任务结果按 task_id 存 redis，TTL 过期 |
| 7 | intent:// 唤起安装 | APK 下载 + **Wear Installer** 方案 | Google 官方无 intent:// 安装通道（规划文档 §1.3 已自我修正） |
| 8 | 编辑器渲染层 CDMRenderer + Fabric 自定义封装 | Fabric.js v6 直接操作对象，**拖拽/缩放事件回写 CDM**（`web/src/components/editor/`） | 减少抽象层。editorStore (Zustand) 是唯一数据源，画布是它的视图投影 |

## 2. 一期实际架构

```
┌────────────────────────────────────────────────────────────────┐
│  web/  Next.js 15 (App Router)                                 │
│                                                                │
│  /                AI 生成流: 提示词 → WebSocket 进度 → CDM 预览  │
│  /editor          可视化编辑器 (Fabric.js v6):                   │
│                   ├─ CanvasStage     画布 (384×384, 圆/方切换)   │
│                   ├─ LayerPanel      图层列表 (显隐/排序)        │
│                   ├─ PropertyPanel   选中对象属性编辑            │
│                   ├─ DataBindingPanel 数据源绑定                 │
│                   └─ TimeSimulator   时间模拟 (指针/数字预览)    │
│                                                                │
│  状态: editorStore.ts (Zustand) — CDM 快照 + undo/redo 栈 (50步) │
└──────────────┬─────────────────────────────────────────────────┘
               │ REST / WebSocket
┌──────────────┴─────────────────────────────────────────────────┐
│  api/  FastAPI                                                 │
│                                                                │
│  同步端点: templates / compile / build / qrcode                 │
│  AI 端点:  generate (提交) + ws/{task_id} (进度推送)             │
│  编辑器:   image/process|upload, task/{id}, cdm/validate        │
│                                                                │
│  services/ai_gateway/    provider 抽象 + 令牌桶限流 + 重试       │
│  services/cdm_generator/ 提示词模板 + CDM 自动修复层             │
│  api/services/image/     Pillow 管线 (抠图/裁剪/压缩)            │
└──────┬──────────────────────────────┬──────────────────────────┘
       │ .delay()                     │ 同步调用
┌──────┴──────────┐          ┌────────┴──────────────┐
│  api/tasks/     │          │  compiler/wff/        │
│  Celery         │          │  CDM → WFF XML        │
│  ├─ image 队列   │          │  (Jinja2 模板)        │
│  └─ build 队列   │          ├───────────────────────┤
│  + 死信队列      │          │  wff-builder/          │
│  (指数退避重试)  │          │  XML→APK: 手动构造ZIP  │
└──────┬──────────┘          │  + pyzipalign + 签名   │
       │                     └────────┬──────────────┘
┌──────┴──────────────────────────────┴──────────────┐
│  redis (broker + result backend)  +  outputs/ (APK) │
└────────────────────────────────────────────────────┘
```

## 3. 关键数据流

### 3.1 AI 生成（Phase 2，2026-10 审计修正后语义）

```
POST /api/generate {prompt, ai_config?}   ← 同步长请求（10–60s），非异步任务
  → 鉴权+配额: X-API-Key（WFF_API_KEYS 配置时强制；production 未配置=503）
    Redis 原子固定窗口 per-key 10/h（WF_QUOTA_GENERATE_PER_HOUR 可覆盖；
    Redis 不可用: production fail-closed / development 进程内降级）
  → ai_gateway: z-ai chat 或用户 BYOK（SSRF 硬检查 + 可选域名白名单）
  → LLM 输出 JSON → pydantic 校验 → 失败则自动修复层修正 (最多 3 轮)
  → 合法 CDM 存 Redis (wff:cdm:{task_id}, TTL 1h; 不可用退进程内存)
    → GET /api/editor/cdm/{task_id} 编辑器导入（构建失败 CDM 仍可取回）
  → 进度事件写入内存 _progress_store（供 /api/ws/{task_id} 事后回放；
    同步请求下前端无法预知 task_id, 当前 UI 为真实等待时长而非事件流）
  → 响应含 CDM + APK download_url；前端可: 跳转 /editor 或直接下载
```

### 3.2 异步图像处理（Phase 3）

```
POST /api/editor/image/process {image_b64, options}
  → process_image_task.delay() → image 队列
  → worker: Pillow 管线
      flood-fill 抠图 (bg_tolerance) → alpha 包围盒裁剪 (auto_crop)
      → 长边缩放 (max_size) → PNG/WebP 编码
  → 结果 base64 存 result backend
  GET /api/editor/task/{task_id} → SUCCESS + {image_b64, ...}
  
降级: broker 不可用时 editor.py 捕获异常 → 同步 Pillow 处理直接返回
```

### 3.3 APK 构建（Phase 1 核心资产）

```
CDM → compiler/wff (Jinja2 模板 → WFF XML, 含 16 条校验)
    → wff-builder:
        ├─ 预编译模板 APK (Docker 构建时 aapt2 生成: 二进制 AXML + resources.arsc)
        ├─ Python 手动构造 ZIP 字节流 (不用 zipfile.ZipFile — 见 NOTES.md)
        ├─ pyzipalign 对齐 (resources.arsc 必须 STORED + 4字节对齐)
        └─ apksigner 签名 (v1+v2+v3)
    → outputs/watchface.apk → /api/qrcode 二维码
```

## 4. 模块职责与边界

| 模块 | 职责 | 禁止事项 |
|------|------|---------|
| `schema/cdm/` | CDM 唯一定义（Pydantic）+ JSON Schema 导出 | 不要在别处重复定义 CDM 字段 |
| `compiler/wff/` | CDM → WFF XML 纯函数转换 | 不做 IO、不读文件 |
| `wff-builder/` | XML+资源 → 签名 APK，可独立 CLI 使用 | 依赖 Docker 预编译模板（aapt2 x86_64） |
| `services/ai_gateway/` | AI provider 抽象 + 限流 + 重试 | 密钥不硬编码，读环境变量 |
| `services/cdm_generator/` | 提示词模板 + CDM 修复 | 修复规则改动需跑 test_phase2 |
| `api/tasks/` | Celery 任务定义 + app 配置 | ⚠️ 启动方式见 DEVELOPMENT.md，错用启动命令会 KeyError |
| `web/src/stores/` | 前端状态唯一来源 | 组件不直接改 CDM，走 store action |

## 5. 二期扩展点（Phase 4-5 预留）

- **编译器可插拔**：`compiler/wff/` 的接口模式可复制到 `compiler/apple_watch/`；`api/routes/compile.py` 按 platform 路由
- **CDM 版本演进**：`schema_version` 字段已预留（当前 "1.0"），升级走 `model_validator` 迁移
- **小程序 API**：规划中的 `/api/mini/*` 前缀未占用，可直接加路由模块
- **存储抽象**：下载端点的文件读取集中在 `api/routes/build.py`/`qrcode.py`，换 S3/OSS 时改这两处

# AI 驱动的 Wear OS 表盘生成与分发平台 — 项目目标文档

> **文档版本:** v2.2
> **创建日期:** 2026-08-12
> **最后更新:** 2026-08-12 (纯 Python APK 构建方案验证通过，ARM64 部署架构确定)
> **状态:** 规划完成，可进入开发

---

## 目录

- [0. 项目愿景与原则](#0-项目愿景与原则)
- [1. 项目概述](#1-项目概述)
- [2. 整体架构设计](#2-整体架构设计)
- [3. 核心数据模型 — CDM JSON 规范](#3-核心数据模型--cdm-json-规范)
- [4. 技术选型总览与许可证审查](#4-技术选型总览与许可证审查)
- [5. 开发阶段详解](#5-开发阶段详解)
  - **一期工程 (Phase 1-3)**
  - [Phase 1 — MVP：WFF 编译器 + APK 下载安装](#phase-1--mvpwff-编译器--apk-下载安装)
  - [Phase 2 — AI 接入：自然语言生成闭环](#phase-2--ai-接入自然语言生成闭环)
  - [Phase 3 — 完整体验：编辑器 + 图像处理 + 异步队列](#phase-3--完整体验编辑器--图像处理--异步队列)
  - **二期工程 (Phase 4-5)**
  - [Phase 4 — 多端拓展：Apple Watch 编译器](#phase-4--多端拓展apple-watch-编译器)
  - [Phase 5 — 微信小程序：轻量客户端与社交分发](#phase-5--微信小程序轻量客户端与社交分发)
- [6. 管理后台](#6-管理后台)
- [7. 部署架构与资源规划](#7-部署架构与资源规划)
- [8. 非功能性需求](#8-非功能性需求)
- [9. 风险登记册](#9-风险登记册)
- [9A. 隐形问题清单 (一期工程审计)](#9a-隐形问题清单-一期工程审计)
- [10. 开发者特别提示与红线规则](#10-开发者特别提示与红线规则)

---

## 0. 项目愿景与原则

### 愿景

让任何人都能通过一句话描述，在 30 秒内获得一块专属的智能手表表盘，并一键安装到手表上——无需写代码、无需 APK、无需 PC。

### 核心原则

| 原则 | 说明 |
|------|------|
| **数据与视图分离** | 前端画布操作的是平台无关的 CDM JSON，编译器负责转译为目标平台格式。前端永远不直接生成 WFF XML。 |
| **AI 外包，本地不做推理** | 所有 AI 能力通过云端 API 调用，本地服务器只做调度、后处理和编译打包。 |
| **只走 WFF 路线** | 绝不在 APK 中包含代码 (hasCode=false)。WFF APK 是纯资源包 (XML + 图片 + 字体)，不是可执行应用。只使用 Google 官方 WFF 声明式格式。 |
| **编译器可插拔** | 新增平台 = 新增一个编译器模块，前端业务逻辑零改动。 |
| **客户端可裁剪** | Web 端是全功能编辑器；微信小程序是轻量浏览/预览/分发客户端，共享同一套 CDM JSON 和 API，但渲染层独立。 |
| **许可证合规** | 所有引入的开源组件必须为宽松许可证（MIT / Apache 2.0 / BSD / ISC），**严禁使用 Copyleft 组件**（GPL / AGPL / LGPL）。 |
| **三次熔断** | 同一组件（库/服务）在同类型问题上修复 3 次仍未解决，必须停止使用该组件，寻找替代方案。 |

---

## 1. 项目概述

### 一句话定义

一个 Web 平台，用户通过自然语言 AI 生成、可视化编辑、验证并一键安装 Wear OS 智能手表表盘，底层架构预留向 Apple Watch、Amazfit 等平台拓展的能力。

### 平台架构鸟瞰

```
                          用户终端
  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐
  │  Web 编辑器   │  │  微信小程序    │  │  管理后台 (Admin)  │
  │  (Next.js)   │  │  (轻量客户端)   │  │  (Next.js)       │
  │              │  │              │  │                 │
  │ Canvas 画布   │  │ 浏览/预览/分享  │  │ 看板/用户/API配置  │
  │ 图层管理      │  │ 扫码安装      │  │ 内容审核/用量统计  │
  │ 数据绑定      │  │              │  │                 │
  │ 模拟预览      │  │              │  │                 │
  └──────┬───────┘  └──────┬───────┘  └────────┬────────┘
         │                  │                    │
         └──────────┬───────┘────────────────────┘
                    │  HTTPS / WebSocket
                    ↓
          ┌─────────────────────────────────┐
          │  API 网关 (FastAPI)              │     ┌──────────────┐
          │  ├─ Auth / Rate Limit             │ ←→  │ OpenAI GPT-4o│
          │  ├─ AI 调度层                      │ ←→  │ Google Gemini│
          │  ├─ 编译器 (CDM → WFF/...)        │ ←→  │ Gemini Imagen  │
          │  ├─ 图像后处理 (Rembg/Sharp)      │     └──────────────┘
          │  ├─ 静态校验器                     │     ┌──────────────┐
          │  ├─ 分发服务 (APK 下载)            │ ←→  │ 对象存储      │
          │  └─ Admin API (看板/配置/用户)    │     │ (S3/OSS+CDN) │
          │                                   │     └──────────────┘
          │  异步队列 (Celery + Valkey)        │
          │  ├─ AI 生成任务                     │
          │  ├─ 图像后处理任务                   │
          │  └─ 编译打包任务                    │
          └─────────────────────────────────┘
```

### 目标用户

- **主要用户：** 智能手表爱好者，有个性化需求但无开发能力
- **次要用户：** 独立设计师，希望快速原型化表盘设计

---

## 2. 整体架构设计

### 2.1 分层架构

```
┌─────────────────────────────────────────────────────────────┐
│              表现层 (Presentation) — 多客户端                │
│                                                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Web 编辑器    │  │ 微信小程序     │  │ 管理后台 (Admin)  │  │
│  │ Next.js +    │  │ 原生小程序 +  │  │ Next.js +        │  │
│  │ Fabric.js    │  │ Canvas 2D API│  │ shadcn/ui        │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│  职责: WYSIWYG编辑   职责: 浏览/预览/分享   职责: 运营管理    │
├─────────────────────────────────────────────────────────────┤
│                    API 网关层 (Gateway)                      │
│  FastAPI + JWT Auth + Rate Limiter                          │
│  职责: 请求路由、鉴权、限流、用量统计、WebSocket 推送           │
│  ├─ /api/*        → 用户端 API                               │
│  ├─ /api/mini/*   → 小程序专用 API (精简字段 + 微信鉴权)        │
│  └─ /admin/api/*  → 管理后台 API (RBAC 权限)                  │
├─────────────────────────────────────────────────────────────┤
│                    业务逻辑层 (Business)                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │
│  │ AI 调度   │ │ 编译器    │ │ 校验器    │ │ 分发服务      │  │
│  │ Service   │ │ Registry │ │ Validator│ │ Distributor  │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                    │
│  │ 用户服务  │ │ 内容审核  │ │ 用量统计  │                    │
│  │ UserService│ │Moderation│ │ UsageStats│                    │
│  └──────────┘ └──────────┘ └──────────┘                    │
├─────────────────────────────────────────────────────────────┤
│                    异步处理层 (Async Workers)                 │
│  Celery + Valkey                                            │
│  ├─ AI 生成 Worker (LLM 调用 + JSON 解析)                    │
│  ├─ 图像处理 Worker (抠图 + 裁剪 + 压缩)                     │
│  └─ 编译打包 Worker (CDM → WFF XML + ZIP)                   │
├─────────────────────────────────────────────────────────────┤
│                    基础设施层 (Infrastructure)               │
│  S3/OSS 对象存储 + CDN  │  PostgreSQL (元数据)  │  Valkey     │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 编译器注册表模式

```python
# 编译器接口定义 (伪代码)
class BaseCompiler(ABC):
    """所有平台编译器的基类"""
    platform: str  # "wearos" | "apple_watch" | "amazfit"

    @abstractmethod
    def compile(self, cdm: CDMModel) -> CompilationResult:
        """将 CDM JSON 编译为目标平台格式"""
        pass

    @abstractmethod
    def validate_target(self, result: CompilationResult) -> list[ValidationError]:
        """目标平台特定的校验"""
        pass

# 注册表
class CompilerRegistry:
    _compilers: dict[str, type[BaseCompiler]] = {}

    @classmethod
    def register(cls, platform: str):
        def decorator(compiler_cls):
            cls._compilers[platform] = compiler_cls
            return compiler_cls
        return decorator

    @classmethod
    def get(cls, platform: str) -> BaseCompiler:
        if platform not in cls._compilers:
            raise CompilerNotFound(f"No compiler for platform: {platform}")
        return cls._compilers[platform]()
```

**关键设计点：** 新增 Apple Watch 支持只需实现 `AppleWatchCompiler(BaseCompiler)` 并注册，前端代码零改动。

### 2.3 AI 调用网关

```
                    ┌──────────────────────────┐
                    │    AI Gateway Service     │
                    │                          │
  用户提示词 ──────→ │  1. 提示词安全过滤          │
                    │  2. 模型路由 (GPT-4o/      │ ──→ OpenAI API
                    │     Gemini/Imagen)          │ ──→ Gemini API
                    │  3. 密钥轮换管理            │ ──→ Gemini Imagen
                    │  4. 限流 (令牌桶)           │
                    │  5. 用量统计与计费           │
                    │  6. 重试 + 超时熔断         │
                    │  7. 响应缓存               │
                    └──────────────────────────┘
                              │
                              ↓
                    结构化 CDM JSON / 图片 URL
```

---

## 3. 核心数据模型 — CDM JSON 规范

> CDM (Common Data Model) 是平台的**核心契约**，是前端编辑器和后端编译器之间的唯一桥梁。设计得好坏直接决定多平台扩展能力。

### 3.1 顶层结构

```jsonc
{
  "$schema": "https://watchface.platform/cdm/v1.0/schema.json",
  "version": "1.0.0",
  "metadata": {
    "name": "Neon Cyber",
    "author": "user_123",
    "platform": "wearos",          // 目标平台
    "shape": "round",               // round | square
    "resolution": { "width": 384, "height": 384 },
    "preview": "s3://bucket/previews/xxx.png",
    "created_at": "2026-08-12T10:00:00Z",
    "tags": ["cyberpunk", "neon", "minimal"]
  },

  "layers": [ /* 见 3.2 */ ],
  "complications": [ /* 见 3.3 */ ],
  "animations": [ /* 见 3.4 */ ]
}
```

### 3.2 图层数组

每个图层是一个独立可渲染单元，按 `zIndex` 从低到高叠加。

```jsonc
{
  "id": "layer_bg_001",
  "type": "background",            // background | image | text | pointer | progress | arc | group
  "zIndex": 0,

  // 资产引用
  "asset": {
    "kind": "image",               // image | color | gradient
    "src": "s3://bucket/assets/bg_001.png",  // image 时必填
    "color": null,                 // color 时使用
    "gradient": null               // gradient 时使用
  },

  // 变换矩阵
  "transform": {
    "x": 192,                      // 中心 X (画布坐标)
    "y": 192,                      // 中心 Y
    "scale": 1.0,
    "rotation": 0,                 // 度
    "opacity": 1.0
  },

  // 数据绑定 (可选)
  "dataBinding": {
    "source": "steps",             // steps | heartRate | battery | date | time | distance | calories
    "format": "{value}",           // 模板字符串
    "updateInterval": 60           // 秒
  },

  // 文本特有
  "textStyle": {
    "fontFamily": "Orbitron",
    "fontSize": 24,
    "fontWeight": "bold",
    "color": "#00FFFF",
    "align": "center",
    "letterSpacing": 2
  },

  // 指针特有
  "pointer": {
    "type": "hour",                // hour | minute | second
    "pivot": { "x": 192, "y": 192 },
    "length": 120,
    "width": 8
  }
}
```

### 3.3 Complications（数据槽）

```jsonc
{
  "id": "comp_top",
  "slot": "top",                   // top | bottom | left | right | center
  "dataSource": "heartRate",
  "renderer": {
    "type": "text_icon",           // text_icon | icon | range | long_text
    "backgroundColor": "#1A1A2E",
    "textColor": "#00FFFF",
    "iconSrc": "s3://bucket/icons/heart.png"
  }
}
```

### 3.4 动画

```jsonc
{
  "id": "anim_001",
  "target": "layer_pointer_second",
  "trigger": "tick_second",        // tick_second | tick_minute | on_notification | on_tap
  "effect": "rotate",              // rotate | fade | scale | slide
  "duration": 200,                 // 毫秒
  "easing": "ease_out"
}
```

### 3.5 CDM 版本演进策略

| 版本 | 策略 |
|------|------|
| Major (2.0) | 破坏性变更，需提供迁移脚本 |
| Minor (1.x) | 新增可选字段，向后兼容 |
| Patch (1.0.x) | Schema 文档修订，不改结构 |

---

## 4. 技术选型总览与许可证审查

### 4.1 前端技术栈

| 组件 | 版本 | 许可证 | 用途 | 合规 |
|------|------|--------|------|------|
| Next.js | 15+ | MIT | 全栈框架 | ✅ |
| React | 19+ | MIT | UI 库 | ✅ |
| TypeScript | 5.x | Apache 2.0 | 类型系统 | ✅ |
| Tailwind CSS | 4.x | MIT | 样式 | ✅ |
| Fabric.js | 6.x | MIT | Canvas 编辑器核心 | ✅ |
| Zustand | 5.x | MIT | 状态管理 | ✅ |
| React Query (TanStack Query) | 5.x | MIT | 服务端状态 | ✅ |
| shadcn/ui | — | MIT | UI 组件库 | ✅ |
| Lucide React | — | ISC | 图标 | ✅ |
| QRCode.js | 1.x | MIT | 二维码生成 | ✅ |

> **Fabric.js 选择理由:** 原生支持图层、变换、序列化/反序列化，MIT 许可，社区活跃。Konva.js（MIT）为备选方案。

### 4.2 后端技术栈

| 组件 | 版本 | 许可证 | 用途 | 合规 |
|------|------|--------|------|------|
| Python | 3.12+ | PSF (Permissive) | 运行时 | ✅ |
| FastAPI | 0.115+ | MIT | Web 框架 | ✅ |
| Uvicorn | 0.30+ | BSD 3-Clause | ASGI 服务器 | ✅ |
| Pydantic | 2.x | MIT | 数据验证 | ✅ |
| Celery | 5.x | BSD 3-Clause | 异步任务队列 | ✅ |
| Valkey | 8.x | BSD 3-Clause | 消息代理 + 缓存 | ✅ |
| SQLAlchemy | 2.x | MIT | ORM | ✅ |
| Alembic | 1.x | MIT | 数据库迁移 | ✅ |
| Pillow | 11.x | MIT-CMU | 图像处理 | ✅ |
| Rembg | 2.x | MIT | AI 抠图 | ✅ |
| oxipng | 9.x | MIT | PNG 无损压缩 | ✅ |
| onnxruntime | 1.x | MIT | 推理引擎 (Rembg 依赖) | ✅ |
| httpx | 0.27+ | BSD 3-Clause | HTTP 客户端 | ✅ |
| PyJWT | 2.x | MIT | JWT 认证 | ✅ |
| lxml | 5.x | BSD 3-Clause | XML 校验 (WFF XSD) | ✅ |
| Jinja2 | 3.x | BSD 3-Clause | WFF XML 模板引擎 | ✅ |
| apksigner | (Android SDK) | Apache 2.0 | APK 签名 | ✅ |

> **Valkey 替代 Redis 的原因:** Redis 7.4+ 采用 SSPL/RSALv2 双协议，不属于 OSI 认可的开源许可。Valkey 是 Linux Foundation 维护的 BSD 3-Clause 分支，功能兼容，许可证安全。

### 4.3 基础设施

| 组件 | 许可证 | 用途 | 合规 |
|------|--------|------|------|
| PostgreSQL 16 | PostgreSQL License (MIT-like) | 元数据存储 | ✅ |
| AWS S3 / 阿里云 OSS | 商业服务 | 对象存储 | ✅ |
| CloudFront / 阿里云 CDN | 商业服务 | CDN 分发 | ✅ |
| Nginx | BSD 2-Clause | 反向代理 | ✅ |
| Docker | Apache 2.0 | 容器化 | ✅ |

> **明确排除 MinIO** — AGPLv3 许可证，Copyleft 传染风险。使用云厂商 S3/OSS 替代。

### 4.4 明确禁止使用的组件

| 组件 | 许可证 | 禁止原因 |
|------|--------|----------|
| MinIO | AGPLv3 | Copyleft 传染 |
| Redis 7.4+ | SSPL/RSALv2 | 非 OSI 认可开源 |
| pngquant | GPL / 商业双协议 | Copyleft 传染 (用 oxipng 替代) |
| 任何 GPL/AGPL/LGPL 库 | Copyleft | 强制开源衍生作品 |

---

## 5. 开发阶段详解

---

### Phase 1 — MVP：WFF 编译器 + APK 下载安装

> **目标：** 跑通"WFF 编译器 + APK 构建 + 下载安装"核心链路。前端使用固定模板编辑器，不接 AI。验证"导出 → 下载 APK → 安装到手表"的完整流程。

#### 1.1 功能需求

| ID | 需求 | 优先级 | 验收标准 |
|----|------|--------|----------|
| P1-F01 | CDM JSON 模型定义 | P0 | Schema 文件可校验任意 CDM JSON 的合法性 |
| P1-F02 | WFF 编译器 (CDM → WFF XML) | P0 | 输入合法 CDM JSON，输出符合 Google WFF 规范的 XML + 资源目录结构 |
| P1-F03 | APK 构建器 | P0 | 将 WFF XML + 资源打包为签名后的 WFF APK (hasCode=false) |
| P1-F04 | WFF 静态校验器 | P0 | 使用 Google 官方 XSD 校验器校验 XML 语法、图片分辨率、资源大小 |
| P1-F05 | 固定模板编辑器 (前端) | P0 | 预设 3 个模板（极简数字、指针+数字、赛博风），用户可切换并微调颜色 |
| P1-F06 | APK 下载端点 | P0 | 提供签名 WFF APK 的 HTTPS 下载链接 (CDN 加速) |
| P1-F07 | 安装引导页 | P0 | 引导用户安装 Wear Installer，并通过它将 APK 推送到手表 |
| P1-F08 | 二维码生成 | P1 | 下载页面生成扫码下载 APK 的二维码 |

#### 1.2 WFF 编译器详细设计

```
输入: CDM JSON
  │
  ├── 1. 解析 & 验证 CDM
  │     └─ Pydantic 模型校验
  │
  ├── 2. 资源准备
  │     ├─ 下载远程图片到临时目录
  │     ├─ 校验图片分辨率 (≤ 384×384 for round)
  │     └─ 生成 APK 资源目录结构
  │         res/
  │         ├─ raw/
  │         │   └─ watchface.xml          ← WFF 主文件
  │         ├─ drawable/
  │         │   ├─ background.png
  │         │   ├─ hour_hand.png
  │         │   └─ minute_hand.png
  │         ├─ font/
  │         │   └─ custom_font.ttf
  │         └── values/
  │             └── strings.xml
  │
  ├── 3. XML 生成
  │     └─ 根据 CDM layers 生成 <WatchFace> XML 树
  │         <WatchFace>
  │           <Scene>
  │             <Group ...>
  │               <PartImage .../>
  │               <PartText .../>
  │               < analog hands .../>
  │             </Group>
  │           </Scene>
  │         </WatchFace>
  │
  ├── 4. 校验
  │     └─ Google 官方 WFF XSD 校验器 (github.com/google/watchface, Apache 2.0)
  │
  └── 5. APK 构建 (纯 Python, 无需 aapt2)
        ├─ 加载预编译模板 (Docker 构建时用 aapt2 生成, 二进制 AXML + resources.arsc)
        ├─ Python zipfile 打包: 模板 + 动态 res/raw/watchface.xml + res/drawable/*.png
        ├─ pyzipalign 对齐 (纯 Python 实现, 通过官方 zipalign -c 验证)
        └─ apksigner 签名 (bash + Java JAR, ARM64 兼容)
        └─ 输出 watchface.apk (签名后, v1+v2+v3)
```

#### 1.3 分发与安装机制

> **⚠️ 架构变更说明 (2026-08-12):**
> 原方案设计的 `intent:// URI` 唤起 Wear OS App 安装 WFF ZIP 的机制 **经官方文档验证不存在**。
> Google 官方分发方式只有三种：Play Store、Watch Face Push API (Wear OS 6+)、ADB sideload。
> 一期采用 "APK 下载 + Wear Installer" 方案，二期评估 Companion App + Watch Face Push API。

**一期安装流程 (APK 下载 + Wear Installer):**

```
用户在 Web 端点击"安装到手表"
  │
  ├── 1. 后端编译生成签名 WFF APK
  │
  ├── 2. 前端展示安装引导页:
  │     ├─ 步骤 A: 手机安装 "Wear Installer" (Play Store 链接)
  │     │   └─ Wear Installer 是开源工具 (Apache 2.0)，可从 Play Store 免费安装
  │     │   └─ 一次性安装，后续无需重复
  │     ├─ 步骤 B: 下载表盘 APK (点击或扫码)
  │     └─ 步骤 C: 在 Wear Installer 中打开 APK，推送到手表
  │
  ├── 3. Wear Installer 通过蓝牙将 APK 推送到手表
  │
  └── 4. 手表弹出安装确认 → 安装完成
```

**二期安装流程 (Companion App + Watch Face Push API):**

```
用户在 Web 端点击"安装到手表"
  │
  ├── 1. 后端编译生成签名 WFF APK + 获取 validation token
  ├── 2. Companion App (已安装在用户手机上) 接收推送通知
  ├── 3. Companion App 通过 Watch Face Push API 安装表盘
  │     └─ 手机端 App → Data Layer API → 手表端 Service → 安装
  └── 4. 手表弹出安装确认 → 安装完成 (需 Wear OS 6+)
```

**三种方案对比:**

| 方案 | UX 体验 | 门槛 | 设备覆盖 | 一期/二期 |
|------|--------|------|---------|----------|
| APK 下载 + Wear Installer | ⚠️ 中等 (需装 Wear Installer) | 低 | Wear OS 4+ | ✅ 一期 |
| Companion App + WFP API | ✅ 好 (一键安装) | 高 (需开发 App) | 仅 Wear OS 6+ | 二期 |
| Play Store 发布 | ✅ 最好 | 中 (审核流程) | 所有 Wear OS | 不适合 (无法即时分发) |

#### 1.4 架构图 (Phase 1)

```
┌─────────────────┐         ┌──────────────────────────┐
│  Next.js 前端    │         │  FastAPI 后端              │
│                 │         │                          │
│  模板选择器      │  HTTP   │  /api/templates           │
│  颜色微调       │ ──────→  │  /api/compile             │
│  预览圆/方画布   │         │  /api/download/{id}       │
│  APK下载+引导    │  ←────── │  /api/install-guide/{id}  │
│                 │         │                          │
└─────────────────┘         │  WFF Compiler Module     │
                            │  WFF XSD Validator       │
                            │  APK Builder (aapt2)     │
                            │                          │
                            │  S3/OSS 存储 (APK+CDN)   │
                            └──────────────────────────┘
```

#### 1.5 技术选型 (Phase 1 特有)

| 层 | 技术 | 说明 |
|----|------|------|
| 前端框架 | Next.js 15 (App Router) | SSR + CSR 混合 |
| Canvas | Fabric.js 6 | 仅用于预览渲染，Phase 1 不启用编辑 |
| 后端框架 | FastAPI | 异步 Python Web 框架 |
| 编译器 | 纯 Python 实现 | 基于 Jinja2 (BSD) 模板引擎生成 XML |
| XML 校验 | lxml (BSD) + Google WFF XSD (Apache 2.0) | 使用 github.com/google/watchface 官方 XSD |
| APK 构建 | Python zipfile + pyzipalign + apksigner | 纯 Python 打包+对齐, Java 签名, ARM64 兼容 |
| APK 模板编译 | aapt2 (Docker 构建时, x86) | 一次性预编译 AndroidManifest.xml → 二进制 AXML |
| APK 签名密钥 | 自签名 RSA 密钥 (keytool) | 需妥善保管，泄露后需轮换 |
| 存储 | 阿里云 OSS + CDN | 存储 APK 文件，CDN 加速下载 |

> **Jinja2 许可证:** BSD 3-Clause ✅。用于 XML 模板渲染，避免硬编码字符串拼接。

#### 1.6 数据库设计 (最小集)

```sql
-- 表盘项目表
CREATE TABLE watchface_projects (
    id          UUID PRIMARY KEY,
    user_id     UUID NOT NULL,
    name        VARCHAR(100) NOT NULL,
    cdm_json    JSONB NOT NULL,
    status      VARCHAR(20) DEFAULT 'draft',  -- draft | compiled | published
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- 编译产物表
CREATE TABLE compilation_artifacts (
    id          UUID PRIMARY KEY,
    project_id  UUID REFERENCES watchface_projects(id),
    platform    VARCHAR(20) NOT NULL,          -- wearos
    apk_url     TEXT NOT NULL,             -- CDN URL of signed APK
    apk_hash    VARCHAR(64),
    xml_hash    VARCHAR(64),
    status      VARCHAR(20) DEFAULT 'pending', -- pending | success | failed
    errors      JSONB,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
```

#### 1.7 交付物清单

- [ ] CDM JSON Schema 文件 (`schema/cdm/v1.0.json`)
- [ ] WFF 编译器 Python 包 (`compiler/wff/`)
- [ ] Google WFF XSD 校验器集成 (`validator/`)
- [ ] APK 构建器 (aapt2 + zipalign + apksigner 管线)
- [ ] FastAPI 后端服务 (`api/`)
- [ ] Next.js 前端 — 3 个固定模板 (`web/`)
- [ ] APK 下载端点 + 安装引导页
- [ ] Docker Compose 开发环境配置 (含 Android Build Tools)
- [ ] 基础测试：编译器单元测试 + APK 构建测试 + API 集成测试

#### 1.8 Phase 1 验收标准

| 验收项 | 标准 |
|--------|------|
| 编译正确性 | 3 个预设模板均可成功编译为 WFF XML，通过 Google 官方 XSD 校验 |
| APK 构建成功 | WFF XML + 资源可成功打包为签名 APK，APK 大小 < 500KB |
| 安装验证 | 生成的 APK 可通过 Wear Installer 在真实 Wear OS 手表上安装 |
| 响应时间 | 编译 + APK 构建 < 5 秒 (标准模板) |
| 错误处理 | 非法 CDM 输入返回结构化错误信息 |

---

### Phase 2 — AI 接入：自然语言生成闭环

> **目标：** 接入 GPT-4o 解析用户提示词生成 CDM JSON，接入 Gemini 生成表盘背景图。跑通"提示词 → 生成 CDM → 渲染到 Canvas → 导出 WFF"完整闭环。

#### 2.1 功能需求

| ID | 需求 | 优先级 | 验收标准 |
|----|------|--------|----------|
| P2-F01 | AI 网关服务 | P0 | 统一封装 OpenAI/Gemini API 调用，支持密钥轮换和限流 |
| P2-F02 | 提示词 → CDM JSON | P0 | 用户输入自然语言描述，GPT-4o 输出合法 CDM JSON |
| P2-F03 | 背景图生成 | P0 | 调用 Gemini Imagen 生成表盘背景图，Pillow 缩放到 384×384 |
| P2-F04 | Canvas 渲染 CDM | P0 | 前端接收 CDM JSON，在 Fabric.js Canvas 上正确渲染所有图层 |
| P2-F05 | 生成结果可编辑 | P1 | AI 生成的 CDM 可在编辑器中进一步微调 |
| P2-F06 | 生成进度反馈 | P0 | 通过 WebSocket 实时推送生成进度 |
| P2-F07 | 用量统计 | P1 | 记录每个用户的 API 调用次数和 Token 消耗 |

#### 2.2 AI 提示词工程

> **技术方案 (2026-08-12 验证修订):** 使用 GPT-4o **Structured Outputs** (strict mode) 而非 JSON Mode。
> Structured Outputs 通过 JSON Schema 强约束输出格式，比 JSON Mode 更可靠。
> 但仍需后端二次校验 + 自动修复，首次成功率约 60-70%，重试后 ≥ 80%。

**GPT-4o Structured Outputs 调用:**

```python
from openai import OpenAI
from pydantic import BaseModel

# 定义 CDM JSON Schema (传给 GPT-4o Structured Outputs)
class CDMSchema(BaseModel):
    """CDM v1.0 Schema for GPT-4o Structured Outputs"""
    version: str = "1.0.0"
    metadata: MetadataSchema
    layers: list[LayerSchema]
    complications: list[ComplicationSchema]
    animations: list[AnimationSchema] = []

# 调用
response = client.beta.chat.completions.parse(
    model="gpt-4o-2024-08-06",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ],
    response_format=CDMSchema,  # Structured Outputs strict mode
)
cdm = response.choices[0].message.parsed  # 直接拿到 Pydantic 对象
```

**System Prompt:**

```
你是一个 Wear OS 表盘设计助手。用户会描述他们想要的表盘样式。
你需要输出一个符合 CDM JSON v1.0 规范的对象。

规则:
1. 画布尺寸固定 384×384
2. 图片素材先用占位描述: "ai_asset://{描述}" (后端后续替换为真实 URL)
3. 数据绑定只能使用标准数据源: steps, heartRate, battery, date, time
4. 图层数量 ≤ 15 个
5. 指针类表盘必须包含 hour, minute 指针
6. 所有坐标必须在 0-384 范围内
7. zIndex 从 0 开始递增
```

**CDM 自动修复层 (后端):**

```python
class CDMAutoFixer:
    """对 GPT-4o 输出的 CDM 进行自动修复"""
    
    def fix(self, cdm: CDMModel) -> CDMModel:
        # 1. 坐标 clamp 到画布范围
        for layer in cdm.layers:
            layer.transform.x = max(0, min(384, layer.transform.x))
            layer.transform.y = max(0, min(384, layer.transform.y))
        
        # 2. zIndex 去重 + 排序
        z_indices = sorted(set(l.zIndex for l in cdm.layers))
        for i, layer in enumerate(sorted(cdm.layers, key=lambda l: l.zIndex)):
            layer.zIndex = i
        
        # 3. 超限图层裁剪 (保留前 15 个)
        if len(cdm.layers) > 15:
            cdm.layers = cdm.layers[:15]
        
        # 4. 指针表盘必须有 hour + minute
        has_pointer = any(l.type == 'pointer' for l in cdm.layers)
        if has_pointer:
            pointer_types = [l.subtype for l in cdm.layers if l.type == 'pointer']
            if 'hour' not in pointer_types or 'minute' not in pointer_types:
                # 补充缺失的指针
                cdm.layers.extend(self._create_default_pointers())
        
        return cdm
```

**提示词安全过滤层:**
- 拒绝包含暴力、色情、政治敏感的提示词
- 使用 OpenAI Moderation API 预过滤

#### 2.3 AI 网关架构

```python
# 伪代码: AI Gateway 核心设计
class AIGateway:
    """
    AI 调用统一网关
    - 密钥管理: 多密钥轮换，单密钥限流时自动切换
    - 限流: 令牌桶算法，按用户和按全局双重限流
    - 重试: 指数退避，最多 3 次
    - 熔断: 5 分钟内失败率 > 50% 时熔断 1 分钟
    - 缓存: 相同提示词 1 小时内返回缓存结果
    """

    providers: dict[str, AIProvider]  # openai, gemini
    key_pool: APIKeyPool
    rate_limiter: TokenBucket
    circuit_breaker: CircuitBreaker
    cache: ResponseCache

    async def generate_cdm(self, prompt: str, user_id: str) -> CDMModel:
        # 1. 安全过滤
        await self.moderate(prompt)
        # 2. 限流检查
        await self.rate_limiter.acquire(user_id)
        # 3. 模型路由
        provider = self.route_model("text_to_cdm")
        # 4. 调用 (带重试 + 熔断)
        response = await self.call_with_resilience(provider, prompt)
        # 5. 解析 & 校验
        cdm = CDMModel.model_validate_json(response)
        return cdm

    async def generate_image(self, prompt: str, user_id: str) -> str:
        """返回图片 URL"""
        provider = self.route_model("text_to_image")
        image_url = await self.call_with_resilience(provider, prompt)
        return image_url
```

#### 2.4 异步任务流 (Phase 2 简化版)

> Phase 2 使用 Celery 但不引入完整图像后处理（Phase 3 才做）。

```python
# Celery 任务链
@celery.task
def generate_watchface_task(prompt: str, user_id: str):
    """
    完整生成链路:
    1. GPT-4o 生成 CDM JSON
    2. 提取所有 ai_asset:// 占位符
    3. 并行调用 Gemini 生成图片
    4. 替换占位符为真实 URL
    5. 保存 CDM 到数据库
    6. WebSocket 通知前端
    """
    chain = (
        generate_cdm.s(prompt, user_id)           # GPT-4o
        | extract_asset_prompts.s()               # 解析占位符
        | generate_images.s()                      # 并行 Gemini 调用
        | replace_placeholders.s()                # 替换 URL
        | save_cdm.s(user_id)                     # 持久化
        | notify_frontend.s(user_id)              # WebSocket 推送
    )
    chain.apply_async()
```

#### 2.5 WebSocket 进度推送

```python
# FastAPI WebSocket
@app.websocket("/ws/generation/{task_id}")
async def generation_progress(websocket: WebSocket, task_id: str):
    await websocket.accept()
    async for event in task_progress_stream(task_id):
        await websocket.send_json({
            "task_id": task_id,
            "stage": event.stage,        # "parsing" | "image_gen" | "compiling"
            "progress": event.progress,  # 0-100
            "message": event.message
        })
```

#### 2.6 前端 Canvas 渲染器

```typescript
// CDM → Fabric.js 渲染器
class CDMRenderer {
  constructor(private canvas: fabric.Canvas) {}

  async render(cdm: CDMModel): Promise<void> {
    this.canvas.clear()

    // 按 zIndex 排序
    const sorted = [...cdm.layers].sort((a, b) => a.zIndex - b.zIndex)

    for (const layer of sorted) {
      const fabricObj = await this.layerToFabricObject(layer)
      this.canvas.add(fabricObj)
    }

    // 渲染 Complications
    for (const comp of cdm.complications) {
      const obj = await this.complicationToFabricObject(comp)
      this.canvas.add(obj)
    }

    this.canvas.renderAll()
  }

  private async layerToFabricObject(layer: CDMLayer): Promise<fabric.Object> {
    switch (layer.type) {
      case 'background':
        return this.createBackground(layer)
      case 'image':
        return this.createImage(layer)
      case 'text':
        return this.createText(layer)
      case 'pointer':
        return this.createPointer(layer)
      // ...
    }
  }
}
```

#### 2.7 交付物清单

- [ ] AI Gateway 服务 (`services/ai_gateway/`)
- [ ] GPT-4o Structured Outputs 调用 + CDM 解析器
- [ ] CDM 自动修复层 (`services/cdm_autofixer/`)
- [ ] Gemini Imagen 图片生成服务 (含 Pillow 缩放后处理)
- [ ] Celery 任务链 (`tasks/generation/`)
- [ ] WebSocket 进度推送端点
- [ ] 前端 Canvas 渲染器 (`web/lib/cdm-renderer/`)
- [ ] 提示词输入 UI
- [ ] 用量统计仪表盘
- [ ] AI 集成测试

#### 2.8 Phase 2 验收标准

| 验收项 | 标准 |
|--------|------|
| 首次生成成功率 | ≥ 60% 的提示词首次即可生成合法 CDM JSON |
| 重试后成功率 | ≥ 80% (含自动修复 + 1 次重试) |
| 图片质量 | Gemini Imagen 生成 → Pillow 缩放到 384×384，视觉质量可接受 |
| 端到端延迟 | 提示词 → 可预览 CDM < 30 秒 |
| 进度可见 | 用户全程可看到生成阶段和进度百分比 |
| 限流生效 | 单用户 10 次/小时，超出返回 429 |

---

### Phase 3 — 完整体验：编辑器 + 图像处理 + 异步队列

> **目标：** 实现完整的 WYSIWYG 可视化编辑器、AI 图片后处理（抠图/裁剪/压缩）、完善的异步任务队列。用户可对 AI 生成结果进行精细编辑。

#### 3.1 功能需求

##### 3.1.1 可视化编辑器

| ID | 需求 | 优先级 | 验收标准 |
|----|------|--------|----------|
| P3-F01 | 拖拽图层 | P0 | 鼠标拖拽图层到任意位置，实时更新 CDM transform |
| P3-F02 | 缩放图层 | P0 | 角点拖拽缩放，等比/自由模式切换 |
| P3-F03 | 旋转图层 | P0 | 旋转手柄，15° 步进吸附可选 |
| P3-F04 | 图层面板 | P0 | 展示所有图层列表，支持拖拽排序、显隐切换、锁定 |
| P3-F05 | 属性面板 | P0 | 选中图层后展示可编辑属性（颜色、透明度、字号等） |
| P3-F06 | 数据绑定面板 | P0 | 下拉选择数据源（步数/心率/电量/日期/时间） |
| P3-F07 | 撤销/重做 | P0 | 历史栈，Ctrl+Z / Ctrl+Y |
| P3-F08 | 圆形/方形画布切换 | P0 | 一键切换预览模式，圆形模式下裁剪边角 |
| P3-F09 | 导出 CDM JSON | P1 | 可手动导出当前编辑器的 CDM JSON |

##### 3.1.2 图像后处理

| ID | 需求 | 优先级 | 验收标准 |
|----|------|--------|----------|
| P3-F10 | 自动抠图 | P0 | Rembg 自动去除图片背景，输出透明 PNG |
| P3-F11 | 智能裁剪 | P0 | 自动检测主体，裁剪到最小包围盒 |
| P3-F12 | 尺寸压缩 | P0 | 压缩到 WFF 规范要求 (单图 ≤ 100KB) |
| P3-F13 | 批量处理 | P1 | 支持一次处理多张图片 |

##### 3.1.3 异步队列完善

| ID | 需求 | 优先级 | 验收标准 |
|----|------|--------|----------|
| P3-F14 | 任务优先级 | P1 | VIP 用户任务优先调度 |
| P3-F15 | 任务重试 | P0 | 失败任务自动重试 3 次，指数退避 |
| P3-F16 | 死信队列 | P0 | 重试耗尽的任务进入死信队列，可手动重放 |
| P3-F17 | 任务监控 | P1 | Celery Flower 监控面板 |
| P3-F18 | 任务取消 | P1 | 用户可取消进行中的生成任务 |

##### 3.1.4 动态模拟校验

| ID | 需求 | 优先级 | 验收标准 |
|----|------|--------|----------|
| P3-F19 | 圆形屏模拟 | P0 | 预览圆形屏幕下的裁剪效果 |
| P3-F20 | 方形屏模拟 | P0 | 预览方形屏幕下的完整渲染 |
| P3-F21 | D-pad 切边模拟 | P1 | 模拟 Wear OS D-pad 导航时的切边区域 |
| P3-F22 | 时间模拟 | P0 | 可拖动时间轴，预览不同时间下指针/数据的变化 |

#### 3.2 图像后处理管线

```
AI 生成的原始图片 (带背景)
  │
  ├── 1. 格式转换
  │     └─ 统一转为 PNG
  │
  ├── 2. 自动抠图 (Rembg)
  │     └─ u2net 模型推理，去除背景
  │     └─ 输出透明 PNG
  │
  ├── 3. 智能裁剪
  │     └─ 检测 alpha 通道最小包围盒
  │     └─ 裁剪到内容区域
  │
  ├── 4. 尺寸规范化
  │     └─ 缩放到 WFF 要求尺寸 (指针长度、图标尺寸)
  │     └─ 保持长宽比
  │
  ├── 5. 压缩
  │     └─ oxipng 无损压缩 (MIT 许可, level 3)
  │     └─ 目标: 单图 ≤ 100KB
  │
  ├── 6. 校验
  │     └─ 分辨率 ≤ 384×384
  │     └─ 文件大小 ≤ 100KB
  │     └─ 格式为 PNG
  │
  └── 7. 上传
        └─ 存储到 S3/OSS
        └─ 返回 CDN URL
```

#### 3.3 Celery 任务架构

```python
# 任务类型定义
CELERY_TASK_ROUTES = {
    'tasks.ai.generate_cdm':       {'queue': 'ai_text'},
    'tasks.ai.generate_image':     {'queue': 'ai_image'},
    'tasks.image.remove_bg':       {'queue': 'image_processing'},
    'tasks.image.crop_and_resize':  {'queue': 'image_processing'},
    'tasks.image.compress':         {'queue': 'image_processing'},
    'tasks.compile.wff':            {'queue': 'compilation'},
}

# Worker 配置
# ai_text Worker:         2 并发 (API 限流约束)
# ai_image Worker:        3 并发
# image_processing Worker: 4 并发 (CPU 密集)
# compilation Worker:      2 并发
```

#### 3.4 前端编辑器架构

```
web/
├── components/
│   ├── editor/
│   │   ├── CanvasStage.tsx          # Canvas 舞台容器
│   │   ├── Toolbar.tsx              # 顶部工具栏
│   │   ├── LayerPanel.tsx           # 右侧图层面板
│   │   ├── PropertyPanel.tsx        # 右侧属性面板
│   │   ├── DataBindingPanel.tsx     # 数据绑定面板
│   │   └── TimelineSimulator.tsx    # 时间模拟器
│   ├── canvas/
│   │   ├── FabricCanvas.tsx         # Fabric.js Canvas 封装
│   │   ├── CDMRenderer.ts           # CDM → Fabric 渲染
│   │   ├── CDMExporter.ts           # Fabric → CDM 导出
│   │   └── interactions/
│   │       ├── DragHandler.ts       # 拖拽处理
│   │       ├── ResizeHandler.ts     # 缩放处理
│   │       └── RotateHandler.ts    # 旋转处理
│   ├── preview/
│   │   ├── RoundPreview.tsx         # 圆形屏预览
│   │   ├── SquarePreview.tsx        # 方形屏预览
│   │   └── DPadOverlay.tsx          # D-pad 切边叠加
│   └── ai/
│       ├── PromptInput.tsx          # 提示词输入
│       └── GenerationProgress.tsx   # 生成进度
├── stores/
│   ├── editorStore.ts               # Zustand: 编辑器状态
│   ├── cdmStore.ts                  # Zustand: CDM 数据
│   └── historyStore.ts              # Zustand: 撤销/重做栈
└── lib/
    ├── cdm/
    │   ├── types.ts                 # CDM TypeScript 类型
    │   ├── validator.ts             # 前端 CDM 校验
    │   └── migration.ts             # CDM 版本迁移
    └── fabric/
        └── extensions.ts            # Fabric.js 自定义扩展
```

#### 3.5 撤销/重做设计

```typescript
// 命令模式 + 快照模式混合
interface HistoryCommand {
  type: 'add' | 'delete' | 'modify' | 'reorder'
  layerId: string
  before: Partial<CDMLayer>   // 变更前快照
  after: Partial<CDMLayer>    // 变更后快照
  timestamp: number
}

class HistoryManager {
  private undoStack: HistoryCommand[] = []
  private redoStack: HistoryCommand[] = []
  private maxSize = 50

  push(cmd: HistoryCommand) {
    this.undoStack.push(cmd)
    this.redoStack = []          // 新操作清空 redo
    if (this.undoStack.length > this.maxSize) {
      this.undoStack.shift()     // 丢弃最旧
    }
  }

  undo(): HistoryCommand | null { /* ... */ }
  redo(): HistoryCommand | null { /* ... */ }
}
```

#### 3.6 交付物清单

- [ ] 完整 WYSIWYG 编辑器前端
- [ ] Fabric.js 交互层 (拖拽/缩放/旋转)
- [ ] 图层面板 + 属性面板
- [ ] 数据绑定面板
- [ ] 撤销/重做系统
- [ ] 圆形/方形/D-pad 模拟预览
- [ ] 时间模拟器
- [ ] Rembg 图像后处理 Worker
- [ ] 图片压缩 + 尺寸规范管线
- [ ] Celery 完整任务队列 (优先级/重试/死信)
- [ ] Celery Flower 监控
- [ ] 任务取消功能

#### 3.7 Phase 3 验收标准

| 验收项 | 标准 |
|--------|------|
| 编辑器响应 | 拖拽/缩放延迟 < 16ms (60fps) |
| 抠图质量 | Rembg 抠图成功率 ≥ 85%，边缘锯齿 ≤ 2px |
| 图片压缩 | 单图压缩后 ≤ 100KB，视觉质量损失可接受 |
| 队列可靠性 | 任务失败率 < 5%，死信队列可重放 |
| 模拟准确度 | 模拟预览与真实手表渲染差异 < 5% |

---

### Phase 4 — 多端拓展：Apple Watch 编译器【二期工程】

> **目标：** 新增 Apple Watch (.watchface) 编译器，验证编译器可插拔架构。前端零改动即可支持 Apple Watch 表盘导出。
> **⚠️ 二期：** 一期 (Phase 1-3) 不实现。但一期架构设计必须保证 CDM 模型和编译器接口不阻碍本阶段。

#### 4.1 功能需求

| ID | 需求 | 优先级 | 验收标准 |
|----|------|--------|----------|
| P4-F01 | Apple Watch 编译器 | P0 | CDM JSON → Apple Watch 表盘格式，通过 Apple 校验 |
| P4-F02 | 平台切换 UI | P0 | 前端编辑器顶部新增平台选择器 (Wear OS / Apple Watch) |
| P4-F03 | 平台特定校验 | P0 | 针对 Apple Watch 的分辨率/资源校验规则 |
| P4-F04 | 平台特定预览 | P1 | Apple Watch 屏幕形状预览 (矩形带圆角) |
| P4-F05 | Apple Watch 安装链路 | P1 | 生成 Apple Watch 安装包并提供安装指引 |

#### 4.2 编译器实现

```python
@CompilerRegistry.register("apple_watch")
class AppleWatchCompiler(BaseCompiler):
    """Apple Watch 表盘编译器"""

    platform = "apple_watch"

    def compile(self, cdm: CDMModel) -> CompilationResult:
        """
        CDM → Apple Watch 表盘格式

        Apple Watch 表盘结构:
        - 使用 ClockKit 框架
        - 复杂体 (Complications) 对应 CDM 的 complications
        - 颜色/布局映射

        注意: Apple Watch 表盘分发受 Apple 限制，
        可能需要通过 companion app 或 TestFlight 分发。
        """
        # 1. 平台差异映射
        apple_cdm = self.map_platform_diffs(cdm)

        # 2. 生成表盘资源
        resources = self.generate_resources(apple_cdm)

        # 3. 生成 .watchface 包
        package = self.package(apple_cdm, resources)

        return CompilationResult(
            platform="apple_watch",
            artifacts=package,
            metadata={...}
        )

    def map_platform_diffs(self, cdm: CDMModel) -> CDMModel:
        """
        平台差异处理:
        - 分辨率: Wear OS 384×384 → Apple Watch 430×352 (Series 10)
        - 形状: Wear OS 圆形 → Apple Watch 圆角矩形
        - Complication slots 映射
        """
        # 缩放坐标
        scale_x = 430 / cdm.metadata.resolution.width
        scale_y = 352 / cdm.metadata.resolution.height
        # ... 坐标变换
```

#### 4.3 平台差异处理矩阵

| 维度 | Wear OS | Apple Watch | 处理策略 |
|------|---------|-------------|----------|
| 屏幕形状 | 圆形 / 方形 | 圆角矩形 | 编译器自动适配 |
| 分辨率 | 384×384 | 484×396 (Ultra 2) | 坐标比例缩放 |
| Complication 位置 | top/bottom/left/right | corner/inline/modular | 位置映射表 |
| 指针样式 | 自定义图片 | 系统样式优先 | 降级策略 |
| 分发方式 | intent:// URI | companion app / TestFlight | 分平台分发服务 |
| 字体 | 自定义 TTF | 系统字体 + 自定义 | 字体回退 |

#### 4.4 前端平台切换 (零改动验证)

```typescript
// 前端只需切换 platform 字段，无需任何业务逻辑改动
const cdm: CDMModel = {
  ...currentCDM,
  metadata: {
    ...currentCDM.metadata,
    platform: selectedPlatform  // "wearos" | "apple_watch"
  }
}

// 编译请求
const result = await api.post('/compile', { cdm })
// 后端 CompilerRegistry 自动路由到对应编译器
```

#### 4.5 交付物清单

- [ ] Apple Watch 编译器 (`compiler/apple_watch/`)
- [ ] 平台差异映射模块
- [ ] Apple Watch 校验规则
- [ ] 前端平台选择器
- [ ] Apple Watch 预览模式
- [ ] Apple Watch 安装链路 (companion app 或指引)
- [ ] 多平台编译集成测试

#### 4.6 Phase 4 验收标准

| 验收项 | 标准 |
|--------|------|
| 架构验证 | 新增 Apple Watch 编译器，前端代码 0 行改动 |
| 编译正确性 | Apple Watch 表盘可通过 Apple 校验 |
| 平台切换 | 切换平台后预览正确渲染 |
| 坐标映射 | 图层位置在不同分辨率下等比例正确映射 |

---

### Phase 5 — 微信小程序：轻量客户端与社交分发【二期工程】

> **目标：** 构建微信小程序客户端，实现表盘浏览、预览渲染、社交分享、扫码安装。验证"多客户端共享 CDM + API"架构——小程序不跑 Fabric.js，用原生 Canvas 2D API 渲染 CDM。
> **⚠️ 二期：** 一期 (Phase 1-3) 不实现。但一期 API 设计需预留 `/api/mini/*` 路由前缀和字段裁剪能力。

#### 5.1 设计定位

| 维度 | Web 编辑器 | 微信小程序 |
|------|-----------|-----------|
| 角色 | 全功能编辑器 | 轻量浏览/预览/分发客户端 |
| 渲染引擎 | Fabric.js | 原生 Canvas 2D API |
| AI 生成 | ✅ 完整支持 | ❌ 不支持（跳转 Web 端） |
| 图层编辑 | ✅ 完整 WYSIWYG | ❌ 只读预览 |
| 模拟预览 | ✅ 圆/方/D-pad/时间轴 | ✅ 简化版圆/方预览 |
| 表盘浏览 | ✅ 社区/我的 | ✅ 社区/我的/精选 |
| 分享 | ✅ 短链接 | ✅ 微信原生分享 + 小程序码 |
| 一键安装 | ✅ intent:// URI | ⚠️ 跳转浏览器触发 intent:// |
| 数据绑定预览 | ✅ 实时模拟 | ✅ 静态截图模拟 |

> **核心原则：** 小程序不做编辑，只做消费端。所有数据通过同一套 `/api/mini/*` 端点获取，CDM JSON 是唯一数据源。

#### 5.2 功能需求

| ID | 需求 | 优先级 | 验收标准 |
|----|------|--------|----------|
| P5-F01 | 小程序框架搭建 | P0 | uni-app/Taro 构建，基础导航和鉴权 |
| P5-F02 | 微信登录鉴权 | P0 | wx.login → code2session → 绑定平台账号 |
| P5-F03 | CDM 渲染器 (Canvas 2D) | P0 | 将 CDM JSON 渲染到小程序 Canvas，支持图层/指针/文本 |
| P5-F04 | 表盘浏览页 | P0 | 精选/最新/热门列表，分页加载 |
| P5-F05 | 表盘详情预览 | P0 | 圆形/方形预览切换，时间模拟 |
| P5-F06 | 小程序码分享 | P0 | 生成小程序码，扫码直达表盘详情 |
| P5-F07 | 安装引导 | P0 | 生成 intent:// 链接，引导用户在浏览器中打开安装 |
| P5-F08 | 我的表盘 | P1 | 用户已创建/已收藏的表盘列表 |
| P5-F09 | 轻量 AI 生成 (模板) | P2 | 基于预设模板快速生成（选风格+选颜色），非自由提示词 |
| P5-F10 | 数据上报 | P1 | 小程序埋点：浏览/PV/UV/分享次数 |

#### 5.3 小程序 CDM 渲染器

```typescript
// 小程序端 CDM → Canvas 2D 渲染 (Taro/uni-app 通用逻辑)
// 注意：不能用 Fabric.js，小程序 Canvas 2D API 是原生的

class MiniCDMRenderer {
  constructor(private canvas: Canvas, private ctx: CanvasRenderingContext2D) {}

  async render(cdm: CDMModel): Promise<void> {
    // 1. 清空画布
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height)

    // 2. 设置圆形裁剪 (如果是 round 表盘)
    if (cdm.metadata.shape === 'round') {
      this.ctx.beginPath()
      this.ctx.arc(
        this.canvas.width / 2, this.canvas.height / 2,
        this.canvas.width / 2, 0, Math.PI * 2
      )
      this.ctx.clip()
    }

    // 3. 按 zIndex 排序渲染
    const sorted = [...cdm.layers].sort((a, b) => a.zIndex - b.zIndex)
    for (const layer of sorted) {
      await this.renderLayer(layer)
    }

    // 4. 渲染 Complications
    for (const comp of cdm.complications) {
      await this.renderComplication(comp)
    }
  }

  private async renderLayer(layer: CDMLayer): Promise<void> {
    this.ctx.save()

    // 变换
    this.ctx.translate(layer.transform.x, layer.transform.y)
    this.ctx.rotate(layer.transform.rotation * Math.PI / 180)
    this.ctx.scale(layer.transform.scale, layer.transform.scale)
    this.ctx.globalAlpha = layer.transform.opacity

    switch (layer.type) {
      case 'background':
        await this.drawBackground(layer)
        break
      case 'image':
        await this.drawImage(layer)
        break
      case 'text':
        this.drawText(layer)
        break
      case 'pointer':
        await this.drawPointer(layer)
        break
    }

    this.ctx.restore()
  }

  // 数据绑定模拟 (静态值，非实时)
  private resolveDataBinding(binding?: DataBinding): string {
    if (!binding) return ''
    const mockValues: Record<string, string> = {
      steps: '8,432',
      heartRate: '72',
      battery: '85%',
      date: '08/12',
      time: '10:42'
    }
    const val = mockValues[binding.source] || ''
    return binding.format.replace('{value}', val)
  }
}
```

#### 5.4 小程序专用 API 设计

```
/api/mini/auth/login          POST   wx.login code → JWT
/api/mini/watchfaces          GET    精选/最新/热门列表 (分页)
/api/mini/watchfaces/{id}     GET    表盘详情 + CDM JSON
/api/mini/watchfaces/{id}/preview GET  预览截图 URL
/api/mini/watchfaces/{id}/install GET  intent:// URI + 浏览器跳转 URL
/api/mini/share/qrcode       POST   生成小程序码
/api/mini/user/watchfaces     GET    我的表盘
/api/mini/user/favorites     GET    我的收藏
```

> **API 字段裁剪原则：** `/api/mini/*` 返回的 CDM JSON 只包含渲染必需字段，剥离编辑器元数据（如 history、dirty flags），减少传输体积。

#### 5.5 技术选型 (Phase 5 特有)

| 层 | 技术 | 许可证 | 说明 |
|----|------|--------|------|
| 小程序框架 | **Taro 4** | MIT | 跨端框架，可同时输出微信/支付宝小程序 |
| UI 组件库 | Taro UI | MIT | 基于 Taro 的组件库 |
| 状态管理 | Zustand | MIT | 与 Web 端一致 |
| Canvas 渲染 | 原生 Canvas 2D API | — | 不用 Fabric.js，自己实现渲染器 |
| 请求封装 | Taro.request | — | 统一请求拦截 + JWT 注入 |
| 图标 | Taro Icon | MIT | — |

> **Taro 选择理由:** MIT 许可，支持 React 语法开发，一套代码可编译到微信/支付宝/字节小程序。备选 uni-app (Apache 2.0) 也可。**不选原生开发**——无法跨平台复用。

#### 5.6 安装链路 (小程序 → 手表)

```
小程序内点击"安装到手表"
  │
  ├── 1. 请求 /api/mini/watchfaces/{id}/install
  │     └─ 后端返回: { intent_uri, browser_url }
  │
  ├── 2. 小程序展示安装引导页
  │     ├─ 方案 A (推荐): 生成小程序码，用户截图后用浏览器扫码
  │     ├─ 方案 B: 点击"复制链接"，引导用户打开浏览器粘贴
  │     └─ 方案 C: 通过 H5 跳转页 (需小程序关联公众号)
  │
  ├── 3. 用户在手机浏览器打开 browser_url
  │     └─ 该页面自动触发 intent:// URI
  │
  └── 4. 唤醒 Wear OS App → 蓝牙推送 → 安装
```

> **限制说明：** 微信小程序不支持直接唤起 intent:// URI，必须通过浏览器中转。这是微信生态的安全限制，无法绕过。

#### 5.7 交付物清单

- [ ] Taro 小程序项目骨架 (`miniapp/`)
- [ ] 微信登录 + 平台账号绑定
- [ ] MiniCDMRenderer (Canvas 2D 渲染器)
- [ ] 表盘浏览/详情/预览页
- [ ] 小程序码生成与分享
- [ ] 安装引导流程
- [ ] 我的表盘/收藏
- [ ] 小程序专用 API 端点 (`/api/mini/*`)
- [ ] 数据埋点
- [ ] 小程序审核上线

#### 5.8 Phase 5 验收标准

| 验收项 | 标准 |
|--------|------|
| 渲染一致性 | 小程序预览与 Web 端预览视觉差异 < 10% |
| 加载性能 | 首屏渲染 < 2s，CDM 渲染 < 1s |
| 分享链路 | 小程序码扫码到表盘详情 < 2s |
| 安装成功率 | 通过浏览器中转的 intent:// 安装成功率 ≥ 90% |
| 包体积 | 小程序主包 ≤ 2MB，分包加载 |

#### 5.9 CDM 模型对小程序的预留

CDM JSON 在设计时已考虑小程序渲染约束：

| 考量 | CDM 字段 | 小程序适配 |
|------|----------|-----------|
| 图片需下载到本地 | `asset.src` | 小程序需先 downloadFile 到临时路径再 drawImage |
| 字体加载 | `textStyle.fontFamily` | 小程序需 loadFontFace，仅支持网络字体 |
| 动画 | `animations[]` | 小程序可用 Canvas.requestAnimationFrame 实现 (Phase 5 暂不支持) |
| 圆形裁剪 | `metadata.shape` | Canvas clip 区域设置 |

> **未来扩展：** 如果小程序端需要支持简单编辑（如换颜色/换背景），可在 CDM 中增加 `variant` 字段，小程序通过修改 variant 值重新请求渲染，不需要完整编辑器。

---

## 6. 管理后台

> **定位：** 运营人员使用的内部管理界面，独立路由 `/admin`，RBAC 权限控制。与用户端共享同一后端 FastAPI 服务，通过 `/admin/api/*` 路由前缀隔离。

### 6.1 功能模块

```
/admin
├── /dashboard          看板首页
├── /users             用户管理
├── /watchfaces        表盘内容管理
├── /api-config         AI API 配置
├── /usage             用量统计
├── /system           系统设置
└── /audit            操作日志
```

### 6.2 看板 (Dashboard)

| 指标 | 说明 | 数据源 |
|------|------|--------|
| 今日 DAU | 日活用户数 | PostgreSQL 聚合查询 |
| 表盘生成数 | 今日 AI 生成次数 | Celery 任务记录 |
| API 调用数 | 今日 AI API 总调用次数 + Token 消耗 | `api_usage_logs` 表 |
| 安装次数 | 今日 intent:// 点击次数 | `install_logs` 表 |
| 在线任务 | 当前 Celery 队列中的活跃任务 | Valkey / Celery inspect |
| 服务健康 | API/DB/Valkey/Worker 状态 | 健康检查端点 |
| 趋势图 | 7 天/30 天 DAU、生成量、安装量趋势 | PostgreSQL 时序查询 |

### 6.3 用户管理

| 功能 | 说明 |
|------|------|
| 用户列表 | 分页查询，支持按注册时间/活跃度/用量排序 |
| 用户详情 | 查看用户信息、表盘列表、API 用量、安装历史 |
| 封禁/解封 | 禁止违规用户使用 AI 生成功能 |
| 配额调整 | 调整单用户的 AI 生成配额 (默认 10 次/小时) |
| 角色分配 | admin / moderator / user 三级角色 |
| 导出 | 导出用户列表 CSV |

### 6.4 API 配置

| 功能 | 说明 |
|------|------|
| AI Provider 管理 | 添加/删除/启停 OpenAI / Gemini API Key |
| 密钥轮换 | 查看密钥状态 (活跃/限流中/失效)，一键切换 |
| 限流配置 | 全局/单用户 速率限制调整 |
| 模型路由 | 配置 "文本生成" / "图片生成" 默认使用的 Provider 和模型 |
| 价格配置 | 各 Provider 的 Token/图片单价，用于用量成本计算 |
| 测试连通 | 对每个 Provider 发送测试请求，验证密钥有效性 |

```python
# API 配置数据模型
class AIProviderConfig(BaseModel):
    name: str                    # "openai" | "gemini"
    display_name: str            # "OpenAI GPT-4o"
    api_keys: list[APIKeyInfo]   # 多密钥池
    models: list[ModelInfo]      # 支持的模型列表
    rate_limit: int              # 单密钥 RPM 限制
    enabled: bool
    priority: int                # 路由优先级

class APIKeyInfo(BaseModel):
    key_id: str                  # 显示前4位 + 后4位，中间打码
    status: str                  # "active" | "rate_limited" | "invalid"
    last_used: datetime | None
    total_requests: int
    total_tokens: int
```

### 6.5 表盘内容管理

| 功能 | 说明 |
|------|------|
| 表盘列表 | 全平台表盘，支持按状态/平台/时间筛选 |
| 内容审核 | 审核 AI 生成的表盘，标记通过/违规/需修改 |
| 下架 | 违规表盘下架，禁止分发 |
| 精选推荐 | 标记精选表盘，在小程序首页展示 |
| 预览 | 管理员直接预览 CDM 渲染效果 |

### 6.6 用量统计

| 维度 | 说明 |
|------|------|
| API 用量 | 按 Provider/模型/用户 维度的调用量和 Token 消耗 |
| 成本分析 | 每日 AI API 成本，按用户/模型分摊 |
| 生成成功率 | AI 生成任务的成功/失败率 |
| 图片处理量 | 抠图/压缩任务数量和耗时 |
| 安装统计 | intent:// 点击次数、安装成功率 |
| 导出报表 | 日/周/月 报表导出 CSV |

### 6.7 技术选型 (Admin 特有)

| 层 | 技术 | 许可证 | 说明 |
|----|------|--------|------|
| 前端框架 | Next.js 15 (同用户端) | MIT | 独立路由 `/admin`，共享组件库 |
| UI 组件库 | shadcn/ui | MIT | 数据表格、表单、图表 |
| 图表 | Recharts | MIT | 趋势图、柱状图、饼图 |
| 表格 | TanStack Table | MIT | 排序/筛选/分页 |
| 认证 | JWT + RBAC | — | 管理员角色独立签发 |
| 导出 | papaparse | MIT | CSV 导出 |

### 6.8 权限模型 (RBAC)

```
角色: admin (超级管理员)
  ├─ 所有权限
  ├─ 管理 API 密钥
  └─ 管理其他管理员

角色: moderator (内容审核员)
  ├─ 查看用户和表盘
  ├─ 审核/下架表盘
  └─ 精选推荐

角色: user (普通用户，不可访问 Admin)
```

### 6.9 数据库表 (Admin 相关)

```sql
-- 管理员表
CREATE TABLE admins (
    id          UUID PRIMARY KEY,
    username    VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role        VARCHAR(20) NOT NULL DEFAULT 'moderator',  -- admin | moderator
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- AI Provider 配置表
CREATE TABLE ai_provider_configs (
    id          UUID PRIMARY KEY,
    name        VARCHAR(50) NOT NULL,         -- openai | gemini
    display_name VARCHAR(100),
    config_json JSONB NOT NULL,              -- 密钥池、模型列表、限流等
    enabled     BOOLEAN DEFAULT true,
    priority    INT DEFAULT 0,
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- API 用量日志表
CREATE TABLE api_usage_logs (
    id          BIGSERIAL PRIMARY KEY,
    user_id     UUID NOT NULL,
    provider    VARCHAR(50) NOT NULL,
    model       VARCHAR(100),
    request_type VARCHAR(50),               -- text_to_cdm | text_to_image
    tokens_in   INT DEFAULT 0,
    tokens_out  INT DEFAULT 0,
    cost        DECIMAL(10, 4) DEFAULT 0,
    status      VARCHAR(20),                 -- success | error | rate_limited
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_api_usage_user_time ON api_usage_logs(user_id, created_at);
CREATE INDEX idx_api_usage_provider_time ON api_usage_logs(provider, created_at);

-- 安装日志表
CREATE TABLE install_logs (
    id          BIGSERIAL PRIMARY KEY,
    project_id  UUID NOT NULL,
    user_id     UUID,
    client_type VARCHAR(20),                -- web | mini_program
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- 操作审计日志
CREATE TABLE audit_logs (
    id          BIGSERIAL PRIMARY KEY,
    admin_id    UUID NOT NULL,
    action      VARCHAR(100) NOT NULL,      -- ban_user | update_api_key | takedown
    target_type VARCHAR(50),
    target_id   UUID,
    detail      JSONB,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 7. 部署架构与资源规划

### 7.1 现有资源盘点

| 服务器 | 规格 | 公网 | 架构 | 优势 | 劣势 |
|--------|------|------|------|------|------|
| **ARM 服务器** | 8 vCPU / 16 GB | ❌ 无 | ARM64 | 算力强、内存大 | 无公网 IP，ARM 架构兼容性需验证 |
| **日本 VPS** | 1 vCPU / 1 GB | ✅ 有 | x86_64 | 公网入口、延迟低到国内 | 配置极低，仅适合做反代 |
| **阿里云 (待购)** | 2 vCPU / 2 GB / 3Mbps | ✅ 有 | x86_64 | 国内访问快、备案可控 | 带宽仅 3Mbps，内存小 |

### 7.2 推荐部署拓扑

```
                         用户 (国内)
                              │
                    ┌─────────┴─────────┐
                    │                   │
                    ↓                   ↓
          ┌─────────────────┐  ┌─────────────────┐
          │  阿里云 ECS      │  │  日本 VPS         │
          │  2u2g 3Mbps     │  │  1u1g            │
          │  (公网入口)       │  │  (备用入口/CDN)   │
          │                 │  │                 │
          │  Nginx (反代+SSL) │  │  Nginx (SSL)     │
          │  Next.js (SSR)   │  │  静态资源缓存     │
          │  FastAPI (API)   │  │                 │
          │  Valkey (缓存)   │  │                 │
          └────────┬─────────┘  └─────────────────┘
                   │ 内网/SSH 隧道/WireGuard VPN
                   ↓
          ┌─────────────────────────────┐
          │  ARM 服务器 (内网计算节点)     │
          │  8u16g ARM64                │
          │                             │
          │  PostgreSQL 16              │
          │  Celery Workers:            │
          │  ├─ AI 生成 (2 并发)         │
          │  ├─ 图像处理 (3 并发)         │
          │  └─ 编译打包 (2 并发)        │
          │  Rembg (懒加载)              │
          │  Celery Flower (监控)        │
          │  Promtail (日志收集)         │
          └─────────────────────────────┘
                   │
                   ↓
          ┌─────────────────┐
          │  对象存储 S3/OSS  │  ← WFF ZIP 包、AI 素材、预览图
          │  + CDN 加速       │
          └─────────────────┘
```

**分工逻辑：**

| 服务器 | 角色 | 部署服务 | 内存预算 |
|--------|------|---------|---------|
| 阿里云 2u2g | 公网入口 (Web + API) | Nginx + Next.js + FastAPI + Valkey | ~1.8 GB |
| 日本 1u1g | 备用入口 / CDN 节点 | Nginx + 静态缓存 | ~512 MB |
| ARM 8u16g | 计算节点 (DB + Workers) | PostgreSQL + Celery + Rembg + Flower | ~8-10 GB |

### 7.3 服务器间通信

```
阿里云 ←→ ARM 服务器: WireGuard VPN 隧道 (反向连接)
  ├─ 方向: ARM 服务器 (无公网 IP) 主动连接 → 阿里云 (公网 Server)
  ├─ ARM 配置: PersistentKeepalive = 25 保持隧道活跃
  ├─ 阿里云: 安全组开放 UDP 51820 端口
  ├─ 阿里云 → ARM: API 请求转发 (数据库读写、任务调度)
  ├─ ARM → 阿里云: WebSocket 事件推送 (通过 Valkey Pub/Sub)
  └─ 延迟: 同城 < 2ms, 跨地域 10-30ms

阿里云 ←→ 对象存储: HTTPS 直连
日本 VPS ←→ 对象存储: HTTPS 直连 (CDN 回源)
```

> **WireGuard 选择理由:** 代码量约 4000 行 (Linux 内核模块)，性能优于 OpenVPN，配置简单，MIT 许可。适用于阿里云到 ARM 服务器的内网打通。

### 7.4 ARM 架构兼容性验证清单

部署前必须验证以下组件在 ARM64 (aarch64) 上的可用性：

| 组件 | ARM64 支持 | 验证方式 | 风险 |
|------|-----------|---------|------|
| Python 3.12 | ✅ 官方支持 | `python3 --version` | 无 |
| PostgreSQL 16 | ✅ 官方支持 | `docker run --platform arm64 postgres:16` | 无 |
| Valkey 8 | ✅ 官方支持 | `docker run --platform arm64 valkey/valkey:8` | 无 |
| Node.js 22 | ✅ 官方支持 | `docker run --platform arm64 node:22` | 无 |
| Nginx | ✅ 官方支持 | `docker run --platform arm64 nginx:1.27` | 无 |
| Celery | ✅ 纯 Python | — | 无 |
| Pillow | ✅ 提供 ARM64 wheel | `pip install Pillow` | 无 |
| Rembg (ONNX Runtime) | ⚠️ 需验证 | `pip install onnxruntime && python -c "import onnxruntime"` | **中** |
| lxml | ✅ 提供 ARM64 wheel | `pip install lxml` | 低 |
| Fabric.js | ✅ 前端组件 (浏览器运行) | — | 无 |

> **Rembg/ONNX Runtime 风险:** ONNX Runtime 官方提供 ARM64 Linux 二进制包，但 Rembg 的 U2-Net 模型推理在 ARM 上可能比 x86 慢 1.5-2x。如果性能不达标，方案是将 Rembg Worker 部署到阿里云 (x86)，或在阿里云上单独跑 Rembg 容器。

### 7.5 资源需求详细分析

#### 各服务内存占用预估

| 服务 | 最小内存 | 推荐内存 | 说明 |
|------|---------|---------|------|
| Nginx | 50 MB | 100 MB | 反向代理 + SSL |
| Next.js (SSR) | 256 MB | 512 MB | 1 worker, standalone mode |
| FastAPI (Uvicorn) | 256 MB | 512 MB | 2 workers |
| PostgreSQL 16 | 256 MB | 1 GB | shared_buffers=256MB, max_connections=50 |
| Valkey | 64 MB | 256 MB | 缓存 + 消息队列 |
| Celery Worker (AI 文本) | 128 MB | 256 MB | 2 并发, 纯 IO |
| Celery Worker (AI 图片) | 128 MB | 256 MB | 2 并发, 纯 IO |
| Celery Worker (图像处理) | 256 MB | 512 MB | 2 并发, CPU 密集 |
| Celery Worker (编译) | 128 MB | 256 MB | 2 并发, CPU+IO |
| Rembg (懒加载) | 0 MB (空闲) | 1.5 GB (加载时) | U2-Net 模型 ~170MB + 推理内存 |
| Celery Flower | 64 MB | 128 MB | 监控面板 |
| Docker + 系统 | 200 MB | 500 MB | 容器运行时 + OS |

#### 三服务器分配

| 服务器 | 部署服务 | 内存占用 (常态) | 内存占用 (峰值) | 可用内存 |
|--------|---------|---------------|---------------|---------|
| **阿里云 2GB** | Nginx + Next.js + FastAPI + Valkey | ~1.1 GB | ~1.6 GB | ~400 MB |
| **日本 1GB** | Nginx + 缓存 | ~200 MB | ~400 MB | ~600 MB |
| **ARM 16GB** | PostgreSQL + 4 Celery Workers + Rembg (峰值) + Flower | ~4.5 GB | ~7 GB | ~9 GB |

### 7.6 4u8g 单机方案可行性分析

> **核心问题：** 20 人并发能否只用 4 vCPU / 8 GB 单台服务器？

#### 结论：✅ 可行，但有条件

```
4u8g 单机部署所有服务:

Nginx              ~100 MB
Next.js (1 worker) ~512 MB
FastAPI (2 workers)~512 MB
PostgreSQL         ~768 MB  (shared_buffers=256MB, max_conn=30)
Valkey             ~128 MB
Celery (3 workers) ~768 MB  (AI×1 + 图像×1 + 编译×1)
Rembg (懒加载)     ~1.5 GB  (仅处理图片时加载)
系统开销           ~500 MB
────────────────────────────
常态占用:          ~3.3 GB
峰值 (Rembg 加载): ~4.8 GB
剩余可用:          ~3.2 GB
```

#### 4u8g 方案的前提条件

| 条件 | 说明 | 调优参数 |
|------|------|---------|
| Rembg 懒加载 | 空闲 5 分钟后卸载模型，释放内存 | `REMBG_IDLE_TIMEOUT=300` |
| Celery 并发限制 | 总并发 ≤ 3 (不跑满 4 核) | `worker_concurrency=1` per queue |
| PostgreSQL 调优 | 小内存配置，限制连接数 | `shared_buffers=256MB`, `max_connections=30` |
| Next.js standalone | 开启 standalone 模式减少内存 | `output: 'standalone'` |
| Uvicorn workers | 限制 2 worker | `--workers 2` |
| Valkey 淘汰策略 | 设置 maxmemory + LRU 淘汰 | `maxmemory 128mb`, `maxmemory-policy allkeys-lru` |
| 无 Rembg 时降级 | 内存不足时跳过抠图，使用原始图片 | 前端提示"背景未移除" |
| Swap 分区 | 配置 2GB swap 兜底 | `swapon /swapfile` |

#### 20 人并发场景分析

| 场景 | 同时活跃用户 | CPU 占用 | 内存占用 | 是否可承受 |
|------|------------|---------|---------|----------|
| 全部浏览 | 20 人浏览/预览 | ~1.5 核 | ~3.5 GB | ✅ 轻松 |
| 混合使用 | 15 浏览 + 5 编辑 | ~2.5 核 | ~4.0 GB | ✅ 正常 |
| 5 人同时 AI 生成 | 5 人生成 + 15 浏览 | ~3.5 核 | ~5.5 GB | ⚠️ 接近上限 |
| 10 人同时 AI 生成 | 10 人生成 + 10 浏览 | ❌ CPU 瓶颈 | ~6.5 GB | ❌ 不可行 |

> **关键瓶颈不是内存而是 CPU。** AI 生成的大部分时间在等外部 API 响应 (IO 等待)，但图像后处理 (Rembg) 是 CPU 密集型。4 核下同时只能处理 1-2 张图片抠图。

#### 4u8g vs 三服务器方案对比

| 维度 | 4u8g 单机 | 三服务器 (现有资源) |
|------|----------|-----------------|
| 月成本 | ~¥150-200 (阿里云 4u8g) | ¥0 (已有) + 阿里云 2u2g ~¥60/月 |
| 20 人并发 | ✅ 可行 (限制并发) | ✅ 轻松 (算力充裕) |
| 50 人并发 | ❌ 不可行 | ✅ 可行 |
| 公网入口 | 需要 | 已有 (日本 + 阿里云) |
| 运维复杂度 | 低 (单机) | 中 (三机 + VPN) |
| 数据安全 | 单点故障 | 计算节点隔离 |
| 扩展性 | 差 (加机器需迁移) | 好 (计算节点可水平扩展) |

#### 推荐方案

```
阶段 1-2 (MVP + AI 接入):
  └─ 使用现有三服务器方案
     ├─ 阿里云 2u2g: 公网入口 (Nginx + Next.js + FastAPI + Valkey)
     ├─ ARM 8u16g: 计算节点 (PostgreSQL + Celery + Rembg)
     └─ 日本 1u1g: 备用入口/CDN (Nginx)
  └─ 成本: 阿里云 2u2g ~¥60/月

阶段 3+ (完整体验):
  └─ 如需更高并发，阿里云升级到 4u8g (~¥200/月)
     ├─ 阿里云 4u8g: 公网入口 (全量部署)
     └─ ARM 8u16g: 计算节点 (PostgreSQL + Celery + Rembg)
  └─ 或: 阿里云保持 2u2g，Rembg Worker 单独部署到阿里云 ECS 按量付费
```

### 7.7 带宽分析

| 操作 | 数据量 | 3Mbps 带宽耗时 | 备注 |
|------|--------|---------------|------|
| 页面加载 | ~500 KB (gzip) | ~1.3s | 首次加载，后续缓存 |
| CDM JSON 传输 | ~10-50 KB | < 0.1s | 可忽略 |
| WFF ZIP 下载 | 1-5 MB | 2.7-13s | ⚠️ 较慢，CDN 缓解 |
| AI 生成图片上传 | 100-500 KB/张 | 0.3-1.3s | 取决于 Gemini 返回速度 |
| 预览图加载 | 50-200 KB | 0.1-0.5s | CDN 缓存 |

> **带宽瓶颈在 WFF ZIP 下载。** 解决方案：阿里云 OSS + CDN，ZIP 包直接从 CDN 节点分发，不占用 ECS 带宽。阿里云 CDN 按流量计费，约 ¥0.24/GB。

### 7.8 Docker Compose 部署配置 (4u8g 方案)

```yaml
# docker-compose.yml (单机方案)
services:
  nginx:
    image: nginx:1.27-alpine
    mem_limit: 128m
    ports: ["80:80", "443:443"]
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl

  web:
    build: ./web
    mem_limit: 512m
    environment:
      - NODE_ENV=production
    command: node server.js  # standalone mode

  api:
    build: ./api
    mem_limit: 512m
    environment:
      - DATABASE_URL=postgresql://...
      - VALKEY_URL=valkey://valkey:6379
      - AI_PROVIDER_OPENAI_KEY=${OPENAI_KEY}
    command: uvicorn main:app --workers 2 --host 0.0.0.0

  valkey:
    image: valkey/valkey:8-alpine
    mem_limit: 128m
    command: valkey-server --maxmemory 96mb --maxmemory-policy allkeys-lru

  db:
    image: postgres:16-alpine
    mem_limit: 768m
    environment:
      - POSTGRES_DB=watchface
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data

  worker:
    build: ./api
    mem_limit: 512m
    environment:
      - DATABASE_URL=postgresql://...
      - VALKEY_URL=valkey://valkey:6379
    command: celery -A tasks worker -Q ai_text,ai_image,image_processing,compilation -c 1
    depends_on: [db, valkey]

  rembg-worker:
    build: ./api
    mem_limit: 2048m
    environment:
      - DATABASE_URL=postgresql://...
      - VALKEY_URL=valkey://valkey:6379
      - REMBG_MODEL=u2net
      - REMBG_IDLE_TIMEOUT=300
    command: celery -A tasks worker -Q image_processing -c 1
    depends_on: [db, valkey]

  flower:
    build: ./api
    mem_limit: 128m
    command: celery -A tasks flower --port=5555
    ports: ["5555:5555"]

volumes:
  pgdata:
```

> **注意：** `rembg-worker` 独立为一个 Celery 进程，专门处理 image_processing 队列。空闲时模型不加载，收到任务时加载 U2-Net 模型 (~170MB)，处理完后 5 分钟超时自动卸载。

### 7.9 最低资源需求总结

| 并发规模 | 最低配置 | 部署方式 | AI 生成并发 |
|---------|---------|---------|------------|
| 5 人 | 2u4g | 单机 | 1 并发 |
| **20 人** | **4u8g** | **单机** | **2-3 并发** |
| 20 人 (三机) | 2u2g + 8u16g | 三机分布式 | 3-4 并发 |
| 50 人 | 8u16g | 单机或双机 | 5 并发 |
| 100 人 | 16u32g | 双机 (Web+DB 分离) | 8 并发 |

> **回答核心问题：20 人并发降到 4u8g 可行吗？**
>
> **可以，但需接受以下限制：**
> 1. AI 生成并发上限 2-3 (同时只有 2-3 人在等 AI 生成)
> 2. Rembg 抠图串行处理 (一次只处理 1 张图)
> 3. 无高可用 (单点故障)
> 4. PostgreSQL 连接数限制 30
>
> 如果可接受以上限制，4u8g 足够。推荐使用现有三服务器方案，因为成本更低 (仅阿里云 2u2g ~¥60/月) 且算力更充裕。

## 8. 非功能性需求

### 8.1 性能需求

| 指标 | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|------|---------|---------|---------|---------|
| 编译响应 | < 3s | < 3s | < 3s | < 5s |
| AI 生成延迟 | — | < 30s | < 30s | < 30s |
| 图像处理延迟 | — | — | < 10s/张 | < 10s/张 |
| 编辑器帧率 | — | — | 60fps | 60fps |
| 页面加载 | < 2s | < 2s | < 2s | < 2s |
| API P99 延迟 | < 200ms | < 500ms | < 500ms | < 500ms |

### 8.2 可用性需求

| 指标 | 目标 |
|------|------|
| 服务可用率 | 99.5% (Phase 1-2) → 99.9% (Phase 3+) |
| 故障恢复时间 | < 5 分钟 |
| 数据持久性 | 99.999999999% (S3/OSS 提供) |

### 8.3 安全需求

| 需求 | 说明 |
|------|------|
| 用户认证 | JWT + Refresh Token，支持 OAuth (Google/GitHub) |
| API 密钥管理 | 环境变量注入 + 密钥轮换，绝不硬编码 |
| 输入校验 | 所有 API 入参经过 Pydantic 校验 |
| SQL 注入防护 | SQLAlchemy ORM 参数化查询 |
| XSS 防护 | React 默认转义 + CSP 头 |
| CORS | 白名单域名策略 |
| 速率限制 | 令牌桶: 全局 1000 req/min，单用户 60 req/min |
| AI 提示词过滤 | OpenAI Moderation API 预过滤 |
| 文件上传限制 | 图片 ≤ 5MB，仅接受 PNG/JPEG/WebP |

### 8.4 可观测性

| 维度 | 工具 | 说明 |
|------|------|------|
| 日志 | structlog (MIT) | 结构化 JSON 日志 |
| 指标 | Prometheus (Apache 2.0) | 自定义业务指标 |
| 链路追踪 | OpenTelemetry (Apache 2.0) | 分布式追踪 |
| 错误监控 | Sentry (商用 / 自建 GlitchTip MIT) | 异常聚合 |
| 任务监控 | Celery Flower (BSD) | 队列健康度 |

---

## 9. 风险登记册

| ID | 风险 | 影响 | 概率 | 缓解策略 |
|----|------|------|------|----------|
| R01 | WFF 规范变更 | 编译器失效 | 中 | 持续关注 Google Wear OS 更新，编译器版本隔离 |
| R02 | AI API 限流/涨价 | 生成功能不可用 | 中 | 多 Provider 热切换，缓存重复请求 |
| R03 | Rembg 抠图质量不稳定 | 用户体验差 | 高 | 提供"手动抠图"回退方案（Phase 3+） |
| R04 | intent:// 兼容性 | 部分手机无法安装 | 中 | 提供手动下载 + ADB 安装指引 |
| R05 | Apple Watch 分发限制 | 无法一键安装 | 高 | Phase 4 调研 companion app 方案 (二期) |
| R06 | AI 生成 CDM 格式错误 | 编译失败 | 中 | GPT-4o Function Calling 强约束 + 后端二次校验 |
| R07 | 图片大小超限 | WFF 打包失败 | 低 | 自动压缩管线，超限自动降质量 |

---

## 9A. 隐形问题清单 (一期工程审计)

> 以下为对一期 (Phase 1-3) 文档逐节审查后发现的隐形问题，按严重程度分级。
> **🔴 阻断性问题必须在 Phase 1 开工前解决，🟡 应在对应 Phase 开发中解决，🔵 建议优化。**

### ✅ P0-01: intent:// 一键安装机制 — ❌ 已确认不存在 (2026-08-12 验证)

**验证结果:** 经 Google 官方文档确认，`intent:// URI` 唤起 Wear OS App 安装 WFF 的机制 **不存在**。

**实际分发方式:**
1. Google Play Store (APK/AAB)
2. Watch Face Push API (Wear OS 6+, 需 companion app)
3. ADB sideload

**已采取的行动:**
- 一期改为 "APK 下载 + Wear Installer" 方案 (见 Phase 1.3 节)
- 编译器输出从 ZIP 改为签名 APK
- 新增 APK 构建管线 (aapt2 + zipalign + apksigner)
- 二期评估 Companion App + Watch Face Push API
- 红线规则从 "绝不编译 APK" 改为 "绝不在 APK 中包含代码 (hasCode=false)"

### ✅ P0-02: WFF 官方 XSD Schema — ✅ 确认可用 (2026-08-12 验证)

**验证结果:** Google 官方仓库 github.com/google/watchface (Apache 2.0) 包含:
- WFF XSD 校验器 (`third_party/wff/` 目录)
- Memory Footprint 评估器
- 示例表盘代码

**已采取的行动:** Phase 1 技术选型已更新为使用官方 XSD 校验器。

### ✅ P0-03: ARM 服务器无公网 IP — ✅ WireGuard 反向连接方案确认 (2026-08-12 验证)

**验证结果:** 标准方案，ARM 服务器作为 WireGuard Client 主动连接阿里云 (Server)。需配置 `PersistentKeepalive = 25` 保持隧道活跃。

**已采取的行动:** 部署架构 (第 7 节) 已说明 ARM → 阿里云方向，PersistentKeepalive 已配置。

### 🟡 P1-01: 数据库跨网络访问延迟

**问题：** FastAPI 在阿里云 (2u2g)，PostgreSQL 在 ARM 服务器。每次 API 请求的 DB 查询都经过 WireGuard 隧道，延迟 10-30ms/次。一个列表页可能 3-5 次 DB 查询，总延迟 30-150ms。

**影响：** API P99 延迟目标 < 200ms 可能难以达到。

**行动项：**
1. 在阿里云 FastAPI 侧加 **PgBouncer** 连接池，减少连接建立开销
2. FastAPI 启用 **SQLAlchemy 连接池** (pool_size=10, max_overflow=5)
3. 高频读操作走 Valkey 缓存 (模板列表、CDM Schema 等静态数据)
4. 如果延迟不可接受：将 PostgreSQL 迁移到阿里云 (但 2GB 内存更紧张)
5. 或者：将 FastAPI 也部署到 ARM 服务器，阿里云只做 Nginx 反代 (延迟最低)

### 🟡 P1-02: CDM 中 asset.src 使用 s3:// URL — 前端无法直接渲染

**问题：** CDM JSON 中 `asset.src` 值为 `s3://bucket/assets/bg_001.png`，这是 S3 内部 URI。前端 Fabric.js 无法直接加载 `s3://` 协议的图片，编译器也需要先下载才能打包。

**影响：** 前端渲染和编译器都需要额外转换步骤。

**行动项：**
- CDM 中 `asset.src` 统一存储为 **CDN HTTPS URL** (如 `https://cdn.platform.com/assets/bg_001.png`)
- 后端在保存 CDM 时自动将 `s3://` 转换为 CDN URL
- 编译器通过 HTTPS 下载 (而非 S3 SDK)，保持一致

### 🟡 P1-03: Gemini 图片生成不保证 384×384 分辨率

**问题：** P2-F03 要求"Gemini 生成 384×384 表盘背景图"，但 Gemini Imagen API **不支持指定精确分辨率输出**。默认输出可能是 1024×1024 或其他尺寸。

**影响：** 需要额外的后处理步骤裁剪/缩放到 384×384。

**行动项：**
- Phase 2 图像生成任务增加固定步骤：AI 生成 → Pillow 缩放到 384×384
- 非正方形图片需要先裁剪为正方形再缩放

### 🟡 P1-04: Phase 1 缺少用户认证但数据库有 user_id

**问题：** Phase 1 数据库 `watchface_projects` 表有 `user_id` 字段，但 Phase 1 功能需求中没有用户注册/登录功能。

**影响：** Phase 1 需要决定是跳过认证 (所有人共享项目) 还是引入最简认证。

**行动项：**
- Phase 1 使用最简认证：匿名用户 + localStorage UUID 作为 user_id
- Phase 2 再接入正式的 OAuth/JWT 认证
- 数据库 user_id 字段保留，Phase 1 存匿名 UUID

### 🟡 P1-05: 阿里云 2GB 内存预算紧张

**问题：** 阿里云 2u2g 部署 Nginx + Next.js + FastAPI + Valkey，常态 ~1.5GB，峰值可能到 1.8GB。系统保留 200MB 后仅剩 ~300MB 余量。如果 Next.js SSR 遇到并发高峰，可能 OOM。

**影响：** 高峰期服务不可用。

**行动项：**
1. Next.js 开启 `output: 'standalone'` 模式，减少内存
2. Next.js 可考虑关闭 SSR，改用 SSG + 客户端渲染 (编辑器页面不需要 SEO)
3. FastAPI Uvicorn 限制 `--workers 1` (而非 2)
4. 配置 1GB Swap 文件兜底
5. 如果仍然不够：升级到 2u4g (~¥120/月)

### 🟡 P1-06: 无 ICP 备案策略

**问题：** 阿里云服务器在中国大陆，绑定域名需要 **ICP 备案** (个人备案需 1-2 周，企业备案需 2-3 周)。文档未提及。

**影响：** 项目上线时间可能因备案延误。

**行动项：**
1. Phase 1 开始时同步提交 ICP 备案申请
2. 备案期间使用日本 VPS 的 IP 直接访问 (临时方案)
3. 备案完成后切换到阿里云域名访问

### 🟡 P1-07: 无 API 版本前缀

**问题：** API 端点为 `/api/compile`、`/api/templates`，无版本前缀。CDM Schema 有版本号 (v1.0)，但 API 没有。

**影响：** 未来如果 API 接口变更 (如 CDM v2.0)，无法平滑迁移。

**行动项：**
- 所有端点加版本前缀：`/api/v1/compile`、`/api/v1/templates`
- Admin 端点：`/admin/api/v1/...`

### 🟡 P1-08: 无 PostgreSQL 备份策略

**问题：** PostgreSQL 部署在 ARM 服务器上，文档中无任何备份策略。如果 ARM 服务器硬盘损坏，所有用户数据和表盘项目丢失。

**影响：** 数据丢失风险。

**行动项：**
1. 每日自动 `pg_dump` 到对象存储 (OSS)
2. 保留 7 天滚动备份
3. Phase 1 实现备份脚本 + cron 定时任务
4. Phase 3 考虑 PostgreSQL 流复制到第二台服务器

### 🟡 P1-09: WebSocket 通过 Nginx 反代需特殊配置

**问题：** FastAPI WebSocket `/ws/generation/{task_id}` 需要通过 Nginx 反向代理。Nginx 默认配置不支持 WebSocket，需要 `Upgrade` 和 `Connection` 头。

**影响：** WebSocket 连接失败，进度推送不工作。

**行动项：**
```nginx
# Nginx WebSocket 代理配置 (必须在部署文档中说明)
location /ws/ {
    proxy_pass http://backend:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_read_timeout 86400;  # 长连接超时
}
```

### 🟡 P1-10: 自定义字体许可证问题

**问题：** CDM 中 `textStyle.fontFamily` 可能引用商业字体 (如 "Orbitron")。将字体文件打包到 WFF ZIP 中分发，可能违反字体许可证。

**影响：** 法律风险。

**行动项：**
1. 维护一个 **允许商业使用的字体白名单** (SIL Open Font License 或 Apache 2.0 字体)
2. 编辑器中只提供白名单字体选择
3. 用户上传自定义字体时需签署授权声明
4. 推荐字体：Orbitron (OFL), Roboto (Apache 2.0), Noto Sans (OFL)

### 🟡 P1-11: LLM 输出 CDM JSON 可靠性 (2026-08-12 验证修订)

**验证结果:** GPT-4o Structured Outputs (strict mode) 比 JSON Mode 更可靠，但仍非 100%。
首次成功率约 60-70%，通过自动修复 + 重试可达 ≥ 80%。

**已采取的行动:**
1. 使用 Structured Outputs (非 JSON Mode)
2. 新增 CDM 自动修复层 (CDMAutoFixer)
3. 验收标准调整为：首次成功率 ≥ 60%，重试后 ≥ 80%

### 🟡 P1-12: 无并发编辑冲突处理

**问题：** 用户在两个浏览器 Tab 中编辑同一个表盘项目，后保存的会覆盖先保存的。

**影响：** 用户数据丢失。

**行动项：**
- 数据库 `watchface_projects` 表增加 `version` 字段
- 保存时检查 version，不匹配则返回 409 Conflict
- 前端提示"在其他设备上有更新，是否刷新"

### 🟡 P1-13: 无 CDN 缓存失效策略

**问题：** WFF ZIP 包上传到 OSS + CDN 后，如果用户更新了表盘并重新编译，CDN 可能仍缓存旧版本。

**影响：** 用户安装到旧版本表盘。

**行动项：**
- WFF ZIP 的 CDN URL 包含版本 hash：`/wff/{project_id}/{version_hash}.zip`
- 新版本生成新 URL，旧 URL 自然失效
- 或使用 CDN API 主动刷新 (阿里云 CDN 支持 URL 刷新)

### 🔵 P2-01: 无文件清理策略

**问题：** 用户删除表盘项目后，OSS 中的 WFF ZIP 和图片素材不会被自动删除，长期积累产生存储成本。

**行动项：**
- Phase 3 实现定时任务：清理 30 天前的孤儿文件
- 删除项目时标记 assets 为 pending_delete，24 小时后清理

### 🔵 P2-02: 无系统监控/告警

**问题：** 文档提及 Celery Flower 监控任务队列，但没有系统级监控 (CPU/内存/磁盘) 和告警机制。

**行动项：**
- Phase 3 引入轻量监控：Node Exporter + Grafana (或者更轻的 uptime-kuma MIT)
- 磁盘使用率 > 80% 时告警
- 服务不可达时告警

### 🔵 P2-03: 无日志轮转策略

**问题：** Docker 容器日志默认无大小限制，长期运行可能占满磁盘。

**行动项：**
```json
// /etc/docker/daemon.json
{
  "log-driver": "json-file",
  "log-opts": { "max-size": "10m", "max-file": "3" }
}
```

### 🔵 P2-04: API 密钥管理安全

**问题：** docker-compose.yml 中 `AI_PROVIDER_OPENAI_KEY=${OPENAI_KEY}` 直接通过环境变量传递。生产环境中如果 Docker inspect 被访问，密钥泄露。

**行动项：**
- 生产环境使用 Docker Secrets 或外部密钥管理 (阿里云 KMS)
- Phase 1 开发期可接受环境变量方式
- Phase 2 迁移到加密配置存储

### 🔵 P2-05: CORS 配置未提及

**问题：** 前端和 API 可能部署在不同子域名 (如 `app.xxx.com` 和 `api.xxx.com`)，需要 CORS 配置。

**行动项：**
- FastAPI 中间件配置 CORS
- 或：Nginx 反代统一域名，无跨域问题

### 🔵 P2-06: 无 CI/CD 策略

**问题：** 文档未提及代码如何从仓库部署到服务器。

**行动项：**
- Phase 1 使用 GitHub Actions (或 Gitea Actions) 自动构建 Docker 镜像
- 部署方式：SSH + docker-compose pull
- Phase 3 可引入蓝绿部署

### 🔵 P2-07: 无成本估算

**问题：** AI API 调用成本未估算。GPT-4o 每次调用约 $0.01-0.03，Gemini 图片生成约 $0.02-0.04/张。

**行动项：**
- 单次表盘生成成本：GPT-4o ($0.02) + Gemini 图片 ×3 ($0.09) ≈ $0.11 ≈ ¥0.8
- 20 人 × 10 次/天 = 200 次/天 ≈ ¥160/天 ≈ ¥4800/月
- 需要设定免费配额 + 付费策略

### 🔵 P2-08: 日本 VPS 可靠性

**问题：** 日本 VPS 仅 1u1g，作为备用入口。如果该服务器宕机，备用入口消失。无自动故障检测和切换。

**行动项：**
- 主入口 (阿里云) 监控日本 VPS 健康状态
- DNS 自动切换 (如果主入口不可用)
- 或接受单点故障，日本 VPS 仅作 CDN 缓存补充

### ✅ P2-09: WFF APK 结构已核实 (2026-08-12 验证)

**验证结果:** Google 官方文档确认 WFF APK 结构为:
- `res/raw/watchface.xml` — WFF 主文件 (必需)
- `res/drawable/` — 图片资源
- `res/font/` — 字体文件
- `res/values/strings.xml` — 字符串
- `AndroidManifest.xml` — `hasCode="false"`, 无 Activity

文档 1.2 节编译器设计已更新为正确结构。

### ✅ P1-14: aapt2 ARM64 兼容性 (2026-08-12 验证通过)

**验证结果:** aapt2 不支持 ARM64，但 **纯 Python APK 构建方案已验证可行**。

**方案:**
- Docker 构建时 (x86): aapt2 预编译 AndroidManifest.xml → 二进制 AXML + resources.arsc
- 运行时 (ARM64): Python zipfile 打包 + 纯 Python zipalign + apksigner (Java) 签名
- 动态替换 `res/raw/watchface.xml` 和 `res/drawable/*.png` 无需 aapt2

**验证详情:** 见 `/home/z/my-project/docs/APK_BUILD_VERIFICATION.md`

**关键代码:**
- `pyzipalign.py` — 纯 Python zipalign 实现，通过官方 `zipalign -c` 验证
- `apksigner` — bash 脚本 + Java JAR，ARM64 完全兼容
- 模板 APK 预编译 → 运行时只替换动态资源 → 签名 → 输出

**对部署架构的影响:** ARM 服务器可承担全部计算 (DB + Celery + Rembg + APK 构建)，阿里云只需做公网入口。

### ✅ P1-15: pngquant 许可证 (2026-08-12 验证)

**验证结果:** pngquant 采用 **GPL / 商业双协议**，不可用于本项目。

**已采取的行动:** 改用 **oxipng** (MIT 许可证)，Rust 编写，无损 PNG 压缩，性能优于 pngquant。

### ✅ P1-16: Seedance API 定位 (2026-08-12 验证)

**验证结果:** Seedance 是 **视频生成 API** (ByteDance)，不适合生成静态表盘素材。

**已采取的行动:** 从技术选型中移除 Seedance。图片生成统一使用 **Gemini Imagen** ($0.034/张)。

---

## 10. 开发者特别提示与红线规则

### 10.1 红线规则（违反即停止）

| 规则 | 说明 |
|------|------|
| **只走 WFF** | 绝不在 APK 中包含代码 (hasCode=false)，只打包 WFF XML + 资源。WFF APK 是纯资源包，不是可执行应用。 |
| **AI 外包** | 绝不在本地服务器部署 AI 大模型推理，所有 AI 走云端 API |
| **许可证合规** | 绝不引入 GPL/AGPL/LGPL 组件，所有依赖必须 MIT/Apache 2.0/BSD/ISC |
| **数据视图分离** | 前端永远不直接生成 WFF XML，只操作 CDM JSON |
| **三次熔断** | 同一组件在同类型问题上修复 3 次未解决，停止使用，寻找替代方案 |

### 10.2 三次熔断执行流程

```
组件 X 出现问题
  │
  ├── 第 1 次修复 → 记录到 daily_notes (edit_daily)
  │     └─ 问题: xxx | 修复: xxx | 结果: 记录
  │
  ├── 第 2 次同类型问题 → 记录 + 寻找根因
  │     └─ 问题: xxx | 修复: xxx | 结果: 记录 | 根因分析
  │
  ├── 第 3 次同类型问题 → 记录 + 启动替代方案调研
  │     └─ 问题: xxx | 结果: ⚠️ 触发熔断
  │
  └── 熔断动作:
        ├─ 1. 停止使用该组件
        ├─ 2. 在 docs/migration/ 记录替代方案
        ├─ 3. 更新本文档技术选型表
        └─ 4. 通知团队 (edit_memory 记录决策)
```

### 10.3 图像处理注意事项

AI 生成的表盘素材通常带背景，后端必须集成强大的图像分割/抠图算法：

1. **首选方案:** Rembg (MIT) — 基于 U2-Net，无需 GPU，CPU 即可运行
2. **备选方案:** 调用云端抠图 API (remove.bg API — 商用，按次计费)
3. **回退方案:** 前端提供简单的魔棒工具，用户手动标记前景/背景

### 10.4 APK 构建注意事项

> **澄清 (2026-08-12 修订):** WFF 表盘的分发载体就是 APK，但这是 **纯资源 APK** (`hasCode="false"`)，不包含任何代码。

**与传统 APK 的区别:**

| 维度 | 传统表盘 APK | WFF 纯资源 APK |
|------|------------|---------------|
| 代码 | 包含 Java/Kotlin 代码 | **无代码** (hasCode="false") |
| Activity | 有 WatchFaceService Activity | **无 Activity** |
| 构建 | 需要 Android Studio + Gradle | **只需 aapt2 + apksigner** |
| 大小 | 1-5 MB | **< 500 KB** |
| 签名 | 需要开发者签名 | 需要签名 (可用统一密钥) |

**服务端 APK 构建方案 (已验证 2026-08-12):**

```
Docker 构建时 (x86, 一次性):
  1. aapt2 compile → 编译 res/ 资源
  2. aapt2 link → 生成 APK 模板 (含二进制 AndroidManifest.xml + resources.arsc)
  3. 提取模板文件: AndroidManifest.xml (binary AXML) + resources.arsc
  4. 打包到 Docker 镜像中

运行时 (ARM64, 每次用户生成表盘):
  1. Python zipfile 打包:
     ├─ 模板 AndroidManifest.xml (二进制 AXML, 固定)
     ├─ 模板 resources.arsc (固定)
     ├─ res/raw/watchface.xml (动态, 编译器生成)
     └─ res/drawable/*.png (动态, AI 生成)
  2. pyzipalign 对齐 (纯 Python, 通过官方验证)
  3. apksigner 签名 (bash + Java, ARM64 兼容)
  4. 输出 → 上传 OSS
```

> **验证结论:** 纯 Python APK 构建方案完全可行。
> - 不需要 aapt2 运行时 (ARM64 不支持)
> - 不需要 zipalign 二进制 (纯 Python 替代)
> - 只需 Java JRE (ARM64 官方支持) 运行 apksigner.jar
> - 详见 `/home/z/my-project/docs/APK_BUILD_VERIFICATION.md`

### 10.5 代码规范

| 维度 | 工具 | 许可证 |
|------|------|--------|
| Python Lint | Ruff | MIT |
| Python 格式 | Ruff (内置) | MIT |
| Python 类型 | mypy | MIT |
| TS/JS Lint | ESLint | MIT |
| TS/JS 格式 | Prettier | MIT |
| Git Hooks | Husky + lint-staged | MIT |
| 提交规范 | Conventional Commits | — |

### 10.6 开发环境配置建议

**开发期 (Phase 1-2):**
- 本地开发: 4u8g (本地 Docker Compose 全量运行)
- 或使用现有 ARM 8u16g 服务器开发

**生产环境 (Phase 1-3):**
- 三服务器拓扑 (见第 7 节部署架构)
  - 阿里云 2u2g 3Mbps: 公网入口 (¥60/月)
  - ARM 8u16g: 计算节点 (已有)
  - 日本 1u1g: 备用入口 (已有)
- 对象存储 + CDN: 阿里云 OSS + CDN (按量计费)

**扩展环境 (Phase 3+ 用户增长):**
- 阿里云升级至 4u8g (~¥200/月) 或 8u16g
- Rembg Worker 可独立部署到阿里云 ECS 按量付费实例

---

## 附录 A: 关键参考资料

| 资料 | 链接 |
|------|------|
| Watch Face Format (WFF) 官方文档 | https://developer.android.com/training/wearables/wff |
| WFF XML Schema | https://developer.android.com/training/wearables/wff/schema |
| Wear OS 设计指南 | https://developer.android.com/design/wear |
| OpenAI API 文档 | https://platform.openai.com/docs |
| Google Gemini API | https://ai.google.dev/gemini-api |
| Rembg 文档 | https://github.com/danielgatis/rembg |
| Fabric.js 文档 | http://fabricjs.com/ |
| FastAPI 文档 | https://fastapi.tiangolo.com/ |
| Celery 文档 | https://docs.celeryq.dev/ |
| Taro 文档 | https://docs.taro.zone/ |
| WireGuard | https://www.wireguard.com/ |
| Valkey | https://valkey.io/ |
| shadcn/ui | https://ui.shadcn.com/ |
| intent:// URI 格式 | https://developer.android.com/training/app-links |

## 附录 B: 许可证合规检查清单

在引入任何新依赖前，必须完成以下检查:

- [ ] 确认许可证类型 (MIT / Apache 2.0 / BSD / ISC → ✅ 通过)
- [ ] 确认非 GPL / AGPL / LGPL / SSPL / RSALv2
- [ ] 确认无 Copyleft 传染风险
- [ ] 确认许可证与项目商业模式兼容
- [ ] 记录到技术选型表 (本文档第 4 节)
- [ ] 如有疑虑，停止并咨询

---

> **文档维护说明:** 本文档随项目进展持续更新。每个 Phase 完成后，回顾并修订下一阶段的架构和选型。重大决策通过 `edit_memory` 记录到长期记忆。

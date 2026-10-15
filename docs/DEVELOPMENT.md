# 开发指南

## 环境要求

| 组件 | 版本 | 用途 |
|------|------|------|
| Python | 3.10+ | 后端（3.12 验证通过） |
| Node.js | 18+ | 前端（20.17 验证通过） |
| redis-server | 任意稳定版 | Celery broker + result backend |
| Docker | — | 仅构建 wff-builder 预编译 APK 模板时需要（aapt2 是 x86_64） |
| Java JRE | 11+ | 仅 APK 签名时需要（apksigner） |

## 服务启动顺序（有依赖 ⚠️）

```bash
# 1. redis 必须最先启动 — API 先于 redis 启动会导致 kombu 连接池缓存坏连接,
#    之后重启 redis 也无效, 必须 kill 掉 API 重启 (实测踩坑)
redis-server --daemonize yes

# 2. Celery worker — ⚠️ 必须用 -A api.tasks (包路径)
python3 -m celery -A api.tasks worker -Q image,default -c 2 --loglevel WARNING
#   ❌ 错误: -A api.tasks.celery_app.celery_app
#      这样只加载 app 配置, 不加载 tasks.py 里的任务定义
#      → worker 收到任务报 KeyError: 'api.tasks.tasks.process_image_task'
#   ❌ 错误: celery_app.py 缺少 celery_app.set_default() 时
#      shared_task 会绑定到默认 amqp://localhost:5672 → Connection refused
#      (两个修复已内置在代码里, 但改动 api/tasks/ 时注意不要破坏)

# 3. API
uvicorn api.app:app --host 0.0.0.0 --port 8000

# 4. 前端
cd web
npm install
npx next dev -p 3000        # 开发
npx next build && npx next start -p 3000   # 生产
```

## 环境变量

### 运行模式与安全（2026-10 审计修复新增）

| 变量 | 说明 | 默认 |
|------|------|------|
| `WF_ENV` | `development` \| `production`；production 强制外部签名、强制 API key、配额 fail-closed | `development` |
| `WFF_API_KEYS` | 逗号分隔 API Key；**generate/ai-test/v1 全部消费**；production 未配置 → 503 | 无 |
| `WF_CORS_ORIGINS` | 逗号分隔来源；配置后启用 credentials，默认 `*`（禁 credentials） | `*` |
| `WF_QUOTA_GENERATE_PER_HOUR` | generate 每 key 每小时配额 | `10` |
| `WF_QUOTA_AI_TEST_PER_HOUR` | ai/test 每 key 每小时配额 | `20` |
| `WF_AI_ALLOWED_HOSTS` | BYOK base_url 域名白名单（逗号分隔，支持 `*.suffix`）。**production 未配置 → BYOK 自定义端点被整体拒绝（R3）**；development 未配置 = 放行任意通过 SSRF 硬检查的公网地址 | 无 |

### AI 后端

| 变量 | 说明 | 默认 |
|------|------|------|
| `OPENAI_API_KEY` | OpenAI 兼容后端密钥（gateway backend=auto 时 z-ai CLI 可用则优先 z-ai） | 无 |
| `OPENAI_BASE_URL` | OpenAI 兼容端点 | 官方 |
| `OPENAI_MODEL` | 服务端默认 OpenAI 模型 | `gpt-4o` |

> ⚠️ 历史文档曾列 `AI_PROVIDER` / `ZAI_API_KEY`——**代码从未读取**（审计确认的
> 文档偏差，已删除）。后端选择由 `AIGateway(backend=...)` 决定：auto 模式优先
> 探测 z-ai CLI，回退 `OPENAI_API_KEY`。密钥缺失时 AI 生成返回普通失败响应
> （`status: failed`），并非 503。

> **BYOK（用户自定义 AI 配置）**：`WF_AI_ALLOWED_HOSTS` 是生产部署前提——
> `WF_ENV=production` 且未配置该白名单时，用户自定义 Base URL 直接被拒绝
> （服务端默认 AI 不受影响）。development 未配置 = 允许通过 SSRF 硬检查的
> 任意公网地址。SSRF 检查含私网/回环/CGN/v4-mapped 全量拒绝；DNS rebinding
> TOCTOU 为已知限制（连接级 pinning 属后续工作）。

### Celery / Redis

| 变量 | 说明 | 默认 |
|------|------|------|
| `CELERY_BROKER_URL` | Celery broker（CDM 存档与配额共用该 Redis） | `redis://127.0.0.1:6379/0` |
| `CELERY_RESULT_BACKEND` | 任务结果后端 | 同 broker |

> ⚠️ 历史版本的 `REDIS_URL` 从未被代码读取（审计确认的文档偏差），实际读取
> `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND`。

### APK 签名（生产必读）

| 变量 | 说明 | 默认 |
|------|------|------|
| `WFF_KEYSTORE` | keystore 路径 | 仓库公开开发证书 `wff-builder/keystore/test.keystore` |
| `WFF_KEYSTORE_ALIAS` | key alias | dev: `wfftest`；production: 必填 |
| `WFF_KEYSTORE_PASSWORD` 或 `WFF_KEYSTORE_PASSWORD_FILE` | store 密码（env 或文件引用） | dev: `wfftest123`；production: 必填 |
| `WFF_KEY_KEY_PASSWORD` 或 `WFF_KEY_KEY_PASSWORD_FILE` | key 密码（缺省同 store 密码） | 同上 |

production 模式下三件套缺一即构建失败，且**证书 SHA-256 指纹等于公开开发证书
时直接拒绝**（把 test.keystore 换文件名也无效）。密码通过 `env:`/`file:` 引用
传给 apksigner/keytool，不出现在进程命令行。开发模式显式设置 `WFF_KEYSTORE`
时同样需要配齐 alias/密码。

首次使用 WFF 直通 API 时执行 `./scripts/create-api-key.sh`，它会生成随机
key 并写入被 Git 忽略的 `.env`。`scripts/dev-services.sh` 启动/重启时会自动
加载该文件。不要把 `.env` 或真实 key 提交到仓库。

### 用户自定义 AI API（BYOK）

前端 `/settings` 可配置用户自己的 OpenAI 兼容 API Key、HTTPS Base URL 和模型。
配置只写入当前标签页的 `sessionStorage`；点击 AI 生成时，以 `ai_config` 随该次
`POST /api/generate` 请求发送。后端只在该请求内构造客户端，不持久化配置，也不
记录密钥；关闭标签页或点击“使用服务端默认”会清除浏览器配置。请求结构为：

```json
{
  "prompt": "极简黑白数字表盘",
  "ai_config": {
    "api_key": "用户密钥",
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-4o"
  }
}
```

`ai_config` 可省略；省略或密钥为空时沿用服务端 AI 配置。不要把真实密钥写进
文档、截图、issue、日志或 Git。自定义 Base URL 仅接受 HTTPS，且不能在 URL
中内嵌用户名、密码、查询参数或片段。设置页的“测试连接”会调用
`POST /api/ai/test` 发起一次最多 16 token 的真实模型请求，以同时验证密钥、
Base URL 和模型；响应不会包含密钥或模型输出。

启动服务后访问 `/ci` 使用 Agent CI 工作台。API Key 只保存在当前浏览器
标签页的 `sessionStorage`，关闭标签页后清除；页面主操作是直接下载 APK，
二维码仅作为手机打开下载页的辅助入口。

## 测试

```bash
# 全量测试 (core: CDM+编译器 / api: 端点 / phase2: AI 生成链路 mock)
python3 -m pytest tests/ -v

# 只跑某模块
python3 -m pytest tests/test_core.py -v
```

> `test_phase2.py` 对 AI 调用做了 mock，不需要真实 API Key。

## WFF Builder 单独使用（不经 API）

```bash
cd wff-builder
python wff_builder.py init projects/my_watch      # 生成项目骨架
python wff_builder.py validate projects/my_watch  # 16 条校验规则
python wff_builder.py build projects/my_watch     # → projects/my_watch/dist/*.apk
```

详细规则和 CLI 参数见 `wff-builder/SKILL.md`。

## 重新构建 APK 模板（很少需要）

预编译模板（二进制 AndroidManifest.xml + resources.arsc）已提交在
`wff-builder/projects/demo/_build/compiled/`，正常开发不需要重建。
只有修改 Manifest（如包名、SDK 版本）时才需要在 **x86_64** 环境（本机
Docker 或 x86 服务器）执行 `aapt2 compile + link` 重算模板，产物覆盖回上述
目录。ARM64 节点（如 DevSpace）不要直接调用 x86_64 的 `aapt2`——构建器在
aapt2 不可用时自动使用仓库内已验证的 ARM 预编译模板。

## Docker Compose（基础栈）

`docker-compose.yml` 提供 api + web 两个服务（开发形态：源码 bind mount +
`next dev`）。redis 与 celery worker 按上文「服务启动顺序」在同一网络内
宿主机上运行；容器内 API 连接宿主 Redis 时给 `api` 服务加：

```yaml
    environment:
      CELERY_BROKER_URL: redis://host.docker.internal:6379/0
      CELERY_RESULT_BACKEND: redis://host.docker.internal:6379/0
    extra_hosts:
      - "host.docker.internal:host-gateway"   # Linux 需要; mac/win 内置
```

生产化注入安全变量（不提交真实值，用环境文件或 secret）：

```yaml
    environment:
      WF_ENV: production
      WFF_API_KEYS: ${WFF_API_KEYS:?set in .env}
      WFF_KEYSTORE: /run/secrets/keystore     # 三件套其余两项见上文表格
```

若全部容器化，把 `CELERY_BROKER_URL` 指向 compose 网络的 redis 服务并补充
worker 服务定义（当前文件未包含，属后续工作）。web 服务通过
`API_PROXY_TARGET=http://api:8000` 让 next rewrites 代理命中容器网络的
API。镜像构建排除项见根目录与 `web/.dockerignore`（审计 S6：`.env*`、
运维备份、日志、Git 元数据不进镜像层；公开开发证书显式保留）。

## 部署环境参考（华为云 DevSpace 实测）

| 项 | 值 |
|----|-----|
| 环境 | 8vCPU ARM64 (aarch64), 16GB RAM, HCE2 |
| Python 服务 | uvicorn :8000 + celery worker (image,default 双队列) |
| 前端 | next build 产物, next start :3000 |
| 验证 | 异步图像管线端到端 SUCCESS; /editor 页面 200 |

DevSpace 特有的连接方法（dbus/keyring/PTY 隧道）见仓库外的工作区 TOOLS.md，与项目代码无关。

### DevSpace 持久工具链

DevSpace 的系统盘可能随容器重建而恢复，但 `/workspace` 数据盘会保留。当前 ARM64
开发环境把 Temurin JRE 17 和 Android Build Tools 34 的 Java 版 `apksigner`
分别安装在：

```text
/workspace/.tools/temurin-17
/workspace/.tools/android-sdk/build-tools/34.0.0
```

`scripts/dev-services.sh` 会自动设置 `JAVA_HOME`、`WFF_JAVA`、`ANDROID_HOME`、
`APKSIGNER` 和 `PATH`。不要在 ARM64 节点调用 Build Tools 压缩包里的 x86_64
`aapt2`；构建器会因为持久 SDK 中没有 `android.jar` 而使用仓库内已验证的 ARM
预编译资源模板，但 APK 签名、官方 validator 和内存评估均使用持久 Java 环境。

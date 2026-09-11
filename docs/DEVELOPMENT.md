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

| 变量 | 说明 | 默认 |
|------|------|------|
| `REDIS_URL` | Celery broker/result | `redis://127.0.0.1:6379/0` |
| `AI_PROVIDER` | `zai` \| `openai` | `zai` |
| `ZAI_API_KEY` / `OPENAI_API_KEY` | AI 密钥 | 无（缺失时 AI 端点返回 503） |
| `OPENAI_BASE_URL` | OpenAI 兼容端点 | 官方 |
| `OPENAI_MODEL` | 服务端默认 OpenAI 模型 | `gpt-4o` |
| `WFF_API_KEYS` | `/api/v1/wff/*` 接受的逗号分隔 API Key | 无（未配置时返回 503） |

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
中内嵌用户名、密码、查询参数或片段。

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

预编译模板（二进制 AndroidManifest.xml + resources.arsc）已提交在仓库里，正常开发不需要重建。
只有修改 Manifest（如包名、SDK 版本）时才需要：

```bash
# 需要 x86_64 + Docker (aapt2 不支持 ARM)
cd wff-builder
docker build -t wff-template -f Dockerfile.template .
docker run --rm -v $(pwd)/template:/out wff-template cp -r /template /out
```

## 部署环境参考（华为云 DevSpace 实测）

| 项 | 值 |
|----|-----|
| 环境 | 8vCPU ARM64 (aarch64), 16GB RAM, HCE2 |
| Python 服务 | uvicorn :8000 + celery worker (image,default 双队列) |
| 前端 | next build 产物, next start :3000 |
| 验证 | 异步图像管线端到端 SUCCESS; /editor 页面 200 |

DevSpace 特有的连接方法（dbus/keyring/PTY 隧道）见仓库外的工作区 TOOLS.md，与项目代码无关。

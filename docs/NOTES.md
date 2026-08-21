# 开发踩坑记录

> 按时间线沉淀的实施教训。**修改构建器/编译器前先读本文档**，很多规则是用真机安装失败换来的。

## 1. WFF APK 构建 16 条规则（真机验证 2026-08-15）

### Manifest / SDK

1. `minSdkVersion=33`（Wear OS 4），不是 30。minSdk=30 会导致真机安装后表盘不显示
2. WFF v1 格式**不需要** `<service>` 声明、intent-filter、`BIND_WATCH_FACE` 权限
3. `uses-sdk` 必须显式声明，缺省时目标设备按 SDK 0 拒绝安装

### ZIP / 对齐

4. `resources.arsc` 必须 `ZIP_STORED`（不压缩）+ **4 字节对齐**，DEFLATED 报 `error -124`（Android R+ 要求）
5. 不要用 pyzipalign 和 apksigner 两步走：apksigner 重签名会丢失 pyzipalign 写入的 extra field
6. 正确做法：**Python 手动构造 ZIP 字节流**（不用 `zipfile.ZipFile`），在 local header 和 central directory 都写对齐 extra field (0xD935)，然后一次签名

### 资源

7. `res/xml/` 必须是 aapt2 编译后的**二进制 AXML**（文件头 0x0300），不能放原始文本 XML
8. `res/values/` 不应独立出现在 APK 中（已编译进 resources.arsc）
9. 模板 APK 里的资源在 Docker 构建时用 aapt2 预编译（aapt2 只有 x86_64 二进制，ARM64 无法本地编译）

### WFF XML 语法

10. 表达式数据源必须用方括号：`[SECOND]`、`[BATTERY]`，裸写 `SECOND` 编译不报错但运行时不显示
11. 时间显示用 `DigitalClock` + `TimeText` 元素，**不要**用 `Text` + `Template`（模板引擎不刷新）
12. 字体用 `family="SYNC_TO_DEVICE"`，不要写 `Roboto`（设备上可能缺失）
13. 颜色用 8 位 ARGB：`#ffRRGGBB`，6 位 `#RRGGBB` 在部分设备上渲染为透明

### 签名

14. 开发密钥 `test.keystore`（pass: `wfftest123`, alias: `wfftest`），v1+v2+v3 全签名
15. 上线前必须换正式密钥，且 keystore 不能提交到公开仓库

### 编译管线

16. CDM → WFF XML 用 Jininja2 模板保持纯函数；XML → APK 的字节流操作集中在 `wff-builder/`，**不要**把 ZIP 逻辑散到编译器里

## 2. Celery 三坑（Phase 3，2026-08-20）

1. **worker 启动必须 `celery -A api.tasks worker`**。用 `-A api.tasks.celery_app.celery_app` 只加载 app 配置不加载任务定义 → 任务注册表为空 → worker 收到任务报 `KeyError: 'api.tasks.tasks.process_image_task'`
2. **`shared_task` 会绑定默认 app**。独立导入 tasks 模块时，shared_task 落到默认 `amqp://localhost:5672`（连接拒绝）。修复：`celery_app.py` 末尾 `celery_app.set_default()` + 包 `__init__.py` 先导入 celery_app 再导入 tasks。改动 `api/tasks/` 时不要破坏这两处
3. **broker 后启动会"中毒"**。API 先于 redis 启动时，kombu 连接池缓存坏连接，重启 redis 后 API 依然报连接拒绝，必须 kill API 重启

降级策略：`editor.py` 的 image/process 对 `.delay()` 捕获所有异常 → 同步 Pillow 处理。broker 挂了功能不中断，只是变慢。

## 3. 环境与依赖

- **rembg/onnxruntime 放弃**：~500MB 依赖在低配/ARM 环境装不上，改用 Pillow flood-fill 阈值抠图。对纯色背景素材够用，复杂照片背景效果有限（已知限制）
- **npm 重依赖超时**：低配 VM 装 fabric 等大包频繁 504。解决：`--registry=https://registry.npmmirror.com` + 分批安装
- **Node ARM64 安装**：从 `npmmirror.com/mirrors/node/` 下载对应架构 tar.xz（需先 `yum install xz`）

## 4. 已修复的 API Bug（Phase 3 验证时发现）

| Bug | 根因 | 修复提交 |
|-----|------|---------|
| CDM 校验端点 500 | `cdm.ClockType` 写成了实例属性（应为导入的枚举）；`AnalogTime` 无 `hands` 字段 | `c8f21f4` |
| `.delay()` 连接拒绝 5672 | shared_task 绑定默认 amqp app | set_default + `__init__` 导入 |
| worker KeyError | 启动命令不加载任务定义 | `__init__.py` 注册 + `-A api.tasks` |

## 5. 历史实验阶段结论（已被推翻，勿参考）

早期实验（`experiments/`，已不维护）曾记录 minSdk=30、"真机安装待确认" 等结论，**均已被 2026-08-15 真机验证推翻**，以本文档第 1 节为准。

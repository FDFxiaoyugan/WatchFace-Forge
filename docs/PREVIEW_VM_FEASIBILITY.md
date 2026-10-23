# WearOS 虚拟机预览模块 · 可行性分析

> 调研日期：2026-10-24 ｜ 调研人：skill 侧 agent
> 需求来源：平台侧提议——表盘打包完成后实时预览；网页控制虚拟手表；开关机；一键预览；加速度传感器/电量等参数修改，方便表盘效果测试。
> 结论有效期：基于 2026-10 官方文档与开源生态实测快照；ARM emulator 相关结论在 POC 实测后可能更新。

---

## 1. 结论速览

| 维度 | 结论 |
|---|---|
| **现成开源项目** | **没有"开箱即用的 Wear OS 网页虚拟机"整机项目**。但拼装件全部齐备：官方 Android Emulator + 官方 Wear OS 6 (API 36) 系统镜像 + scrcpy（Apache-2.0）串流 + adb 官方传感器/电量/健康数据 mock 命令。需要自建的只有**编排层**（实例池管理 + 一键装盘 + 控制面板 API） |
| **推荐方案** | **方案 A（Emulator 云农场）**：Wear OS 6 headless emulator 实例池 + scrcpy 串流到浏览器 + adb 控制链。降级预案两条：截图农场（无交互）／真机农场 |
| **系统占用** | 单实例 RAM 2.5–3.5GB、磁盘 4–6GB、CPU 空闲 0.1–0.3 核／动画渲染 0.5–2 核（软件渲染）。主力 ARM 8u16g 可承载 **2–3 并发**（需给构建服务留余量）；日本 VPS 1u1g 只能做公网反代入口，跑不动实例 |
| **工期** | **POC 1–2 天**（杀三个风险变量）→ **MVP 4–6 周**（单实例全自动预览+控制面板）→ 生产化 +1.5–2 周（实例池/配额/容器化）。降级路线（截图农场）1.5–2 周 |
| **头号风险** | ARM64 Linux host 的 emulator 二进制**无官方分发渠道**（源码 30.0.26 起支持交叉编译，但 sdkmanager 至今不装 aarch64 版）+ /dev/kvm 可用性未知。两个变量 POC 一天内可判定 |
| **可行性总评** | **有条件可行**。无理论阻断，三个待实测变量全部收敛在 1–2 天 POC 内；失败有三条降级路径，最坏情况（ARM 完全跑不动）加一台 2C8G x86 专机（约 100–200 元/月）即可解决 |

---

## 2. 需求解读：功能 → 技术能力映射

| 用户需求 | 技术实现路径 | 成熟度 |
|---|---|---|
| 网页上控制虚拟手表 | scrcpy-server 拉取 emulator 画面（H.264）→ WebSocket → 浏览器 WebCodecs 解码渲染；鼠标事件回传 adb 触摸注入 | 串流组件成熟，需自建约 1 周胶水层 |
| 开关机 | emulator 实例生命周期管理（启动 1–2 分钟／快照恢复 10–30 秒）。建议用**快照恢复代替真开关机** | 成熟，注意价值/成本比 |
| 表盘打包后一键预览 | 打包流水线尾部 hook：adb install（debug APK）→ 设为活动表盘 → 串流会话自动切到表盘画面 | 自动化路径明确，设活动表盘命令有版本差异（坑 7） |
| 加速度传感器修改 | emulator console 官方命令 `adb emu sensor set acceleration x:y:z`（同时支持磁力/方向/温湿度/气压/距离/光等） | 官方文档明确支持 |
| 电量修改 | `adb shell dumpsys battery set level N`（官方标准命令，表盘低电图标/电量 complication 立即响应） | 成熟 |
| 心率/步数（表盘核心数据源） | Health Services 官方模拟数据机制（synthetic data 广播命令），emulator 上可 mock 心率/步数/锻炼状态 | 官方支持，覆盖度需逐项实测 |
| 时间/时区/12-24h 切换 | root 下 date 命令 + 设置项修改（对表盘日期/时间渲染测试价值极高） | 成熟 |

**定位澄清（重要）**：现有编辑器内已有 CDM 级 TimeSimulator 预览（低保真、编辑用）。本模块的增量价值是 **APK 级高保真预览**——所见即真机渲染引擎所出。两者互补不互替：编辑器预览管"改得快"，虚拟机预览管"验得真"。

---

## 3. 开源生态盘点（按拼装层分解）

| 层 | 需要什么 | 现成项目 | License | 判定 |
|---|---|---|---|---|
| 虚拟化引擎 | 跑 Wear OS 的 Android 虚拟设备 | **Android Emulator**（Google 官方） | Apache-2.0 | ✅ 官方现成；⚠️ ARM64 Linux host 二进制获取是坑（见坑 1） |
| 系统镜像 | Wear OS 6 / API 36 圆屏镜像 | **官方 SDK system image**（`sdkmanager "system-images;android-36;wear;..."`) | SDK 条款 | ✅ 官方提供；arm64-v8a 变体覆盖待实测（坑 3） |
| 画面串流 | 画面推到浏览器 | **scrcpy**（Genymobile） | Apache-2.0 | ✅ 活跃维护 |
| Web 控制面板 | 浏览器多设备管理 | **ws-scrcpy**（NetrisTV） | MIT | ⚠️ 可用但上游低维护；建议只参考其架构，自建薄层 |
| Web 视频解码 | 浏览器解 H.264 | WebCodecs API（浏览器原生） | 无依赖 | ✅ 零 license 负担，优于引第三方解码库 |
| 传感器/电量/健康数据 mock | 虚拟参数注入 | emulator console + dumpsys + Health Services synthetic data（全官方命令） | 官方文档 | ✅ 命令路径全部官方存在 |
| WFF 渲染器（替代路线） | 网页直接渲染表盘 XML | **无成熟开源项目**（2026-09-22 生态调研 + 本次复查确认；商业工具 Facer/WFS 预览器均闭源） | — | ❌ 自研 = 重复实现整个渲染规范，保真度永远存疑 |
| 编排层 | 实例池/一键装盘/API | **无现成** | — | 🔧 自建（本模块主要工程量所在） |

**排除项**（查过为什么不行）：
- **Waydroid / redroid**（容器跑 Android）：只支持 phone ROM，无 Wear OS 镜像，不可行。
- **Cuttlefish**（Google 云虚拟设备）：需要 AOSP 全量自编译 + crosvm/KVM，重量级不匹配，且 wear target 要自己 build。
- **Genymotion**：商业闭源，不支持 wear 镜像，且 license 政策与自建平台冲突。
- **三星 Remote Test Lab**：托管**真机**网页控制，可作补充验证渠道（免费时长有限），不是可自建的虚拟机。
- **Firebase Test Lab**：能装 APK+截图（截图农场的外包版），但不能交互控制。

---

## 4. 方案对比

| 维度 | A：Emulator 云农场（推荐） | B：Web 自研 WFF 渲染器 | C：真机农场 |
|---|---|---|---|
| 保真度 | 高（真 WOS 渲染引擎，AOSP 镜像） | **中，永远存疑**（自实现 ≠ 真机引擎，与"真机是最终真相源"方法论冲突） | 最高（三星 One UI 实机） |
| 传感器/电量控制 | 全部可程序化注入 | 全部虚拟（无限自由） | 部分受限（电量注入需 root/调试桥） |
| 并发扩展 | 实例池，2-3 并发起步 | 无限（浏览器渲染） | 硬件数量限制 |
| 系统占用 | 高（每实例 2.5-3.5GB） | 近零（服务器不渲染） | 中（每台 1-2GB + hub） |
| 工期 | MVP 4-6 周 | 6-10 周+（WFF v1-v5 全覆盖）且**永远做不完像** | 2-3 周 |
| 头号风险 | ARM emulator 二进制（POC 可杀） | 保真度悖论（无法验收"像不像真机"） | 硬件磨损/采购/单台故障 |
| License | 全 Apache/MIT/官方，合规 | 自研无风险 | 无 |
| 判定 | **主路线** | **不推荐**（做低保真预览不如用现有 CDM 预览增强） | **降级预案/高保真补充** |

**推荐组合**：A 为主线（MVP），预览页面明确标注"预览不可替代真机验证"；若 POC 判定 ARM 跑不动且不加机器，则降级到截图农场（A 的子集）；真机农场作为二期高保真补充。

---

## 5. 系统占用分析

### 5.1 单实例资源账（headless + 软件渲染，估算值）

| 资源 | 空闲/静态表盘 | 动画渲染中 |
|---|---|---|
| RAM | 2.5–3.5 GB（qemu + guest 1.5GB + SwiftShader） | 同左（峰值 +0.5GB） |
| CPU | 0.1–0.3 核 | 0.5–2 核（SwiftShader 软渲染；无 KVM 再 +30–50%） |
| 磁盘 | 镜像+data 4–6 GB（COW 克隆后每实例增量 <1GB） | — |
| 串流带宽 | 200–500 kbps（表盘画面低运动量） | 峰值 800 kbps–1.5 Mbps |
| 串流延迟 | 300–800 ms（采集+编码+网络+解码） | 同左，预览用途可接受 |

### 5.2 三台机器资源判定

| 机器 | 角色 | 判定 |
|---|---|---|
| ARM 8u16g（无公网，后端容器化已拍板） | 预览实例宿主 | ✅ 可承载 **2–3 并发实例**（预留构建服务 4GB + 系统 2GB 余量）；超并发走排队（复用平台 Redis 配额体系）；需实测 /dev/kvm |
| 日本 VPS 1u1g（前端公网入口） | WebSocket 反代/信令 | ✅ 只做入口转发（带宽轻）；❌ 跑不动实例；WebRTC P2P 打洞失败时需其兼做 TURN（1u1g 带宽下单会话够用） |
| 华为 DevSpace 8u16g ARM（CI 现役） | POC 试验场 | ✅ POC 用（与生产隔离）；❌ 不建议生产混跑（CI 任务与预览会话互相干扰） |

**网络拓扑**：浏览器 → VPS（ws 入口）→ 隧道 → ARM 机串流服务 → emulator 实例。与现有"前端公网入口在 VPS、后端在 ARM 机"拓扑同构，无新增链路类型。

---

## 6. 工期估算

| 阶段 | 内容 | 工期 | 出口判据 |
|---|---|---|---|
| **Phase A：POC** | ① ARM 上 emulator 二进制三路径实测（社区构建/自编译/备选）② `ls /dev/kvm` + KVM/TCG 双模式跑分 ③ WOS6 镜像 arch 覆盖实测 ④ adb 装一个我方 WFF APK 并截图 | **1–2 天** | Go/No-Go 判定书（三个变量全部有实测数值） |
| **Phase B：MVP（单实例全自动）** | B1 emulator 服务化+快照生命周期（3–5 天）→ B2 scrcpy 串流 + WebCodecs 播放器 + 触摸回传（5–7 天）→ B3 一键预览 API（打包 hook + 装盘 + 会话直达）（2–3 天）→ B4 控制面板（传感器/电量/心率/时间/息屏 API + 前端 UI）（3–5 天） | **2–3 周** | 网页上完整走通"打包→预览→调加速度→调电量"闭环 |
| **Phase C：生产化** | 实例池（2-3 并发+排队）、容器化（KVM 挂载/seccomp/自愈）、配额接入、串流会话管理、与 API_CONTRACT 契约扩展 | **1.5–2 周** | 平台侧可按契约集成；异常注入测试（杀进程/断连）全自愈 |
| **降级路线：截图农场** | 砍掉串流，定时截图 → 网页图廊/GIF。传感器扫描（每参数一帧）仍可自动执行 | **1.5–2 周** | 无交互预览可用 |
| **合计** | MVP 交付 **4–6 周**；生产化总计 6–8 周 | — | — |

---

## 7. 坑点清单（分级）

### P0 阻断级（POC 必须先杀掉）

| # | 坑 | 事实依据 | 缓解 |
|---|---|---|---|
| 1 | **ARM64 Linux 无官方 emulator 二进制**：sdkmanager 在 aarch64 上装的是 x86_64 binary；官方 issue（242699119）自 2022 挂至今；源码自 30.0.26 起支持交叉编译 | 2026-10 实测快照 | 三路径：① 社区 aarch64 构建（GitHub gist 实践存在）② 自编译（工作量大，最后手段）③ 放弃 ARM host，加 2C8G x86 专机（约 100–200 元/月，emulator 官方一等公民支持） |
| 2 | **/dev/kvm 可用性未知**：ARM 云 VM 大概率无 KVM → 落 TCG 软翻译（同架构，性能 5–7 折）；ARM 物理机则大概率有 KVM | 需实测 `ls /dev/kvm` | KVM 有→最优；无→TCG 跑帧率基准，达标即用；不达标→x86 专机 |

### P1 高（影响体验/工期）

| # | 坑 | 事实依据 | 缓解 |
|---|---|---|---|
| 3 | WOS6 (API 36) 镜像 arm64-v8a 变体覆盖未确认（Wear OS 5.1 有 arm64 先例，API 36 待 `sdkmanager --list` 实测） | 待 POC | 若无 arm64 镜像 → 只能 x86 路线 |
| 4 | SwiftShader 软渲染帧率：60fps 动画可能掉到 20–40fps（预览够用但需实测）；表达式驱动的连续动画场景是压力测试点 | — | POC 跑 R53–R55 同款表盘做基准 |
| 5 | 串流网络路径：ARM 机无公网，ws 隧道加一跳；延迟预算 300–800ms | — | 预览非游戏场景可接受；超 1s 则排查隧道 |
| 6 | **保真度声明（架构性）**：emulator 是 AOSP 系 wear 镜像 ≠ 三星 One UI 8.0（真机字体集/OEM 表盘引擎差异，WFF version≥2 新特性表现可能分叉） | 既有矩阵测试方法论 | 产品文案必须标注"预览=冒烟+参数扫描，真机矩阵仍是验收源"；预览发现的 bug 真机复核后才修 |

### P2 中（工程细节）

| # | 坑 | 缓解 |
|---|---|---|
| 7 | 设活动表盘的 CLI 因 WOS 版本而异（`cmd watchface` / SysUI intent / picker 模拟），无单一官方命令 | POC 定版命令矩阵；最坏用 UI 自动化兜底 |
| 8 | 传感器覆盖差异：加速度/磁力/方向走 console；心率/步数走 Health Services mock（非 sensor 通道）；个别传感器镜像可能缺失 | 逐项实测后冻结"可 mock 清单"进 API 文档 |
| 9 | 容器化：emulator 是有状态服务（与平台无状态容器哲学冲突）；需 /dev/kvm 挂载、seccomp profile、崩溃自愈 | 独立 compose 单元，不进无状态 K8s；生命周期管理器独立进程 |
| 10 | 实例池与构建服务抢资源：wff-builder 构建峰值与预览渲染峰值叠加时 8u16g 紧张 | 配额互斥：预览会话与构建任务共享资源池，排队调度 |
| 11 | 心率 mock 依赖 Health Services 服务的 broadcast 接口，个别 wear 镜像 GMS 组件不完整时 mock 失效 | POC 验证；失效则换 AOSP wear 镜像变体 |
| 12 | 时间旅行（改系统时间）在高版本 Android 有时间同步守护进程回写问题 | 用 root date + 关闭自动时间同步，实测确认 |

### P3 低

| # | 坑 | 缓解 |
|---|---|---|
| 13 | system image 几 GB 不入 git（合规+体积） | .gitignore 封禁 system-images/；部署时 sdkmanager 拉（CI 已有此模式） |
| 14 | ws-scrcpy 上游低维护 | 只参考架构自建薄层（scrcpy-server 直连 + 自写 ws 网关） |
| 15 | 开关机（冷启动）1–2 分钟，用户等不起 | 默认"快照恢复"（10–30 秒）；真冷启动做成高级选项 |
| 16 | GMS 镜像的多租户使用边界（SDK 条款主要面向开发测试） | 内部预览用途无碍；若未来对公网用户提供，法务再评估 |

---

## 8. 可行性分析（三维判定）

### 8.1 技术可行性：有条件可行 ✅（附判定链）

```
已确认事实（官方文档级证据）            待实测变量（POC 1-2 天内全部可判定）        已证伪/排除
─────────────────────────────         ─────────────────────────────         ─────────────
✅ WOS6 API36 wear 镜像官方存在         ① aarch64 emulator 二进制可获取性        ✗ Waydroid/redroid（无 wear 镜像）
✅ sensor console / battery /          ② /dev/kvm 存在性与 TCG 性能档位         ✗ Cuttlefish（重量不匹配）
   Health Services mock 官方命令        ③ API36 镜像 arm64-v8a 覆盖              ✗ 开源 WFF 渲染器（不存在）
✅ scrcpy(Apache) / ws-scrcpy(MIT)                                               ✗ Genymotion（无 wear）
✅ WFF APK 装载路径 = 普通 adb install
```

三个待实测变量**全部收敛在同一场 POC**，且每个失败都有明确降级出口 → 技术可行性判定：**无理论阻断，风险可在 48 小时内价格化**。

### 8.2 经济可行性：可行 ✅

- **零新增硬件起步**：主力 8u16g 承载 2–3 并发预览，POC 在 DevSpace 免费（CI 空闲时段）。
- **最坏情况成本**：加一台 2C8G x86 云主机专跑预览（100–200 元/月，无公网即可，走既有隧道拓扑）——**不是决策阻断级的成本**。
- **运维成本**：实例自愈 + 快照管理做好后，日常运维接近零；镜像更新（WOS 大版本）每半年一次手工动作。

### 8.3 时间可行性：可行，与主线不冲突 ✅

- 预览模块是**独立服务**（编排器+实例池），不触碰 CDM/编译器/builder 核心链路，与 v0.6 美学打磨并行开发无依赖冲突。
- API_CONTRACT 扩展（/preview/* 路由组）在平台侧预留的扩展点内，不需要重构现有契约。
- 4–6 周 MVP 与用户的"先确认能力边界→对齐需求→再做计划"方法论兼容：**POC 即是能力边界确认，1–2 天出 Go/No-Go**。

### 8.4 降级预案（显式声明，不默默打折）

| 触发条件 | 降级到 | 交付物 | 工期 |
|---|---|---|---|
| POC 变量 ①/③ 双杀（ARM 二进制+镜像都没有） | x86 专机 emulator（方案 A 变体） | 同原方案 | MVP 4–6 周（+月成本 100–200 元） |
| POC 变量 ②/④ 杀（KVM 无且 TCG 帧率不达标） | 截图农场（无交互预览） | 自动参数扫描+图廊/GIF | 1.5–2 周 |
| 全部 emulator 路线放弃 | 真机农场（用户现有 Watch6 起步） | 单真机串流+控制 | 2–3 周 |
| 方案 B（自研渲染器） | — | **不推荐**：与"真机是最终真相源"哲学冲突，保真度无法验收 | — |

---

## 9. 建议下一步（POC 决策清单）

**一句话版本：先花 1–2 天做 POC（在 DevSpace 上），拿到三个实测数值后回来定 Go/No-Go。**

POC 清单（全部命令级，可直接执行）：
1. `ls /dev/kvm`（DevSpace + 主力机各跑一次）→ KVM 存在性
2. `sdkmanager --list | grep -E "wear.*36"` → API36 wear 镜像 arch 覆盖
3. aarch64 emulator 二进制获取实测（社区构建渠道优先）→ 能跑/不能跑
4. 跑通一个现有 v0.5.2 表盘 APK：`adb install` → 截图比对（与真机矩阵 R62 基准图对照）
5. `adb emu sensor set acceleration 2:3:9` + `dumpsys battery set level 15` → mock 链路验证
6. TCG 模式跑动画表盘 30 秒，记录帧率 → 性能档位

判定标准：1/2/3 至少一条活路 + 4/5/6 全通 → Go（方案 A）；否则按降级预案表走。

---

*附：本分析的原始搜索证据存档于 research/preview-vm/（s1–s9）；上游规范版本背景（WFF v1–v5、R53–R55 矩阵）见 unpack-audit/ 与 ROADMAP.md。*

---

## 10. 部署架构演进（2026-10-24 与用户对齐，四轮结论）

> 本节为模块定性升级的记录：从「平台内嵌模块」改为**独立项目 wear-vm-farm**，安装/调试全部封装在服务内，对外只露 API。

### 10.1 独立项目定案

| 决策点 | 结论 |
|---|---|
| 项目形态 | 独立仓库 wear-vm-farm；WatchFace-Forge 平台作为纯 API 客户端 |
| API 面 | /health（能力报告）· POST /sessions · WS /sessions/{id}/stream · POST /sessions/{id}/commands（统一命令信封：sensor/battery/health/time/power）· GET /sessions/{id}/screenshot · DELETE /sessions/{id} |
| 鉴权 | 照抄平台 X-API-Key + 配额模式；串流 WS 用一次性 token |
| 契约文档 | 独立 docs/API_PREVIEW_FARM.md，与 API_CONTRACT.md 并列 |
| 架构收益 | 消化两个结构性坑：有状态 emulator vs 无状态容器冲突；ARM 风险与主力机绑定（可平移） |

### 10.2 Docker 形态

- **control-plane 容器**（无状态：API/会话/配额/doctor）+ **worker 容器 ×N**（一容器一 emulator）
- worker 必需参数：`--device /dev/kvm`（无 KVM 走 TCG 降档）· `--security-opt seccomp=unconfined` · `--shm-size=1g` · `--memory` 限额
- 磁盘分层：system image 5GB 只读共享 + data 层 per-instance COW（多实例磁盘省一半以上）
- 单容器 all-in-one 方案否决：OOM 连坐 / 6-8GB 巨镜像更新耦合 / 无法水平扩展；compose 一键（`docker compose up`）满足同等部署体验
- 前端归宿：生产预览组件嵌平台前端（VPS）；farm 自带极简 demo UI（MB 级静态页）作独立调试入口

### 10.3 架构矩阵（guest × host 解耦）

| Profile | Host | Guest 镜像 | 执行方式 | 性能 | 用途 |
|---|---|---|---|---|---|
| fidelity（默认） | ARM64 | arm64-v8a | KVM 同架构直执行 | ★★★★ | 与真机指令级一致，保真天花板 |
| speed | x86_64 | x86_64 | KVM 直执行 | ★★★★★ | ARM 二进制不可得时的平移档；WFF 纯 XML 无 native，渲染结果几乎无损 |
| fallback | 任意 | 任意 | TCG | ★★（同架构 5-7 折） | 无 KVM 降档；跨架构仅配截图模式 |

- Guest 统一 arm64-v8a：WFF 最低 WOS4 (API33) 全为 ARM64，arm32 排除；Google 不发 wear arm32 镜像
- Host 二进制跟机器走：Docker multi-arch 镜像（buildx 双平台 manifest），同一 tag 自动分发
- aarch64 emulator 二进制风险 → 完整逃逸路径：fidelity 不可得 → 平移 x86 机跑 speed 档，API/平台零改动
- doctor 命令 = 探测当前机器可用 profile（原 POC 六项沉淀为子命令）

### 10.4 开建默认方案

独立仓库 wear-vm-farm：bootstrap（SDK/镜像/依赖全自动）+ doctor（能力探测）+ API 契约骨架先行（约 1 天），然后 doctor 实测出 Go/No-Go 与 profile 档位。

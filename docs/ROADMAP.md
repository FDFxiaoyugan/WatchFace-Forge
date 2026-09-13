# WatchFace-Forge 开发规划（2026-09-13 状态快照）

> 分工：skill 侧（wff-watchface-dev 知识层）归 skill agent；平台侧（CI API/
> Web）归平台 agent；契约 docs/API_CONTRACT.md。

## 当前状态

### skill 侧（v0.5.2 → v0.6 开发中）
- **58 条规则**（pitfalls R01-R58）、5 配方（recipes §1-§5）、**styles.md 设计层**
  （5 美学风格：Material You/极简 Mono/暗色能量/拟物表冠/信息仪表盘）
- 六轮盲测全 PASS（BT-01~08）+ BT-09 动画包真机实证（WOS6 只渲染帧序列动画，
  R53/R54/R55）
- 本日新增：R52 Metadata 层级（CI 抓获）、R53-R55 动画渲染边界、R56-R58
  美学层实测坑（letterSpacing 虚构/Template 子元素层级/BATTERY_PERCENT）

### 平台 CI（今日全链路验收通过）
- validate（lxml XSD + 官方 jar + lint 三级）/ preview / build（多资源）/
  下载 / 二维码 / memory 评估 / 401 全绿
- 容器工具链：qemu-x86_64-static + aapt2 wrapper + android.jar + temurin-17
  （/workspace/.tools/，持久化）；多资源打包补丁 `ac546db`
- 遗留：lint R13 白名单缺 [ANIMATION_VALUE]；build 请求字段名 assets[]/assets

### 部署架构（用户已拍板）
- 前端：日本 VPS 1u1g（公网入口）
- 后端：自有机房 ARM 8u16g 容器化（frp 长连接隧道方案待平台 agent 落地）
- skill agent 开发流：本地改知识层 → git push（token）→ 测试打包走 CI API

## v0.6 美学打磨路线（进行中）

1. **风格 demo 三连 v2 已交付真机验收**（S1 Material You / S2 极简 Mono /
   S3 暗色能量）：位图字体（BitmapFonts+PIL 字模）、白图标+数据胶囊、
   6 主题色含纯黑省电、内接圆安全区布局、日期格式统一"周X M.D"、
   [BATTERY_PERCENT] 修复、S2 字号 116
2. 待用户真机反馈 → 选定主打风格 → 细节层级/素材质感/编辑器体验打磨
3. S4 拟物表冠（刻度环+渐变指针素材）、S5 信息仪表盘（三环数据布局）待做
4. 美学方向固化进 styles.md → 美学盲测（BT-10 候选：按风格卡片出题）
5. CI 流水线出包验证（今日 hdspace 网关限流，隧道恢复后补验——CI 功能
   下午已全链路验收）

## 版本史

- v0.1.0（08-24）首次端到端
- v0.2.0/0.2.2（08-27/08-31）盲测 R1 + 真机三轮
- v0.3.0（09-08）四轮盲测全 PASS（条件变色/ambient）
- v0.4.0（09-09/10）颜色包 + P2 编辑器按钮破案（Editable）
- v0.5.0（09-11）组件包（BT-08 五轮盲测收官）
- v0.5.2（09-13）动画包真机实证（WOS6 渲染边界 R53-R55）
- v0.6（开发中）美学设计层（styles.md + 风格 demo 真机验收中）

# Material Refresh (S1) — 真机验收通过版 2026-09-15

Galaxy Watch6 / One UI 8.0 / WOS6 上经六轮迭代验收通过（"这次对了"）。
Material You 风格: 大圆角主胶囊 + B 通道时间 + 中式日期 + 双数据胶囊。

## 关键实现定案（全部真机实证）

- **时间 = B 通道**: `PartText > Text > Font(SYNC_TO_DEVICE, weight=BOLD)` +
  `Template floor([HOUR_1_12])` / `floor([MINUTE])`
- **BitmapFont 在 WOS6 全通道不可用**（TimeText/PartText 均不渲染, R61 终判）
  ——本表盘曾用 A/B/C/D 四方案并存矩阵实测判明
- **图标 = Phosphor sneaker-fill**（MIT, api.iconify.design 拉取,
  cairosvg 栅格化 + PIL 黑转白 + getbbox 裁切）+ Material Symbols bolt
- **中式日期**: `floor([MONTH])月floor([MONTH_DAY])日 [DAY_OF_WEEK_S]`
- AMBIENT: 整组 `Variant target="alpha" value="60"` 压暗

## 文件

- `watchface.xml` — WFF v1, 双级验证 PASS (wff-validator 1 & 5)
- `res/drawable/` — ic_steps(鞋 87x66) / ic_batt(闪电)
- `preview.png` — 450x450 画布口径预览
- 验收 APK 为构建产物, 按仓库惯例 (`*.apk` gitignore) 不入库; 本地留档:
  `deliverables/style-demos/S1-Refresh-v6.apk` (workspace)

复刻: 把本目录(不含 apk)作为 wff_builder 项目目录直接 `build`。
注意 res/drawable 更新依赖 builder R62 修复版(始终覆盖同步)。

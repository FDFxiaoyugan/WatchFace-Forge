# Minimal Digital Watchface

极简数字表盘 — 大字时间 + 日期 + 电池。真机验证通过 (2026-08-15)。

## 文件

- `watchface.xml` — WFF v1 主文件

## 特性

- 450×450 画布（Pixel Watch 2 / Galaxy Watch 6+）
- DigitalClock + TimeText 自动刷新时间
- Active/AMBIENT 双模式（亮色 + 暗色）
- 日期显示 `[MONTH]/[DAY]`
- 电池百分比 `[BATTERY_PERCENT]`

## 构建验证

```bash
python wff-builder/wff_builder.py validate .
python wff-builder/wff_builder.py build .
```

验证状态：✅ 真机显示成功 (2026-08-15)

# Changelog

All notable changes to the WFF Watch Face Development Skill.

## [0.2.0] - 2026-08-27

Blind test Round 1 (BT-03) feedback backfill. Fresh agent delivered a PASS
(static 7/7, validate 16/16, signed APK) in 4 rounds; its 11 feedback items were
all verified against XSD and fixed. Official XSD validation is now a mandatory
workflow step.

### Fixed (knowledge-layer conflicts with XSD v5 — blind-test findings)
- **Nesting direction reversed**: shape wraps style (`<Arc><Stroke/></Arc>`), not
  `<Stroke><Arc/></Stroke>` — elements.md, recipes.md (R17)
- **`HH:mm` illegal**: timeFormatType only accepts lowercase `hh:mm` — all docs,
  examples, demo, wff_builder init skeleton (R18)
- **Recipe 3 Complication attrs don't exist**: Complication has only `@type`;
  default provider semantics belong to `<DefaultProviderPolicy>` (recipe rewritten)
- **Comma-separated lists illegal**: colors/positions/supportedTypes are
  space-separated `xs:list` (R19)
- **BoundingShape is abstract**: must use BoundingBox/BoundingRoundBox/
  BoundingOval/BoundingArc; ComplicationSlot requires supportedTypes +
  ≥1 Complication child (R20)

### Fixed (doc-vs-XSD errors found during backfill verification)
- **Hands require image resources**: HourHand/MinuteHand/SecondHand have NO
  `color` attribute; `resource` (drawable) is required, `tintColor` optional;
  pure-vector hands impossible — Pillow-generated PNG hands (R25)
- **Hand pivot is `pivotX/pivotY`** (normalized 0~1), not offsetX/offsetY
- **Arc has no `sweepAngle`**: uses required `startAngle`/`endAngle`, static
  values only — dynamic progress rings must use ComplicationSlot RANGED_VALUE
- **Circle/Path don't exist**: shapes are Arc/Ellipse/Line/Rectangle/
  RoundRectangle; circles via Ellipse (width=height)
- **SecondHand child order**: Variant must precede Sweep/Tick (xs:sequence)
- **booleanType enum is uppercase TRUE/FALSE** (R21)

### Added
- Two-tier validation workflow in SKILL.md: 16-rule pre-check + official
  wff-validator.jar (mandatory final gate) (R22)
- pitfalls.md R17-R25 (blind-test evidence + XSD verification)
- BT-02 card boundary fix: allow programmatically generated PNGs (hands require
  image resources — "pure vector" was unsatisfiable)
- score_blindtest.py: auto-inject ANDROID_HOME from SDK candidates

### Verified
- All 3 recipe XML blocks pass official wff-validator (v5)
- examples/minimal-digital + wff-builder demo: official XSD PASS + 16/16 rules

## [0.1.0] - 2026-08-24

### Added
- Initial skill scaffold: SKILL.md + references/ + examples/ + client/ + tests/
- Knowledge layer v0:
  - `references/elements.md` — WFF v5 full element tree (90 elements, 29 enums)
  - `references/expressions.md` — Data sources, operators, functions, conditionals
  - `references/pitfalls.md` — 16 build rules (real-device verified 2026-08-15) + XSD diff
  - `references/recipes.md` — 3 recipe templates (minimal-digital, analog-hands, hybrid-complication)
- `examples/minimal-digital/` — Verified working watchface (real device display confirmed)
- `client/wff_api.py` — HTTP + local dual-mode client (validate/preview/build)
- `data/wff_inventory_v5.json` + `.md` — Full XSD v5 inventory (parsed from google/watchface)
- `config.example.json` — Client configuration template

### Knowledge Sources
- google/watchface XSD v5 (Apache-2.0, 99 files, 90 elements, 29 enums)
- Phase 1 16 build rules (real-device verified 2026-08-15)
- Phase 1-3 development experience (NOTES.md pitfalls, Celery/ARM/environment)

### Known Limitations
- Preview renderer not yet implemented in local mode (requires platform API)
- examples/analog-hands and examples/hybrid-complication are templates only (not yet built/verified)
- No blind-test harness yet (Phase 4C)
- XSD documentation (xs:annotation) partially extracted; some elements lack doc strings
- Complication/UserConfiguration/Gyro coverage is from XSD only, not real-device tested

# Changelog

All notable changes to the WFF Watch Face Development Skill.

## [0.2.2] - 2026-08-31

Third real-device round (Galaxy Watch6, One UI 8.0 / Wear OS 6): complication
now renders with live heart-rate data (R26/R28 fixes confirmed), but the watch
face editor still shows no customize entry.

### Root Cause 4 (R30, suspected): displayName must be a resource ID
- Official semantics: displayName is "A resource ID corresponding to a localized
  name ... displayed in the watch face editor" — bare "DATA" is XSD-valid but
  OEM editors (Samsung One UI) may fail resolving it, hiding the customize entry
- BT-03: displayName -> @string/complication_slot_display (project
  res/values/strings.xml); slotId 0 -> 1 (official example convention)
- wff_builder: project-level res/values/strings.xml auto-merged into resources.arsc
- Next diagnostic if still missing: long-press a stock Samsung face as control
- Heart rate ~1/s updates = Samsung Health provider push behavior; WFF has no
  provider throttling

## [0.2.1] - 2026-08-31

Real-device spot-check of blind-test R1 (BT-03) revealed: complication rendered
blank on watch. Root cause is a "valid-but-empty" class of errors no validation
layer catches — XSD allows `<Complication type="..."/>` with no children, but
the renderer draws nothing. This is the first truth source beyond static
validation: device behavior.

### Root Cause (BT-03, real-device evidence)
- `<Complication>` must contain PartText/PartImage/PartDraw children; provider
  data binds via the special `COMPLICATION.*` data source
  (`[COMPLICATION.TEXT]`, `[COMPLICATION.TITLE]`, ...) — NOT via slotId paths
  (the old `[COMPLICATION.<slotId>.TEXT]` syntax in expressions.md was wrong)
- Complication children use slot-local coordinates (0,0 = slot top-left)
- BoundingShape is hit-testing only — it renders nothing; draw the frame yourself

### Fixed
- expressions.md: COMPLICATION.* table rewritten (20 fields, per-type), usage
  example, "no slotId in path" warning
- elements.md: ComplicationSlot example with full rendering content; removed
  the misleading "minimal placeholder" advice (the source of this bug)
- recipes.md recipe 3: Complication with PartText + Template + Parameter binding
- BT-03 deliverable XML fixed + APK rebuilt (real-device retest pending)
- wff_builder: validate summary counts now derive from WFF_RULES (was hardcoded 16)

### Added
- wff_builder rules R26 (empty Complication = blank render, error) and
  R27 (vector RoundRectangle needs cornerRadiusX/Y, error) — both comment-stripped
- pitfalls.md R26/R27 (aligned numbering with wff_builder rules)
- SKILL.md quick rules: Complication rendering requirement

### Verified
- 6/6 official XSD PASS (3 recipes + example + demo + fixed BT-03)
- 18/18 builder rules PASS on BT-03 fixed; R26/R27 negative tests trigger correctly
- Full test suite: 41 passed (1 pre-existing env-dependent failure, unrelated)

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

# Changelog

All notable changes to the WFF Watch Face Development Skill.

## [0.5.0] - 2026-09-11

Component pack closed loop. Blind-test round 5 (BT-08 configurable components)
PASS with zero validate-error rounds — the agent delivered a fully
user-configurable face (clock style switch / seconds toggle / dual
complication slots / theme colors) and the real device (Galaxy Watch6,
One UI 8.0) confirmed ALL four customization features work.

### Knowledge: List/Boolean two-mode configuration (R37)
- XSD include-chain + official Flavors/Complications samples cross-check:
  container mode (UserConfigurations = editor UI metadata) vs render mode
  (Scene/Group/hands = Option id + embedded part) coexist — unlike Color
  whose standalone element version is deprecated; ids must match on both
  sides; render-mode BooleanOption TRUE-only = off hides content (showHr)
- ListOption complicationSlotIds / childSettingIds (slot visibility
  cascading); Flavors presets + PhotosConfiguration documented
- slotId starts at 0 in official samples (old "start at 1" fixed);
  ComplicationSlot cap 8; XSD xs:unique
- PartText > Text > Font three-layer structure (R39, validator-enforced;
  renderer-tolerated shortcuts fail official validation);
  [CONFIGURATION.<id>.<N>] color-index syntax; CDATA for && expressions;
  null-check ternary + Condition branching (R40)
- elements.md ghost element purged: `<UserConfiguration type=...>` never
  existed in XSD v5; recipes.md §4 full component-pack recipe (validator
  PASSED, e2e build+sign verified before merging)

### Builder: rules 24 → 27
- R37: render-mode List/Boolean id correspondence + BooleanOption enum
- R38: ComplicationSlot cap/uniqueness
- R39: PartText>Text>Font layering check
- R34 fix (BT-08 feedback #3): nested local-coordinate blocks
  (ComplicationSlot / config render modes / clocks) now stripped before
  inscribed-circle scan — BT-08 false positive eliminated while P2 and
  full-width-band true positives retained

### Blind-test round 5 (BT-08)
- static 28/28, validate 25/27 (0 errors), build 132.6KB signed APK,
  real-device: all four customization features confirmed
- Agent self-audited APK internals (binary AXML Editable + raw XML
  byte-identical); slot bezels moved to Scene-level PartDraw per R26
- 4 feedback items verified & merged: R34 nested-coordinate bug (fixed),
  BoundingOval uses x/y not centerX/centerY (XSD geometricAttributesRequired,
  elements.md corrected), Windows host adaptation (AAPT2/APKSIGNER env
  vars documented), icon attribute optional (text-label fallback)

## [0.4.0] - 2026-09-10

P2 breakthrough day (2026-09-09) + Arc semantics closure (2026-09-10): the
editor customize-button mystery is fully solved, and the color-configuration
pipeline is real-device verified end-to-end (button appears → 3 color options
→ global color change on selection).

### Root Cause 5 (R33, CONFIRMED): watch_face_info.xml needs `<Editable value="true"/>`
- Four single-variable iterations: wff_version=2 (no effect) → displayName bare
  resource name (no effect) → **watch_face_info.xml + Editable (SOLVED)**:
  editor customize button appears, 3 color options selectable, selection
  changes face colors globally
- Behavior matrix: missing Editable = everything renders but NO customize entry
  (all prior UserConfigurations fixes were masked by this); Editable without
  UserConfigurations = button present but empty options page (ArcLab evidence);
  Editable + ColorConfiguration = full custom color flow
- This was the true root cause behind the entire R30/UserConfigurations/
  wff_version dead-end history
- Official samples: android/wear-os-samples/WatchFaceFormat

### Root Cause 6 (R30 REVERSED): displayName uses bare resource names
- res/raw/watch_face.xml and res/xml/watch_face_info.xml are NOT compiled by
  aapt2 — `@string/xxx` is a literal string there; the WFF runtime looks
  resources up by bare name in arsc
- Old R30 ("must use @string/") had the direction backwards; retest failures
  were masked by the missing Editable switch. Official tutorials + samples
  all use bare names

### Arc semantics locked by pixel-level experiment (R36)
- ArcLab control face: 6 arcs (0→90, 90→180, 180→270, 270→360, -90→90,
  annotated) rendered on device; per-color pixel clustering identified each
  arc's quadrant — all 5 matched the hypothesis
- **0° = 12 o'clock, clockwise positive, negative angles legal**
- upper arch = `-90→90` (opening down); `180→360` = left C-arc (opening right)
- official battery ring `-150→150` gap-down explained; cap="ROUND" confirmed safe

### Arc geometry is PartDraw-local (R35) + round-screen clipping (R34)
- P2 arc "looks like a diagonal line" mystery: centerX=225 in a 320-wide
  PartDraw → ellipse bbox overflows container → overflow arc clipped; only
  the ascending half remained. Fix: centerX = containerWidth/2
- P2 v5 real-device: arc top clipped a few pixels at round-screen edge →
  new R34 geometry rule: top-level element bbox corners vs inscribed circle
  (450 canvas: circle center 225,225 r=225; y<25 rows mostly invisible)

### Added
- wff_builder rules R34 (inscribed-circle overflow, warn) and R35 (Arc ellipse
  vs PartDraw container overflow, warn); R33 project-level check
  (watch_face_info.xml + Editable: missing file = warn, file without
  Editable = error); total rules 21 → 24 (23 in-rule + 1 project-level)
- wff_builder WATCH_FACE_INFO_TEMPLATE now emits `<Editable value="true"/>`
- pitfalls.md R33/R34/R35/R36; elements.md Arc semantics quick-reference box;
  recipes.md color-configuration snippet rewritten to XSD v5 authoritative
  structure (old `UserConfiguration type="Color"` was invalid) + passed
  wff-validator before merging
- SKILL.md quick-rules updated: R30 reversed, R33 two-piece customize kit,
  R34/R35/R36 arc & screen geometry

### Verified
- Color recipe + R33/R35 doc snippets pass official wff-validator v5
- R34 correctly flags P2 project (23px corner overflow = real device symptom);
  R35 reproduces the diagonal-line case (bad→FAIL, good→PASS); R33 comment-
  stripping can't be fooled
- P2 terminal APK real-device verified: customize button + 3-color selection
  + symmetric upper-arch arc (user accepted; top edge clipping accepted as
  known cosmetic)

## [0.3.0] - 2026-09-08

Blind-test Phase 4C complete: 4/4 rounds PASS (BT-02 analog three-hands,
BT-03 digital layout, BT-04 conditional color, BT-05 ambient variant).
BT-01 demoted to smoke card. Skill declared production-ready for the
agent-driven workflow.

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

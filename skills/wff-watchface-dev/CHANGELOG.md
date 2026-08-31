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

# Changelog

All notable changes to the WFF Watch Face Development Skill.

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

# Google Watch Face Format vendored files

- Upstream: `https://github.com/google/watchface`
- Commit: `d1cdafa953c95d5554fc54df4bc3948befbefc4d` (2026-10-16, "Disable XML entity size limits when parsing watchface XML (#116)")
- Retrieved: 2026-10-24
- License: Apache License 2.0 (`LICENSE.txt`)
- Included now: `third_party/wff/specification/documents/{1,2,3,4,5}/**` — **全五版本规范树**
- Release tools: `wff-validator.jar` 1.7.0 (Maximum Supported Format Version #5) and
  `memory-footprint.jar` 1.7.0

## 上游监控 (REPAIR_PLAN P3)

`tools/check-upstream.sh` 比对本文件钉定的 commit 与上游 HEAD；**任何边界相关
会话必跑**（skill 更新三触发器之一）。上游更新 → 重跑本目录升级流程并同步
SOURCE.md。

## 历史与教训

- 前一钉定: `44b1855d445686ac8de5dbc95003d6f8e6623643` (取回于 2026-08-24)。该
  commit 已包含 v1–v5 五版本树（PR#113 "Support schema version 5"），但当时只
  vendor 入了 `documents/1/**` —— 与 builder 的 `format.version=1` 声明互相锁死，
  是 2026-10-23 归因复盘确认的"数据源自锁"起点。2026-10-24 起全五版本入库。
- 2026-10-24 release 资产核验: 上游 2026-10-16 release 的 `wff-validator.jar` /
  `memory-footprint.jar` 与钉定 1.7.0 **SHA-256 完全一致**（资产为原文件重挂，
  无需升级；GitHub API 的 size 字段与实际差 438B 属元数据滞后）。
- 校验器用法: `java -jar wff-validator.jar <format-version> <watchface.xml>` —
  **按声明版本分别校验**（本地工作机 Java 21 可直接跑）。

Release artifact SHA-256:

- `wff-validator.jar`: `90257944251f16b3c01fa1722e923acc5d5681262d3532cf8c733cbd19725265`
- `memory-footprint.jar`: `ee4d344d41d1288255ca1bd117d58d5a5bbb7bd33cac217562f052fc2bd4457c`
- both release license files: `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`

The directory structure is preserved because `watchface.xsd` imports/includes
the other schema documents by relative path. Do not flatten this tree.

Google's schema uses XSD 1.1 constructs that libxml2/xmllint cannot compile. The
API loads it with the MIT-licensed Python `xmlschema.XMLSchema11` implementation
and `allow="local"`, preventing runtime network schema access. Java validator and
memory evaluator artifacts require Java 17+ and are integrated separately so
absence of their runtime is visible.

The pinned release JARs require Java 17. The DevSpace container keeps its
system Java 11 unchanged and installs an explicit Temurin 17 runtime at
`/opt/temurin-17`; production may instead set `WFF_JAVA` to another Java 17
binary. 本地工作机 (x86_64): Java 21 + `ANDROID_HOME=/home/z/android-sdk`
(build-tools 34.0.0 + platform-34, 2026-10-24 部署于 `/home/z/android-sdk`)。

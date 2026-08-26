# Google Watch Face Format vendored files

- Upstream: `https://github.com/google/watchface`
- Commit: `44b1855d445686ac8de5dbc95003d6f8e6623643`
- Retrieved: 2026-08-24
- License: Apache License 2.0 (`LICENSE.txt`)
- Included now: `third_party/wff/specification/documents/1/**`
- Release tools: `wff-validator.jar` 1.7.0 and `memory-footprint.jar` 1.7.0

Release artifact SHA-256:

- `wff-validator.jar`: `90257944251f16b3c01fa1722e923acc5d5681262d3532cf8c733cbd19725265`
- `memory-footprint.jar`: `ee4d344d41d1288255ca1bd117d58d5a5bbb7bd33cac217562f052fc2bd4457c`
- both release license files: `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`

The directory structure is preserved because `watchface.xsd` imports/includes
the other schema documents by relative path. Do not flatten this tree.

Google's schema uses XSD 1.1 constructs that libxml2/xmllint cannot compile. The
API loads it with the MIT-licensed Python `xmlschema.XMLSchema11` implementation
and `allow="local"`, preventing runtime network schema access. Java validator and
memory evaluator artifacts require Java 17 and are integrated separately so
absence of their runtime is visible.

The pinned release JARs require Java 17. The development container keeps its
system Java 11 unchanged and installs an explicit Temurin 17 runtime at
`/opt/temurin-17`; production may instead set `WFF_JAVA` to another Java 17 binary.

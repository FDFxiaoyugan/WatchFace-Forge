# WFF Direct API Contract v1.1

Base path: `/api/v1/wff`. Requests use `multipart/form-data` and authenticate with
`X-API-Key`. Server keys are configured through the comma-separated `WFF_API_KEYS`
environment variable; keys are never stored in source code. **Keys are
deployment-specific** (e.g. set in the server's `.env`): the `dev-key` shown in
examples below is a placeholder only and will return 401 against a real
deployment unless that exact key happens to be configured.

## Common errors

```json
{"error":{"code":"INVALID_API_KEY","message":"X-API-Key 无效或缺失"}}
```

> **入口一致性（2026-10-23 G1/G2/G3）**：除 v1 直通路由外，旧 CDM 入口
> `POST /api/build`、`GET /api/editor/cdm/{task_id}` 与图片端点
> `POST /api/editor/image/{process,upload}` 同样消费 `X-API-Key`：
> production fail-closed（未配 keys → 503、无效 → 401、Redis 配额后端不可用
> → 503）；development 匿名请求走固定开发身份并计入配额桶（前端 dev 流程
> 不变）。`POST /api/build` 在 production 还要求分层校验非 degraded，且
> 响应携带 `warnings[]`（模板降级时点名未打包资源）。CDM 记录按生成者
> 身份摘要绑定所有权——他人 key 取回 → 404。图片请求预算：b64 ≤ 14M
> 字符、原始字节 ≤ 12MB、解码像素 ≤ 50MP、`max_size` clamp 到 [64, 2048]。

| HTTP | code | Meaning |
|---|---|---|
| 401 | `INVALID_API_KEY` | Missing or unknown key |
| 200 | — | Validation **result**: body carries `valid:false` + `errors[]` (see below) |
| 422 | `VALIDATION_FAILED` | The **request** is malformed: missing required fields, oversized files |
| 422 | `INVALID_PREVIEW_OPTIONS` | Unsupported shape or size |
| 422 | `INVALID_TIME` | A preview time is not in `HH:MM:SS` format |
| 422 | `INVALID_MODE` | A preview mode is not `active` or `ambient` |
| 429 | `RATE_LIMITED` | Per-key token bucket exhausted |
| 500 | `BUILD_FAILED` | APK packaging or signing failed |
| 503 | `API_KEYS_NOT_CONFIGURED` | Server has no `WFF_API_KEYS` |

> Validation outcome semantics (v1.1, aligned with the implementation after the
> 2026-09-12 cross-team integration test): a syntactically valid request whose
> XML fails validation returns **200** with `valid:false` and structured
> `errors[]` — the same shape as a passing response. This keeps client-side
> handling uniform (lint-API convention). `422 VALIDATION_FAILED` is reserved
> for request-level problems such as a missing `xml` field or an oversized
> upload, which are rejected by request validation before any WFF checking.

Quotas per API key are validate 60/hour, preview 20/hour, and build 10/hour.
Quota state lives in Redis (atomic fixed window per key per endpoint) when the
shared instance is reachable; development falls back to a process-local window.
The AI-consumption endpoints (`/api/generate`, `/api/ai/test`) use the
2026-10 audit quota layer instead — see `docs/DEVELOPMENT.md` §环境变量
(`WF_QUOTA_GENERATE_PER_HOUR`, `WF_QUOTA_AI_TEST_PER_HOUR`).

## POST `/validate`

Fields: `xml` (required file), `assets[]` (optional files; clients may also send
the multipart field repeatedly as `assets`). XML is limited to 2MB and each asset
to 10MB.

```bash
curl -H 'X-API-Key: dev-key' \
  -F 'xml=@watchface.xml;type=application/xml' \
  -F 'assets=@background.png' \
  http://localhost:8000/api/v1/wff/validate
```

The response contains `valid`, structured `errors[]`, and `stats`, plus two
audit-added fields: `layers` and `degraded`. `layers` maps each validation
stage to `passed | failed | unavailable | not_run`:

- `syntax` — XML well-formedness/size/encoding/root element (always available)
- `xsd` — vendored Google WFF v1 XSD 1.1 (Apache-2.0, pinned upstream commit)
  through the MIT `xmlschema` engine, local-only resource access
- `official_validator` — Google `wff-validator.jar` (needs Java 17)
- `lint` — repo rule pack + asset cross-checks (always available)

`not_run` means the layer never executed (e.g. XML syntax failure short-circuits
the pipeline); `unavailable` means the toolchain is missing. `degraded: true`
when any layer is `unavailable` or `not_run` — treat such results as
incomplete, not as a pass. `WF_ENV=production` rejects `/build` with
`503 VALIDATION_LAYER_UNAVAILABLE` when validation is degraded instead of
silently proceeding. Every issue
has `source` (`xsd`, `official_validator`, or `lint`), `rule`, `severity`,
`element`, `line`, `message`, and `hint`. `validate` reports quick
`stats.memory_source: "estimate"` figures only; the official Google
`memory-footprint.jar` numbers appear in the `build` response (v1.1: the
official evaluator is integrated and returns `source: "official"` whenever
Java 17 + the pinned jar are available, as verified in the 2026-09-12
integration test: 2,371,712 bytes for the BT-08 sample).

## POST `/preview`

Fields: `xml`, optional repeated `assets`, JSON-array strings `times` and `modes`,
plus `shape=round|square` and `size=128..1024`. At most six times and two modes
are rendered per request. `times` entries use `HH:MM:SS`. Malformed/empty JSON
arrays or arrays over those limits return `422 INVALID_PREVIEW_OPTIONS`; invalid
entries return `INVALID_TIME` or `INVALID_MODE` rather than silently falling back.

```bash
curl -H 'X-API-Key: dev-key' -F 'xml=@watchface.xml' \
  -F 'times=["10:08:32","23:59:59"]' \
  -F 'modes=["active","ambient"]' -F 'shape=round' -F 'size=384' \
  http://localhost:8000/api/v1/wff/preview
```

Each frame includes its time, mode, and a PNG data URL. The response always warns
that this renderer is an approximation and not the Wear OS source of truth.

## POST `/build`

Fields: `xml`, optional repeated `assets`, `name`, `package`, and positive integer
`version`. Validation is mandatory and happens before packaging.

```bash
curl -H 'X-API-Key: dev-key' -F 'xml=@watchface.xml' \
  -F 'name=Quiet Mono' -F 'package=com.example.quietmono' -F 'version=1' \
  http://localhost:8000/api/v1/wff/build
```

```json
{
  "build_id": "f5b2f28674c8",
  "apk": {
    "url": "/api/v1/wff/builds/quietmono-f5b2f28674c8.apk",
    "size": 12859,
    "sha256": "c43f...c33a0"
  },
  "qr_url": "/api/qrcode/quietmono-f5b2f28674c8.apk",
  "warnings": []
}
```

`GET /api/v1/wff/builds/{filename}` downloads the generated APK. Multi-asset
packaging is standard: every uploaded image in `assets[]` is packed under
`res/drawable/` (2026-09-13 `ac546db`, qemu-user aapt2 toolchain). When aapt2
is unavailable the build falls back to the ARM precompiled template: the
response then carries structured `warnings[]` naming the fallback reason, every
dropped resource, and any package-name mismatch against the fixed template
identity (2026-10-17 audit fix). `WF_ENV=production` rejects such builds with
`500 BUILD_FAILED` instead of silently downgrading.

`qr_url` is an optional phone convenience link, not a watch-side installation
mechanism. Watches commonly have no camera, and scanning on a phone still needs
Wear Installer, wireless ADB, a companion app, or a Play testing track to transfer
the APK. Product UI must make direct APK download the primary action.

Successful builds also include `memory` from Google's pinned
`memory-footprint.jar` (`total_bytes`, `max_active_bytes`, and
`max_ambient_bytes`). If Java 17 or the tool is unavailable, `source` is
`unavailable` and the reason is repeated in `warnings`; estimated validation
statistics are never labeled as official.

Field semantics were confirmed against the pinned upstream source at commit
`44b1855`: `total_bytes` is the total footprint of referenced assets;
`max_active_bytes` and `max_ambient_bytes` are the maximum simultaneously active
footprints in their respective modes. The ambient calculator also accounts for
the 450x450 render buffer, so `max_ambient_bytes` can legitimately exceed
`total_bytes` (as in the BT-08 result). Clients must compare the active and
ambient figures with their respective platform budgets and must not clamp either
one to `total_bytes`.

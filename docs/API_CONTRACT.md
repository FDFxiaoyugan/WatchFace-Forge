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
The current limiter is process-local and intentionally conservative; a shared
Redis limiter is required before horizontally scaling the API.

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

The response contains `valid`, structured `errors[]`, and `stats`. The first
validation layer uses the Apache-2.0 Google WFF v1 XSD vendored at a pinned
upstream commit and runs through the MIT `xmlschema` XSD 1.1 engine with local-only
resource access. Every issue
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

`GET /api/v1/wff/builds/{filename}` downloads the generated APK. On the ARM64
development environment the verified precompiled resource table supports one
uploaded bitmap slot. A build with more bitmap resources returns an explicit
warning; use a full aapt2 environment for complete multi-resource packaging.

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

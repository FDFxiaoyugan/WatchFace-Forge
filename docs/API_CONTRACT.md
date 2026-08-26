# WFF Direct API Contract v1.0

Base path: `/api/v1/wff`. Requests use `multipart/form-data` and authenticate with
`X-API-Key`. Server keys are configured through the comma-separated `WFF_API_KEYS`
environment variable; keys are never stored in source code.

## Common errors

```json
{"error":{"code":"INVALID_API_KEY","message":"X-API-Key 无效或缺失"}}
```

| HTTP | code | Meaning |
|---|---|---|
| 401 | `INVALID_API_KEY` | Missing or unknown key |
| 422 | `VALIDATION_FAILED` | XML/resources failed validation |
| 422 | `INVALID_PREVIEW_OPTIONS` | Unsupported shape or size |
| 429 | `RATE_LIMITED` | Per-key token bucket exhausted |
| 500 | `BUILD_FAILED` | APK packaging or signing failed |
| 503 | `API_KEYS_NOT_CONFIGURED` | Server has no `WFF_API_KEYS` |

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
`element`, `line`, `message`, and `hint`. Until the official Google evaluator is
integrated, `stats.memory_source` is `estimate`.

## POST `/preview`

Fields: `xml`, optional repeated `assets`, JSON-array strings `times` and `modes`,
plus `shape=round|square` and `size=128..1024`. At most six times and two modes
are rendered per request.

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

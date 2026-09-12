"""Phase 4 direct WFF API contract tests."""

import os
from types import SimpleNamespace

from fastapi.testclient import TestClient

from api.app import app
from api.services.wff_access import limiter

client = TestClient(app)

VALID_XML = b'''<?xml version="1.0"?>
<WatchFace width="450" height="450">
  <Metadata key="CLOCK_TYPE" value="DIGITAL"/>
  <Metadata key="PREVIEW_TIME" value="10:08:32"/>
  <Scene backgroundColor="#ff000000">
    <DigitalClock x="0" y="0" width="450" height="450">
      <TimeText format="hh:mm" x="0" y="150" width="450" height="100">
        <Variant mode="AMBIENT" target="alpha" value="0"/>
        <Font family="SYNC_TO_DEVICE" size="80" color="#ffffffff"/>
      </TimeText>
    </DigitalClock>
  </Scene>
</WatchFace>'''


def setup_function():
    os.environ["WFF_API_KEYS"] = "test-key"
    limiter.reset()


def test_validate_requires_api_key():
    response = client.post("/api/v1/wff/validate", files={"xml": ("watchface.xml", VALID_XML, "application/xml")})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_API_KEY"


def test_validate_valid_xml_returns_stats():
    response = client.post(
        "/api/v1/wff/validate",
        headers={"X-API-Key": "test-key"},
        files={"xml": ("watchface.xml", VALID_XML, "application/xml")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is True
    assert body["stats"]["element_count"] >= 7
    assert body["stats"]["memory_source"] == "estimate"
    assert not any(item["source"] == "official_validator" and item["severity"] == "error" for item in body["errors"])


def test_validate_reports_parse_and_lint_errors():
    response = client.post(
        "/api/v1/wff/validate",
        headers={"X-API-Key": "test-key"},
        files={"xml": ("watchface.xml", b"<WatchFace>", "application/xml")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is False
    assert body["errors"][0]["source"] == "xsd"
    assert body["errors"][0]["line"] == 1


def test_validate_missing_xml_is_request_level_422():
    response = client.post(
        "/api/v1/wff/validate",
        headers={"X-API-Key": "test-key"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_FAILED"


def test_validate_oversized_xml_is_request_level_422(monkeypatch):
    from api.routes import wff

    monkeypatch.setattr(wff, "MAX_XML_BYTES", 8)
    response = client.post(
        "/api/v1/wff/validate",
        headers={"X-API-Key": "test-key"},
        files={"xml": ("watchface.xml", VALID_XML, "application/xml")},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_FAILED"


def test_validate_oversized_asset_is_request_level_422(monkeypatch):
    from api.routes import wff

    monkeypatch.setattr(wff, "MAX_ASSET_BYTES", 3)
    response = client.post(
        "/api/v1/wff/validate",
        headers={"X-API-Key": "test-key"},
        files=[
            ("xml", ("watchface.xml", VALID_XML, "application/xml")),
            ("assets", ("too-large.png", b"1234", "image/png")),
        ],
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_FAILED"


def test_validate_accepts_assets_bracket_field():
    response = client.post(
        "/api/v1/wff/validate",
        headers={"X-API-Key": "test-key"},
        files=[
            ("xml", ("watchface.xml", VALID_XML, "application/xml")),
            ("assets[]", ("background.png", b"png" * 400, "image/png")),
        ],
    )
    assert response.status_code == 200
    assert response.json()["stats"]["asset_kb"] > 0


def test_validate_reports_official_xsd_errors():
    invalid = VALID_XML.replace(b'<Scene backgroundColor="#ff000000">', b'<Scene backgroundColor="#ff000000" madeUp="yes">')
    response = client.post(
        "/api/v1/wff/validate",
        headers={"X-API-Key": "test-key"},
        files={"xml": ("watchface.xml", invalid, "application/xml")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is False
    assert any(item["source"] == "xsd" and item["rule"] == "OFFICIAL_XSD" for item in body["errors"])
    assert any(item["source"] == "official_validator" for item in body["errors"])


def test_preview_returns_png_data_url_and_warning():
    response = client.post(
        "/api/v1/wff/preview",
        headers={"X-API-Key": "test-key"},
        data={"times": '["10:08:32"]', "modes": '["active","ambient"]', "shape": "round", "size": "256"},
        files={"xml": ("watchface.xml", VALID_XML, "application/xml")},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body["frames"]) == 2
    assert body["frames"][0]["image"].startswith("data:image/png;base64,")
    assert "不代表" in body["warnings"][0]


def test_preview_rejects_non_json_time_list():
    response = client.post(
        "/api/v1/wff/preview",
        headers={"X-API-Key": "test-key"},
        data={"times": "10:08:32,23:59:59"},
        files={"xml": ("watchface.xml", VALID_XML, "application/xml")},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_PREVIEW_OPTIONS"


def test_preview_rejects_more_than_six_times():
    response = client.post(
        "/api/v1/wff/preview",
        headers={"X-API-Key": "test-key"},
        data={"times": '["00:00:00","01:00:00","02:00:00","03:00:00","04:00:00","05:00:00","06:00:00"]'},
        files={"xml": ("watchface.xml", VALID_XML, "application/xml")},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_PREVIEW_OPTIONS"


def test_build_refuses_invalid_xml_before_builder():
    response = client.post(
        "/api/v1/wff/build",
        headers={"X-API-Key": "test-key"},
        data={"package": "com.example.valid"},
        files={"xml": ("watchface.xml", b"<WatchFace>", "application/xml")},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_FAILED"


def test_official_memory_preserves_ambient_value_above_total(monkeypatch, tmp_path):
    from api.services import wff_official

    apk = tmp_path / "watchface.apk"
    apk.write_bytes(b"apk")
    monkeypatch.setattr(wff_official, "_java", lambda: "/java17")
    monkeypatch.setattr(wff_official.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(
        stdout='{"totalBytes":2371712,"maxActiveBytes":2371712,"maxAmbientBytes":6363424}',
        stderr="",
    ))
    result = wff_official.evaluate_memory(apk)
    assert result["source"] == "official"
    assert result["max_ambient_bytes"] > result["total_bytes"]

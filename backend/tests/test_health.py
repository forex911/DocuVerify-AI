"""
Tests for System Health Endpoint.
"""

def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded")
    assert "version" in data
    assert "database" in data
    assert data["database"] == "connected"
    assert "tesseract_ocr_available" in data
    assert "gemini_configured" in data


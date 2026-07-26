"""Tests du notifieur d'alerte drift — sans accès réseau."""
import scripts.monitoring.notify as notify

_SUMMARY = {
    "n_drifted_features": 16,
    "n_features": 37,
    "drift_share": 0.43,
    "threshold": 0.3,
    "dataset_drift": True,
    "reference_rows": 700,
    "current_rows": 300,
    "generated_at": "20260726_120000",
}


def test_send_drift_alert_is_noop_when_url_missing(monkeypatch):
    # Aucun webhook configuré -> pas d'envoi, retourne False, aucune exception.
    monkeypatch.setattr(notify, "ALERT_WEBHOOK_URL", "")
    assert notify.send_drift_alert(_SUMMARY) is False


def test_send_drift_alert_posts_payload(monkeypatch):
    captured = {}

    class _FakeResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    def _fake_urlopen(request, timeout=None):
        captured["url"] = request.full_url
        captured["body"] = request.data.decode("utf-8")
        return _FakeResponse()

    monkeypatch.setattr(notify, "ALERT_WEBHOOK_URL", "http://hooks.example/test")
    monkeypatch.setattr(notify.urllib.request, "urlopen", _fake_urlopen)

    assert notify.send_drift_alert(_SUMMARY) is True
    assert captured["url"] == "http://hooks.example/test"
    assert '"text"' in captured["body"]
    assert "43.0%" in captured["body"]


def test_send_drift_alert_swallows_network_error(monkeypatch):
    def _boom(request, timeout=None):
        raise OSError("connection refused")

    monkeypatch.setattr(notify, "ALERT_WEBHOOK_URL", "http://hooks.example/test")
    monkeypatch.setattr(notify.urllib.request, "urlopen", _boom)

    # Une erreur réseau ne doit jamais propager : retourne False.
    assert notify.send_drift_alert(_SUMMARY) is False


def test_format_message_contains_key_facts():
    msg = notify._format_message(_SUMMARY)
    assert "16/37" in msg
    assert "gravity_classification" in msg

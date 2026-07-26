"""
Alerting — envoi de notifications de drift vers un webhook (Slack-compatible).

Fonctionnement volontairement minimal et sans dépendance externe : si
``ALERT_WEBHOOK_URL`` n'est pas défini, la fonction ne fait rien (no-op) et
retourne ``False``. Toute erreur réseau est journalisée mais **non** propagée :
une alerte qui échoue ne doit jamais faire échouer le calcul de drift.

Format du payload : ``{"text": "..."}`` — compatible Slack / Mattermost /
Discord (via ``/slack``) et la plupart des webhooks entrants.
"""
import json
import logging
import os
import urllib.request

ALERT_WEBHOOK_URL = os.environ.get("ALERT_WEBHOOK_URL", "").strip()
_TIMEOUT_SECONDS = 5


def _format_message(summary: dict) -> str:
    """Construit un message lisible à partir du résumé de drift."""
    return (
        ":rotating_light: *Alerte drift — gravity_classification*\n"
        f"• Features driftées : {summary.get('n_drifted_features')}/{summary.get('n_features')} "
        f"({summary.get('drift_share', 0.0) * 100:.1f}%)\n"
        f"• Seuil : {summary.get('threshold', 0.0) * 100:.0f}%\n"
        f"• dataset_drift : {summary.get('dataset_drift')}\n"
        f"• Fenêtre : {summary.get('reference_rows')} réf. / {summary.get('current_rows')} courant\n"
        f"• Généré : {summary.get('generated_at')}"
    )


def send_drift_alert(summary: dict) -> bool:
    """
    Envoie une alerte de drift au webhook configuré.

    Retourne ``True`` si la notification a été envoyée, ``False`` si aucun
    webhook n'est configuré ou si l'envoi a échoué (l'échec est journalisé).
    """
    if not ALERT_WEBHOOK_URL:
        logging.info("Aucun ALERT_WEBHOOK_URL configuré — alerte drift non envoyée.")
        return False

    payload = json.dumps({"text": _format_message(summary)}).encode("utf-8")
    request = urllib.request.Request(
        ALERT_WEBHOOK_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:  # noqa: S310
            logging.info("Alerte drift envoyée (HTTP %s).", response.status)
            return True
    except Exception as exc:  # noqa: BLE001 — une alerte ne doit jamais casser le pipeline
        logging.error("Échec de l'envoi de l'alerte drift : %s", exc)
        return False

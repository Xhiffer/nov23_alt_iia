"""
Canary routing — logique pure de répartition du trafic champion/canary.

Isolée du serving (pas d'import MLflow/FastAPI) pour être testable directement.
`CANARY_TRAFFIC_PCT` (0–100) fixe la part de trafic routée vers le challenger.
"""
import os
import random

CHAMPION = "champion"
CANARY = "canary"


def read_canary_pct(env: dict | None = None) -> float:
    """Lit CANARY_TRAFFIC_PCT et le borne dans [0, 100]. Valeur invalide -> 0."""
    source = os.environ if env is None else env
    raw = str(source.get("CANARY_TRAFFIC_PCT", "0")).strip()
    try:
        pct = float(raw)
    except ValueError:
        return 0.0
    return max(0.0, min(100.0, pct))


def should_route_to_canary(pct: float, rng: random.Random | None = None) -> bool:
    """True si la requête doit être servie par le canary, selon `pct` (0–100).

    Bornes strictes : pct<=0 -> jamais, pct>=100 -> toujours. Entre les deux,
    tirage uniforme (rng injectable pour des tests déterministes).
    """
    if pct <= 0.0:
        return False
    if pct >= 100.0:
        return True
    draw = (rng or random).uniform(0.0, 100.0)
    return draw < pct

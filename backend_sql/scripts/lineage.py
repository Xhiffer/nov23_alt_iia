"""
Lineage — empreinte déterministe du jeu d'entraînement + provenance code.

Objectif : rendre chaque run MLflow **traçable et reproductible** en l'attachant à
1) une empreinte (`dataset_digest`) qui identifie de façon déterministe le contenu
   exact des données d'entraînement, et
2) le **SHA du commit git** du code qui a produit le modèle.

Volontairement sans dépendance MLflow : les fonctions sont pures (pandas + stdlib)
et testables hors conteneur. Le script d'entraînement se charge de logger le
dictionnaire retourné par `build_lineage` dans MLflow.
"""
import hashlib
import os
import subprocess

import pandas as pd

_UNKNOWN = "unknown"


def dataset_digest(df: pd.DataFrame) -> str:
    """SHA-256 déterministe du contenu du DataFrame (valeurs + index).

    Deux DataFrames au contenu identique produisent la même empreinte, quel que
    soit l'ordre d'exécution — c'est l'identité du jeu de données pour un run.
    """
    row_hashes = pd.util.hash_pandas_object(df, index=True).values
    columns_repr = ",".join(map(str, df.columns)).encode("utf-8")
    hasher = hashlib.sha256()
    hasher.update(columns_repr)
    hasher.update(row_hashes.tobytes())
    return hasher.hexdigest()


def git_sha() -> str:
    """SHA du commit courant.

    Priorité aux variables d'environnement (`GIT_COMMIT_SHA`/`GIT_SHA`), injectées
    au build/déploiement, car le conteneur d'entraînement n'embarque pas `.git`.
    Repli sur `git rev-parse` si disponible, sinon ``"unknown"``.
    """
    for var in ("GIT_COMMIT_SHA", "GIT_SHA"):
        value = os.environ.get(var, "").strip()
        if value:
            return value
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
        return out.stdout.strip() or _UNKNOWN
    except Exception:
        return _UNKNOWN


def build_lineage(df: pd.DataFrame) -> dict:
    """Résumé de lineage sérialisable, à logger comme params/tags MLflow."""
    return {
        "dataset_digest": dataset_digest(df),
        "dataset_rows": int(len(df)),
        "dataset_cols": int(df.shape[1]),
        "dataset_columns": ",".join(map(str, df.columns)),
        "git_sha": git_sha(),
    }

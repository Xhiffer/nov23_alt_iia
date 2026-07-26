"""Test modèle (smoke) : l'entraînement produit un modèle utilisable, sans DB ni MLflow."""
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score


def _synthetic_dataset(n: int = 400, seed: int = 42):
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, 8))
    # Cible binaire corrélée aux features (signal apprenable)
    y = (X[:, 0] + 0.5 * X[:, 1] - X[:, 2] + rng.normal(scale=0.3, size=n) > 0).astype(int)
    return X, y


def test_training_produces_usable_model():
    X, y = _synthetic_dataset()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    model = RandomForestClassifier(
        n_estimators=50, max_depth=5, class_weight="balanced", random_state=42
    )
    model.fit(X_train, y_train)

    preds = model.predict(X_test)

    # Un artefact entraîné doit prédire une valeur par ligne, sans NaN...
    assert len(preds) == len(y_test)
    assert not np.isnan(preds).any()
    # ...et battre nettement le hasard sur un signal apprenable.
    assert f1_score(y_test, preds, average="macro") > 0.6


def test_predict_proba_is_valid_distribution():
    X, y = _synthetic_dataset()
    model = RandomForestClassifier(n_estimators=25, random_state=42).fit(X, y)
    proba = model.predict_proba(X[:5])
    assert proba.shape[1] == 2
    assert np.allclose(proba.sum(axis=1), 1.0)

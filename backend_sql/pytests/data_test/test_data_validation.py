"""Tests data : validation bloquante (Pandera) + preprocessing déterministe."""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import pandas as pd
import pandera as pa
import pytest

from scripts.data_validation import validate_training_data, REQUIRED_FEATURES
from scripts.general_tain_setup import group_grav_values


def _valid_df(n: int = 30) -> pd.DataFrame:
    """DataFrame d'entraînement minimal mais conforme au schéma."""
    data = {c: [1] * n for c in REQUIRED_FEATURES}
    data["mois"] = [6] * n
    data["jour"] = [15] * n
    data["grav"] = [0, 1] * (n // 2)
    return pd.DataFrame(data)


def test_valid_data_passes():
    # Ne doit pas lever
    validate_training_data(_valid_df())


def test_missing_column_is_blocked():
    df = _valid_df().drop(columns=["catr"])
    with pytest.raises(pa.errors.SchemaErrors):
        validate_training_data(df)


def test_target_out_of_range_is_blocked():
    df = _valid_df()
    df.loc[0, "grav"] = 2  # gravité hors {0, 1}
    with pytest.raises(pa.errors.SchemaErrors):
        validate_training_data(df)


def test_month_out_of_range_is_blocked():
    df = _valid_df()
    df.loc[0, "mois"] = 13
    with pytest.raises(pa.errors.SchemaErrors):
        validate_training_data(df)


def test_group_grav_values_maps_binary():
    out = group_grav_values(pd.DataFrame({"grav": [1, 2, 3, 4]}))
    # 1,4 -> 0 (indemne/léger) ; 2,3 -> 1 (tué/hospitalisé)
    assert out["grav"].tolist() == [0, 1, 1, 0]

"""Tests du lineage : empreinte déterministe du dataset + provenance git."""
import pandas as pd

import scripts.lineage as lineage


def _frame():
    return pd.DataFrame({"a": [1, 2, 3], "grav": [0, 1, 0]})


def test_digest_is_deterministic_for_identical_data():
    assert lineage.dataset_digest(_frame()) == lineage.dataset_digest(_frame())


def test_digest_changes_when_values_change():
    other = _frame()
    other.loc[0, "a"] = 999
    assert lineage.dataset_digest(_frame()) != lineage.dataset_digest(other)


def test_digest_changes_when_columns_change():
    renamed = _frame().rename(columns={"a": "b"})
    assert lineage.dataset_digest(_frame()) != lineage.dataset_digest(renamed)


def test_git_sha_prefers_env(monkeypatch):
    monkeypatch.setenv("GIT_COMMIT_SHA", "deadbeef")
    assert lineage.git_sha() == "deadbeef"


def test_git_sha_falls_back_to_unknown(monkeypatch):
    monkeypatch.delenv("GIT_COMMIT_SHA", raising=False)
    monkeypatch.delenv("GIT_SHA", raising=False)

    def _boom(*args, **kwargs):
        raise FileNotFoundError("git absent")

    monkeypatch.setattr(lineage.subprocess, "run", _boom)
    assert lineage.git_sha() == "unknown"


def test_build_lineage_shape(monkeypatch):
    monkeypatch.setenv("GIT_COMMIT_SHA", "abc123")
    result = lineage.build_lineage(_frame())
    assert result["dataset_rows"] == 3
    assert result["dataset_cols"] == 2
    assert result["dataset_columns"] == "a,grav"
    assert result["git_sha"] == "abc123"
    assert len(result["dataset_digest"]) == 64  # sha-256 hex

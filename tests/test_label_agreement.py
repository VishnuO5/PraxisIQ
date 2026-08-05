"""
tests/test_label_agreement.py
===============================
Unit tests for analytics/label_agreement_check.py (Phase 4 — Cohen's Kappa
label-agreement exercise).

Run with:
    python -m pytest tests/test_label_agreement.py -v

Tests cover:
    - generate_relabel_sample produces the expected real, blank template
    - Sample is reproducible (same random_state -> identical Review_IDs)
    - compute_agreement refuses to score an empty/unfilled template
      (regression guard against ever fabricating a fake kappa score)
"""

import sys
import os
import pytest
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DB_PATH
from analytics.label_agreement_check import (
    generate_relabel_sample,
    compute_agreement,
    SAMPLE_SIZE,
    VALID_LABELS,
)


@pytest.fixture(scope="module")
def sample():
    if not os.path.exists(DB_PATH):
        pytest.skip("Requires PraxisIQ.db — run create_database.py first.")
    return generate_relabel_sample()


def test_sample_has_expected_size(sample):
    assert len(sample) == SAMPLE_SIZE


def test_sample_has_expected_columns(sample):
    expected = {"Review_ID", "Review_Text", "Original_Label", "Second_Pass_Label"}
    assert expected.issubset(set(sample.columns))


def test_second_pass_label_starts_blank(sample):
    assert (sample["Second_Pass_Label"] == "").all()


def test_original_labels_are_valid(sample):
    assert set(sample["Original_Label"].unique()).issubset(set(VALID_LABELS))


def test_review_ids_are_unique(sample):
    assert sample["Review_ID"].is_unique


def test_sample_reproducible(sample):
    rerun = generate_relabel_sample()
    assert sorted(sample["Review_ID"].tolist()) == sorted(rerun["Review_ID"].tolist())


def test_compute_agreement_refuses_empty_template(sample):
    """Regression guard: must never produce a kappa score from an
    unfilled template — that would be a fabricated result."""
    result = compute_agreement()
    assert result is None

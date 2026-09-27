from copy import deepcopy
import pytest
from pydantic import ValidationError
from case_study import Lead, estimate_batch_cost, sample_records, validate_batch


def test_batch_reconciles_and_normalizes_without_mutating_input():
    records = sample_records()
    original = deepcopy(records)
    accepted, rejected = validate_batch(records)
    assert len(accepted) == 2 and len(rejected) == 6
    assert records == original
    assert accepted[0].contact.name == "Example Person"
    assert accepted[0].lead_id == 1
    assert rejected[0]["errors"][0]["location"] == ["contact", "phone"]
    assert all("input" not in error for row in rejected for error in row["errors"])


@pytest.mark.parametrize("value", ["yes", "false", 1, 0, None])
def test_consent_is_not_coerced(value):
    row = sample_records()[0]
    row["marketing_consent"] = value
    with pytest.raises(ValidationError):
        Lead.model_validate(row)


def test_consent_evidence_chronology():
    row = sample_records()[0]
    row["consent_at"] = "2026-01-16T12:00:00Z"
    with pytest.raises(ValidationError, match="postdate"):
        Lead.model_validate(row)


def test_roundtrip_and_independent_defaults():
    a = Lead.model_validate(sample_records()[0])
    b = Lead.model_validate_json(a.model_dump_json())
    assert a == b
    a.tags.append("review")
    assert b.tags == []


@pytest.mark.parametrize("messages,price", [("2", 3), (-1, 3), (True, 3), (2, -1)])
def test_function_rejects_invalid_inputs(messages, price):
    with pytest.raises(ValidationError):
        estimate_batch_cost(messages, price)


def test_function_cost():
    assert estimate_batch_cost(4, 3) == 12
    assert estimate_batch_cost(0, 3) == 0

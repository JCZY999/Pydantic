"""Synthetic lead-intake case study. No network calls or messaging side effects."""
from copy import deepcopy
from typing import Annotated, Any, Literal, Self, TypeAlias, TypedDict
from uuid import UUID

from pydantic import (
    AwareDatetime, BaseModel, ConfigDict, Field, StrictBool,
    ValidationError, field_validator, model_validator, validate_call,
)

# External payloads may contain any value, including deliberately invalid data.
RawRecord: TypeAlias = dict[str, Any]


class ValidationIssue(TypedDict):
    location: list[str | int]
    type: str
    message: str


class RejectedRecord(TypedDict):
    row: int
    errors: list[ValidationIssue]


class Contact(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=80)
    phone: str = Field(pattern=r"^\+[1-9][0-9]{7,14}$")

    @field_validator("name", mode="before")
    @classmethod
    def trim_name(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class Lead(BaseModel):
    model_config = ConfigDict(extra="forbid")
    lead_id: Annotated[int, Field(gt=0)]
    business_id: UUID
    contact: Contact
    service: Literal["interior", "exterior"]
    received_at: AwareDatetime
    marketing_consent: StrictBool = False
    consent_source: Literal["web_form", "signed_import"] | None = None
    consent_at: AwareDatetime | None = None
    tags: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def consent_has_evidence(self) -> Self:
        if self.marketing_consent:
            if self.consent_source is None or self.consent_at is None:
                raise ValueError("marketing consent requires source and timestamp")
            if self.consent_at > self.received_at:
                raise ValueError("consent cannot postdate this intake event")
        return self


def sample_records() -> list[RawRecord]:
    """Eight deliberately constructed examples, not a measured customer sample."""
    base: RawRecord = dict(lead_id="1", business_id="00000000-0000-0000-0000-000000000001",
                contact={"name": "  Example Person  ", "phone": "+12025550101"},
                service="interior", received_at="2026-01-15T12:00:00Z",
                marketing_consent=True, consent_source="web_form",
                consent_at="2026-01-15T11:00:00Z")
    records = [deepcopy(base) for _ in range(8)]
    for i, row in enumerate(records, 1):
        row["lead_id"] = str(i)
    records[1].update(marketing_consent=False, consent_source=None, consent_at=None)
    records[2]["contact"]["phone"] = "not-a-phone"
    records[3]["marketing_consent"] = "yes"
    records[4]["consent_source"] = None
    records[5]["service"] = "unapproved-service"
    records[6]["received_at"] = "2026-01-15T12:00:00"
    records[7]["unexpected"] = "schema drift"
    return records


def validate_batch(records: list[RawRecord]) -> tuple[list[Lead], list[RejectedRecord]]:
    accepted: list[Lead] = []
    rejected: list[RejectedRecord] = []
    for row_number, record in enumerate(records, 1):
        try:
            accepted.append(Lead.model_validate(record))
        except ValidationError as exc:
            # Deliberately omit raw inputs and validator context from reports.
            rejected.append({"row": row_number, "errors": [
                {"location": list(e["loc"]), "type": e["type"], "message": e["msg"]}
                for e in exc.errors(include_input=False, include_context=False, include_url=False)
            ]})
    return accepted, rejected


@validate_call(config=ConfigDict(strict=True), validate_return=True)
def estimate_batch_cost(
    messages: Annotated[int, Field(ge=0)],
    cents_per_message: Annotated[int, Field(ge=0)],
) -> int:
    """Illustrative arithmetic, not provider pricing or a send operation."""
    return messages * cents_per_message


if __name__ == "__main__":
    accepted, rejected = validate_batch(sample_records())
    print(f"Accepted: {len(accepted)}; quarantined: {len(rejected)}")
    print("No records were sent to any external system.")

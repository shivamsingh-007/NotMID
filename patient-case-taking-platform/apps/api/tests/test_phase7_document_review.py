"""Safety rules for human review decisions."""

from uuid import uuid4

import pytest

from app.documents.review import (
    CandidateDecision,
    ManualCandidate,
    ReviewAction,
    ReviewState,
)


def test_accept_requires_explicit_source_verification() -> None:
    with pytest.raises(ValueError, match="Source verification"):
        CandidateDecision(
            action=ReviewAction.ACCEPT,
            expected_candidate_version=1,
        ).validate()


def test_correction_requires_a_non_blank_value() -> None:
    with pytest.raises(ValueError, match="corrected value"):
        CandidateDecision(
            action=ReviewAction.CORRECT,
            expected_candidate_version=1,
            corrected_value="  ",
            source_verified=True,
        ).validate()


def test_non_correction_cannot_smuggle_a_corrected_value() -> None:
    with pytest.raises(ValueError, match="only valid"):
        CandidateDecision(
            action=ReviewAction.REJECT,
            expected_candidate_version=1,
            corrected_value="unsafe",
            reason_code="not_present",
        ).validate()


@pytest.mark.parametrize(
    ("action", "expected"),
    [
        (ReviewAction.ACCEPT, ReviewState.ACCEPTED),
        (ReviewAction.CORRECT, ReviewState.CORRECTED),
        (ReviewAction.REJECT, ReviewState.REJECTED),
        (ReviewAction.UNREADABLE, ReviewState.UNREADABLE),
        (ReviewAction.REQUEST_RESCAN, ReviewState.RESCAN_REQUESTED),
        (ReviewAction.DEFER, ReviewState.DEFERRED),
        (ReviewAction.MANUAL_ENTRY, ReviewState.CORRECTED),
    ],
)
def test_each_action_maps_to_an_explicit_review_state(
    action: ReviewAction,
    expected: ReviewState,
) -> None:
    decision = CandidateDecision(
        action=action,
        expected_candidate_version=1,
        corrected_value=(
            "500"
            if action in {ReviewAction.CORRECT, ReviewAction.MANUAL_ENTRY}
            else None
        ),
        reason_code=(
            "source_quality"
            if action
            in {
                ReviewAction.REJECT,
                ReviewAction.UNREADABLE,
                ReviewAction.REQUEST_RESCAN,
            }
            else None
        ),
        source_verified=action
        in {ReviewAction.ACCEPT, ReviewAction.CORRECT, ReviewAction.MANUAL_ENTRY},
    )

    assert decision.validate() is expected


def test_manual_entry_requires_supported_type_and_source_verification() -> None:
    with pytest.raises(ValueError, match="unsupported"):
        ManualCandidate(
            entity_type="diagnosis",
            normalized_value="unsafe",
            unit=None,
            source_page_artifact_id=uuid4(),
            source_page_number=1,
            source_verified=True,
        ).validate()

    with pytest.raises(ValueError, match="Source verification"):
        ManualCandidate(
            entity_type="instructions",
            normalized_value="after food",
            unit=None,
            source_page_artifact_id=uuid4(),
            source_page_number=1,
            source_verified=False,
        ).validate()

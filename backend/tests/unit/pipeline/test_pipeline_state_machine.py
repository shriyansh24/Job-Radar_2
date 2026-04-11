"""Unit tests for the pipeline status state machine."""

from __future__ import annotations

import pytest

from app.pipeline.state_machine import (
    VALID_STATUSES,
    VALID_TRANSITIONS,
    validate_transition,
)
from app.shared.errors import ValidationError


class TestValidStatuses:
    def test_contains_expected_statuses(self):
        expected = {
            "saved", "applied", "screening", "interviewing",
            "offer", "rejected", "withdrawn", "accepted",
        }
        assert set(VALID_STATUSES) == expected

    def test_every_status_has_a_transitions_entry(self):
        for status in VALID_STATUSES:
            assert status in VALID_TRANSITIONS, f"'{status}' missing from VALID_TRANSITIONS"

    def test_all_transition_targets_are_valid_statuses(self):
        for src, targets in VALID_TRANSITIONS.items():
            for tgt in targets:
                assert tgt in VALID_STATUSES, f"Target '{tgt}' from '{src}' is not a valid status"


class TestValidateTransitionHappyPath:
    """Every allowed transition should succeed without raising."""

    @pytest.mark.parametrize(
        "current, new",
        [
            ("saved", "applied"),
            ("saved", "withdrawn"),
            ("applied", "screening"),
            ("applied", "interviewing"),
            ("applied", "rejected"),
            ("applied", "withdrawn"),
            ("screening", "interviewing"),
            ("screening", "rejected"),
            ("screening", "withdrawn"),
            ("interviewing", "offer"),
            ("interviewing", "rejected"),
            ("interviewing", "withdrawn"),
            ("offer", "accepted"),
            ("offer", "rejected"),
            ("offer", "withdrawn"),
            # Re-entry transitions
            ("rejected", "saved"),
            ("withdrawn", "saved"),
        ],
    )
    def test_valid_transition_does_not_raise(self, current: str, new: str):
        validate_transition(current, new)  # should not raise


class TestValidateTransitionInvalidStatus:
    def test_unknown_new_status_raises(self):
        with pytest.raises(ValidationError, match="Invalid status"):
            validate_transition("saved", "nonexistent")

    def test_empty_new_status_raises(self):
        with pytest.raises(ValidationError, match="Invalid status"):
            validate_transition("saved", "")

    def test_misspelled_status_raises(self):
        with pytest.raises(ValidationError, match="Invalid status"):
            validate_transition("applied", "Screening")  # wrong case


class TestValidateTransitionDisallowed:
    """Disallowed but otherwise valid status combinations should raise."""

    @pytest.mark.parametrize(
        "current, new",
        [
            # Cannot go backwards in the funnel
            ("screening", "applied"),
            ("interviewing", "screening"),
            ("offer", "interviewing"),
            ("accepted", "offer"),
            # Cannot skip stages improperly
            ("saved", "screening"),
            ("saved", "interviewing"),
            ("saved", "offer"),
            ("saved", "accepted"),
            ("applied", "accepted"),
            ("applied", "offer"),
            # Cannot re-enter from accepted
            ("accepted", "saved"),
            ("accepted", "rejected"),
            ("accepted", "withdrawn"),
        ],
    )
    def test_disallowed_transition_raises(self, current: str, new: str):
        with pytest.raises(ValidationError):
            validate_transition(current, new)


class TestTerminalState:
    """'accepted' is a terminal state — no outgoing transitions are allowed."""

    def test_accepted_has_no_allowed_transitions(self):
        assert VALID_TRANSITIONS["accepted"] == []

    @pytest.mark.parametrize("new_status", VALID_STATUSES)
    def test_accepted_to_any_status_raises(self, new_status: str):
        with pytest.raises(ValidationError):
            validate_transition("accepted", new_status)


class TestReEntryTransitions:
    """rejected and withdrawn can return to saved (and only saved)."""

    def test_rejected_can_go_to_saved(self):
        validate_transition("rejected", "saved")

    def test_withdrawn_can_go_to_saved(self):
        validate_transition("withdrawn", "saved")

    @pytest.mark.parametrize(
        "current, disallowed",
        [
            ("rejected", "applied"),
            ("rejected", "screening"),
            ("rejected", "interviewing"),
            ("rejected", "offer"),
            ("rejected", "accepted"),
            ("rejected", "withdrawn"),
            ("withdrawn", "applied"),
            ("withdrawn", "screening"),
            ("withdrawn", "rejected"),
        ],
    )
    def test_re_entry_only_allows_saved(self, current: str, disallowed: str):
        with pytest.raises(ValidationError):
            validate_transition(current, disallowed)

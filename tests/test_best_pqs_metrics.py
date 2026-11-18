
from types import SimpleNamespace

from src.evaluation.proposal_metrics import (
    calculate_proposal_metrics,
)


def make_proposal(quality, status):
    return SimpleNamespace(
        quality=quality,
        status=status,
        rejection_reason=None,
    )


def test_best_pqs_accepted():
    proposals = [
        make_proposal(0.6, "rejected"),
        make_proposal(0.9, "accepted"),
        make_proposal(0.7, "accepted"),
    ]

    metrics = calculate_proposal_metrics(proposals)

    assert metrics["best_pqs"] == 0.9
    assert metrics["best_pqs_accepted"] == 1
    assert metrics["best_pqs_eligible"] == 1


def test_best_pqs_rejected():
    proposals = [
        make_proposal(0.6, "accepted"),
        make_proposal(0.9, "rejected"),
    ]

    metrics = calculate_proposal_metrics(proposals)

    assert metrics["best_pqs_accepted"] == 0


def test_best_pqs_tie():
    proposals = [
        make_proposal(0.9, "rejected"),
        make_proposal(0.9, "accepted"),
    ]

    metrics = calculate_proposal_metrics(proposals)

    assert metrics["best_pqs_accepted"] == 1


def test_no_proposals():
    metrics = calculate_proposal_metrics([])

    assert metrics["best_pqs"] is None
    assert metrics["best_pqs_accepted"] == 0
    assert metrics["best_pqs_eligible"] == 0

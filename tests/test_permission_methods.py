from types import SimpleNamespace

from src.simulation.permission import (
    calculate_multi_trust,
    get_permission_score,
    update_trust_permissions,
)

from src.simulation.permission import (
    calculate_multi_trust,
    get_permission_score,
    update_trust_permissions,
    update_permissions,
)

def create_test_agent():
    return SimpleNamespace(
        chat_permission=False,
        vote_permission=False,
        proposal_permission=False,
    )

def create_test_passport():
    return {
        "participation": 0.70,
        "contribution": 0.50,
        "reliability": 0.80,
        "governance": 0.60,
    }

def test_pt_score():
    passport = create_test_passport()

    score = get_permission_score(
        passport,
        "PT",
    )

    assert score == 0.70

def test_ct_score():
    passport = create_test_passport()

    score = get_permission_score(
        passport,
        "CT",
    )

    assert score == 0.50

def test_multi_score():
    passport = create_test_passport()

    score = calculate_multi_trust(passport)

    assert abs(score - 0.65) < 1e-9

def test_pt_permissions():
    agent = create_test_agent()
    passport = create_test_passport()

    unlocked = update_trust_permissions(
        agent=agent,
        passport=passport,
        method="PT",
    )

    assert agent.chat_permission is True
    assert agent.vote_permission is True
    assert agent.proposal_permission is True

    assert unlocked == [
        "chat",
        "vote",
        "proposal",
    ]

def test_ct_permissions():
    agent = create_test_agent()
    passport = create_test_passport()

    unlocked = update_trust_permissions(
        agent=agent,
        passport=passport,
        method="CT",
    )

    assert agent.chat_permission is True
    assert agent.vote_permission is True
    assert agent.proposal_permission is False

    assert unlocked == [
        "chat",
        "vote",
    ]

def test_multi_permissions():
    agent = create_test_agent()
    passport = create_test_passport()

    unlocked = update_trust_permissions(
        agent=agent,
        passport=passport,
        method="Multi",
    )

    assert agent.chat_permission is True
    assert agent.vote_permission is True
    assert agent.proposal_permission is True


def test_permission_dispatch_pt():
    agent = create_test_agent()
    passport = create_test_passport()

    unlocked = update_permissions(
        agent=agent,
        method="PT",
        passport=passport,
    )

    assert unlocked == [
        "chat",
        "vote",
        "proposal",
    ]


def test_permission_dispatch_requires_passport():
    agent = create_test_agent()

    try:
        update_permissions(
            agent=agent,
            method="CT",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Trust Passportがない場合はエラーになるべきです"
        )


def test_permission_dispatch_unknown_method():
    agent = create_test_agent()

    try:
        update_permissions(
            agent=agent,
            method="Unknown",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "未対応方式はエラーになるべきです"
        )

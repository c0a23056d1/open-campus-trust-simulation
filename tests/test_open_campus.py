import random

from config.settings import (
    NUM_AGENTS,
    RANDOM_SEED,
    OC_STEPS,
    COMMUNITY_STEPS,
    LABS,
)

from src.utils.random_utils import generate_agents

from src.simulation.simulator import (
    run_open_campus_simulation,
    run_community_simulation,
)


def create_test_simulation():

    random.seed(RANDOM_SEED)

    agents = generate_agents(NUM_AGENTS)

    _, activity_logs = (
        run_open_campus_simulation(
            agents=agents,
            labs=LABS,
            oc_steps=OC_STEPS,
        )
    )

    return agents, activity_logs


def test_stamp_equals_visited_labs():

    agents, _ = create_test_simulation()

    for agent in agents:

        assert agent.stamp_count == len(
            agent.visited_labs
        )


def test_chat_permission_with_stamp():

    agents, _ = create_test_simulation()

    for agent in agents:

        if agent.stamp_count >= 1:

            assert agent.chat_permission is True


def test_no_chat_permission_without_stamp():

    agents, _ = create_test_simulation()

    for agent in agents:

        if agent.stamp_count == 0:

            assert agent.chat_permission is False


def test_unlock_chat_only_once():

    agents, activity_logs = (
        create_test_simulation()
    )

    for agent in agents:

        unlock_logs = [
            log
            for log in activity_logs
            if (
                log.agent_id == agent.agent_id
                and log.action == "unlock_chat"
            )
        ]

        assert len(unlock_logs) <= 1


def test_stamp_count_equals_get_stamp_logs():

    agents, activity_logs = (
        create_test_simulation()
    )

    for agent in agents:

        stamp_logs = [
            log
            for log in activity_logs
            if (
                log.agent_id == agent.agent_id
                and log.action == "get_stamp"
            )
        ]

        assert agent.stamp_count == len(
            stamp_logs
        )

def test_one_main_action_per_step():
    """
    1 Agent・1 Stepにつき
    メイン行動は最大1つだけであることを確認する。
    """

    _, activity_logs = (
        create_test_simulation()
    )

    main_actions = {
        "visit_lab",
        "chat",
        "reply",
        "no_action",
    }

    action_counts = {}

    for log in activity_logs:

        if log.action not in main_actions:
            continue

        key = (
            log.agent_id,
            log.step,
        )

        action_counts[key] = (
            action_counts.get(key, 0) + 1
        )

    for count in action_counts.values():

        assert count <= 1

def test_post_visit_comment_requires_visit():
    """
    post_visit_commentが存在する場合、
    同じAgent・同じStepにvisit_labが
    存在することを確認する。
    """

    _, activity_logs = (
        create_test_simulation()
    )

    visit_keys = {
        (
            log.agent_id,
            log.step,
            log.target,
        )
        for log in activity_logs
        if log.action == "visit_lab"
    }

    for log in activity_logs:

        if log.action != "post_visit_comment":
            continue

        key = (
            log.agent_id,
            log.step,
            log.target,
        )

        assert key in visit_keys

def create_test_full_simulation():

    random.seed(RANDOM_SEED)

    agents = generate_agents(NUM_AGENTS)

    _, activity_logs = (
        run_open_campus_simulation(
            agents=agents,
            labs=LABS,
            oc_steps=OC_STEPS,
        )
    )

    activity_logs = (
        run_community_simulation(
            agents=agents,
            activity_logs=activity_logs,
            community_steps=COMMUNITY_STEPS,
            start_step=OC_STEPS + 1,
        )
    )

    return agents, activity_logs

def test_one_community_main_action_per_login():
    _, activity_logs = (
        create_test_full_simulation()
    )

    main_actions = {
        "chat",
        "reply",
        "no_action",
    }

    login_keys = {
        (log.agent_id, log.step)
        for log in activity_logs
        if (
            log.phase == "community"
            and log.action == "login_community"
        )
    }

    for key in login_keys:

        agent_id, step = key

        actions = [
            log
            for log in activity_logs
            if (
                log.agent_id == agent_id
                and log.step == step
                and log.phase == "community"
                and log.action in main_actions
            )
        ]

        assert len(actions) == 1

def test_community_action_requires_login():

    _, activity_logs = (
        create_test_full_simulation()
    )

    login_keys = {
        (log.agent_id, log.step)
        for log in activity_logs
        if (
            log.phase == "community"
            and log.action == "login_community"
        )
    }

    main_actions = {
        "chat",
        "reply",
        "no_action",
    }

    for log in activity_logs:

        if (
            log.phase != "community"
            or log.action not in main_actions
        ):
            continue

        key = (
            log.agent_id,
            log.step,
        )

        assert key in login_keys
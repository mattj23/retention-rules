from retention_rules.builder import PolicyBuilder
from retention_rules.policy import RetainStrategy


def test_build_default_strategy_oldest():
    policy = PolicyBuilder().build(simple_config())
    assert policy.retain_strategy == RetainStrategy.OLDEST


def test_build_strategy_newest():
    config = simple_config()
    config["retain"] = "newest"
    policy = PolicyBuilder().build(config)

    assert policy.retain_strategy == RetainStrategy.NEWEST


def test_build_strategy_oldest():
    config = simple_config()
    config["retain"] = "oldest"
    policy = PolicyBuilder().build(config)

    assert policy.retain_strategy == RetainStrategy.OLDEST


def test_build_default_reuse_off():
    policy = PolicyBuilder().build(simple_config())
    assert not policy.reuse_in_group


def test_build_reuse_off():
    config = simple_config()
    config["reuse"] = False
    policy = PolicyBuilder().build(config)
    assert not policy.reuse_in_group


def test_build_reuse_on():
    config = simple_config()
    config["reuse"] = True
    policy = PolicyBuilder().build(config)
    assert policy.reuse_in_group


def test_build_policy_notes_default():
    policy = PolicyBuilder().build(simple_config())
    assert policy.rules[0].note == "1D retain 1H"


def test_build_policy_custom_note():
    config = simple_config()
    config["rules"][0]["note"] = "custom note"
    policy = PolicyBuilder().build(config)
    assert policy.rules[0].note == "custom note"


def simple_config():
    return {
        "rules": [
            {"applies_for": "1D", "retain_every": "1H"},
        ]
    }

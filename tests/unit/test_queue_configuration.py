"""Configured bounds and UUID identity are independent of their text spelling."""

import pytest

from services.workers.settings import QueueSettings

TENANT = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"


def config(**overrides):
    return QueueSettings(
        redis_url="redis://127.0.0.1",
        endpoint_url="http://127.0.0.1",
        access_key="",
        secret_key="",
        **overrides,
    )


@pytest.mark.parametrize("spelling", [TENANT.upper(), TENANT.replace("-", "")])
def test_allowlist_uses_canonical_uuid_identity(spelling):
    assert config(tenants=(spelling,)).tenants == (TENANT,)


@pytest.mark.parametrize(
    "values",
    [
        {"backoff_seconds": float("nan")},
        {"backoff_seconds": float("inf")},
        {"republish_seconds": float("nan")},
        {"republish_seconds": float("inf")},
        {"backoff_seconds": 1e100},
        {"republish_seconds": 1e100},
        {"capacity": True},
        {"capacity": 1.5},
        {"max_attempts": True},
        {"max_attempts": 2.5},
    ],
)
def test_queue_configuration_rejects_unbounded_or_nonintegral_values(values):
    with pytest.raises(ValueError):
        config(**values)

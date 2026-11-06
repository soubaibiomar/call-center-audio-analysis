"""Real private PostgreSQL/S3/Redis collaborators, isolated synthetic identities."""

import json
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

import pytest

from services.api.auth import Principal
from services.workers.settings import QueueSettings
from services.workers.storage import AudioStore
from tests.api.test_api import api as api
from tests.api.test_api import keys as keys


@pytest.fixture
def jobs(request):
    api_context = request.getfixturevalue("api")
    path = Path(".local/queue_host.json")
    if not path.exists():
        pytest.skip("Configure isolated local S3/Redis services")
    settings = QueueSettings(**json.loads(path.read_text()))
    settings = replace(
        settings,
        tenants=(api_context[5],),
        namespace="test_" + uuid4().hex,
        max_attempts=2,
        backoff_seconds=0.01,
        republish_seconds=0.1,
        capacity=3,
    )
    storage = AudioStore(settings)
    identity = Principal(api_context[5], api_context[9]["agent"], "agent")
    return api_context[7], storage, settings, identity

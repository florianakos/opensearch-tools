import enum
import gzip
import json
import os
import time
import uuid
from itertools import repeat
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

import boto3
import pytest
import zstandard as zstd

LOCALSTACK_ENDPOINT = os.environ["AWS_ENDPOINT_URL"]
AWS_REGION = os.environ["AWS_DEFAULT_REGION"]
OPENSEARCH_ENGINE = os.environ["OPENSEARCH_ENGINE"]
OPENSEARCH_DOMAIN_NAME = os.environ["OPENSEARCH_DOMAIN_NAME"]


class Compression(enum.Enum):
    gzip = "gz"
    zstd = "zst"


@pytest.fixture(scope="session", autouse=True)
def localstack():
    url = f"{LOCALSTACK_ENDPOINT}/health?reload"
    interval = 0.1  # 100ms
    attempts = int(60 / interval)
    for _ in range(attempts):
        time.sleep(interval)
        try:
            with urlopen(url) as resp:
                body = json.load(resp)
            if all(s in {"running", "available", "disabled"} for s in body["services"].values()):
                print("Localstack running")
                break
        except URLError as err:
            print(err)
    else:
        pytest.exit("Timeout waiting for localstack")


@pytest.fixture
def opensearch():
    os_client = boto3.client("opensearch", endpoint_url=LOCALSTACK_ENDPOINT)
    try:
        response = os_client.describe_domain(DomainName=OPENSEARCH_DOMAIN_NAME)
    except os_client.exceptions.ResourceNotFoundException:
        response = os_client.create_domain(DomainName=OPENSEARCH_DOMAIN_NAME, EngineVersion=OPENSEARCH_ENGINE)
    for _ in range(60):
        if response["DomainStatus"]["Created"] and not response["DomainStatus"]["Processing"]:
            hostname, port = response["DomainStatus"]["Endpoint"].split(':')
            return hostname, port
        time.sleep(5)
        response = os_client.describe_domain(DomainName=OPENSEARCH_DOMAIN_NAME)
    pytest.exit("Timed out waiting for Opensearch domain to be ready")


def get_object(compression: Compression, num_events=1_000) -> tuple[str, tuple[Any, ...]]:
    with open("integration_tests/shovel/fixtures/sample_data.json", encoding="utf-8") as f:
        event = json.load(f)
    key = f"{uuid.uuid4()}.json.{compression.value}"
    content = b"".join(repeat(f"{json.dumps(event)}\n".encode(), num_events))
    match compression:
        case Compression.zstd:
            content = zstd.compress(content)
        case Compression.gzip:
            content = gzip.compress(content)
    with open(key, "wb") as bf:
        bf.write(content)
    return key, tuple(repeat(event, num_events))


@pytest.fixture(params=(Compression.zstd, Compression.gzip))
def linux_events(request):
    key, events = get_object(request.param)
    yield key, events

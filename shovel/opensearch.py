import os
import uuid
from collections.abc import Iterable, Iterator, Sequence
from datetime import datetime, timezone
from json import loads
from typing import Any, AnyStr, Protocol

from boto3 import Session
from opensearchpy import AWSV4SignerAuth, OpenSearch, RequestsHttpConnection, helpers


class AWSOpensearch:
    def __init__(self, host: str, port: str) -> None:
        aws_auth = AWSV4SignerAuth(  # type: ignore [no-untyped-call]
            credentials=Session().get_credentials(), region=os.environ["AWS_DEFAULT_REGION"]
        )
        self.client = OpenSearch(
            use_ssl=True,
            verify_certs=True,
            hosts=[{"host": host, "port": port}],
            http_auth=aws_auth,
            connection_class=RequestsHttpConnection,
        )


class LocalstackOpensearch:
    def __init__(self, host: str, port: str) -> None:
        self.client = OpenSearch([{"host": host, "port": port}])


class OSWrapper(Protocol):
    client: OpenSearch

    def __init__(self, host: str, port: str) -> None:
        ...


def get_os_client(host: str, port: str) -> OSWrapper:
    if port == "443":
        return AWSOpensearch(host, port)
    return LocalstackOpensearch(host, port)


def enrich_docs(documents: Iterable[AnyStr], index: str) -> Iterator[dict[str, Any]]:
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    for doc in map(loads, documents):
        doc["_id"] = doc["id"] if doc["id"] else uuid.uuid4()
        doc["_index"] = index
        doc["@timestamp"] = now
        yield doc


def bulk_index(events: Sequence[AnyStr], index: str, os_wrapper: OSWrapper) -> tuple[int, int]:
    return helpers.bulk(
        client=os_wrapper.client,
        actions=enrich_docs(events, index),
        max_retries=5,
        initial_backoff=1,
        request_timeout=120,
        stats_only=True,
        raise_on_error=False,
    )

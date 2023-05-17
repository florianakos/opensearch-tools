from __future__ import annotations

import argparse
import gzip
import io
import logging
import os
import sys
from collections.abc import Iterable, Iterator
from itertools import islice
from typing import TypeVar

import zstandard as zstd

from shovel.opensearch import OSWrapper, bulk_index, get_os_client

T = TypeVar("T")
GZIP_PREFIX = b"\x1f\x8b"
ZSTD_START = b"(\xb5/\xfd"

EVENT_BATCH_SIZE = 200
log = logging.getLogger("shovel")

for name in logging.Logger.manager.loggerDict:
    if ("boto" in name) or ("urllib3" in name) or ("opensearch" in name):
        logging.getLogger(name).setLevel(logging.ERROR)


def chunker(iterable: Iterable[T], n: int) -> Iterator[list[T]]:
    """Splits iterable into chunks"""
    i = iter(iterable)
    yield from iter(lambda: list(islice(i, n)), [])


def get_events(body: bytes) -> Iterator[list[bytes] | list[str]]:
    if body.startswith(ZSTD_START):
        with zstd.ZstdDecompressor().stream_reader(body) as f:
            with io.TextIOWrapper(f) as lines:
                yield from chunker(lines, EVENT_BATCH_SIZE)
    elif body.startswith(GZIP_PREFIX):
        with io.BytesIO(body) as f:
            with gzip.GzipFile(fileobj=f) as lines:
                yield from chunker(lines, EVENT_BATCH_SIZE)
    else:
        raise RuntimeError("Unsupported compression format")


def get_files(files: str) -> Iterator[str]:
    print("TODO: add validation that to skip non JSON uncompressed files")
    if os.path.isdir(files):
        for file in os.listdir(files):
            if os.path.isfile(os.path.join(files, file)):
                yield file
    else:
        for file in files.split(","):
            yield file


def shovel_index(index: str, files: str, opensearch: OSWrapper) -> int:
    log.debug("Processing %d files", len(files))
    failed = 0
    for file in get_files(files):
        try:
            log.debug("Processing files: %s", file)
            with open(file, "rb") as f:
                for events in get_events(f.read()):
                    _, fail = bulk_index(events, index, opensearch)  # type: ignore[type-var]
                    if fail:
                        failed += 1
        except Exception as err:  # pylint: disable=broad-except
            log.error("Indexing (%s) failed with unknown exception", file, exc_info=err)
            failed += 1
    return failed


def shovel_dump() -> int:
    print("TODO: Implement DUMPING!")
    return 0


def main(argv: list[str]) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--host",
        type=str,
        required=True,
        help="The hostname of the Opensearch cluster",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=443,
        help="The port of the Opensearch cluster",
    )
    parser.add_argument(
        "--index",
        type=str,
        required=True,
        help="The index of the Opensearch cluster",
    )
    parser.add_argument(
        "--files",
        type=str,
        required=True,
        # type=lambda keys: [key.strip() for key in keys.split(",")],
        help="Directory or list of files to shovel into Opensearch",
    )
    parser.add_argument(
        "--action",
        type=str,
        required=True,
        # type=lambda keys: [key.strip() for key in keys.split(",")],
        help="Directory or list of files to shovel into Opensearch",
    )
    args = parser.parse_args(argv)
    os_client = get_os_client(args.host, str(args.port))
    if args.action == "index":
        failed = shovel_index(index=args.index, files=args.files, opensearch=os_client)
    else:
        failed = shovel_dump()
    if failed:
        raise RuntimeError(f"{failed} file(s) failed to be indexed")


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    main(sys.argv[1:])

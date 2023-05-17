from shovel import main
from shovel.opensearch import get_os_client
import pytest


def test_trigger_shovel_indexing(opensearch, linux_events):
    index = "test_index"
    host, port = opensearch
    file_names, events = linux_events
    print(file_names)
    main.main([f"--host={host}", f"--port={port}", f"--files={file_names}", f"--index={index}", "--action=index"])
    _verify_doc_indexed(host, port, events[0], index)
    _verify_doc_count(host, port, index, 1)


def test_trigger_shovel_missing_params(opensearch):
    host, port = opensearch
    with pytest.raises(SystemExit) as exc:
        main.main([f"--host={host}", f"--port={port}"])
        assert exc.value.code == 2


def _verify_doc_indexed(host, port, document, index):
    os = get_os_client(host, port)
    response = os.client.get(index=index, id=document["id"])
    response["_source"].pop("@timestamp")
    assert response["_source"] == document


def _verify_doc_count(host, port, index, count):
    os = get_os_client(host, port)
    assert os.client.count(index=index)['count'] == 1

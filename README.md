# opensearch-tools

Tools for configuring of and interacting with Opensearch clusters.

# shovel

Tool for indexing contents of directories (or list of files) to Opensearch in bulk, as well as dumping data from Opensearch 
to files.

# conductor

Tool for configuring Opensearch clusters, such as ISM, security, index templates, etc...


$ curl -d '{"some":"data", "lol":1, "what": ["is", "this"]}' -H "Content-Type: application/json" -X POST http://localhost:4510/test_index/doc
$ curl http://localhost:4510/test_index/_search | jq

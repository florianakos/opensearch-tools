# shovel

Tool for shoveling data in an out of Opensearch cluster.
To implement both functionalities, the tool uses command line arguments:

```shell
$ shovel \
  --host OS_HOST \
  --port OS_PORT \
  --index-name INDEX_NAME \
  --file_name FILE_NAME \
  --action {index/dump}
```

Depending on the specified action, index or dump, the shovel will connect to the 
Opensearch cluster via the given hostname and port, target the specified index,
and use the given file_name to either load data into Opensearch from a local file
or load data from Opensearch into a local file.

If the index action is specified, the files param can be a comma separated list of files
or it can also be just a directory which contains the files to take and index 
into Opensearch.



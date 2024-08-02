echo Making .secrets directory
mkdir -p .secrets
echo Making .secrets/bazel-cache-key.json
echo $GCP_CLOZE_DATA_CACHE_KEY > .secrets/bazel-cache-key.json
echo Printing environment
printenv | sort

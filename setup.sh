echo Making .secrets directory
mkdir -p .secrets
echo Making .secrets/bazel-cache-key.json
echo $GCP_CLOZE_DATA_CACHE_KEY > .secrets/bazel-cache-key.json

# Set up unidic
wget https://storage.googleapis.com/cloze-data-bazel-cache/unidic-3.1.0.zip
unzip unidic-3.1.0.zip
touch unidic/mecabrc

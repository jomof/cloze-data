# Function to find WORKSPACE file walking up the directory tree
find_workspace_dir() {
    dir="$PWD"
    while [ "$dir" != "/" ]; do
        if [ -f "$dir/WORKSPACE" ]; then
            echo "$dir"
            return 0
        fi
        dir="$(dirname "$dir")"
    done
    return 1
}

# Store the result in a variable
workspace_dir=$(find_workspace_dir)

echo Making $workspace_dir/.secrets directory
mkdir -p $workspace_dir/.secrets
echo $GCP_CLOZE_DATA_CACHE_KEY > $workspace_dir/.secrets/bazel-cache-key.json

sudo npm install -g npm@10.8.2
sudo npm install -g @bazel/bazelisk
sudo pip install mecab-python3==1.0.9
sudo pip install unidic==1.1.0
sudo python -m unidic download
export HISTFILE=$workspace_dir/.bash_history



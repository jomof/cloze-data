rm -rf files

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

mkdir -p files/bunpro-fixed-yaml-all
cp -rf $workspace_dir/bazel-bin/resources/grammar/create-bunpro-fixed-yaml-all/. files/bunpro-fixed-yaml-all

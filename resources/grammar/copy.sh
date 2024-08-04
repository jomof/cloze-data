rm -rf files

# mkdir -p files/bs4-stripped-all
# cp -rf /workspaces/cloze-data/bazel-bin/resources/grammar/bs4-stripped-all files/bs4-stripped-all

# mkdir -p files/extracted-yaml-all
# cp -rf /workspaces/cloze-data/bazel-bin/resources/grammar/extracted-yaml-all files/extracted-yaml-all

mkdir -p files/bunpro-fixed-yaml-all
cp -rf /workspaces/cloze-data/bazel-bin/resources/grammar/create-bunpro-fixed-yaml-all/. files/bunpro-fixed-yaml-all

rm -rf /workspaces/cloze-data/cache_data/*
bazel clean
bazel run //resources/grammar:publish-ai-cleaned-merge-grammars
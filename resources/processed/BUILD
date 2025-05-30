# Regenerate with bazel run //resources/grammar:publish-merged
filegroup(
    name = "merge-grammars",
    srcs = glob(
        ["merge-grammars/**"],
        allow_empty = True,
    ),
    visibility = ["//visibility:public"],
)

# Regenerate with bazel run //resources/grammar:publish-ai-cleaned-merge-grammars
filegroup(
    name = "ai-cleaned-merge-grammars",
    srcs = glob(
        ["ai-cleaned-merge-grammars/**"],
        allow_empty = True,
    ),
    visibility = ["//visibility:public"],
)

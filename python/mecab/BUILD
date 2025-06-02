load("@rules_python//python:defs.bzl", "py_library", "py_test")

py_library(
    name = "mecab",
    srcs = [
        "compact_sentence.py",
        "tagger.py",
    ],
    visibility = ["//visibility:public"],
    deps = [
        "@pip//mecab_python3",
        "@pip//unidic",
    ],
)

# bazel test //python/mecab:compact_sentence_test
py_test(
    name = "compact_sentence_test",
    srcs = ["compact_sentence_test.py"],
    deps = [":mecab"],
)

load("@rules_python//python:defs.bzl", "py_library", "py_test")

py_library(
    name = "utils",
    srcs = ["compact_sentence.py", "tagger.py"],
    visibility = ["//visibility:public"],
)

filegroup(
    name = "unidic-dir",
    srcs = glob(["dicdir/**"]),
    visibility = ["//visibility:public"],
)

py_test(
    name = "compact_sentence_test",
    srcs = ["compact_sentence_test.py"],
    data = [":unidic-dir"],
    deps = [
        ":utils",
        "@pip//mecab_python3",
    ],
)

sh_binary(
    name = "download-unidic",
    srcs = ["download_unidic.sh"],
)

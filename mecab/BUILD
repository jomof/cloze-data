exports_files([
    "compact_sentence.py"])


py_library(
    name = "compact_sentence",
    srcs = ["compact_sentence.py"],
    visibility = ["//visibility:public"],
)

py_test(
    name = "compact_sentence_test",
    srcs = ["compact_sentence_test.py"],
    deps = [":compact_sentence"],
)

sh_binary(
    name = "download-unidic",
    srcs = ["download_unidic.sh"],
)
exports_files([
    "compact_sentence.py",
])

py_library(
    name = "compact_sentence",
    srcs = ["compact_sentence.py"],
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
        ":compact_sentence",
        "@pip//mecab_python3",
    ],
)

sh_binary(
    name = "download-unidic",
    srcs = ["download_unidic.sh"],
)

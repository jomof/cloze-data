load("@rules_python//python:defs.bzl", "py_binary", "py_library")
load("//json_rules:json.bzl", "json_concat")
load("//python_rules:python_build.bzl", "py_build_tool")

json_concat(
    name = "concatenated-sentences-json",
    srcs = [
        "//resources/curated:grammar-point-sentences-json",
        "//resources/original/jmdict:jmdict-sentences",
    ],
    output = "concatenated-sentences.json",
)

py_build_tool(
    name = "tokenized-sentences",
    outs = ["tokenized-sentences.json"],
    ins = ["concatenated-sentences.json"],
    main = ":tokenize_sentences",
    deps = [
        "//python/mecab",
    ],
)

py_build_tool(
    name = "grammar-compliance-report",
    outs = ["grammar-compliance-report.txt"],
    ins = [
        "//resources/curated:grammar-points-flat.json",
        "tokenized-sentences.json",
    ],
    main = ":grammar_compliance_report",
    deps = [
        "//python/mecab",
    ],
)

py_binary(
    name = "grammar_compliance_report",
    srcs = ["grammar_compliance_report.py"],
    visibility = ["//:__subpackages__"],
    deps = [
        "//python/mecab",
        "@pip//mecab_python3",
        "@pip//unidic",
    ],
)

py_binary(
    name = "tokenize_sentences",
    srcs = ["tokenize_sentences.py"],
    visibility = ["//:__subpackages__"],
    deps = ["//python/mecab"],
)

py_library(
    name = "sentences",
    srcs = [
        "grammar_compliance_report.py",
        "tokenize_sentences.py",
    ],
    visibility = ["//:__subpackages__"],
    deps = [
        "//python/mecab",
        "@pip//mecab_python3",
        "@pip//unidic",
    ],
)

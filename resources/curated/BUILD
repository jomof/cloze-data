load("@rules_python//python:defs.bzl", "py_binary", "py_library")
load("//json_rules:json.bzl", "json_concat")
load("//python_rules:python_build.bzl", "py_build_tool")
load(":annotate_vocab.bzl", "annotate_vocab")

# A hand-curated list of Japanese grammar points roughty aligned with JLPT level
filegroup(
    name = "grammar-by-jlpt-level",
    srcs = [
        "grammar-by-jlpt-level.json",
    ],
)

json_concat(
    name = "concatenated-vocab-json",
    srcs = [
        ":jlpt-n1-vocab-json",
        ":jlpt-n2-vocab-json",
        ":jlpt-n3-vocab-json",
        ":jlpt-n4-vocab-json",
        ":jlpt-n5-vocab-json",
        ":jlpt-non-vocab-json",
    ],
    output = "concatenated-vocab.json",
    visibility = ["//visibility:public"],
)

py_build_tool(
    name = "grammar-points-json",
    outs = [
        "grammar-points-flat.json",
        "grammar-points-special.json",
    ],
    ins = ["grammar-by-jlpt-level.json"],
    main = ":grammar_to_array",
    visibility = ["//visibility:public"],
)

py_build_tool(
    name = "grammar-summary-text",
    outs = ["grammar-summary.txt"],
    ins = ["grammar-points-flat.json"],
    main = "grammar_summary.py",
)

py_build_tool(
    name = "grammar-point-sentences-json",
    outs = ["grammar-point-sentences.json"],
    ins = ["grammar-points-flat.json"],
    main = "sentences_flattened.py",
    visibility = ["//visibility:public"],
)

annotate_vocab(
    name = "jlpt-n5-vocab-json",
    level = "n5",
)

annotate_vocab(
    name = "jlpt-n4-vocab-json",
    level = "n4",
)

annotate_vocab(
    name = "jlpt-n3-vocab-json",
    level = "n3",
)

annotate_vocab(
    name = "jlpt-n2-vocab-json",
    level = "n2",
)

annotate_vocab(
    name = "jlpt-n1-vocab-json",
    level = "n1",
)

annotate_vocab(
    name = "jlpt-non-vocab-json",
    level = "non",
)

py_binary(
    name = "annotate_vocab",
    srcs = ["annotate_vocab.py"],
    visibility = ["//:__subpackages__"],
)

py_binary(
    name = "grammar_summary",
    srcs = ["grammar_summary.py"],
    visibility = ["//:__subpackages__"],
)

py_binary(
    name = "grammar_to_array",
    srcs = ["grammar_to_array.py"],
    visibility = ["//:__subpackages__"],
)

py_binary(
    name = "sentences_flattened",
    srcs = ["sentences_flattened.py"],
    visibility = ["//:__subpackages__"],
)

py_library(
    name = "curated",
    srcs = [
        "annotate_vocab.py",
        "grammar_summary.py",
        "grammar_to_array.py",
        "sentences_flattened.py",
    ],
    visibility = ["//:__subpackages__"],
)

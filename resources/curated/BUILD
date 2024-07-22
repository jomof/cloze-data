load("//json_rules:json.bzl", "json_concat")
load(":annotate_vocab.bzl", "annotate_vocab")
load("//python_rules:python_build.bzl", "py_build_tool")

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
    output = "concatenated-vocab.json"
)

py_build_tool(
    name = "grammar-points-json",
    main = "grammar_to_array.py",
    ins = ["grammar-by-jlpt-level.json"],
    outs = ["grammar-points-flat.json", "grammar-points-special.json"],
    visibility = ["//visibility:public"]
)

py_build_tool(
    name = "grammar-summary-text",
    main = "grammar_summary.py",
    ins = ["grammar-points-flat.json"],
    outs = ["grammar-summary.txt"]
)

py_build_tool(
    name = "grammar-point-sentences-json",
    main = "sentences_flattened.py",
    ins = ["grammar-points-flat.json"],
    outs = ["grammar-point-sentences.json"],
    visibility = ["//visibility:public"],
)

annotate_vocab(name = "jlpt-n5-vocab-json", level = 'n5')
annotate_vocab(name = "jlpt-n4-vocab-json", level = 'n4')
annotate_vocab(name = "jlpt-n3-vocab-json", level = 'n3')
annotate_vocab(name = "jlpt-n2-vocab-json", level = 'n2')
annotate_vocab(name = "jlpt-n1-vocab-json", level = 'n1')
annotate_vocab(name = "jlpt-non-vocab-json", level = 'non')

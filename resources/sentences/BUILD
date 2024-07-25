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
    main = "tokenize_sentences.py",
    deps = ["//mecab:compact_sentence"],
)

py_build_tool(
    name = "grammar-compliance-report",
    outs = ["grammar-compliance-report.txt"],
    ins = [
        "//resources/curated:grammar-points-flat.json",
        "tokenized-sentences.json",
    ],
    main = "grammar_compliance_report.py",
    deps = ["//mecab:compact_sentence"],
)

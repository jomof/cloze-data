load("//json_rules:json.bzl", "json_concat")
load(":annotate_vocab.bzl", "annotate_vocab")

# A hand-curated list of Japanese grammar points roughty aligned with JLPT level
filegroup(
    name = "grammar-by-jlpt-level",
    srcs = [
        "grammar-by-jlpt-level.json",
    ],
)

filegroup(
    name = "all-vocab-json",
    srcs = [
        ":jlpt-n1-vocab-json",
        ":jlpt-n2-vocab-json",
        ":jlpt-n3-vocab-json",
        ":jlpt-n4-vocab-json",
        ":jlpt-n5-vocab-json",
        ":jlpt-non-vocab-json",
    ]
)

json_concat(
    name = "concatenated-vocab-json",
    srcs = [
        ":all-vocab-json"
    ],
    output = "concatenated-vocab.json"
)

genrule(
    name = "grammar-points-json",
    srcs = ["grammar_to_array.py", ":grammar-by-jlpt-level.json"],
    outs = ["grammar-points-flat.json", "grammar-points-special.json"],
    cmd = "python $(SRCS) $(OUTS)",
)

genrule(
    name = "grammar-point-sentences-json",
    srcs = ["sentences_flattened.py", ":grammar-points-flat.json"],
    outs = ["grammar-point-sentences.json"],
    cmd = "python $(SRCS) $(OUTS)",
    visibility = ["//visibility:public"],
)

annotate_vocab(level = 'n5')
annotate_vocab(level = 'n4')
annotate_vocab(level = 'n3')
annotate_vocab(level = 'n2')
annotate_vocab(level = 'n1')
annotate_vocab(level = 'non')



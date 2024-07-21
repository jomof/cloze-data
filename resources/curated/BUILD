load("//json_rules:json.bzl", "json_concat")

# A hand-curated list of Japanese grammar points roughty aligned with JLPT level
filegroup(
    name = "grammar-by-jlpt-level",
    srcs = [
        "grammar-by-jlpt-level.json",
    ],
)

filegroup(
    name = "all-vocab",
    srcs = [
        ":jlpt-n1-vocab",
        ":jlpt-n2-vocab",
        ":jlpt-n3-vocab",
        ":jlpt-n4-vocab",
        ":jlpt-n5-vocab",
        ":non-jlpt-vocab",
    ]
)

filegroup(
    name = "all-vocab-json",
    srcs = [
        ":jlpt-n1-vocab-json",
        ":jlpt-n2-vocab-json",
        ":jlpt-n3-vocab-json",
        ":jlpt-n4-vocab-json",
        ":jlpt-n5-vocab-json",
        ":non-jlpt-vocab-json",
    ]
)

json_concat(
    name = "concatenated-vocab-json",
    srcs = [
        ":all-vocab-json"
    ],
    output = "concatenated-vocab.json"
)

filegroup(
    name = "jlpt-n1-vocab",
    srcs = [
        "jlpt-n1-vocab.txt"
    ]
)

filegroup(
    name = "jlpt-n2-vocab",
    srcs = [
        "jlpt-n2-vocab.txt"
    ]
)

filegroup(
    name = "jlpt-n3-vocab",
    srcs = [
        "jlpt-n3-vocab.txt"
    ]
)

filegroup(
    name = "jlpt-n4-vocab",
    srcs = [
        "jlpt-n4-vocab.txt"
    ]
)

filegroup(
    name = "jlpt-n5-vocab",
    srcs = [
        "jlpt-n5-vocab.txt"
    ]
)

filegroup(
    name = "non-jlpt-vocab",
    srcs = [
        "non-jlpt-vocab.txt"
    ]
)

genrule(
    name = "jlpt-n5-vocab-json",
    srcs = ["annotate_vocab.py", ":jlpt-n5-vocab"],
    outs = ["jlpt-n5-vocab.json"],
    cmd = "python $(SRCS) $(OUTS) n5",
)

genrule(
    name = "jlpt-n4-vocab-json",
    srcs = ["annotate_vocab.py", ":jlpt-n4-vocab"],
    outs = ["jlpt-n4-vocab.json"],
    cmd = "python $(SRCS) $(OUTS) n4",
)

genrule(
    name = "jlpt-n3-vocab-json",
    srcs = ["annotate_vocab.py", ":jlpt-n3-vocab"],
    outs = ["jlpt-n3-vocab.json"],
    cmd = "python $(SRCS) $(OUTS) n3",
)

genrule(
    name = "jlpt-n2-vocab-json",
    srcs = ["annotate_vocab.py", ":jlpt-n2-vocab"],
    outs = ["jlpt-n2-vocab.json"],
    cmd = "python $(SRCS) $(OUTS) n2",
)

genrule(
    name = "jlpt-n1-vocab-json",
    srcs = ["annotate_vocab.py", ":jlpt-n1-vocab"],
    outs = ["jlpt-n1-vocab.json"],
    cmd = "python $(SRCS) $(OUTS) n1",
)

genrule(
    name = "non-jlpt-vocab-json",
    srcs = ["annotate_vocab.py", ":non-jlpt-vocab"],
    outs = ["non-jlpt-vocab.json"],
    cmd = "python $(SRCS) $(OUTS) non",
)


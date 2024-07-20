
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
    name = "run_hello",
    outs = ["hello_output.txt"],
    cmd = "python --version > $(OUTS)"
)


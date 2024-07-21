load("//json_rules:json.bzl", "json_concat")

json_concat(
    name = "concatenated-sentences-json",
    srcs = [
        "//resources/curated:grammar-point-sentences-json",
        "//resources/original/jmdict:jmdict-sentences"
    ],
    output = "concatenated-sentences.json"
)

genrule(
    name = "tokenized",
    srcs = ["tokenize_sentences.py", "concatenated-sentences.json"],
    outs = ["tokenized-sentences.json"],
    cmd = "python $(SRCS) $(OUTS)"
)

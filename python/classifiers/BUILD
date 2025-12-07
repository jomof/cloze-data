load("@rules_python//python:defs.bzl", "py_binary", "py_library")

py_library(
    name = "grammar",
    srcs = ["grammar.py"],
    visibility = ["//visibility:public"],
    deps = [
        "//python/console:display",
        "//python/mecab",
        "@pip//numpy",
        "@pip//scikit_learn",
    ],
)

py_library(
    name = "classifiers",
    srcs = [
        "__init__.py",
        "gather_sentences.py",
        "grammar.py",
        "token_tuples.py",
        "training_tokens.py",
        "word2vec.py",
    ],
    visibility = ["//:__subpackages__"],
    deps = [
        "//python/console:display",
        "//python/grammar",
        "//python/mapreduce",
        "//python/mecab",
        "@pip//gensim",
        "@pip//numpy",
        "@pip//scikit_learn",
        "@pip//scikit_multilearn",
    ],
)

# bazel run //python/classifiers:word2vec
py_binary(
    name = "word2vec",
    srcs = ["word2vec.py"],
    data = [
        "//resources/processed:ai-cleaned-merge-grammars",
    ],
    visibility = ["//:__subpackages__"],
    deps = [
        ":classifiers",
        "//python/console:display",
        "//python/mecab",
        "@pip//gensim",
        "@pip//numpy",
        "@pip//scikit_learn",
    ],
)


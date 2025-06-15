load("@rules_python//python:defs.bzl", "py_library")

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
        "grammar.py",
    ],
    visibility = ["//:__subpackages__"],
    deps = [
        "//python/console:display",
        "//python/mecab",
        "@pip//numpy",
        "@pip//scikit_learn",
    ],
)

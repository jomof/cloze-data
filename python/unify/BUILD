load("@rules_python//python:defs.bzl", "py_library", "py_test")

py_library(
    name = "unify",
    srcs = ["unify.py"],
    visibility = ["//visibility:public"],
)

py_test(
    name = "unify_test",
    srcs = ["unify_test.py"],
    deps = [":unify"],
)

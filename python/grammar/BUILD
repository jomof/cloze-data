load("@rules_python//python:defs.bzl", "py_library", "py_test")

filegroup(
    name = "grammar-schema.json",
    srcs = ["grammar-schema.json"],
    visibility = ["//visibility:public"], 
)

py_library(
    name = "utils",
    srcs = [
        "clean_lint.py",
    ],
    visibility = ["//visibility:public"],
    deps = [
        "@pip//jsonschema",
    ],
)

py_test(
    name = "clean_lint_test",
    srcs = ["clean_lint_test.py"],
    deps = [":grammar"],
)

py_library(
    name = "grammar",
    srcs = [
        "__init__.py",
        "clean_lint.py",
    ],
    visibility = ["//:__subpackages__"],
    deps = ["@pip//jsonschema"],
)

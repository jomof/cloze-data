load("@rules_python//python:defs.bzl", "py_library", "py_test")

# bazel test //python/grammar:clean_lint_test
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
        "grammar_schema.py",
    ],
    data = [":grammar-schema.json"],
    visibility = ["//:__subpackages__"],
    deps = [
        "@pip//json5",
        "@pip//jsonschema",
    ],
)

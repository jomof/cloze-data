load("@rules_python//python:defs.bzl", "py_library", "py_test")

# bazel test //python/grammar:clean_lint_test
py_test(
    name = "clean_lint_test",
    srcs = ["clean_lint_test.py"],
    deps = [
        ":grammar",
        "//python/utils/visit_json",
    ],
)

# bazel test //python/grammar:matcher_test
py_test(
    name = "matcher_test",
    srcs = ["matcher_test.py"],
    deps = [
        ":grammar",
        "//python/mecab",
    ],
)

py_library(
    name = "grammar",
    srcs = [
        "__init__.py",
        "clean_lint.py",
        "grammar_schema.py",
        "matcher.py",
    ],
    data = [":grammar-schema.json"],
    visibility = ["//:__subpackages__"],
    deps = [
        "//python/mecab",
        "//python/utils/visit_json",
        "@pip//json5",
        "@pip//jsonschema",
    ],
)

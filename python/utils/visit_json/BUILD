load("@rules_python//python:defs.bzl", "py_library", "py_test")

py_library(
    name = "visit_json",
    srcs = [
        "__init__.py",
        "visit_json.py",
    ],
    visibility = ["//visibility:public"],
)

# bazel test //python/utils/visit_json:visit_json_test
py_test(
    name = "visit_json_test",
    srcs = ["visit_json_test.py"],
    deps = [":visit_json"],
)

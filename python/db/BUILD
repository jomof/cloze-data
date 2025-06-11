load("@rules_python//python:defs.bzl", "py_library", "py_test")

py_library(
    name = "db",
    srcs = [
        "__init__.py",
        "db.py",
    ],
    visibility = ["//visibility:public"],
)

# bazel test //python/db:db_test
py_test(
    name = "db_test",
    srcs = ["db_test.py"],
    deps = [":db"],
)

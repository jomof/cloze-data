load("@rules_python//python:defs.bzl", "py_library")

py_library(
    name = "mapreduce",
    srcs = [
        "__init__.py",
        "mapreduce.py",
    ],
    visibility = ["//visibility:public"],
    deps = [
        "//python/console:display",
        "@pip//aiofiles",
        "@pip//pyyaml",
    ],
)

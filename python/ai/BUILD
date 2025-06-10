load("@rules_python//python:defs.bzl", "py_library")

py_library(
    name = "ai",
    srcs = [
        "__init__.py",
        "aichat.py",
        "aigen.py",
        "util.py",
    ],
    visibility = ["//visibility:public"],
    deps = [
        "//python/gcp",
        "@pip//google_genai",
        "@pip//json5",
        "@pip//jsonref",
        "@pip//jsonschema",
    ],
)

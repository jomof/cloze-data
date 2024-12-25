load("@rules_python//python:defs.bzl", "py_library")

py_library(
    name = "aigen",
    srcs = [
        "aigen.py",
    ],
    visibility = ["//visibility:public"],
    deps = [
        "@pip//google_cloud_aiplatform",
        "@pip//google_genai",
    ],
)

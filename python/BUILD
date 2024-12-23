load("@rules_python//python:defs.bzl", "py_library")

py_library(
    name = "aigen",
    srcs = [
        "aigen.py",
    ],
    deps = [
        "@pip//google_genai",
        "@pip//google_cloud_aiplatform",
    ],
    visibility = ["//visibility:public"]
)

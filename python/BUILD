load("@rules_python//python:defs.bzl", "py_library")

py_library(
    name = "gcp",
    srcs = [
        "gcp.py",
    ],
    visibility = ["//visibility:public"],
)

py_library(
    name = "aigen",
    srcs = [
        "aigen.py",
    ],
    visibility = ["//visibility:public"],
    deps = [
        "//python:gcp",
        "@pip//google_cloud_aiplatform",
        "@pip//google_genai",
    ],
)

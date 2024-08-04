load("@rules_python//python:defs.bzl", "py_binary", "py_library")

filegroup(
    name = "dojg-all",
    srcs = glob(["all/*"]),
    visibility = ["//visibility:public"],
)

py_binary(
    name = "split",
    srcs = ["split.py"],
    visibility = ["//:__subpackages__"],
    deps = [
        "@pip//beautifulsoup4",
        "@pip//pyyaml",
    ],
)

py_library(
    name = "dojg",
    srcs = ["split.py"],
    visibility = ["//:__subpackages__"],
    deps = [
        "@pip//beautifulsoup4",
        "@pip//pyyaml",
    ],
)

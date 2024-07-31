load("@rules_python//python:defs.bzl", "py_binary", "py_library")
load("//python_rules:python_build.bzl", "py_build_tool_stream")

py_build_tool_stream(
    name = "bs4-stripped-sample",
    srcs = ["//resources/original/bunpro:bunpro-sample"],
    tool = ":bs4-strip",
)

py_build_tool_stream(
    name = "extracted-yaml-sample",
    srcs = [":bs4-stripped-sample"],
    extension = ".yaml",
    tool = ":extract-yaml",
)

py_build_tool_stream(
    name = "ai-cleaned-sample",
    srcs = [":extracted-yaml-sample"],
    extension = ".yaml",
    tool = ":ai-clean",
)

py_build_tool_stream(
    name = "yaml-cleaned-sample",
    srcs = [":ai-cleaned-sample"],
    extension = ".yaml",
    tool = ":yaml-clean",
)

py_binary(
    name = "ai-clean",
    srcs = ["ai-clean.py"],
    visibility = ["//:__subpackages__"],
    deps = [
        "@pip//google_cloud_aiplatform",
        "@pip//google_cloud_logging",
        "@pip//pyyaml",
    ],
)

py_binary(
    name = "bs4-strip",
    srcs = ["bs4-strip.py"],
    visibility = ["//:__subpackages__"],
    deps = [
        "@pip//beautifulsoup4",
        "@pip//pyyaml",
    ],
)

py_binary(
    name = "extract-yaml",
    srcs = ["extract-yaml.py"],
    visibility = ["//:__subpackages__"],
    deps = ["@pip//beautifulsoup4"],
)

py_binary(
    name = "yaml-clean",
    srcs = ["yaml-clean.py"],
    visibility = ["//:__subpackages__"],
    deps = ["@pip//pyyaml"],
)

py_library(
    name = "grammar",
    srcs = [
        "ai-clean.py",
        "bs4-strip.py",
        "extract-yaml.py",
        "yaml-clean.py",
    ],
    visibility = ["//:__subpackages__"],
    deps = [
        "@pip//beautifulsoup4",
        "@pip//google_cloud_aiplatform",
        "@pip//google_cloud_logging",
        "@pip//pyyaml",
    ],
)

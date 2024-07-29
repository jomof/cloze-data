load("@rules_python//python:defs.bzl", "py_binary", "py_library")
load("//python_rules:python_build.bzl", "py_build_tool_stream")

py_build_tool_stream(
    name = "bs4-stripped",
    srcs = glob(["sample/*"]),
    script = "bs4-strip.py",
)

py_build_tool_stream(
    name = "extracted-yaml",
    srcs = [":bs4-stripped"],
    extension = ".yaml",
    script = "extract-yaml.py",
)

py_build_tool_stream(
    name = "ai-cleaned",
    srcs = [":extracted-yaml"],
    extension = ".yaml",
    script = "ai-clean.py",
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
    name = "ai-clean",
    srcs = ["ai-clean.py"],
    visibility = ["//:__subpackages__"],
    deps = ["@pip//google_cloud_aiplatform"],
)

py_library(
    name = "bunpro",
    srcs = [
        "ai-clean.py",
        "bs4-strip.py",
        "extract-yaml.py",
    ],
    visibility = ["//:__subpackages__"],
    deps = [
        "@pip//beautifulsoup4",
        "@pip//google_cloud_aiplatform",
        "@pip//pyyaml",
    ],
)

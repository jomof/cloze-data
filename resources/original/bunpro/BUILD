load("@rules_python//python:defs.bzl", "py_binary", "py_library")
# load("//zip_rules:zip.bzl", "process_zip_stream", "unzip_files")

load("//python_rules:python_build.bzl", "py_build_tool_stream")

py_build_tool_stream(
    name = "bs4-stripped",
    srcs = glob(["grammar_points/*"]),
    script = "bs4-strip.py",
)

py_build_tool_stream(
    name = "bunpro-grammar-point-summaries",
    srcs = [":bs4-stripped"],
    extension = ".yaml",
    script = "extract-yaml.py",
)

py_binary(
    name = "bs4-strip",
    srcs = ["bs4-strip.py"],
    visibility = ["//:__subpackages__"],
    deps = ["@pip//beautifulsoup4"],
)

py_binary(
    name = "extract-yaml",
    srcs = ["extract-yaml.py"],
    visibility = ["//:__subpackages__"],
    deps = ["@pip//beautifulsoup4"],
)


py_library(
    name = "bunpro",
    srcs = [
        "bs4-strip.py",
        "extract-yaml.py",
    ],
    visibility = ["//:__subpackages__"],
    deps = [
        "@pip//beautifulsoup4",
        "@pip//pyyaml",
    ],
)

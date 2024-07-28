load("@rules_python//python:defs.bzl", "py_binary", "py_library")
load("//zip_rules:zip.bzl", "process_zip_stream", "unzip_files")

process_zip_stream(
    name = "stripped-bunpro-grammar-points",
    src = "grammar-points.zip",
    script = "html-strip.py",
)

process_zip_stream(
    name = "formatted-bunpro-grammar-points",
    src = ":stripped-bunpro-grammar-points",
    script = "bs4-strip.py",
)

unzip_files(
    name = "stripped-bunpro-grammar-points-unzipped",
    src = ":stripped-bunpro-grammar-points",
)

unzip_files(
    name = "formatted-bunpro-grammar-points-unzipped",
    src = ":formatted-bunpro-grammar-points",
)

py_binary(
    name = "bs4-strip",
    srcs = ["bs4-strip.py"],
    visibility = ["//:__subpackages__"],
    deps = [
        ":bunpro",
        "@pip//beautifulsoup4",
        "@pip//pyyaml",
    ],
)

py_binary(
    name = "html-strip",
    srcs = ["html-strip.py"],
    visibility = ["//:__subpackages__"],
    deps = [
        ":bunpro",
        "@pip//beautifulsoup4",
    ],
)

py_library(
    name = "bunpro",
    srcs = [
        "bs4-strip.py",
        "check.py",
        "html-strip.py",
        "stripper.py",
    ],
    visibility = ["//:__subpackages__"],
    deps = [
        "@pip//beautifulsoup4",
        "@pip//pyyaml",
    ],
)

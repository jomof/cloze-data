load("@rules_python//python:defs.bzl", "py_binary", "py_library")

exports_files([
    "zip_files.py",
    "process_zip_stream.py",
    "unzip_files.py",
])

py_binary(
    name = "process_zip_stream",
    srcs = ["process_zip_stream.py"],
    visibility = ["//:__subpackages__"],
)

py_binary(
    name = "unzip_files",
    srcs = ["unzip_files.py"],
    visibility = ["//:__subpackages__"],
)

py_binary(
    name = "zip_files",
    srcs = ["zip_files.py"],
    visibility = ["//:__subpackages__"],
)

py_library(
    name = "zip_rules",
    srcs = [
        "process_zip_stream.py",
        "unzip_files.py",
        "zip_files.py",
    ],
    visibility = ["//:__subpackages__"],
)

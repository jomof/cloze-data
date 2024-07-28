load("@rules_python//python:defs.bzl", "py_binary", "py_library")

# json_rules/BUILD
exports_files([
    "concat_json_arrays.py",
    "check_json_array_distinct.py",
    "concat_multiple_file_contents.py",
])

py_binary(
    name = "concat_json_arrays",
    srcs = ["concat_json_arrays.py"],
    visibility = ["//:__subpackages__"],
)

py_binary(
    name = "concat_multiple_file_contents",
    srcs = ["concat_multiple_file_contents.py"],
    visibility = ["//:__subpackages__"],
    deps = ["@pip//pyyaml"],
)

py_library(
    name = "json_rules",
    srcs = [
        "check_json_array_distinct.py",
        "concat_json_arrays.py",
        "concat_multiple_file_contents.py",
    ],
    visibility = ["//:__subpackages__"],
    deps = ["@pip//pyyaml"],
)

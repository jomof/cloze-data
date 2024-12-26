load("@rules_python//python:defs.bzl", "py_binary", "py_library")

py_library(
    name = "memoize",
    srcs = [
        "memoize_to_disk.py",
    ],
    visibility = ["//visibility:public"],
)

# Execute the cache service: bazel run //python/utils/build_cache:cache-service
py_binary(
    name = "cache-service",
    srcs = ["cache-service.py"],
    visibility = ["//visibility:public"],
    deps = [
        "@pip//aiofiles",
    ],
)

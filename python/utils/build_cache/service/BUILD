load("@rules_python//python:defs.bzl", "py_binary", "py_library")

# Execute the cache service: bazel run //python/utils/build_cache/service:cache-service
py_binary(
    name = "cache-service",
    srcs = ["cache-service.py"],
    visibility = ["//visibility:public"],
)

py_library(
    name = "service",
    srcs = ["cache-service.py"],
    visibility = ["//:__subpackages__"],
)

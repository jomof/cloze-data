filegroup(
    name = "bunpro-sample",
    srcs = glob(["sample/*"]),
    visibility = ["//visibility:public"],
)

filegroup(
    name = "bunpro-all",
    srcs = glob(["all/*"]),
    visibility = ["//visibility:public"],
)

# bazel run //resources/original/bunpro:more-samples
sh_binary(
    name = "more-samples",
    srcs = ["sample.sh"],
    visibility = ["//visibility:public"],
)

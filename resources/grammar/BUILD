load("//python_rules:python_build.bzl", "py_build_tool_stream")


py_build_tool_stream(
    name = "bs4-stripped",
    srcs = ["//resources/original/bunpro:bunpro-sample"], 
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

py_build_tool_stream(
    name = "yaml-cleaned",
    srcs = [":ai-cleaned"],
    extension = ".yaml",
    script = "yaml-clean.py",
)
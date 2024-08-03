load("@rules_python//python:defs.bzl", "py_binary", "py_library")
load("//python_rules:python_build.bzl", "py_build_tool", "py_build_tool_stream")

py_build_tool_stream(
    name = "bs4-stripped-sample",
    srcs = ["//resources/original/bunpro:bunpro-sample"],
    tool = ":bs4-strip",
)

py_build_tool_stream(
    name = "bs4-stripped-all",
    srcs = ["//resources/original/bunpro:bunpro-all"],
    tool = ":bs4-strip",
)

py_build_tool_stream(
    name = "extracted-yaml-sample",
    srcs = [":bs4-stripped-sample"],
    extension = ".yaml",
    tool = ":extract-yaml",
)

py_build_tool_stream(
    name = "extracted-yaml-all",
    srcs = [":bs4-stripped-all"],
    extension = ".yaml",
    tool = ":extract-yaml",
)

py_build_tool_stream(
    name = "fixed-yaml-sample",
    srcs = [":extracted-yaml-sample"],
    data = ["bunpro-grammar-fixes.yaml"],
    tool = ":fixup-bunpro-grammar",
)

py_build_tool_stream(
    name = "fixed-yaml-all",
    srcs = [":extracted-yaml-all"],
    data = ["bunpro-grammar-fixes.yaml"],
    tool = ":fixup-bunpro-grammar",
)


genrule(
    name = "fixed-yaml-all-list",
    srcs = [":fixed-yaml-all"],
    outs = ["fixed-yaml-all-list.txt"],
    cmd = "for file in $(SRCS); do echo $$file >> $(OUTS); done",
)


py_build_tool(
    name = "lint-bunpro",
    outs = ["lint-bunpro-report.txt"],
    ins = [":fixed-yaml-all"],
    main = ":bunpro-lint",
)

py_build_tool_stream(
    name = "ai-cleaned-sample",
    srcs = [":fixed-yaml-sample"],
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
        ":grammar",
        "@pip//google_generativeai",
        "@pip//pyyaml",
    ],
)

py_binary(
    name = "bs4-strip",
    srcs = ["bs4-strip.py"],
    visibility = ["//:__subpackages__"],
    deps = [
        ":grammar",
        "@pip//beautifulsoup4",
        "@pip//pyyaml",
    ],
)

py_binary(
    name = "bunpro-lint",
    srcs = ["bunpro-lint.py"],
    visibility = ["//:__subpackages__"],
    deps = ["@pip//pyyaml"],
)

py_binary(
    name = "extract-grammar-point-names",
    srcs = ["extract-grammar-point-names.py"],
    visibility = ["//:__subpackages__"],
    deps = [
        ":grammar",
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
    name = "fixup-bunpro-grammar",
    srcs = ["fixup-bunpro-grammar.py"],
    visibility = ["//:__subpackages__"],
    deps = [
        ":grammar",
        "@pip//pyyaml",
    ],
)

py_binary(
    name = "yaml-clean",
    srcs = ["yaml-clean.py"],
    visibility = ["//:__subpackages__"],
    deps = [
        ":grammar",
        "@pip//pyyaml",
    ],
)

py_library(
    name = "grammar",
    srcs = [
        "ai-clean.py",
        "bs4-strip.py",
        "bunpro-lint.py",
        "dumpyaml.py",
        "extract-grammar-point-names.py",
        "extract-yaml.py",
        "fixup-bunpro-grammar.py",
        "yaml-clean.py",
    ],
    visibility = ["//:__subpackages__"],
    deps = [
        "@pip//beautifulsoup4",
        "@pip//google_generativeai",
        "@pip//pyyaml",
    ],
)

load("@rules_python//python:defs.bzl", "py_binary", "py_library")
load("//file_rules:file_rules.bzl", "write_file_list")
load("//python_rules:python_build.bzl", "py_build_tool", "py_build_tool_stream")

py_build_tool_stream(
    name = "bs4-stripped-sample",
    srcs = ["//resources/original/bunpro:bunpro-sample"],
    tool = ":bs4-strip",
)

py_build_tool_stream(
    name = "create-bs4-stripped-all",
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
    name = "create-extracted-yaml-all",
    srcs = [":create-bs4-stripped-all"],
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
    name = "create-bunpro-fixed-yaml-all",
    srcs = [":create-extracted-yaml-all"],
    data = ["bunpro-grammar-fixes.yaml"],
    tool = ":fixup-bunpro-grammar",
)

filegroup(
    name = "bunpro-fixed-yaml-all",
    srcs = glob(["files/bunpro-fixed-yaml-all/**"]),
)

write_file_list(
    name = "bunpro-fixed-yaml-all-list",
    srcs = [":bunpro-fixed-yaml-all"],
    out = "bunpro-fixed-yaml-all-list.txt",
)

write_file_list(
    name = "dojg-yaml-list",
    srcs = ["//resources/original/dojg:dojg-all"],
    out = "dojg-yaml-list.txt",
)

py_build_tool(
    name = "merge-bunpro-dojg",
    outs = ["xxx.yaml"],
    out_dirs = ["merged-grammars"],
    ins = [
        "bunpro-fixed-yaml-all-list.txt",
        "dojg-yaml-list.txt",
    ],
    main = ":merge-grammars",
    deps = [
        ":bunpro-fixed-yaml-all",
        "//resources/original/dojg:dojg-all",
    ],
)

py_build_tool(
    name = "lint-bunpro",
    outs = ["lint-bunpro-report.txt"],
    ins = [":bunpro-fixed-yaml-all"],
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
        "@pip//google_genai",
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
    name = "merge-grammars",
    srcs = ["merge-grammars.py"],
    visibility = ["//:__subpackages__"],
    deps = ["@pip//pyyaml"],
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
        "merge-grammars.py",
        "yaml-clean.py",
    ],
    visibility = ["//:__subpackages__"],
    deps = [
        "@pip//beautifulsoup4",
        "@pip//google_generativeai",
        "@pip//pyyaml",
    ],
)

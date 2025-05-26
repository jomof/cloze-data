load("@rules_python//python:defs.bzl", "py_binary", "py_library")
load("//python_rules:python_build.bzl", "py_build_tool")

genrule(
    name = "jmdict-unzip",
    srcs = ["JMdict_e_examp.gz"],
    outs = ["JKMdict_e_examp"],
    cmd = "gunzip -k -c $(SRCS) > $(OUTS)",
)

py_build_tool(
    name = "jmdict-sentences",
    outs = ["jmdict-sentences.json"],
    ins = ["JKMdict_e_examp"],
    main = ":sentences",
    visibility = ["//visibility:public"],
)

py_build_tool(
    name = "jmdict-words",
    outs = ["jmdict-words.json"],
    ins = ["JKMdict_e_examp"],
    main = ":words",
    visibility = ["//visibility:public"],
)

py_binary(
    name = "sentences",
    srcs = ["sentences.py"],
    visibility = ["//:__subpackages__"],
)

# bazel build //resources/original/jmdict:jmdict-words
py_binary(
    name = "words",
    srcs = ["words.py"],
    visibility = ["//:__subpackages__"],
)

py_library(
    name = "jmdict",
    srcs = ["sentences.py"],
    visibility = ["//:__subpackages__"],
)

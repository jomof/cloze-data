load("@rules_python//python:defs.bzl", "py_binary", "py_library")

#load("//zip_rules:zip.bzl", "process_zip_stream", "process_zip_stream_2", "unzip_files", "zip_manifest")
load("//python_rules:python_build.bzl", "py_batch_build_tool")
load(":junk.bzl", "number_files")

number_files(
    name = "bunpro-grammar-points",
    srcs = glob(["sample/*"]),
)

py_binary(
    name = "bs4-strip",
    main = "bs4-strip.py",
    srcs = ["bs4-strip.py"],
)

genrule(
    name = "run-bs4-strip",
    srcs = [":bs4-strip"],
    outs = ["output_file.txt"],
    cmd = "$(locations :bs4-strip) > $@",
)

# py_batch_build_tool(
#     name = "bunpro-grammar-points-stripped",
#     srcs = [":bunpro-grammar-points"],
#     script = ":my_script",
# )

# hash_link(
#     manifest = "grammar-points.manifest",
#     srcs = glob(["sample/*"])
# )

# process_zip_stream_2(
#     name = "stripped-bunpro-grammar-points",
#     manifest = "grammar-points.manifest",
#     src = "grammar-points-small.zip",
#     script = "html-strip.py",
# )

# process_zip_stream(
#     name = "formatted-bunpro-grammar-points",
#     src = ":stripped-bunpro-grammar-points",
#     script = "bs4-strip.py",
# )

# unzip_files(
#     name = "stripped-bunpro-grammar-points-unzipped",
#     src = ":stripped-bunpro-grammar-points",
# )

# unzip_files(
#     name = "formatted-bunpro-grammar-points-unzipped",
#     src = ":formatted-bunpro-grammar-points",
# )

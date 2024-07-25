load("//zip_rules:zip.bzl", "process_zip_stream")
load("//zip_rules:zip.bzl", "unzip_files")

process_zip_stream(
    name = "stripped-bunpro-grammar-points",
    script = "html-strip.py",
    src = "grammar-points-small.zip"
)

process_zip_stream(
    name = "formatted-bunpro-grammar-points",
    script = "bs4-strip.py",
    src = ":stripped-bunpro-grammar-points"
)

unzip_files(
    name = "stripped-bunpro-grammar-points-unzipped",
    src = ":stripped-bunpro-grammar-points"
)

unzip_files(
    name = "formatted-bunpro-grammar-points-unzipped",
    src = ":formatted-bunpro-grammar-points"
)

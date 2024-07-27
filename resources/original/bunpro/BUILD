load("//zip_rules:zip.bzl", "process_zip_stream", "unzip_files")

process_zip_stream(
    name = "stripped-bunpro-grammar-points",
    src = "grammar-points.zip",
    script = "html-strip.py",
)

process_zip_stream(
    name = "formatted-bunpro-grammar-points",
    src = ":stripped-bunpro-grammar-points",
    script = "bs4-strip.py",
)

unzip_files(
    name = "stripped-bunpro-grammar-points-unzipped",
    src = ":stripped-bunpro-grammar-points",
)

unzip_files(
    name = "formatted-bunpro-grammar-points-unzipped",
    src = ":formatted-bunpro-grammar-points",
)

load("//zip_rules:zip.bzl", "process_zip_stream")

process_zip_stream(
    name = "stripped-bunpro-grammar-points",
    script = "html-strip.py",
    zip_in = "grammar-points-small.zip",
    zip_out = "stripped-bunpro-grammar-points.zip",
)

process_zip_stream(
    name = "formatted-bunpro-grammar-points",
    script = "bs4-strip.py",
    zip_in = ":stripped-bunpro-grammar-points",
    zip_out = "formatted-bunpro-grammar-points.zip",
)

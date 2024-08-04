def _write_file_list_impl(ctx):
    output_file = ctx.outputs.out
    input_files = ctx.files.srcs

    # Create the content of the output file with the list of input files
    content = "\n".join([f.path for f in input_files])

    # Write the content to the output file
    ctx.actions.write(
        output = output_file,
        content = content,
    )

write_file_list = rule(
    implementation = _write_file_list_impl,
    attrs = {
        "srcs": attr.label_list(allow_files = True),
        "out": attr.output(mandatory = True),
    },
)

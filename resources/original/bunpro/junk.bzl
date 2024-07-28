def _number_files(ctx):
    input_files = ctx.files.srcs

    i = 0
    numbered_files = []
    for input_file in input_files:
        numbered = "{}#/{}".format(ctx.attr.name, i)
        numbered_file = ctx.actions.declare_file(numbered)
        numbered_files.append(numbered_file)
        ctx.actions.symlink(
            output = numbered_file,
            target_file = input_file,
        )
        i += 1

    return [DefaultInfo(files = depset(numbered_files))]

number_files = rule(
    implementation = _number_files,
    attrs = {
        "srcs": attr.label_list(allow_files = True, mandatory = True),
    },
)

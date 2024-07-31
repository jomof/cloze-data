def py_build_tool(
        name,
        main,
        outs,
        ins = [],
        deps = [],
        visibility = []):
    """
    A custom Bazel rule to run a Python script with specified input and output files.

    Args:
        name (str): The name of the genrule.
        main (str): The main Python script to run.
        outs (list): List of output files.
        ins (list): List of input files (default is an empty list).
        deps (list): List of dependencies (default is an empty list).
        visibility (list): List of visibility rules (default is an empty list).
    """

    # Generate the locations for the main script, input files, and output files
    main_location = "$(location " + main + ")"
    in_locations = " ".join(["$(locations " + arg + ")" for arg in ins])
    out_locations = " ".join(["$(locations " + arg + ")" for arg in outs])

    # Define the genrule with the provided arguments
    native.genrule(
        name = name,
        srcs = deps + ins,
        outs = outs,
        cmd = main_location + " " + in_locations + " " + out_locations,
        visibility = visibility,
        tools = [main],
    )

def _py_build_tool_stream_impl(ctx):
    srcs = ctx.files.srcs
    extension = ctx.attr.extension

    outs = []
    for i, src in enumerate(srcs):
        numbered_output = ctx.actions.declare_file("{}/{}-{}{}".format(ctx.label.name, ctx.label.name, i, extension))
        outs.append(numbered_output)
        ctx.actions.run(
            inputs = [src] + ctx.files.data,
            outputs = [numbered_output],
            executable = ctx.executable.tool,
            arguments = [src.path, numbered_output.path] + [df.path for df in ctx.files.data],
            use_default_shell_env = True,
            progress_message = "{} {}".format(ctx.label.name, src.basename),
            tools = [ctx.executable.tool],  # This should be a list
        )
    return [DefaultInfo(files = depset(outs))]

py_build_tool_stream = rule(
    implementation = _py_build_tool_stream_impl,
    attrs = {
        "srcs": attr.label_list(allow_files = True),
        "script": attr.label(allow_single_file = True),
        "extension": attr.string(default = ""),
        "tool": attr.label(
            allow_files = True,
            executable = True,
            cfg = "exec",
        ),
        "data": attr.label_list(
            allow_files = True,
            default = [],
        ),
    },
)

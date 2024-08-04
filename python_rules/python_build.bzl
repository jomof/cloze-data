def _py_build_tool_impl(ctx):
    # Generate the locations for the main script, input files, and output files
    main = ctx.executable.main.path
    ins = [f.path for f in ctx.files.ins]
    outs = [f.path for f in ctx.outputs.outs]
    out_dirs = [ctx.actions.declare_directory("{}".format(f)) for f in ctx.attr.out_dirs]
    out_dirs_paths = [f.path for f in out_dirs]
    
    args = ctx.actions.args()
    args.add_all(ctx.files.ins)
    args.add_all(ctx.outputs.outs)
    args.add_all(out_dirs_paths)

    # Execute the command
    all_outs = ctx.outputs.outs + out_dirs

    ctx.actions.run(
        outputs = all_outs,
        inputs = ctx.files.ins + [ctx.executable.main] + ctx.files.deps,
        arguments = [args],
        executable = ctx.executable.main,
        progress_message = "{}".format(ctx.label.name),
    )
    return [DefaultInfo(files = depset(all_outs))]

py_build_tool = rule(
    implementation = _py_build_tool_impl,
    attrs = {
        "main": attr.label(allow_files = True, executable = True, cfg = "exec"),
        "outs": attr.output_list(mandatory = True),
        "out_dirs": attr.string_list(),
        "ins": attr.label_list(allow_files = True),
        "deps": attr.label_list(),
    },
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

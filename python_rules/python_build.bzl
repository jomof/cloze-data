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
        "deps": attr.label_list(),
        "ins": attr.label_list(allow_files = True),
        "main": attr.label(allow_files = True, executable = True, cfg = "exec"),
        "out_dirs": attr.string_list(),
        "outs": attr.output_list(mandatory = True),
    },
)

def _py_build_tool_stream_impl(ctx):
    srcs = ctx.files.srcs
    extension = ctx.attr.extension

    outs = []
    for src in srcs:
        base_name = src.basename
        if "." in base_name:
            base_name = base_name[:base_name.rindex(".")]

        output_file = ctx.actions.declare_file(
            "{}/{}{}".format(ctx.label.name, base_name, extension),
        )
        outs.append(output_file)
        arguments = [
                        "--source={}".format(src.path),
                        "--destination={}".format(output_file.path),
                    ]
        arguments.extend(["--data={}".format(df.path) for df in ctx.files.data])
        if ctx.attr.pass_target_name:
            arguments.append("--bazel-target={}".format(ctx.label.name))

        ctx.actions.run(
            inputs = [src] + ctx.files.data,
            outputs = [output_file],
            executable = ctx.executable.tool,
            arguments = arguments,
            use_default_shell_env = True,
            progress_message = "{} processing {}".format(ctx.label.name, src.basename),
            tools = [ctx.executable.tool],
        )

    return [DefaultInfo(files = depset(outs))]

py_build_tool_stream = rule(
    implementation = _py_build_tool_stream_impl,
    attrs = {
        "data": attr.label_list(
            allow_files = True,
            default = [],
        ),
        "extension": attr.string(default = ""),
        "pass_target_name": attr.bool(default = False),
        "script": attr.label(allow_single_file = True),
        "srcs": attr.label_list(allow_files = True),
        "tool": attr.label(
            allow_files = True,
            executable = True,
            cfg = "exec",
        ),
    },
)

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
    # Collect sources, optionally limiting to top N
    srcs = ctx.files.srcs
    top_n = ctx.attr.top
    if top_n and top_n > 0:
        srcs = srcs[:top_n]

    extension = ctx.attr.extension

    # correlated: list of Files; we’ll derive keys from each file’s parent directory
    correlated_files = ctx.files.correlated

    # constant inputs & flags
    non_src_inputs = ctx.files.data + ctx.files.deps
    data_args = ["--data={}".format(df.path) for df in ctx.files.data]

    # group correlated files by stem
    correlated_by_stem = {}
    for cf in correlated_files:
        stem = cf.basename
        if "." in stem:
            stem = stem[:stem.rindex(".")]
        correlated_by_stem.setdefault(stem, []).append(cf)

    filters = ctx.attr.filter
    if filters:
        def matches_any_filter(src):
            for f in filters:
                if f in src.basename:
                    return True
            return False

        srcs = [src for src in srcs if matches_any_filter(src)]

    outs = []
    for src in srcs:
        stem = src.basename
        if "." in stem:
            stem = stem[:stem.rindex(".")]

        output_file = ctx.actions.declare_file(
            "{}/{}{}".format(ctx.label.name, stem, extension),
        )
        outs.append(output_file)

        arguments = [
            "--source={}".format(src.path),
            "--destination={}".format(output_file.path),
        ]
        arguments.extend(data_args)
        if ctx.attr.pass_target_name:
            arguments.append("--bazel-target={}".format(ctx.label.name))

        arguments.extend(ctx.attr.args)

        matches = correlated_by_stem.get(stem, [])
        for cf in matches:
            parent_path = cf.path
            parent_dir = parent_path[:parent_path.rfind("/")]
            key = parent_dir[parent_dir.rfind("/") + 1:]
            arguments.append("--{}={}".format(key, cf.path))

        ctx.actions.run(
            inputs = [src] + non_src_inputs + matches,
            outputs = [output_file],
            executable = ctx.executable.tool,
            arguments = arguments,
            use_default_shell_env = True,
            progress_message = "{} processing {}".format(ctx.label.name, src.basename),
            tools = [ctx.executable.tool],
            execution_requirements = {"no-sandbox": "1"},
        )

    return [DefaultInfo(files = depset(outs))]

py_build_tool_stream = rule(
    implementation = _py_build_tool_stream_impl,
    attrs = {
        "args": attr.string_list(),
        "correlated": attr.label_list(allow_files = True, default = []),
        "data": attr.label_list(allow_files = True, default = []),
        "deps": attr.label_list(allow_files = True, default = []),
        "extension": attr.string(default = ""),
        "filter": attr.string_list(
            # TODO: implement filtering by basename
            default = [],
            doc = "List of strings to filter srcs by whether their basename contains one of the filter strings. If empty, no filtering is applied.",
        ),
        "pass_target_name": attr.bool(default = False),
        "script": attr.label(allow_single_file = True),
        "srcs": attr.label_list(allow_files = True),
        "tool": attr.label(allow_files = True, executable = True, cfg = "exec"),
        "top": attr.int(default = 0),  # if >0, only process first N srcs
    },
)

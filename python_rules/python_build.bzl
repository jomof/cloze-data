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

    # correlated: list of Files; we’ll derive keys from each file’s parent directory
    correlated_files = ctx.files.correlated  # list of File

    # constant inputs & flags
    non_src_inputs = ctx.files.data + ctx.files.deps
    data_args = ["--data={}".format(df.path) for df in ctx.files.data]

    # group correlated files by their stem (filename without extension)
    correlated_by_stem = {}
    for cf in correlated_files:
        stem = cf.basename
        if "." in stem:
            stem = stem[:stem.rindex(".")]
        correlated_by_stem.setdefault(stem, []).append(cf)

    outs = []
    for src in srcs:
        # derive this src’s stem (for matching)
        stem = src.basename
        if "." in stem:
            stem = stem[:stem.rindex(".")]

        # declare its output
        output_file = ctx.actions.declare_file(
            "{}/{}{}".format(ctx.label.name, stem, extension),
        )
        outs.append(output_file)

        # base arguments for this run
        arguments = [
            "--source={}".format(src.path),
            "--destination={}".format(output_file.path),
        ]
        arguments.extend(data_args)
        if ctx.attr.pass_target_name:
            arguments.append("--bazel-target={}".format(ctx.label.name))

        # find correlated files matching this src
        matches = correlated_by_stem.get(stem, [])
        if matches:
            for cf in matches:
                # derive key from cf's parent directory name
                parent_path = cf.path
                # strip filename
                parent_dir = parent_path[: parent_path.rfind("/")] if "/" in parent_path else ""
                # get last component as key
                key = parent_dir[parent_dir.rfind("/") + 1 :] if "/" in parent_dir else parent_dir
                arguments.append("--{}={}".format(key, cf.path))

        # run for this src
        ctx.actions.run(
            inputs            = [src] + non_src_inputs + matches,
            outputs           = [output_file],
            executable        = ctx.executable.tool,
            arguments         = arguments,
            use_default_shell_env = True,
            progress_message  = "{} processing {}".format(ctx.label.name, src.basename),
            tools             = [ctx.executable.tool],
            execution_requirements = {"no-sandbox": "1"},
        )

    return [DefaultInfo(files = depset(outs))]

py_build_tool_stream = rule(
    implementation = _py_build_tool_stream_impl,
    attrs = {
        "data":            attr.label_list(allow_files = True, default = []),
        "extension":       attr.string(default = ""),
        "pass_target_name": attr.bool(default = False),
        "script":          attr.label(allow_single_file = True),
        "srcs":            attr.label_list(allow_files = True),
        "tool":            attr.label(allow_files = True, executable = True, cfg = "exec"),
        "deps":            attr.label_list(),
        # correlated is a flat list; key derived from folder
        "correlated":      attr.label_list(allow_files = True, default = []),
    },
)

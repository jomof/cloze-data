def py_build_tool(
        name,
        main,
        outs,
        ins = [],
        deps = [],
        visibility = []):
    main_location = "$(location " + main + ")"
    in_locations = " ".join(["$(location " + arg + ")" for arg in ins])
    out_locations = " ".join(["$(location " + arg + ")" for arg in outs])
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
    user_script = ctx.file.script
    extension = ctx.attr.extension

    outs = []
    for i, src in enumerate(srcs):
        numbered_output = ctx.actions.declare_file("{}/#/{}{}".format(ctx.label.name, i, extension))
        outs.append(numbered_output)
        ctx.actions.run(
            inputs=[src, user_script],
            outputs=[numbered_output],
            executable=user_script.path,
            arguments=[src.path, numbered_output.path],
            use_default_shell_env=True,
            progress_message="{} {}".format(user_script.basename, src.basename),
        )
    return [DefaultInfo(files=depset(outs))]

py_build_tool_stream = rule(
    implementation=_py_build_tool_stream_impl,
    attrs={
        "srcs": attr.label_list(allow_files=True),
        "script": attr.label(allow_single_file=True),
        "extension": attr.string(default=""),
    },
)
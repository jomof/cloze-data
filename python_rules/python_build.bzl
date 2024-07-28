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
        srcs = ["//python_rules:call_python.sh", main] + deps + ins,
        outs = outs,
        cmd = "$(location //python_rules:call_python.sh) " + main_location + " " + in_locations + " " + out_locations,
        visibility = visibility,
    )

def _py_batch_build_tool(ctx):
    input_files = ctx.files.srcs
    output_files = []
    user_script = ctx.file.script

    for input_file in input_files:
        output_file = ctx.actions.declare_file(input_file.basename + ".out")
        output_files.append(output_file)

        ctx.actions.run(
            inputs = [input_file, user_script, ctx.executable._call_python],
            outputs = [output_file],
            executable = ctx.executable._call_python,
            arguments = [
                user_script.path,
                "required",
                input_file.path,
                output_file.path,
            ],
        )

    # Return the DefaultInfo provider with the output files
    return [DefaultInfo(files = depset(output_files))]

py_batch_build_tool = rule(
    implementation = _py_batch_build_tool,
    attrs = {
        "srcs": attr.label_list(allow_files = True, mandatory = True),
        "script": attr.label(allow_single_file = True, mandatory = True),
        "_call_python": attr.label(
            default = Label("//python_rules:call_python.sh"),
            allow_single_file = True,
            executable = True,
            cfg = "host",
        ),
    },
)

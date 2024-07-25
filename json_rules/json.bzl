def _json_concat_impl(ctx):
    # Define the output file
    output_file = ctx.outputs.output
    
    # Collect the paths of all input JSON files
    input_files = [f.path for f in ctx.files.srcs]
    
    # Path to the Python script
    script_file = ctx.executable._concat_script
    
    # Run the Python script to concatenate JSON arrays
    ctx.actions.run(
        inputs=ctx.files.srcs + [script_file],
        outputs=[output_file],
        executable="python",
        arguments=[script_file.path, output_file.path] + input_files,
        use_default_shell_env=True,
    )

    return [DefaultInfo(files=depset([output_file]))]

json_concat = rule(
    implementation=_json_concat_impl,
    attrs={
        "srcs": attr.label_list(allow_files=[".json"]),  # Allow only JSON files as input
        "output": attr.output(),  # Specify the output attribute
        "_concat_script": attr.label(
            default = Label("//json_rules:concat_json_arrays.py"),  # Update the label to the new package
            executable = True,
            cfg = "host",
            allow_files = True,
        ),
    },
)

def _check_json_array_distinct_test_impl(ctx):
    script_file = ctx.attr._script
    json_file = ctx.attr.json
    required_key = ctx.attr.keyField
    validation_output = ctx.actions.declare_file(ctx.attr.name + ".validation")

    ctx.actions.write(ctx.outputs.main, "main output\n")
    ctx.actions.write(ctx.outputs.implicit, "implicit output\n")

    ctx.actions.run(
        # inputs=[script_file, input_file],
        outputs=[validation_output],
        executable='python',
        arguments=[script_file, required_key, json_file]
        # use_default_shell_env=True
    )
    return [
        DefaultInfo(files = depset([ctx.outputs.main])),
        OutputGroupInfo(_validation = depset([validation_output])),
    ]

check_json_array_distinct_test = rule(
    implementation=_check_json_array_distinct_test_impl,
    attrs={
        "json": attr.label(allow_single_file=True),
        "keyField": attr.string(),
        "_script": attr.label(
            allow_single_file = True,
            executable = True,
            default = Label("//json_rules:check_json_array_distinct.py"),
            cfg = "exec"
        ),
    },
    test=True,
)

def _concat_multiple_file_contents_impl(ctx):
    # Define the output file
    output_file = ctx.outputs.output
    
    # Collect the paths of all input files
    input_files = [f.path for f in ctx.files.srcs]
    
    # Path to the Python script
    script_file = ctx.executable._concat_script
    
    # Run the Python script to concatenate file contents into a JSON
    ctx.actions.run(
        inputs=ctx.files.srcs + [script_file],
        outputs=[output_file],
        executable="python",
        arguments=[script_file.path, output_file.path] + input_files,
        use_default_shell_env=True,
    )

    return [DefaultInfo(files=depset([output_file]))]

concat_multiple_file_contents = rule(
    implementation=_concat_multiple_file_contents_impl,
    attrs={
        "srcs": attr.label_list(allow_files=True),  # Allow any file types as input
        "output": attr.output(),  # Specify the output attribute
        "_concat_script": attr.label(
            default = Label("//json_rules:concat_multiple_file_contents.py"),  # Update the label to the script's path
            executable = True,
            cfg = "host",
            allow_files = True,
        ),
    },
)


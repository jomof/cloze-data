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

    # Return DefaultInfo with the output file
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

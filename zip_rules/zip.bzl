def _zip_files_impl(ctx):
    # Define the output file
    output_file = ctx.outputs.output

    # Collect the paths of all input files
    input_files = [f.path for f in ctx.files.srcs]

    # Path to the Python script
    script_file = ctx.executable._zip_script

    # Run the Python script to concatenate file contents into a JSON
    ctx.actions.run(
        inputs = ctx.files.srcs + [script_file],
        outputs = [output_file],
        executable = "python",
        arguments = [script_file.path, output_file.path] + input_files,
        use_default_shell_env = True,
    )

    return [DefaultInfo(files = depset([output_file]))]

zip_files = rule(
    implementation = _zip_files_impl,
    attrs = {
        "srcs": attr.label_list(allow_files = True),  # Allow any file types as input
        "output": attr.output(),  # Specify the output attribute
        "_zip_script": attr.label(
            default = Label("//zip_rules:zip_files.py"),
            executable = True,
            cfg = "host",
            allow_files = True,
        ),
    },
)

def _unzip_files_impl(ctx):
    # Define the input ZIP file
    input_file = ctx.file.src

    # Define the output directory
    if ctx.attr.output:
        output_dir = ctx.outputs.output
    else:
        out_name = ctx.label.name + ".dir"
        output_dir = ctx.actions.declare_directory(out_name)

    # Path to the Python script
    script_file = ctx.executable._unzip_script

    # Run the Python script to unzip the contents
    ctx.actions.run(
        inputs = [input_file, script_file],
        outputs = [output_dir],
        executable = script_file.path,
        arguments = [input_file.path, output_dir.path],
        use_default_shell_env = True,
    )

    return [DefaultInfo(files = depset([output_dir]))]

unzip_files = rule(
    implementation = _unzip_files_impl,
    attrs = {
        "src": attr.label(allow_single_file = True),  # Specify the input ZIP file
        "output": attr.output(),  # Specify the output directory attribute
        "_unzip_script": attr.label(
            default = Label("//zip_rules:unzip_files.py"),
            executable = True,
            cfg = "host",
            allow_files = True,
        ),
    },
)

def _process_zip_stream_impl(ctx):
    src = ctx.file.src
    process_zip_stream = ctx.executable._script
    user_script = ctx.file.script
    if ctx.attr.zip_out:
        zip_out = ctx.outputs.zip_out
    else:
        zip_out_name = ctx.label.name + ".zip"
        zip_out = ctx.actions.declare_file(zip_out_name)

    ctx.actions.run(
        inputs = [src, user_script, process_zip_stream],
        outputs = [zip_out],
        executable = process_zip_stream,
        arguments = [src.path, zip_out.path, user_script.path],
        use_default_shell_env = True,
    )

    return [DefaultInfo(files = depset([zip_out]))]

process_zip_stream = rule(
    implementation = _process_zip_stream_impl,
    attrs = {
        "src": attr.label(allow_single_file = True),
        "script": attr.label(allow_single_file = True),
        "zip_out": attr.output(),
        "_script": attr.label(
            default = Label("//zip_rules:process_zip_stream.py"),
            executable = True,
            cfg = "host",
            allow_files = True,
        ),
    },
)

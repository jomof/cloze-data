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

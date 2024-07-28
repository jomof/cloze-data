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
        tools = [main]
    )

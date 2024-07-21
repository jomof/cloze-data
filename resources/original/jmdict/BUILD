
genrule(
    name = "jmdict",
    srcs = ["JMdict_e_examp.gz"],
    outs = ["JKMdict_e_examp"],
    cmd = "gunzip -k -c $(SRCS) > $(OUTS)",
)

genrule(
    name = "jmdict-sentences",
    srcs = ["sentences.py", "JKMdict_e_examp"],
    outs = ["jmdict-sentences.json"],
    cmd = "python $(SRCS) $(OUTS)",
    visibility = ["//visibility:public"],
)


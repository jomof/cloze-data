def annotate_vocab(name,level):
  native.genrule(
    name = name,
    srcs = ["annotate_vocab.py", "jlpt-"+level+"-vocab.txt"],
    outs = ["jlpt-"+level+"-vocab.json"],
    cmd = "python $(SRCS) $(OUTS) "+level,
)
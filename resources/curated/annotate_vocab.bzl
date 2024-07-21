def annotate_vocab(level, visibility=None):
  native.genrule(
    name = "jlpt-"+level+"-vocab-json",
    srcs = ["annotate_vocab.py", "jlpt-"+level+"-vocab.txt"],
    outs = ["jlpt-"+level+"-vocab.json"],
    cmd = "python $(SRCS) $(OUTS) "+level,
)
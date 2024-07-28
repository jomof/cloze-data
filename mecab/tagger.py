import MeCab
import os

def get_mecab_tagger():
    dicdir = "/home/codespace/.python/current/lib/python3.10/site-packages/unidic/dicdir"
    if not os.path.exists(dicdir): raise ValueError(f"Unidic not found at {dicdir}")
    return MeCab.Tagger('-r "{}" -d "{}"'.format(f"{dicdir}/mecabrc", dicdir))

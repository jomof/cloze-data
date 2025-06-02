import MeCab
import unidic
import os

tagger = None

def get_mecab_tagger():
    global tagger
    if not tagger:
        unidic.DICDIR = "/usr/local/python/3.10.13/lib/python3.10/site-packages/unidic/dicdir"
        if not os.path.isdir(unidic.DICDIR):
            unidic.DICDIR = "/usr/local/lib/python3.10/dist-packages/unidic/dicdir"
        if not os.path.isdir(unidic.DICDIR):
            unidic.DICDIR = "/usr/local/python/3.12.1/lib/python3.12/site-packages/unidic/dicdir"

        tagger = MeCab.Tagger('-d "{}"'.format(unidic.DICDIR))
    return tagger

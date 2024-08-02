import MeCab
import os
import unidic

def get_mecab_tagger():
    unidic.DICDIR = "unidic/dicdir"
    return MeCab.Tagger('-d "{}"'.format(unidic.DICDIR))

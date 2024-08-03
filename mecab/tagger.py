import MeCab
import unidic

def get_mecab_tagger():
    unidic.DICDIR = "/usr/local/python/3.10.13/lib/python3.10/site-packages/unidic/dicdir"
    return MeCab.Tagger('-d "{}"'.format(unidic.DICDIR))

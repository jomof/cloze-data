import MeCab
import unidic
import os

def get_mecab_tagger():
    unidic.DICDIR = "/usr/local/python/3.10.13/lib/python3.10/site-packages/unidic/dicdir"
    if not os.path.isdir(unidic.DICDIR):
        unidic.DICDIR = "/usr/local/lib/python3.10/dist-packages/unidic/dicdir"
    
    return MeCab.Tagger('-d "{}"'.format(unidic.DICDIR))

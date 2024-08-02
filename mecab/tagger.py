import MeCab
import os

def get_mecab_tagger():
    worskpace = os.environ.get('BUILD_WORKSPACE_DIRECTORY', os.getcwd())
    dicdir = f"{worskpace}/unidic/dicdir"
    if not os.path.exists(dicdir): raise ValueError(f"Unidic not found at {dicdir}")
    return MeCab.Tagger('-r "{}" -d "{}"'.format(f"{dicdir}/mecabrc", dicdir))

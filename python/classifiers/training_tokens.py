import re
from python.mecab.compact_sentence import japanese_to_compact_sentence



def prepare_sentence_for_tokenization(text: str) -> str:
    """
    Parses the augmented text and creates a clean 'word_pos' sequence.
    Example: '⌈ˢ机ᵖnʳツクエ⌉' -> '机_n'
    """

    # Strip grammar denoting brackets.
    text = text.replace('{', '').replace('}', '')

    # If it looks like a plain japanese sentence, then convert to compact
    if '⌈' not in text:
        text = japanese_to_compact_sentence(text)

    # This regex is an example to find all augmented words. You may need to refine it.
    # It looks for the surface form (ˢ...) and the part-of-speech (ᵖ...).
    pattern = re.compile(r'⌈ˢ(?P<surface>.+?)ᵖ(?P<pos>.+?)ʳ.+?(?P<last>.?)⌉')
    
    # Function to replace each match with the 'word_pos' format, now with leading/trailing spaces
    def repl(match):
        surface = match.group('surface')
        pos = match.group('pos')
        last = match.group('last')
        # Clean up the POS tag (e.g., 'v' instead of 'vb') if necessary
        clean_pos = pos.split(' ')[0] # Example of simplification
        # Add spaces to ensure token separation
        return f" {surface}{clean_pos}{last} "

    # Replace all augmented words
    processed_text = pattern.sub(repl, text)
    
    # Remove any remaining special characters that are not part of words
    processed_text = re.sub(r'[⌈⌉ˢᵖʳ]', '', processed_text)
    
    # Normalize whitespace: collapse multiple spaces into one and strip ends.
    # This is the key to ensuring ' 机_n の ' becomes '机_n の'.
    result = ' '.join(processed_text.split())
    return result
import re
import unicodedata

def preprocess_input_string(text, lower_case=False):
    text = str(text)
    text = unicodedata.normalize("NFKC", text)
    text = text.strip()
    text = re.sub(r"\s+", " ", text)

    if lower_case:
        text = text.lower()
    return text

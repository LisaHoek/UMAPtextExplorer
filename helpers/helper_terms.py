import re
import pandas as pd
from helpers.helper_utils import rgb_tuple_to_plotly

TERM_SOURCE_COL = "OCR extended stripped"
TERM_SOURCE_COL_ALT  = "OCR extended"
TERM_BLEND_OPTION = "Terms (traditional/modern/hobby)"

MODERN_BASE_RGB = (252/255, 141/255, 98/255)   # coral
HOBBY_BASE_RGB = (102/255, 194/255, 165/255)   # teal-green
TRAD_BASE_RGB = (141/255, 160/255, 203/255)    # lavender-blue
NO_MATCH_RGB = (0.9, 0.9, 0.9)

modern_terms = [
    "ik", "zelf", "zelfstandig", "eigen", "ontplooi", "ontwikkeling", "vrij", "onafhankelijk",
    "geëmancipeerd", "emotie", "gevoel", "passie", "interesse", "romantisch", "romantiek",
    "intimiteit", "seksueel", "seks", "sex", "geluk", "gelukkig", "onbezorgd"
]

hobby_terms = [
    "vrije tijd", "sport", "wandelen", "fietsen", "skiën", "golven", "sportief", "cultuur", "theater",
    "kunst", "schilderen", "creatief", "kunstzinnig", "artistiek", "muzikaal", "muziek",
    "bioscoop", "lezen", "natuur", "buiten", "uitgaan", "reizen", "zee", "bergen", "vakantie", "dieren"
]

trad_terms = [
    "huiselijk", "huishoudelijk", "huishouden", "kinderen", "zorg", "zorgzaam",
    "hardwerkend", "degelijk", "flink", "serieus", "ernstig"
]

def compile_term_patterns(terms):
    return {
        term: re.compile(
            r'\b' + re.escape(term) + r'(en|e|ig|isch|lijk)?\b',
            re.IGNORECASE
        )
        for term in terms
    }

MODERN_PATTERNS = compile_term_patterns(modern_terms)
HOBBY_PATTERNS = compile_term_patterns(hobby_terms)
TRAD_PATTERNS = compile_term_patterns(trad_terms)

def count_unique_terms(text, patterns):
    if pd.isna(text):
        return 0

    text = str(text)
    matches = set()

    for term, pattern in patterns.items():
        if pattern.search(text):
            matches.add(term)

    return len(matches)

def soften_rgb(rgb, amount=0.12):
    """
    Mix the color slightly with white so blends stay soft/pastel.
    """
    return tuple((1 - amount) * c + amount for c in rgb)

def blend_term_rgb(row):
    m = row["modern_count_unique"]
    h = row["hobby_count_unique"]
    t = row["trad_count_unique"]
    s = m + h + t

    if s == 0:
        return rgb_tuple_to_plotly(NO_MATCH_RGB)

    r = (m * MODERN_BASE_RGB[0] + h * HOBBY_BASE_RGB[0] + t * TRAD_BASE_RGB[0]) / s
    g = (m * MODERN_BASE_RGB[1] + h * HOBBY_BASE_RGB[1] + t * TRAD_BASE_RGB[1]) / s
    b = (m * MODERN_BASE_RGB[2] + h * HOBBY_BASE_RGB[2] + t * TRAD_BASE_RGB[2]) / s

    blended = soften_rgb((r, g, b), amount=0.10)
    return rgb_tuple_to_plotly(blended)

def prepare_term_blend(df, source_col):
    df = df.copy()

    df[source_col] = df[source_col].fillna("").astype(str)

    df["modern_count_unique"] = df[source_col].apply(lambda t: count_unique_terms(t, MODERN_PATTERNS))
    df["hobby_count_unique"] = df[source_col].apply(lambda t: count_unique_terms(t, HOBBY_PATTERNS))
    df["trad_count_unique"] = df[source_col].apply(lambda t: count_unique_terms(t, TRAD_PATTERNS))

    df["term_rgb_color"] = df.apply(blend_term_rgb, axis=1)

    return df
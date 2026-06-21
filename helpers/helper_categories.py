import seaborn as sns
from helpers.helper_utils import GRAY_RGB, rgb_tuple_to_plotly

# ── Column name constants ─────────────────────────────────────────────
SEX_SS_COL = "Sex (SS)"
SEX_DS_COL = "Sex (DS)"
SEX_COLS = [SEX_SS_COL, SEX_DS_COL]

CIVIL_STATUS_COL = "Civil status (SS)"
STRUCTURE_COL = "Structure"
CIRCULATION_AREA_COL = "Circulation area"
AREA_NUMBER_COL = "Area number"
PERIOD_COL = "Period"

# Columns whose only non-null values are "Positive" and "Not mentioned"
POSITIVE_ONLY_COLS = frozenset({
    "Financial status (SS)",
    "Social status (SS)",
    "Health (SS)",
    "Appearance (SS)",
    "Intimacy (SS)",
    "Hobbies /interests (SS)",
    "Character (SS)",
    "Children (SS)",
    "Geography (SS)",
    "Eductional level (SS)",
    "Intimacy (DS)",
})

# Columns whose non-null values are "Positive", "Not mentioned", and sometimes "Negative"
POSITIVE_NEGATIVE_COLS = frozenset({
    "Financial status (DS)",
    "Educational level (DS)",
    "Social status (DS)",
    "Health (DS)",
    "Appearance (DS)",
    "Photo (DS)",
    "Hobbies/ interests (DS)",
    "Character (DS)",
    "Children (DS)",
    "Geography (DS)",
})

_POSITIVE_COLOR = "#2ca02c"
_NEGATIVE_COLOR = "#d62728"


def _normalize_col(df, col, default="Not mentioned"):
    df[col] = (
        df[col].fillna(default).astype(str).str.strip()
        .replace({"not mentioned": "Not mentioned", "": default})
    )
    return df


def prepare_positive_only(df, source_col):
    df = df.copy()
    df = _normalize_col(df, source_col)
    color_discrete_map = {
        "Positive": _POSITIVE_COLOR,
        "Not mentioned": GRAY_RGB,
    }
    category_orders = {source_col: ["Positive", "Not mentioned"]}
    return df, source_col, color_discrete_map, category_orders


def prepare_positive_negative(df, source_col):
    df = df.copy()
    df = _normalize_col(df, source_col)
    color_discrete_map = {
        "Positive": _POSITIVE_COLOR,
        "Negative": _NEGATIVE_COLOR,
        "Not mentioned": GRAY_RGB,
    }
    category_orders = {source_col: ["Positive", "Negative", "Not mentioned"]}
    return df, source_col, color_discrete_map, category_orders


def prepare_sex(df, source_col):
    df = df.copy()
    df[source_col] = (
        df[source_col].fillna("Not mentioned").astype(str).str.strip()
        .replace({"": "Not mentioned"})
    )
    color_discrete_map = {
        "Male": "#1f77b4",
        "Female": "#e377c2",
        "Not mentioned": GRAY_RGB,
    }
    category_orders = {source_col: ["Male", "Female", "Not mentioned"]}
    return df, source_col, color_discrete_map, category_orders


def prepare_circulation_area(df, source_col):
    df = df.copy()
    df[source_col] = (
        df[source_col].fillna("Other").astype(str).str.strip()
        .replace({"": "Other"})
    )
    color_discrete_map = {
        "Regional": "#1f77b4",
        "National": "#ff7f0e",
        "Other": GRAY_RGB,
    }
    category_orders = {source_col: ["Regional", "National", "Other"]}
    return df, source_col, color_discrete_map, category_orders


_STRUCTURE_ORDER = ["Supply, Demand", "Demand, Supply", "Mix"]


def prepare_structure(df, source_col):
    df = df.copy()
    df[source_col] = (
        df[source_col].fillna("").astype(str).str.strip()
        .replace({"Mixed": "Mix", "": "Other"})
    )
    color_discrete_map = {
        "Supply, Demand": "#1f77b4",
        "Demand, Supply": "#ff7f0e",
        "Mix": "#2ca02c",
        "Other": GRAY_RGB,
    }
    category_orders = {source_col: _STRUCTURE_ORDER}
    return df, source_col, color_discrete_map, category_orders


def prepare_area_number(df, source_col):
    df = df.copy()
    df[source_col] = (
        df[source_col].fillna("").astype(str).str.strip()
        .replace({"1.0": "Area 1", "2.0": "Area 2", "3.0": "Area 3", "": "Other"})
    )
    color_discrete_map = {
        "Area 1": "#1f77b4",
        "Area 2": "#ff7f0e",
        "Area 3": "#2ca02c",
        "Other": GRAY_RGB,
    }
    category_orders = {source_col: ["Area 1", "Area 2", "Area 3"]}
    return df, source_col, color_discrete_map, category_orders


_CIVIL_STATUS_ORDER = ["Widowed", "Single", "Divorced", "Married", "Other", "Not mentioned"]


def prepare_civil_status(df, source_col):
    df = df.copy()
    df[source_col] = (
        df[source_col].fillna("Not mentioned").astype(str).str.strip()
        .replace({"": "Not mentioned"})
    )
    color_discrete_map = {
        "Widowed": "#1f77b4",
        "Single": "#ff7f0e",
        "Divorced": "#d62728",
        "Married": "#2ca02c",
        "Other": "#9467bd",
        "Not mentioned": GRAY_RGB,
    }
    category_orders = {source_col: _CIVIL_STATUS_ORDER}
    return df, source_col, color_discrete_map, category_orders


_PERIOD_ORDER = [
    "1840-1849", "1850-1859", "1860-1869", "1870-1879", "1880-1889",
    "1890-1899", "1900-1909", "1910-1919", "1920-1929", "1930-1939",
    "1940-1949", "1950-1959", "1960-1969", "1970-1979", "1980-1989",
    "1990-1999",
]


def prepare_period(df, source_col):
    df = df.copy()
    df[source_col] = (
        df[source_col].fillna("").astype(str).str.strip()
        .replace({"": "Unknown"})
    )
    palette = sns.color_palette("plasma", len(_PERIOD_ORDER))
    color_discrete_map = {
        period: rgb_tuple_to_plotly(color)
        for period, color in zip(_PERIOD_ORDER, palette)
    }
    color_discrete_map["Unknown"] = GRAY_RGB
    category_orders = {source_col: _PERIOD_ORDER + ["Unknown"]}
    return df, source_col, color_discrete_map, category_orders

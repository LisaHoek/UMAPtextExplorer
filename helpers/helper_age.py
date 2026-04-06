import seaborn as sns
from helpers.helper_utils import (
    GRAY_RGB,
    rgb_tuple_to_plotly,
)

AGE_COL = "Age Group (SS)"

AGE_GROUP_INTERNAL_COL = "age_group"

AGE_GROUPS_ORDER = [
    "Young (<25)",
    "25–29",
    "30–34",
    "35–39",
    "40–49",
    "Middle-aged",
    "50+",
    "Elderly person",
    "Not mentioned"
]

def prepare_age_groups(df):
    """
    Returns:
        df
        plot_color_col
        color_discrete_map
        category_orders
    """
    df = df.copy()

    # Use internal grouped column if present, otherwise fall back to the selected column
    source_col = AGE_GROUP_INTERNAL_COL if AGE_GROUP_INTERNAL_COL in df.columns else AGE_COL

    df[source_col] = df[source_col].fillna("Not mentioned").astype(str).str.strip()
    df[source_col] = df[source_col].replace({"": "Not mentioned"})

    # Spectral palette for all categories except "Not mentioned"
    kleur_lijst = sns.color_palette("Spectral", n_colors=len(AGE_GROUPS_ORDER[:-1]))
    cat2kleur = {
        cat: rgb_tuple_to_plotly(kleur)
        for cat, kleur in zip(AGE_GROUPS_ORDER[:-1], kleur_lijst)
    }
    cat2kleur["Not mentioned"] = GRAY_RGB

    category_orders = {
        source_col: AGE_GROUPS_ORDER
    }

    return df, source_col, cat2kleur, category_orders
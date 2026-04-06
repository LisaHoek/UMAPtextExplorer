import seaborn as sns
from helpers.helper_utils import (
    GRAY_RGB,
    rgb_tuple_to_plotly,
)

RELIGION_COLS = ["Religion advertisement","Religion (SS)", "Religion (DS)"]

RELIGIOUS_VALUES = ["Protestant", "Catholic", "Other", "Jewish"]

NO_PREF_VALUES = ["Not mentioned", "No preference"]

RELIGION_ORDER = [
    "Protestant",
    "Catholic",
    "Other",
    "Jewish",
    "No preference",
    "Not mentioned",
]

def religion_or_not(x):
    if x in RELIGIOUS_VALUES:
        return "Religious"
    elif x in NO_PREF_VALUES:
        return "No preference"
    else:
        return "Religious"
    
def get_religion_color_map():
    kleuren = sns.color_palette("Set2", 4)
    return {
        "Protestant": rgb_tuple_to_plotly(kleuren[0]),
        "Catholic": rgb_tuple_to_plotly(kleuren[1]),
        "Jewish": rgb_tuple_to_plotly(kleuren[2]),
        "No preference": rgb_tuple_to_plotly(kleuren[3]),
        "Other": "rgb(180,180,180)",
        "Not mentioned": GRAY_RGB,
    }

def prepare_religion_column(df, source_col, mode):
    """
    source_col can be:
    - Religion advertisement
    - Religion (SS)
    - Religion (DS)

    Returns:
        df
        plot_color_col
        color_discrete_map
        category_orders
    """
    df = df.copy()

    df[source_col] = df[source_col].fillna("Not mentioned").astype(str).str.strip()
    df[source_col] = df[source_col].replace({"": "Not mentioned"})

    if mode == "Show merged options":
        merged_col = f"{source_col} (y/n)"
        df[merged_col] = df[source_col].map(religion_or_not)

        kleuren = sns.color_palette("Set2", 2)
        color_discrete_map = {
            "Religious": rgb_tuple_to_plotly(kleuren[0]),
            "No preference": rgb_tuple_to_plotly(kleuren[1]),
        }

        category_orders = {
            merged_col: ["Religious", "No preference"]
        }

        return df, merged_col, color_discrete_map, category_orders

    # Show all options
    color_discrete_map = get_religion_color_map()

    category_orders = {
        source_col: RELIGION_ORDER
    }

    return df, source_col, color_discrete_map, category_orders
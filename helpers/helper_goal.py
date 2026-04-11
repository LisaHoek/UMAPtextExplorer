import plotly.colors as pc
from helpers.helper_utils import GRAY_RGB

GOAL_COL = "Goal of advertisement"

GOAL_ORDER = [
    "Marriage",
    "Getting-to-know each other",
    "Relationship",
    "Living-together",
    "LAT relationship",
    "Sex",
    "Other",
]

def marriage_or_not(x):
    if x == "Marriage":
        return "Marriage"
    else:
        return "Alternative relationship"


def prepare_goal_of_advertisement(df, mode):
    """
    Returns:
        df
        plot_color_col
        color_discrete_map
        category_orders
    """
    df = df.copy()

    # Normalize missing values for this column
    df[GOAL_COL] = df[GOAL_COL].fillna("Not mentioned").astype(str).str.strip()

    if mode == "Show merged options":
        df["Goal of advertisement (alt)"] = df[GOAL_COL].map(marriage_or_not)

        color_discrete_map = {
            "Marriage": pc.qualitative.Set2[0],
            "Alternative relationship": pc.qualitative.Set2[1],
        }

        category_orders = {
            "Goal of advertisement (alt)": ["Marriage", "Alternative relationship"]
        }

        return df, "Goal of advertisement (alt)", color_discrete_map, category_orders

    # Show all options
    # Custom color mapping with fixed gray for Other / Not mentioned
    set2 = pc.qualitative.Set2

    color_discrete_map = {
        "Marriage": set2[0],
        "Getting-to-know each other": set2[1],
        "Relationship": set2[2],
        "Living-together": set2[3],
        "LAT relationship": set2[4],
        "Sex": set2[5],
        "Other": GRAY_RGB,
        "Not mentioned": GRAY_RGB,
    }

    category_orders = {
        GOAL_COL: GOAL_ORDER
    }

    return df, GOAL_COL, color_discrete_map, category_orders
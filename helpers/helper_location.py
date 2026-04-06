import seaborn as sns
from helpers.helper_utils import (
    GRAY_RGB,
    rgb_tuple_to_plotly,
)

LOCATION_COL = "Location publisher"

LOCATION_GROUP_ORDER = [
    'Limburg', 'Brabant',
    'Zuid-Holland', 'Noord-Holland',
    'Utrecht', 'Gelderland',
    'Overijssel', 'Groningen',
    'Friesland', 'Other']

LOCATION_CITY_ORDER = [
    'Heerlen', 'Kerkrade', 'Maastricht', 'Venlo',
    'Helmond', 'Eindhoven', '\'s-Hertogenbosch', 'Tilburg', 
    'Breda', 'Rotterdam', '\'s-Gravenhage', 'Zaandam',
    'Amsterdam', 'Haarlem', 'Hilversum', 'Utrecht', 
    'Amersfoort', 'Ede', 'Arnhem', 'Nijmegen', 
    'Doetinchem', 'Deventer', 'Zwolle', 'Enschede',
    'Wildervank', 'Groningen', 'Heerenveen', 'Leeuwarden']

def make_city_color_map(city_values):
    """
    Create a unique color for each city value.
    'Other' is always light grey.
    """
    city_values = [c for c in city_values if c != "Other"]
    palette = sns.color_palette("husl", n_colors=len(city_values))

    color_map = {
        city: rgb_tuple_to_plotly(color)
        for city, color in zip(city_values, palette)
    }
    color_map["Other"] = GRAY_RGB
    return color_map

def mapping_locations(x):
    if x in ['Heerlen', 'Kerkrade', 'Maastricht', 'Venlo']:
        return 'Limburg'
    elif x in ['Helmond', 'Eindhoven', '\'s-Hertogenbosch', 'Tilburg', 'Breda']:
        return 'Brabant'
    elif x in ['Zaandam', 'Amsterdam', 'Haarlem', 'Hilversum']:
        return 'Noord-Holland'
    elif x in ['Rotterdam', '\'s-Gravenhage']:
        return 'Zuid-Holland'
    elif x in ['Utrecht', 'Amersfoort']:
        return 'Utrecht'
    elif x in ['Ede', 'Arnhem', 'Nijmegen', 'Doetinchem']:
        return 'Gelderland'
    elif x in ['Zwolle', 'Deventer', 'Enschede']:
        return 'Overijssel'
    elif x in ['Leeuwarden', 'Heerenveen']:
        return 'Friesland'
    elif x in ['Wildervank', 'Groningen']:
        return 'Groningen'
    else:
        return 'Other'
    
def prepare_location_publisher(df, mode):
    """
    Returns:
        df
        plot_color_col
        color_discrete_map
        category_orders
    """
    df = df.copy()

    df[LOCATION_COL] = df[LOCATION_COL].fillna("").astype(str).str.strip()
    df[LOCATION_COL] = df[LOCATION_COL].replace({"": "Other"})

    if mode == "Show merged options":
        df["Location publisher (prov)"] = df[LOCATION_COL].map(mapping_locations)

        kleuren = sns.color_palette("husl", 10)
        color_discrete_map = {
            'Limburg': rgb_tuple_to_plotly(kleuren[0]),
            'Brabant': rgb_tuple_to_plotly(kleuren[1]),
            'Zuid-Holland': rgb_tuple_to_plotly(kleuren[2]),
            'Noord-Holland': rgb_tuple_to_plotly(kleuren[3]),
            'Utrecht': rgb_tuple_to_plotly(kleuren[4]),
            'Gelderland': rgb_tuple_to_plotly(kleuren[5]),
            'Overijssel': rgb_tuple_to_plotly(kleuren[6]),
            'Groningen': rgb_tuple_to_plotly(kleuren[7]),
            'Friesland': rgb_tuple_to_plotly(kleuren[8]),
            'Other': GRAY_RGB,
        }

        category_orders = {
            "Location publisher (prov)": LOCATION_GROUP_ORDER
        }

        return df, "Location publisher (prov)", color_discrete_map, category_orders

    # Show all options: every city gets its own color
    df[LOCATION_COL] = df[LOCATION_COL].replace({"": "Other"})

    # Use only cities that are actually present, but keep preferred order if available
    present_cities = df[LOCATION_COL].dropna().astype(str).unique().tolist()

    ordered_present_cities = [city for city in LOCATION_CITY_ORDER if city in present_cities]
    remaining_cities = [city for city in present_cities if city not in ordered_present_cities]
    final_city_order = ordered_present_cities + sorted(remaining_cities)

    color_discrete_map = make_city_color_map(final_city_order)

    category_orders = {
        LOCATION_COL: final_city_order
    }

    return df, LOCATION_COL, color_discrete_map, category_orders
GRAY_RGB = "rgb(230,230,230)"
YEAR_COL = "Year"

def rgb_tuple_to_plotly(rgb_tuple):
    return f"rgb({int(rgb_tuple[0]*255)},{int(rgb_tuple[1]*255)},{int(rgb_tuple[2]*255)})"
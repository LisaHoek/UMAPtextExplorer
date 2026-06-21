import re
from io import BytesIO

import pandas as pd
import plotly.express as px
import streamlit as st

from helpers.helper_utils import YEAR_COL, rgb_tuple_to_plotly
from helpers.helper_hover import wrap_hover_text

from helpers.helper_goal import (
    GOAL_COL,
    prepare_goal_of_advertisement,
)

from helpers.helper_religion import (
    RELIGION_COLS,
    prepare_religion_column,
)

from helpers.helper_age import (
    AGE_COL,
    prepare_age_groups,
)

from helpers.helper_location import (
    LOCATION_COL,
    prepare_location_publisher,
)

from helpers.helper_terms import (
    TERM_SOURCE_COL,
    TERM_SOURCE_COL_ALT,
    TERM_BLEND_OPTION,
    HOBBY_BASE_RGB,
    MODERN_BASE_RGB,
    TRAD_BASE_RGB,
    NO_MATCH_RGB,
    prepare_term_blend,
)

from helpers.helper_animation import (
    build_time_window_df,
    build_categorical_animation_figure,
    build_term_blend_animation_figure,
)


TERM_MATCH_OPTION = "Term match"
TERM_MATCH_COL = "_term_match"


def normalize_column_name(name):
    return re.sub(r"\s+", " ", str(name).strip()).casefold()


EXCLUDED_COLOR_SELECTOR_COLUMNS = {
    normalize_column_name("Nr advertisement"),
    normalize_column_name("Link"),
    normalize_column_name("OCR - Delpher"),
    normalize_column_name("OCR remediated"),
    normalize_column_name("Delimiter or manual split"),
    normalize_column_name("Advertisement nr/code/motto"),
    normalize_column_name("Date"),
    normalize_column_name("Oversampling"),
    normalize_column_name("Year"),
    normalize_column_name("Position delimiter"),
    normalize_column_name("Text before delimiter/SUPPLY SIDE"),
    normalize_column_name("Text as of delimiter/DEMAND SIDE"),
    normalize_column_name("OCR stripped"),
    normalize_column_name("SS stripped"),
    normalize_column_name("DS stripped"),
    normalize_column_name("OCR extended"),
    normalize_column_name("SS extended"),
    normalize_column_name("DS extended"),
    normalize_column_name("OCR extended profile reduced"),
    normalize_column_name("SS extended profile reduced"),
    normalize_column_name("DS extended profile reduced"),
    normalize_column_name("words OCR extended"),
    normalize_column_name("single adjectives OCR extended"),
    normalize_column_name("single nouns OCR extended"),
    normalize_column_name("phrase nouns OCR extended"),
    normalize_column_name("single and phrase nouns OCR extended"),
    normalize_column_name("words SS extended"),
    normalize_column_name("single adjectives SS extended"),
    normalize_column_name("single nouns SS extended"),
    normalize_column_name("phrase nouns SS extended"),
    normalize_column_name("single and phrase nouns SS extended"),
    normalize_column_name("words DS extended"),
    normalize_column_name("single adjectives DS extended"),
    normalize_column_name("single nouns DS extended"),
    normalize_column_name("phrase nouns DS extended"),
    normalize_column_name("single and phrase nouns DS extended"),
    normalize_column_name("Terms (traditional/modern/hobby)"),
}


def get_coordinate_pairs(df):
    """
    Detect valid coordinate pairs in the dataframe.

    A valid pair is:
    - x / y
    - x_* / y_*
    where the suffix after x matches the suffix after y.
    """
    x_candidates = [col for col in df.columns if re.match(r"^x($|_)", str(col))]
    pairs = []

    for x_col in x_candidates:
        y_col = "y" + x_col[1:]
        if y_col in df.columns:
            pairs.append((x_col, y_col))

    preferred_order = {
        ("x", "y"): 0,
        ("x_profile_reduced", "y_profile_reduced"): 1,
        ("x_ss", "y_ss"): 2,
        ("x_ss_profile_reduced", "y_ss_profile_reduced"): 3,
        ("x_ds", "y_ds"): 4,
        ("x_ds_profile_reduced", "y_ds_profile_reduced"): 5,
    }

    return sorted(
        pairs,
        key=lambda pair: (preferred_order.get(pair, 999), pair[0], pair[1])
    )


def format_coordinate_pair_label(x_col, y_col):
    if x_col == "x" and y_col == "y":
        return "OCR extended"

    if x_col == "x_profile_reduced" and y_col == "y_profile_reduced":
        return "OCR profile reduced"

    if x_col == "x_ss" and y_col == "y_ss":
        return "SS extended"

    if x_col == "x_ss_profile_reduced" and y_col == "y_ss_profile_reduced":
        return "SS profile reduced"

    if x_col == "x_ds" and y_col == "y_ds":
        return "DS extended"

    if x_col == "x_ds_profile_reduced" and y_col == "y_ds_profile_reduced":
        return "DS profile reduced"

    if x_col.startswith("x_"):
        suffix = x_col[2:]
    else:
        suffix = ""

    is_profile_reduced = suffix.endswith("_profile_reduced")
    base = suffix[:-len("_profile_reduced")] if is_profile_reduced else suffix

    if base in {"", "ocr"}:
        source_label = "OCR"
    elif base == "ss":
        source_label = "SS"
    elif base == "ds":
        source_label = "DS"
    else:
        source_label = base.replace("_", " ").title()

    representation_label = "profile reduced" if is_profile_reduced else "extended"
    return f"{source_label} {representation_label}"


def parse_search_terms(raw_text):
    if not raw_text:
        return []

    parts = re.split(r"[\n,;|]+", str(raw_text))
    terms = []

    for part in parts:
        term = re.sub(r"\s+", " ", part).strip()
        if term:
            terms.append(term)

    return terms


def tokenize_text(value):
    value = str(value).lower()
    return set(re.findall(r"(?u)\b\w+\b", value))


@st.cache_data(show_spinner=False)
def load_and_prepare_csv(file_bytes):
    df = pd.read_csv(BytesIO(file_bytes))

    coordinate_pairs = get_coordinate_pairs(df)
    coordinate_columns = sorted({col for pair in coordinate_pairs for col in pair})

    for col in coordinate_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    if YEAR_COL in df.columns:
        df[YEAR_COL] = pd.to_numeric(df[YEAR_COL], errors="coerce")

    return df, coordinate_pairs, coordinate_columns


@st.cache_data(show_spinner=False)
def cached_wrap_hover_texts(values, width=50, max_lines=10):
    return [wrap_hover_text(v, width=width, max_lines=max_lines) for v in values]


@st.cache_data(show_spinner=False)
def cached_tokenize_values(values):
    return [tokenize_text(v) for v in values]


@st.cache_data(show_spinner=False)
def cached_build_time_window_df(df, year_col, window_size):
    return build_time_window_df(df, year_col=year_col, window_size=window_size)


def prepare_term_match(df, text_col, contains_terms=None, exact_terms=None):
    contains_terms = contains_terms or []
    exact_terms = exact_terms or []

    text_series = df[text_col].fillna("").astype(str)
    text_values = text_series.tolist()

    match_mask = pd.Series(False, index=df.index)

    if contains_terms:
        for term in contains_terms:
            match_mask = match_mask | text_series.str.contains(
                term,
                case=False,
                na=False,
                regex=False,
            )

    if exact_terms:
        exact_tokens = set()
        for term in exact_terms:
            exact_tokens.update(tokenize_text(term))

        if exact_tokens:
            token_sets = cached_tokenize_values(text_values)
            exact_mask = pd.Series(
                [bool(tokens & exact_tokens) for tokens in token_sets],
                index=df.index
            )
            match_mask = match_mask | exact_mask

    df = df.copy()
    df[TERM_MATCH_COL] = "No match"
    df.loc[match_mask, TERM_MATCH_COL] = "Term match"

    color_discrete_map = {
        "Term match": "#d62728",
        "No match": "#bdbdbd",
    }

    category_orders = {
        TERM_MATCH_COL: ["No match", "Term match"]
    }

    return df, TERM_MATCH_COL, color_discrete_map, category_orders


st.set_page_config(page_title="UMAP Text Explorer", layout="wide")

st.title("UMAP Text Explorer")
st.write(
    "Upload a CSV file with coordinate pairs such as `x/y`, "
    "`x_profile_reduced/y_profile_reduced`, `x_ss/y_ss`, or `x_ds/y_ds`. "
    "Then choose which coordinate pair to analyze, which text column to inspect, "
    "and which column to use for color."
)

uploaded_file = st.file_uploader("Upload your CSV", type="csv")

if uploaded_file is not None:
    file_bytes = uploaded_file.getvalue()
    df, coordinate_pairs, coordinate_columns = load_and_prepare_csv(file_bytes)
    df = df.copy()

    if not coordinate_pairs:
        st.error(
            "No valid coordinate pairs found. Expected matching columns like "
            "`x` and `y`, or `x_*` and `y_*`."
        )
        st.stop()

    all_columns = df.columns.tolist()
    non_xy_columns = [col for col in all_columns if col not in coordinate_columns]

    if not non_xy_columns:
        st.error(
            "Your CSV only contains coordinate columns. "
            "Please add at least one extra column for text."
        )
        st.stop()

    pair_options = []
    pair_lookup = {}

    for x_pair, y_pair in coordinate_pairs:
        label = format_coordinate_pair_label(x_pair, y_pair)
        if label in pair_lookup:
            label = f"{label} ({x_pair} / {y_pair})"
        pair_options.append(label)
        pair_lookup[label] = (x_pair, y_pair)

    default_pair_index = 0
    for i, label in enumerate(pair_options):
        if pair_lookup[label] == ("x", "y"):
            default_pair_index = i
            break

    color_candidate_columns = [
        col for col in non_xy_columns
        if normalize_column_name(col) not in EXCLUDED_COLOR_SELECTOR_COLUMNS
        and normalize_column_name(col) != normalize_column_name(YEAR_COL)
    ]

    color_options = ["None"] + color_candidate_columns
    if (
        (TERM_SOURCE_COL in all_columns or TERM_SOURCE_COL_ALT in all_columns)
        and normalize_column_name(TERM_BLEND_OPTION) not in EXCLUDED_COLOR_SELECTOR_COLUMNS
    ):
        color_options.append(TERM_BLEND_OPTION)

    st.sidebar.header("Settings")
    st.sidebar.caption("Change settings and click Apply to update the plot.")

    with st.sidebar.form("settings_form"):
        selected_pair_label = st.selectbox(
            "Coordinate pair",
            options=pair_options,
            index=default_pair_index,
        )

        x_col, y_col = pair_lookup[selected_pair_label]

        _text_col_default = next(
            (i for i, col in enumerate(non_xy_columns) if col == "OCR extended"),
            0
        )
        text_col = st.selectbox(
            "Text column",
            options=non_xy_columns,
            index=_text_col_default
        )

        use_term_match_color = st.checkbox(
            "Color by term match in selected text",
            value=False,
            help=(
                "If enabled, points are colored based on literal term matching in "
                "the selected text column. Regex is not used."
            )
        )

        contains_search_input = ""
        exact_search_input = ""

        if use_term_match_color:
            st.markdown("### Term search")

            contains_search_input = st.text_area(
                "Term contains",
                value="",
                height=90,
                help=(
                    "Enter one or more literal partial search terms. "
                    "Use one per line, or separate with commas, semicolons, or pipes."
                ),
            )

            exact_search_input = st.text_area(
                "Term is exact token",
                value="",
                height=90,
                help=(
                    "Enter one or more terms that must occur as complete tokens/words. "
                    "For example, `man` matches `jonge man zoekt vrouw`, "
                    "but not `mantel`."
                ),
            )

            color_col = TERM_MATCH_OPTION
        else:
            color_col = st.selectbox(
                "Color column",
                options=color_options,
                index=0
            )

        point_size = st.slider("Point size", 1, 30, 4)
        marker_opacity = st.slider("Opacity", 0.1, 1.0, 0.7)

        animate_time = False
        window_size = 5
        frame_duration = 100
        selected_years = None

        if YEAR_COL in df.columns:
            year_values = df[YEAR_COL].dropna()

            if not year_values.empty:
                year_min = int(year_values.min())
                year_max = int(year_values.max())

                selected_years = st.slider(
                    "Year range",
                    min_value=year_min,
                    max_value=year_max,
                    value=(year_min, year_max),
                    step=1
                )

                animate_time = st.checkbox("Animate 10-year moving window", value=False)

                if animate_time:
                    window_size = st.slider(
                        "Years on each side of center year",
                        min_value=1,
                        max_value=20,
                        value=5,
                        step=1
                    )
                    frame_duration = st.slider(
                        "Animation speed (ms per frame)",
                        min_value=50,
                        max_value=200,
                        value=100,
                        step=50
                    )
            else:
                st.info("Column 'Year' exists, but contains no valid numeric values.")

        goal_color_mode = "Show all options"
        location_color_mode = "Show all options"
        religion_color_mode = "Show all options"

        if color_col == GOAL_COL:
            goal_color_mode = st.radio(
                "Goal of advertisement display mode",
                options=["Show all options", "Show merged options"],
                index=0
            )

        elif color_col == LOCATION_COL:
            location_color_mode = st.radio(
                "Location publisher display mode",
                options=["Show all options", "Show merged options"],
                index=0
            )

        elif color_col in RELIGION_COLS:
            religion_color_mode = st.radio(
                f"{color_col} display mode",
                options=["Show all options", "Show merged options"],
                index=0
            )

        apply_settings = st.form_submit_button("Apply")

    x_col, y_col = pair_lookup[selected_pair_label]

    df = df.dropna(subset=[x_col, y_col])

    if selected_years is not None and YEAR_COL in df.columns:
        df = df[
            (df[YEAR_COL] >= selected_years[0]) &
            (df[YEAR_COL] <= selected_years[1])
        ]

    df = df.reset_index(drop=True)

    if df.empty:
        st.warning("No rows remain after applying the current filters.")
        st.stop()

    df[text_col] = df[text_col].fillna("").astype(str)

    plot_color_col = None
    color_discrete_map = None
    category_orders = None
    use_term_blend = False

    if color_col == GOAL_COL:
        df, plot_color_col, color_discrete_map, category_orders = (
            prepare_goal_of_advertisement(df, goal_color_mode)
        )

    elif color_col == LOCATION_COL:
        df, plot_color_col, color_discrete_map, category_orders = (
            prepare_location_publisher(df, location_color_mode)
        )

    elif color_col == AGE_COL:
        df, plot_color_col, color_discrete_map, category_orders = prepare_age_groups(df)

    elif color_col in RELIGION_COLS:
        df, plot_color_col, color_discrete_map, category_orders = (
            prepare_religion_column(df, color_col, religion_color_mode)
        )

    elif color_col == TERM_BLEND_OPTION:
        if TERM_SOURCE_COL not in df.columns:
            df = prepare_term_blend(df, TERM_SOURCE_COL_ALT)
        else:
            df = prepare_term_blend(df, TERM_SOURCE_COL)
        use_term_blend = True

    elif color_col == TERM_MATCH_OPTION:
        contains_terms = parse_search_terms(contains_search_input)
        exact_terms = parse_search_terms(exact_search_input)

        if not contains_terms and not exact_terms:
            st.sidebar.error(
                "Please enter at least one value in `Term contains` or "
                "`Term is exact token`."
            )
            st.stop()

        df, plot_color_col, color_discrete_map, category_orders = prepare_term_match(
            df=df,
            text_col=text_col,
            contains_terms=contains_terms,
            exact_terms=exact_terms,
        )

        st.sidebar.caption(f"Contains search terms: {len(contains_terms)}")
        st.sidebar.caption(f"Exact-token search terms: {len(exact_terms)}")

    elif color_col != "None":
        plot_color_col = color_col

    if plot_color_col is not None and plot_color_col in df.columns:
        if df[plot_color_col].dtype == object:
            unique_count = df[plot_color_col].nunique(dropna=False)
            if unique_count < max(len(df) * 0.5, 100):
                df[plot_color_col] = df[plot_color_col].astype("category")

    hide_not_mentioned = False

    if plot_color_col is not None:
        has_not_mentioned = df[plot_color_col].astype(str).eq("Not mentioned").any()

        if has_not_mentioned:
            hide_not_mentioned = st.sidebar.checkbox(
                'Hide "Not mentioned"',
                value=False
            )

    if hide_not_mentioned:
        df = df[df[plot_color_col].astype(str) != "Not mentioned"].reset_index(drop=True)

        if df.empty:
            st.warning('No rows remain after hiding "Not mentioned".')
            st.stop()

        if color_discrete_map is not None and "Not mentioned" in color_discrete_map:
            color_discrete_map = {
                k: v for k, v in color_discrete_map.items()
                if k != "Not mentioned"
            }

        if category_orders is not None and plot_color_col in category_orders:
            category_orders = {
                **category_orders,
                plot_color_col: [
                    cat for cat in category_orders[plot_color_col]
                    if cat != "Not mentioned"
                ]
            }

    if use_term_blend:
        st.sidebar.markdown("**Term blend key**")
        st.sidebar.markdown(
            f"""
            <div style="display:flex; flex-direction:column; gap:6px; margin-bottom:8px;">
                <div style="display:flex; align-items:center; gap:8px;">
                    <div style="width:14px; height:14px; background:{rgb_tuple_to_plotly(MODERN_BASE_RGB)}; border-radius:3px;"></div>
                    <div>Modern</div>
                </div>
                <div style="display:flex; align-items:center; gap:8px;">
                    <div style="width:14px; height:14px; background:{rgb_tuple_to_plotly(HOBBY_BASE_RGB)}; border-radius:3px;"></div>
                    <div>Hobby / leisure</div>
                </div>
                <div style="display:flex; align-items:center; gap:8px;">
                    <div style="width:14px; height:14px; background:{rgb_tuple_to_plotly(TRAD_BASE_RGB)}; border-radius:3px;"></div>
                    <div>Traditional</div>
                </div>
                <div style="display:flex; align-items:center; gap:8px;">
                    <div style="width:14px; height:14px; background:{rgb_tuple_to_plotly(NO_MATCH_RGB)}; border-radius:3px; border:1px solid #ccc;"></div>
                    <div>No match</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    if not animate_time and plot_color_col is not None:
        is_categorical_color = (
            color_discrete_map is not None
            or category_orders is not None
            or not pd.api.types.is_numeric_dtype(df[plot_color_col])
        )

        if is_categorical_color:
            group_counts = df[plot_color_col].value_counts(dropna=False)

            if not group_counts.empty:
                max_group_count = int(group_counts.max())

                min_group_size = st.sidebar.slider(
                    "Minimum group size",
                    min_value=1,
                    max_value=max_group_count,
                    value=1,
                    step=1,
                    help="Hide color groups with fewer points than this number."
                )

                keep_groups = group_counts[group_counts >= min_group_size].index.tolist()
                df = df[df[plot_color_col].isin(keep_groups)].reset_index(drop=True)

                if df.empty:
                    st.warning("No rows remain after applying the minimum group size filter.")
                    st.stop()

                if category_orders is not None and plot_color_col in category_orders:
                    kept_set = set(keep_groups)
                    category_orders = {
                        **category_orders,
                        plot_color_col: [
                            cat for cat in category_orders[plot_color_col]
                            if cat in kept_set
                        ]
                    }

    df = df.copy()
    df["_row_id"] = range(len(df))

    hover_values = cached_wrap_hover_texts(df[text_col].tolist(), width=50, max_lines=10)
    df["hover_text_wrapped"] = hover_values

    custom_data_cols = ["_row_id", "hover_text_wrapped"]

    if use_term_blend:
        custom_data_cols += [
            "modern_count_unique",
            "hobby_count_unique",
            "trad_count_unique"
        ]

    base_plot_kwargs = dict(
        x=x_col,
        y=y_col,
        custom_data=custom_data_cols,
    )

    if not animate_time and not use_term_blend:
        base_plot_kwargs["render_mode"] = "webgl"

    x_min = df[x_col].min()
    x_max = df[x_col].max()
    y_min = df[y_col].min()
    y_max = df[y_col].max()

    x_pad = max((x_max - x_min) * 0.05, 1e-6)
    y_pad = max((y_max - y_min) * 0.05, 1e-6)
    x_range = [x_min - x_pad, x_max + x_pad]
    y_range = [y_min - y_pad, y_max + y_pad]

    if use_term_blend:
        hover_template = (
            "<b>%{customdata[1]}</b><br>"
            "Modern terms: %{customdata[2]}<br>"
            "Hobby terms: %{customdata[3]}<br>"
            "Traditional terms: %{customdata[4]}<br>"
            f"{x_col}=%{{x}}<br>"
            f"{y_col}=%{{y}}<extra></extra>"
        )
    else:
        hover_template = (
            "<b>%{customdata[1]}</b><br>"
            f"{x_col}=%{{x}}<br>"
            f"{y_col}=%{{y}}<extra></extra>"
        )

    if animate_time and use_term_blend:
        df_anim = cached_build_time_window_df(df, year_col=YEAR_COL, window_size=window_size)

        if df_anim.empty:
            st.warning("Not enough valid years to build the animation for this window size.")
            st.stop()

        if x_col != "x":
            df_anim = df_anim.copy()
            df_anim["x"] = df_anim[x_col]
            df_anim["y"] = df_anim[y_col]

        df_anim = df_anim.sort_values(["frame_year", "_row_id"]).reset_index(drop=True)

        fig = build_term_blend_animation_figure(
            df_anim=df_anim,
            point_size=point_size,
            marker_opacity=marker_opacity,
            x_range=x_range,
            y_range=y_range,
            frame_duration=frame_duration,
            x_col=x_col,
            y_col=y_col,
        )

    elif animate_time:
        if plot_color_col is not None and category_orders is not None:
            if plot_color_col in category_orders:
                df[plot_color_col] = pd.Categorical(
                    df[plot_color_col],
                    categories=category_orders[plot_color_col],
                    ordered=True
                )

        df_anim = cached_build_time_window_df(df, year_col=YEAR_COL, window_size=window_size)

        if df_anim.empty:
            st.warning("Not enough valid years to build the animation for this window size.")
            st.stop()

        is_categorical_color = (
            plot_color_col is not None and (
                color_discrete_map is not None
                or category_orders is not None
                or not pd.api.types.is_numeric_dtype(df[plot_color_col])
            )
        )

        if is_categorical_color and plot_color_col is not None:
            if category_orders is not None and plot_color_col in category_orders:
                categories = category_orders[plot_color_col]
            else:
                categories = list(dict.fromkeys(df_anim[plot_color_col].dropna().tolist()))

            fig = build_categorical_animation_figure(
                df_anim=df_anim,
                x_col=x_col,
                y_col=y_col,
                color_col=plot_color_col,
                categories=categories,
                point_size=point_size,
                marker_opacity=marker_opacity,
                x_range=x_range,
                y_range=y_range,
                frame_duration=frame_duration,
                hover_template=hover_template,
                custom_data_cols=custom_data_cols,
                color_discrete_map=color_discrete_map,
                legend_title_text=plot_color_col,
            )

        else:
            df_anim = df_anim.sort_values(["frame_year", "_row_id"]).reset_index(drop=True)

            plot_kwargs = dict(
                data_frame=df_anim,
                animation_frame="frame_label",
                animation_group="_row_id",
                **base_plot_kwargs
            )

            if plot_color_col is not None:
                plot_kwargs["color"] = plot_color_col

            if color_discrete_map is not None:
                plot_kwargs["color_discrete_map"] = color_discrete_map

            if category_orders is not None:
                plot_kwargs["category_orders"] = category_orders

            fig = px.scatter(**plot_kwargs)

            fig.update_traces(hovertemplate=hover_template)
            for _frame in fig.frames:
                for _trace in _frame.data:
                    _trace.update(hovertemplate=hover_template)
            fig.update_traces(
                marker=dict(size=point_size, opacity=marker_opacity),
                selector=dict(mode="markers")
            )

            fig.update_layout(
                height=700,
                dragmode="pan",
                margin=dict(l=10, r=10, t=40, b=10),
                xaxis_title=x_col,
                yaxis_title=y_col,
                legend_title_text=plot_color_col if plot_color_col is not None else ""
            )

            fig.update_xaxes(range=x_range)
            fig.update_yaxes(range=y_range)

            if fig.layout.updatemenus and len(fig.layout.updatemenus) > 0:
                for button in fig.layout.updatemenus[0].buttons:
                    if len(button.args) > 1 and isinstance(button.args[1], dict):
                        button.args[1]["frame"] = {"duration": frame_duration, "redraw": True}
                        button.args[1]["transition"] = {"duration": 0}
                        button.args[1]["fromcurrent"] = True
                        button.args[1]["mode"] = "immediate"

            if fig.layout.sliders:
                fig.layout.sliders[0]["currentvalue"]["prefix"] = "Window: "

    else:
        plot_kwargs = dict(
            data_frame=df,
            **base_plot_kwargs
        )

        if plot_color_col is not None:
            plot_kwargs["color"] = plot_color_col

        if color_discrete_map is not None:
            plot_kwargs["color_discrete_map"] = color_discrete_map

        if category_orders is not None:
            plot_kwargs["category_orders"] = category_orders

        fig = px.scatter(**plot_kwargs)

        fig.update_traces(hovertemplate=hover_template)

        if use_term_blend:
            fig.update_traces(
                marker=dict(
                    color=df["term_rgb_color"].tolist(),
                    size=point_size,
                    opacity=marker_opacity
                ),
                showlegend=False,
                selector=dict(mode="markers")
            )
        else:
            fig.update_traces(
                marker=dict(size=point_size, opacity=marker_opacity),
                selector=dict(mode="markers")
            )

        fig.update_layout(
            height=700,
            dragmode="lasso",
            uirevision=f"keep_zoom_{selected_pair_label}",
            margin=dict(l=10, r=10, t=40, b=10),
            xaxis_title=x_col,
            yaxis_title=y_col,
            legend_title_text=plot_color_col if plot_color_col is not None else "",
            showlegend=not use_term_blend
        )

        fig.update_xaxes(range=x_range)
        fig.update_yaxes(range=y_range)

    left, right = st.columns([2, 1], gap="large")

    with left:
        st.subheader("Scatter Plot")
        st.caption(f"Currently plotting: {selected_pair_label}")

        if animate_time:
            st.caption("Use the Play button below the chart to animate the moving year window.")
            event = st.plotly_chart(
                fig,
                use_container_width=True,
                key=f"scatter_plot_variant_animated_{x_col}_{y_col}",
                config={
                    "scrollZoom": True,
                    "displaylogo": False
                }
            )
        else:
            event = st.plotly_chart(
                fig,
                use_container_width=True,
                key=f"scatter_plot_variant_{x_col}_{y_col}",
                on_select="rerun",
                selection_mode=("box", "lasso"),
                config={
                    "scrollZoom": True,
                    "displaylogo": False
                }
            )

    selected_row_ids = []
    selected_df = pd.DataFrame()
    display_selected_df = pd.DataFrame()

    if not animate_time:
        points = []

        try:
            if event and event.selection and event.selection.points:
                points = event.selection.points
        except Exception:
            try:
                points = event.get("selection", {}).get("points", [])
            except Exception:
                points = []

        if points:
            selected_row_ids = [p["customdata"][0] for p in points]

    with right:
        st.subheader("Selection")

        if animate_time:
            st.info("Selection is disabled in animation mode. Turn off animation to lasso points and inspect text.")
        elif selected_row_ids:
            selected_df = (
                df.set_index("_row_id")
                .loc[selected_row_ids]
                .reset_index()
            )

            display_selected_df = selected_df.drop(
                columns=["_row_id", "hover_text_wrapped"],
                errors="ignore"
            )

            st.success(f"{len(selected_df)} point(s) selected")

            st.text_area(
                "Selected text",
                value="\n\n".join(selected_df[text_col].astype(str).tolist()),
                height=500
            )

        else:
            st.info("Select points using lasso or box selection.")

    st.divider()

    st.subheader("Data Preview (selected)")
    if not display_selected_df.empty:
        st.dataframe(display_selected_df, use_container_width=True)
    else:
        st.info("No points selected.")

    with st.expander("Data Preview (plot)", expanded=False):
        preview_limit = min(1000, len(df))
        st.dataframe(df.head(preview_limit), use_container_width=True)
        if len(df) > preview_limit:
            st.caption(f"Showing first {preview_limit:,} of {len(df):,} rows.")

else:
    st.info("Please upload a CSV file first.")
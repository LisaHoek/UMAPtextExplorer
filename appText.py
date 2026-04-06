import streamlit as st
import pandas as pd
import plotly.express as px
from helpers.helper_utils import YEAR_COL
from helpers.helper_hover import wrap_hover_text

from helpers.helper_utils import (
    rgb_tuple_to_plotly,
)

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
    add_animation_category_dummies,
    build_term_blend_animation_figure,
)

# Set up Streamlit app
st.set_page_config(page_title="CSV Scatter Explorer", layout="wide")
st.title("CSV Scatter Explorer")
st.write(
    "Upload a CSV file with at least columns `x` and `y`. "
    "Then choose which column should be used as text and which one for color."
)

uploaded_file = st.file_uploader("Upload your CSV", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    # Required columns
    required_cols = {"x", "y"}
    missing = required_cols - set(df.columns)
    if missing:
        st.error(f"Missing required columns: {', '.join(missing)}")
        st.stop()

    # Clean x/y
    df = df.copy()
    df["x"] = pd.to_numeric(df["x"], errors="coerce")
    df["y"] = pd.to_numeric(df["y"], errors="coerce")

    if YEAR_COL in df.columns:
        df[YEAR_COL] = pd.to_numeric(df[YEAR_COL], errors="coerce")
    df = df.dropna(subset=["x", "y"]).reset_index(drop=True)

    if df.empty:
        st.warning("No valid rows remain after cleaning x and y.")
        st.stop()

    all_columns = df.columns.tolist()
    non_xy_columns = [col for col in all_columns if col not in ["x", "y"]]

    if not non_xy_columns:
        st.error("Your CSV only contains x and y. Please add at least one extra column for text.")
        st.stop()

    # Sidebar
    st.sidebar.header("Settings")

    text_col = st.sidebar.selectbox(
        "Text column",
        options=non_xy_columns,
        index=0
    )

    color_options = ["None"] + all_columns
    if TERM_SOURCE_COL or TERM_SOURCE_COL_ALT in all_columns:
        color_options.append(TERM_BLEND_OPTION)
    color_col = st.sidebar.selectbox(
        "Color column",
        options=color_options,
        index=0
    )

    point_size = st.sidebar.slider("Point size", 1, 30, 8)
    marker_opacity = st.sidebar.slider("Opacity", 0.1, 1.0, 0.7)
    max_texts = st.sidebar.number_input(
        "Maximum number of selected texts to display",
        min_value=10,
        max_value=10000,
        value=500
    )
    # Year sidebar settings and filtering
    if YEAR_COL in df.columns:
        year_values = df[YEAR_COL].dropna()

        if not year_values.empty:
            year_min = int(year_values.min())
            year_max = int(year_values.max())

            selected_years = st.sidebar.slider(
                "Year range",
                min_value=year_min,
                max_value=year_max,
                value=(year_min, year_max),
                step=1
            )

            df = df[
                (df[YEAR_COL] >= selected_years[0]) &
                (df[YEAR_COL] <= selected_years[1])
            ].reset_index(drop=True)

            if df.empty:
                st.warning("No rows remain after applying the Year filter.")
                st.stop()

            animate_time = st.sidebar.checkbox("Animate 10-year moving window", value=False)

            if animate_time:
                window_size = st.sidebar.slider(
                    "Years on each side of center year",
                    min_value=1,
                    max_value=20,
                    value=5,
                    step=1
                )
                frame_duration = st.sidebar.slider(
                    "Animation speed (ms per frame)",
                    min_value=50,
                    max_value=200,
                    value=100,
                    step=50
                )
        else:
            animate_time = False
            st.sidebar.info("Column 'Year' exists, but contains no valid numeric values.")
    else:
        animate_time = False
    
    # Ensure text column is string
    df[text_col] = df[text_col].astype(str)

    # Defaults for plotting
    plot_color_col = None
    color_discrete_map = None
    category_orders = None
    use_term_blend = False

    if color_col == GOAL_COL:
        color_mode = st.sidebar.radio(
            "Goal of advertisement display mode",
            options=["Show all options", "Show merged options"],
            index=0
        )

        df, plot_color_col, color_discrete_map, category_orders = prepare_goal_of_advertisement(
            df, color_mode
        )

    elif color_col == LOCATION_COL:
        color_mode = st.sidebar.radio(
            "Location publisher display mode",
            options=["Show all options", "Show merged options"],
            index=0
        )

        df, plot_color_col, color_discrete_map, category_orders = prepare_location_publisher(
            df, color_mode
        )

    elif color_col == AGE_COL:
        df, plot_color_col, color_discrete_map, category_orders = prepare_age_groups(df)

    elif color_col in RELIGION_COLS:
        color_mode = st.sidebar.radio(
            f"{color_col} display mode",
            options=["Show all options", "Show merged options"],
            index=0
        )

        df, plot_color_col, color_discrete_map, category_orders = prepare_religion_column(
            df, color_col, color_mode
        )

    elif color_col == TERM_BLEND_OPTION:
        if TERM_SOURCE_COL not in df.columns:
            df = prepare_term_blend(df, TERM_SOURCE_COL_ALT)
        else:
            df = prepare_term_blend(df, TERM_SOURCE_COL)
        use_term_blend = True

        # No categorical legend in this mode
        plot_color_col = None
        color_discrete_map = None
        category_orders = None

    elif color_col != "None":
        plot_color_col = color_col

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

    # Static-only minimum group size filter for categorical color groups
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

                # Also trim category order so removed groups do not linger conceptually
                if category_orders is not None and plot_color_col in category_orders:
                    kept_set = set(keep_groups)
                    category_orders = {
                        **category_orders,
                        plot_color_col: [
                            cat for cat in category_orders[plot_color_col]
                            if cat in kept_set
                        ]
                    }

    # Build plot
    df = df.copy()
    df["_row_id"] = range(len(df))
    df["hover_text_wrapped"] = df[text_col].apply(lambda x: wrap_hover_text(x, width=50, max_lines=10))

    custom_data_cols = ["_row_id", "hover_text_wrapped"]

    if use_term_blend:
        custom_data_cols += [
            "modern_count_unique",
            "hobby_count_unique",
            "trad_count_unique"
        ]

    base_plot_kwargs = dict(
        x="x",
        y="y",
        custom_data=custom_data_cols,
    )

    # Use WebGL only in static non-term-blend mode
    if not animate_time and not use_term_blend:
        base_plot_kwargs["render_mode"] = "webgl"

    # Fixed axis range
    x_pad = max((df["x"].max() - df["x"].min()) * 0.05, 1e-6)
    y_pad = max((df["y"].max() - df["y"].min()) * 0.05, 1e-6)
    x_range = [df["x"].min() - x_pad, df["x"].max() + x_pad]
    y_range = [df["y"].min() - y_pad, df["y"].max() + y_pad]

    if use_term_blend:
        hover_template = (
            "<b>%{customdata[1]}</b><br>"
            "Modern terms: %{customdata[2]}<br>"
            "Hobby terms: %{customdata[3]}<br>"
            "Traditional terms: %{customdata[4]}<br>"
            "x=%{x}<br>"
            "y=%{y}<extra></extra>"
        )
    else:
        hover_template = (
            "<b>%{customdata[1]}</b><br>"
            "x=%{x}<br>"
            "y=%{y}<extra></extra>"
        )

    if animate_time and use_term_blend:
        df_anim = build_time_window_df(df, year_col=YEAR_COL, window_size=window_size)

        if df_anim.empty:
            st.warning("Not enough valid years to build the animation for this window size.")
            st.stop()

        df_anim = df_anim.sort_values(["frame_year", "_row_id"]).reset_index(drop=True)

        fig = build_term_blend_animation_figure(
            df_anim=df_anim,
            point_size=point_size,
            marker_opacity=marker_opacity,
            x_range=x_range,
            y_range=y_range,
            frame_duration=frame_duration
        )

    elif animate_time:
        if plot_color_col is not None and category_orders is not None:
            if plot_color_col in category_orders:
                df[plot_color_col] = pd.Categorical(
                    df[plot_color_col],
                    categories=category_orders[plot_color_col],
                    ordered=True
                )

        df_anim = build_time_window_df(df, year_col=YEAR_COL, window_size=window_size)

        if df_anim.empty:
            st.warning("Not enough valid years to build the animation for this window size.")
            st.stop()

        if category_orders is not None and plot_color_col in category_orders:
            df_anim = add_animation_category_dummies(
                df_anim,
                color_col=plot_color_col,
                categories=category_orders[plot_color_col]
            )

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

        fig.update_traces(
            marker=dict(size=point_size, opacity=marker_opacity),
            selector=dict(mode="markers")
        )

        fig.update_layout(
            height=700,
            dragmode="pan",
            margin=dict(l=10, r=10, t=40, b=10),
            xaxis_title="x",
            yaxis_title="y",
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
            uirevision="keep_zoom",
            margin=dict(l=10, r=10, t=40, b=10),
            xaxis_title="x",
            yaxis_title="y",
            legend_title_text=plot_color_col if plot_color_col is not None else "",
            showlegend=not use_term_blend
        )

        fig.update_xaxes(range=x_range)
        fig.update_yaxes(range=y_range)

    left, right = st.columns([2, 1], gap="large")

    with left:
        st.subheader("Scatter Plot")

        if animate_time:
            st.caption("Use the Play button below the chart to animate the moving year window.")
            event = st.plotly_chart(
                fig,
                use_container_width=True,
                key="scatter_plot_variant_animated",
                config={
                    "scrollZoom": True,
                    "displaylogo": False
                }
            )
        else:
            event = st.plotly_chart(
                fig,
                use_container_width=True,
                key="scatter_plot_variant",
                on_select="rerun",
                selection_mode=("box", "lasso"),
                config={
                    "scrollZoom": True,
                    "displaylogo": False
                }
            )

    # Read selected points
    selected_indices = []

    if not animate_time:
        try:
            if event and event.selection and event.selection.points:
                selected_indices = [p["point_index"] for p in event.selection.points]
        except Exception:
            try:
                selected_indices = [p["point_index"] for p in event["selection"]["points"]]
            except Exception:
                selected_indices = []

    with right:
        st.subheader("Selection")

        if animate_time:
            st.info("Selection is disabled in animation mode. Turn off animation to lasso points and inspect text.")
        elif selected_indices:
            selected_df = df.iloc[selected_indices]

            st.success(f"{len(selected_df)} point(s) selected")

            shown_df = selected_df.head(max_texts)

            st.text_area(
                "Selected text",
                value="\n\n".join(shown_df[text_col].astype(str).tolist()),
                height=500
            )

            with st.expander("Show selected rows"):
                st.dataframe(selected_df, use_container_width=True)

            csv_selected = selected_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download selection as CSV",
                data=csv_selected,
                file_name="selection.csv",
                mime="text/csv"
            )
        else:
            st.info("Select points using lasso or box selection.")

    st.divider()
    st.subheader("Data Preview")
    st.dataframe(df.head(20), use_container_width=True)

else:
    st.info("Please upload a CSV file first.")
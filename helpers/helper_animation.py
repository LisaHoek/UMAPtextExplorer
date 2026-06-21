import pandas as pd
import plotly.graph_objects as go


def build_time_window_df(df, year_col="Year", window_size=5):
    """
    Build an animated dataframe where each frame shows a moving year window.
    Example: window_size=5 means center_year-5 through center_year+5.
    """
    df = df.copy()

    if year_col not in df.columns:
        return pd.DataFrame()

    year_values = pd.to_numeric(df[year_col], errors="coerce").dropna().astype(int)
    if year_values.empty:
        return pd.DataFrame()

    df[year_col] = pd.to_numeric(df[year_col], errors="coerce")
    df = df.dropna(subset=[year_col]).copy()
    df[year_col] = df[year_col].astype(int)

    min_year = int(df[year_col].min())
    max_year = int(df[year_col].max())

    frames = []
    for center_year in range(min_year + window_size, max_year - window_size + 1):
        start = center_year - window_size
        end = center_year + window_size

        temp_df = df[(df[year_col] >= start) & (df[year_col] <= end)].copy()
        temp_df["frame_year"] = center_year
        temp_df["frame_label"] = f"{start}–{end}"
        frames.append(temp_df)

    if not frames:
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True)


def _apply_animation_layout(
    fig,
    frame_labels,
    first_label,
    frame_duration,
    x_range,
    y_range,
    x_col,
    y_col,
    show_legend=True,
    legend_title_text="",
):
    fig.update_layout(
        height=700,
        dragmode="pan",
        margin=dict(l=10, r=10, t=40, b=120),
        xaxis_title=x_col,
        yaxis_title=y_col,
        showlegend=show_legend,
        legend_title_text=legend_title_text,
        title=f"Context window: {first_label}",
        xaxis=dict(range=x_range),
        yaxis=dict(range=y_range),
        updatemenus=[
            dict(
                type="buttons",
                direction="left",
                x=0.0,
                xanchor="left",
                y=-0.10,
                yanchor="top",
                pad=dict(r=10, t=0),
                showactive=False,
                buttons=[
                    dict(
                        label="Play",
                        method="animate",
                        args=[
                            None,
                            {
                                "frame": {"duration": frame_duration, "redraw": True},
                                "transition": {"duration": 0},
                                "fromcurrent": True,
                                "mode": "immediate",
                            },
                        ],
                    ),
                    dict(
                        label="Pause",
                        method="animate",
                        args=[
                            [None],
                            {
                                "frame": {"duration": 0, "redraw": False},
                                "transition": {"duration": 0},
                                "mode": "immediate",
                            },
                        ],
                    ),
                ],
            )
        ],
        sliders=[
            dict(
                active=0,
                currentvalue={"prefix": "Window: "},
                x=0.0,
                xanchor="left",
                y=-0.18,
                yanchor="top",
                len=1.0,
                pad={"t": 0, "b": 0},
                steps=[
                    dict(
                        label=label,
                        method="animate",
                        args=[
                            [label],
                            {
                                "frame": {"duration": 0, "redraw": True},
                                "transition": {"duration": 0},
                                "mode": "immediate",
                            },
                        ],
                    )
                    for label in frame_labels
                ],
            )
        ],
    )


def build_categorical_animation_figure(
    df_anim,
    x_col,
    y_col,
    color_col,
    categories,
    point_size,
    marker_opacity,
    x_range,
    y_range,
    frame_duration,
    hover_template,
    custom_data_cols,
    color_discrete_map=None,
    legend_title_text="",
):
    """
    Build a stable Plotly animation for categorical colors using one trace
    per category in every frame.

    This avoids Plotly Express legend/category issues when some categories
    do not appear in the first animation frames.
    """
    frame_info = (
        df_anim[["frame_year", "frame_label"]]
        .drop_duplicates()
        .sort_values("frame_year")
        .reset_index(drop=True)
    )

    if frame_info.empty:
        return go.Figure()

    if not categories:
        categories = (
            df_anim[color_col]
            .dropna()
            .astype(str)
            .drop_duplicates()
            .tolist()
        )

    frame_labels = frame_info["frame_label"].tolist()
    first_label = frame_labels[0]

    def make_trace(frame_df, category):
        cat_df = frame_df[frame_df[color_col] == category].copy()

        marker = dict(
            size=point_size,
            opacity=marker_opacity,
            line=dict(width=0),
        )

        if color_discrete_map is not None and category in color_discrete_map:
            marker["color"] = color_discrete_map[category]

        existing_custom_cols = [col for col in custom_data_cols if col in cat_df.columns]
        if existing_custom_cols:
            customdata = cat_df[existing_custom_cols].to_numpy()
        else:
            customdata = None

        return go.Scatter(
            x=cat_df[x_col].tolist(),
            y=cat_df[y_col].tolist(),
            mode="markers",
            name=str(category),
            legendgroup=str(category),
            showlegend=True,
            marker=marker,
            customdata=customdata,
            hovertemplate=hover_template,
        )

    first_df = df_anim[df_anim["frame_label"] == first_label]

    initial_traces = [
        make_trace(first_df, category)
        for category in categories
    ]

    frames = []
    for _, row in frame_info.iterrows():
        label = row["frame_label"]
        frame_df = df_anim[df_anim["frame_label"] == label]

        frame_traces = [
            make_trace(frame_df, category)
            for category in categories
        ]

        frames.append(
            go.Frame(
                name=label,
                data=frame_traces,
                layout=go.Layout(
                    title_text=f"Context window: {label}"
                )
            )
        )

    fig = go.Figure(
        data=initial_traces,
        frames=frames
    )

    _apply_animation_layout(
        fig,
        frame_labels=frame_labels,
        first_label=first_label,
        frame_duration=frame_duration,
        x_range=x_range,
        y_range=y_range,
        x_col=x_col,
        y_col=y_col,
        show_legend=True,
        legend_title_text=legend_title_text,
    )

    return fig


def build_term_blend_animation_figure(
    df_anim,
    point_size,
    marker_opacity,
    x_range,
    y_range,
    frame_duration,
    x_col="x",
    y_col="y",
):
    """
    Build a Plotly animation for term-blend colors.
    Uses one scatter trace per frame with precomputed RGB colors.
    """
    frame_info = (
        df_anim[["frame_year", "frame_label"]]
        .drop_duplicates()
        .sort_values("frame_year")
        .reset_index(drop=True)
    )

    if frame_info.empty:
        return go.Figure()

    frame_labels = frame_info["frame_label"].tolist()
    first_label = frame_labels[0]

    def make_trace(frame_df):
        customdata = list(zip(
            frame_df["_row_id"],
            frame_df["hover_text_wrapped"],
            frame_df["modern_count_unique"],
            frame_df["hobby_count_unique"],
            frame_df["trad_count_unique"],
        ))

        return go.Scatter(
            x=frame_df["x"],
            y=frame_df["y"],
            mode="markers",
            marker=dict(
                color=frame_df["term_rgb_color"].tolist(),
                size=point_size,
                opacity=marker_opacity,
                line=dict(width=0)
            ),
            customdata=customdata,
            hovertemplate=(
                "<b>%{customdata[1]}</b><br>"
                "Modern terms: %{customdata[2]}<br>"
                "Hobby terms: %{customdata[3]}<br>"
                "Traditional terms: %{customdata[4]}<br>"
                "x=%{x}<br>"
                "y=%{y}<extra></extra>"
            ),
            showlegend=False
        )

    first_df = df_anim[df_anim["frame_label"] == first_label]

    frames = []
    for _, row in frame_info.iterrows():
        label = row["frame_label"]
        frame_df = df_anim[df_anim["frame_label"] == label]

        frames.append(
            go.Frame(
                name=label,
                data=[make_trace(frame_df)],
                layout=go.Layout(
                    title_text=f"Context window: {label}"
                )
            )
        )

    fig = go.Figure(
        data=[make_trace(first_df)],
        frames=frames
    )

    _apply_animation_layout(
        fig,
        frame_labels=frame_labels,
        first_label=first_label,
        frame_duration=frame_duration,
        x_range=x_range,
        y_range=y_range,
        x_col=x_col,
        y_col=y_col,
        show_legend=False,
    )

    return fig

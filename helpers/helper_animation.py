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

def add_animation_category_dummies(df_anim, color_col, categories, x_col="x", y_col="y"):
    """
    Add one off-screen dummy point per category per frame.
    This keeps Plotly animation traces stable across frames.
    """
    if df_anim.empty:
        return df_anim

    x_span = df_anim[x_col].max() - df_anim[x_col].min()
    y_span = df_anim[y_col].max() - df_anim[y_col].min()

    dummy_x = df_anim[x_col].min() - max(x_span * 100, 1)
    dummy_y = df_anim[y_col].min() - max(y_span * 100, 1)

    dummy_rows = []

    frame_info = df_anim[["frame_year", "frame_label"]].drop_duplicates()

    for _, row in frame_info.iterrows():
        for cat in categories:
            dummy_rows.append({
                x_col: dummy_x,
                y_col: dummy_y,
                color_col: cat,
                "frame_year": row["frame_year"],
                "frame_label": row["frame_label"],
                "_row_id": f"dummy_{cat}_{row['frame_year']}",
                "hover_text_wrapped": "",
            })

    df_dummy = pd.DataFrame(dummy_rows)
    return pd.concat([df_anim, df_dummy], ignore_index=True)

def build_term_blend_animation_figure(
    df_anim,
    point_size,
    marker_opacity,
    x_range,
    y_range,
    frame_duration
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
                "<b>%{customdata[0]}</b><br>"
                "Modern terms: %{customdata[1]}<br>"
                "Hobby terms: %{customdata[2]}<br>"
                "Traditional terms: %{customdata[3]}<br>"
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

    fig.update_layout(
        height=700,
        dragmode="pan",
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis_title="x",
        yaxis_title="y",
        showlegend=False,
        title=f"Context window: {first_label}",
        xaxis=dict(range=x_range),
        yaxis=dict(range=y_range),
        updatemenus=[
            dict(
                type="buttons",
                direction="left",
                x=0.0,
                y=1.08,
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
                pad={"t": 40},
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

    return fig
import pandas as pd
import textwrap

def wrap_hover_text(text, width=50, max_lines=4):
    if pd.isna(text):
        return ""
    lines = textwrap.wrap(str(text), width=width)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1] + " ..."
    return "<br>".join(lines)
from pathlib import Path

import pandas as pd
from dash import Dash, dcc, html, Input, Output
import plotly.graph_objects as go

# ---------- Paths & data ----------

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_PATH = SCRIPT_DIR / "data" / "dc_impact_summary.csv"

df = pd.read_csv(DATA_PATH)

# Make sure year is int
df["year"] = df["year"].astype(int)

print("Loaded dc_impact_summary.csv:")
print(df.head())

# Metrics we support
METRICS = {
    "energy_TWh": ("energy_TWh", "Energy use (TWh)"),
    "water_Mm3": ("water_Mm3", "Water use (million m³)"),
    "carbon_MtCO2": ("carbon_MtCO2", "Carbon emissions (Mt CO₂)"),
}

YEARS = sorted(df["year"].unique())
YEAR_MIN, YEAR_MAX = int(min(YEARS)), int(max(YEARS))

# Fixed colors per scenario so legend + lines are consistent
SCENARIO_COLORS = {
    "Best carbon": "#60a5fa",   # blue
    "Best water": "#22c55e",    # green
    "Worst carbon": "#f97316",  # orange
    "Worst water": "#a855f7",   # purple
}


# ---------- Small helper for KPI chips ----------

def _kpi_chip(label, value, year, unit):
    subtitle = f"in {year}" if year is not None else "across selection"
    return html.Div(
        style={
            "padding": "10px 12px",
            "borderRadius": "999px",
            "border": "1px solid #1f2937",
            "backgroundColor": "#020617",
            "minWidth": "120px",
        },
        children=[
            html.Div(
                label,
                style={
                    "fontSize": "11px",
                    "textTransform": "uppercase",
                    "letterSpacing": "0.06em",
                    "color": "#9ca3af",
                    "marginBottom": "2px",
                },
            ),
            html.Div(
                f"{value:,.2f} {unit}",
                style={"fontSize": "15px", "fontWeight": "600"},
            ),
            html.Div(
                subtitle,
                style={"fontSize": "11px", "color": "#9ca3af"},
            ),
        ],
    )


# ---------- Dash app ----------

app = Dash(__name__)
server = app.server  #

app.layout = html.Div(
    style={
        "backgroundColor": "#020617",
        "minHeight": "100vh",
        "padding": "32px 24px 40px 24px",
        "fontFamily": "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    },
    children=[
        html.Div(
            style={
                "maxWidth": "1200px",
                "margin": "0 auto",
                "color": "#e5e7eb",
            },
            children=[
                # ---------- Header ----------
                html.Div(
                    style={"marginBottom": "24px", "textAlign": "center"},
                    children=[
                        html.H1(
                            "Projected Environmental Impact of Data Centers(2025–2030)",
                            style={"marginBottom": "8px", "fontSize": "30px"},
                        ),
                        html.P(
                            "This dashboard shows projected water use and carbon emissions from AI data centers "
                            "under different deployment scenarios. Use the controls below to switch metrics, "
                            "compare scenarios, and focus on specific years.",
                            style={
                                "color": "#9ca3af",
                                "fontSize": "14px",
                                "maxWidth": "820px",
                                "margin": "0 auto",
                            },
                        ),
                    ],
                ),

                # ---------- Control panel ----------
                html.Div(
                    style={
                        "display": "flex",
                        "flexWrap": "wrap",
                        "gap": "16px",
                        "marginBottom": "18px",
                        "alignItems": "flex-end",
                    },
                    children=[
                        # Metric dropdown
                        html.Div(
                            style={"flex": "1 1 240px"},
                            children=[
                                html.Label(
                                    "Metric",
                                    style={"fontWeight": "600", "fontSize": "13px"},
                                ),
                                dcc.Dropdown(
                                    id="metric-dropdown",
                                    options=[
                                        {"label": label, "value": key}
                                        for key, (col, label) in METRICS.items()
                                    ],
                                    value="carbon_MtCO2",
                                    clearable=False,
                                    style={"color": "#020617"},
                                ),
                            ],
                        ),
                        # Scenario checklist
                        html.Div(
                            style={"flex": "2 1 360px"},
                            children=[
                                html.Label(
                                    "Scenarios",
                                    style={"fontWeight": "600", "fontSize": "13px"},
                                ),
                                dcc.Checklist(
                                    id="scenario-checklist",
                                    options=[
                                        {"label": s, "value": s}
                                        for s in sorted(df["scenario"].unique())
                                    ],
                                    value=sorted(df["scenario"].unique()),
                                    inline=True,
                                    style={"marginTop": "6px", "fontSize": "13px"},
                                ),
                            ],
                        ),
                        # Chart style toggle
                        html.Div(
                            style={"flex": "0 0 180px"},
                            children=[
                                html.Label(
                                    "Chart style",
                                    style={"fontWeight": "600", "fontSize": "13px"},
                                ),
                                dcc.RadioItems(
                                    id="chart-style-radio",
                                    options=[
                                        {"label": "Line", "value": "line"},
                                        {"label": "Area", "value": "area"},
                                    ],
                                    value="line",
                                    inline=True,
                                    style={"marginTop": "6px", "fontSize": "13px"},
                                ),
                            ],
                        ),
                    ],
                ),

                # Year range slider
                html.Div(
                    style={
                        "backgroundColor": "#020617",
                        "borderRadius": "10px",
                        "padding": "10px 16px 4px 4px",
                        "marginBottom": "18px",
                    },
                    children=[
                        html.Label(
                            "Year range",
                            style={"fontWeight": "600", "fontSize": "13px"},
                        ),
                        dcc.RangeSlider(
                            id="year-range-slider",
                            min=YEAR_MIN,
                            max=YEAR_MAX,
                            value=[YEAR_MIN, YEAR_MAX],
                            marks={int(y): str(int(y)) for y in YEARS},
                            step=None,
                            tooltip={"placement": "bottom", "always_visible": False},
                        ),
                    ],
                ),

                # ---------- Main chart card ----------
                html.Div(
                    style={
                        "backgroundColor": "#020617",
                        "borderRadius": "14px",
                        "padding": "14px 14px 4px 14px",
                        "boxShadow": "0 16px 40px rgba(15,23,42,0.9)",
                        "border": "1px solid #1f2937",
                        "marginBottom": "24px",
                    },
                    children=[
                        dcc.Graph(
                            id="impact-graph",
                            config={"displayModeBar": True},
                            style={"height": "460px"},
                        )
                    ],
                ),

                # ---------- KPI + data source summary ----------
                html.Div(
                    id="metric-summary",
                    style={
                        "display": "flex",
                        "flexWrap": "wrap",
                        "gap": "16px",
                        "marginBottom": "24px",
                    },
                ),
            ],
        )
    ],
)


# ---------- Callback ----------

@app.callback(
    Output("impact-graph", "figure"),
    Output("metric-summary", "children"),
    Input("metric-dropdown", "value"),
    Input("scenario-checklist", "value"),
    Input("year-range-slider", "value"),
    Input("chart-style-radio", "value"),
)
def update_graph(metric_key, selected_scenarios, year_range, chart_style):
    # If Dash passes None
    if not selected_scenarios:
        selected_scenarios = []

    # 1. Metric + label
    if metric_key not in METRICS:
        metric_key = list(METRICS.keys())[0]
    col_name, y_label = METRICS[metric_key]

    # For hover: split into name + unit
    if "(" in y_label:
        metric_name = y_label.split(" (")[0]
        unit = y_label.split("(", 1)[1].rstrip(")")
    else:
        metric_name = y_label
        unit = ""

    # 2. Year range
    if not year_range or len(year_range) != 2:
        start_year, end_year = YEAR_MIN, YEAR_MAX
    else:
        start_year, end_year = map(int, year_range)

    hover_text = (
        "<b>Scenario:</b> %{name}<br>"
        "<b>Year:</b> %{x}<br>"
        f"<b>{metric_name}:</b> %{{y:,.2f}} {unit}<extra></extra>"
    )

    # ---------- Build figure with ALL scenarios ----------
    #   • Every scenario always has a trace (so legend is stable)
    #   • If a scenario is not selected, we set visible="legendonly"
    all_scenarios = sorted(df["scenario"].unique())
    fig = go.Figure()

    for scenario in all_scenarios:
        mask = (
            (df["scenario"] == scenario)
            & (df["year"] >= start_year)
            & (df["year"] <= end_year)
        )
        scenario_df = df[mask].sort_values("year")
        if scenario_df.empty:
            continue

        is_selected = scenario in selected_scenarios
        visible = True if is_selected else "legendonly"

        if chart_style == "area":
            mode = "lines"
            fill = "tozeroy" if is_selected else None
        else:
            mode = "lines+markers"
            fill = None

        fig.add_trace(
            go.Scatter(
                x=scenario_df["year"],
                y=scenario_df[col_name],
                name=scenario,
                mode=mode,
                line=dict(
                    width=3,
                    color=SCENARIO_COLORS.get(scenario, None),
                ),
                fill=fill,
                visible=visible,
                hovertemplate=hover_text,
            )
        )

    # 3. Layout
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#020617",
        title={
            "text": f"{y_label} by scenario",
            "x": 0.5,
            "xanchor": "center",
        },
        margin=dict(l=50, r=20, t=60, b=60),
        xaxis_title="Year",
        yaxis_title=y_label,
        hovermode="x unified",
        legend=dict(
            title="Scenario",
            orientation="h",
            yanchor="top",
            y=-0.18,
            xanchor="left",
            x=0.0,
            bgcolor="rgba(15,23,42,0.9)",
            bordercolor="rgba(55,65,81,0.8)",
            borderwidth=1,
        ),
        font=dict(size=13, color="#e5e7eb"),
    )

    # ---------- KPI summary (only over selected scenarios) ----------
    metrics_mask = (
        df["scenario"].isin(selected_scenarios)
        & (df["year"] >= start_year)
        & (df["year"] <= end_year)
    )
    filtered = df[metrics_mask].copy()

    if filtered.empty:
        # Still show the card, just with a friendly note
        summary_block = html.Div(
            style={
                "display": "flex",
                "flexWrap": "wrap",
                "gap": "16px",
                "width": "100%",
            },
            children=[
                html.Div(
                    style={
                        "flex": "2 1 320px",
                        "backgroundColor": "#020617",
                        "borderRadius": "14px",
                        "padding": "16px 18px",
                        "boxShadow": "0 12px 30px rgba(15,23,42,0.8)",
                        "border": "1px solid #1f2937",
                    },
                    children=[
                        html.H3(
                            "Quick metrics",
                            style={"marginBottom": "8px", "fontSize": "16px"},
                        ),
                        html.P(
                            "Select at least one scenario to see summary metrics.",
                            style={"color": "#9ca3af", "fontSize": "12px"},
                        ),
                    ],
                ),
                html.Div(
                    style={
                        "flex": "1 1 260px",
                        "backgroundColor": "#020617",
                        "borderRadius": "14px",
                        "padding": "16px 18px",
                        "boxShadow": "0 12px 30px rgba(15,23,42,0.8)",
                        "border": "1px solid #1f2937",
                    },
                    children=[
                        html.H3(
                            "Data notes & sources",
                            style={"marginBottom": "8px", "fontSize": "16px"},
                        ),
                        html.Ul(
                            style={
                                "fontSize": "12px",
                                "color": "#d1d5db",
                                "paddingLeft": "18px",
                            },
                            children=[
                                html.Li(
                                    "Values are scenario-based projections for AI data centers, 2025–2030."
                                ),
                                html.Li(
                                    "Inspired by public estimates from IEA reports, academic work on AI energy use, "
                                    "and cloud provider sustainability disclosures."
                                ),
                                html.Li(
                                    "Use these numbers directionally to compare scenarios rather than as precise forecasts."
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        )
        return fig, summary_block

    metric_series = filtered[col_name]
    metric_max = metric_series.max()
    metric_min = metric_series.min()
    metric_mean = metric_series.mean()

    year_max = int(filtered.loc[metric_series.idxmax(), "year"])
    year_min = int(filtered.loc[metric_series.idxmin(), "year"])

    summary_block = html.Div(
        style={
            "display": "flex",
            "flexWrap": "wrap",
            "gap": "16px",
            "width": "100%",
        },
        children=[
            # KPI cards
            html.Div(
                style={
                    "flex": "2 1 320px",
                    "backgroundColor": "#020617",
                    "borderRadius": "14px",
                    "padding": "16px 18px",
                    "boxShadow": "0 12px 30px rgba(15,23,42,0.8)",
                    "border": "1px solid #1f2937",
                },
                children=[
                    html.H3(
                        "Quick metrics",
                        style={"marginBottom": "8px", "fontSize": "16px"},
                    ),
                    html.P(
                        "Across selected years and scenarios.",
                        style={"color": "#9ca3af", "fontSize": "12px"},
                    ),
                    html.Div(
                        style={
                            "display": "flex",
                            "flexWrap": "wrap",
                            "gap": "12px",
                            "marginTop": "10px",
                        },
                        children=[
                            _kpi_chip("Highest", metric_max, year_max, unit),
                            _kpi_chip("Lowest", metric_min, year_min, unit),
                            _kpi_chip("Average", metric_mean, None, unit),
                        ],
                    ),
                ],
            ),
            # Data sources / reading
            html.Div(
                style={
                    "flex": "1 1 260px",
                    "backgroundColor": "#020617",
                    "borderRadius": "14px",
                    "padding": "16px 18px",
                    "boxShadow": "0 12px 30px rgba(15,23,42,0.8)",
                    "border": "1px solid #1f2937",
                },
                children=[
                    html.H3(
                        "Data notes & sources",
                        style={"marginBottom": "8px", "fontSize": "16px"},
                    ),
                    html.Ul(
                        style={
                            "fontSize": "12px",
                            "color": "#d1d5db",
                            "paddingLeft": "18px",
                        },
                        children=[
                            html.Li(
                                "Values are scenario-based projections for AI data centers, 2025–2030."
                            ),
                            html.Li(
                                "Inspired by public estimates from IEA reports, academic work on AI energy use, "
                                "and cloud provider sustainability disclosures."
                            ),
                            html.Li(
                                "Use these numbers directionally to compare scenarios rather than as precise forecasts."
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )

    return fig, summary_block


# ---------- Entry point ----------

if __name__ == "__main__":
    app.run(debug=True, port=8051)

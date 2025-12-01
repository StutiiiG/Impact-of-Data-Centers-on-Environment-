from pathlib import Path

import pandas as pd
from dash import Dash, dcc, html, Input, Output
import plotly.express as px

# ---------- Paths & data ----------

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_PATH = SCRIPT_DIR / "data" / "dc_impact_summary.csv"

df = pd.read_csv(DATA_PATH)

# Sanity check: print a bit of the data when app starts
print("Loaded dc_impact_summary.csv:")
print(df.head())

# Map metric keys to column names + pretty labels + units
METRICS = {

    "water_Mm3": ("water_Mm3", "Water use (million m³)"),
    "carbon_MtCO2": ("carbon_MtCO2", "Carbon emissions (Mt CO₂)"),
}

# ---------- Dash app ----------

app = Dash(__name__)

app.layout = html.Div(
    style={
        "maxWidth": "1000px",
        "margin": "40px auto",
        "fontFamily": "Arial, sans-serif",
        "padding": "0 20px",
    },
    children=[
        html.H1("AI Data Center Environmental Impact (2025–2030)"),

        html.P(
            "Explore projected energy, water, and carbon impacts under different "
            "AI data center scenarios (best vs worst, water vs carbon)."
        ),

        # Controls row
        html.Div(
            style={"display": "flex", "gap": "24px", "marginBottom": "24px"},
            children=[
                # Metric dropdown
                html.Div(
                    style={"flex": 1},
                    children=[
                        html.Label("Metric", style={"fontWeight": "bold"}),
                        dcc.Dropdown(
                            id="metric-dropdown",
                            options=[
                                {"label": label, "value": key}
                                for key, (col, label) in METRICS.items()
                            ],
                            value="water_Mm3",  # default metric
                            clearable=False,
                        ),
                    ],
                ),
                # Scenario multi-select
                html.Div(
                    style={"flex": 1},
                    children=[
                        html.Label("Scenarios", style={"fontWeight": "bold"}),
                        dcc.Checklist(
                            id="scenario-checklist",
                            options=[
                                {"label": s, "value": s}
                                for s in sorted(df["scenario"].unique())
                            ],
                            value=sorted(df["scenario"].unique()),  # all selected by default
                            inline=True,
                        ),
                    ],
                ),
            ],
        ),

        # Graph
        dcc.Graph(id="impact-graph"),

        # Optional: little table preview of the data
        html.H3("Data preview"),
        html.Div(
            id="table-preview",
            style={
                "maxHeight": "250px",
                "overflowY": "auto",
                "border": "1px solid #ccc",
                "padding": "8px",
                "borderRadius": "4px",
                "fontSize": "13px",
            },
        ),
    ],
)


# ---------- Callbacks ----------

@app.callback(
    Output("impact-graph", "figure"),
    Input("metric-dropdown", "value"),
    Input("scenario-checklist", "value"),
)
def update_graph(metric_key, selected_scenarios):
    """
    Update the line chart when user changes metric or scenarios.
    """
    col_name, y_label = METRICS[metric_key]

    if not selected_scenarios:
        # If user deselects everything, show empty plot with message
        fig = px.line()
        fig.update_layout(
            title="Select at least one scenario to view the chart",
            xaxis_title="Year",
            yaxis_title=y_label,
        )
        return fig

    filtered = df[df["scenario"].isin(selected_scenarios)]

    fig = px.line(
        filtered,
        x="year",
        y=col_name,
        color="scenario",
        markers=True,
        title=f"{y_label} by scenario (2025–2030)",
    )

    fig.update_layout(
        xaxis_title="Year",
        yaxis_title=y_label,
        legend_title="Scenario",
        template="plotly_white",
    )

    fig.update_traces(mode="lines+markers")

    return fig


@app.callback(
    Output("table-preview", "children"),
    Input("metric-dropdown", "value"),
)
def update_table(metric_key):
    """
    Show a small HTML table so you can sanity-check the numbers driving the plot.
    """
    col_name, y_label = METRICS[metric_key]

    preview_cols = ["year", "scenario", col_name]
    preview_df = df[preview_cols].copy().sort_values(["year", "scenario"])

    # Build a simple HTML table manually
    header = html.Tr([html.Th(c) for c in preview_cols])
    rows = []
    for _, row in preview_df.iterrows():
        rows.append(html.Tr([html.Td(row[c]) for c in preview_cols]))

    return html.Table(
        [header] + rows,
        style={"width": "100%", "borderCollapse": "collapse"},
    )


# ---------- Entry point ----------

if __name__ == "__main__":
    app.run(debug=True)

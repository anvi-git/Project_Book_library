# ============================================================
# Bookshelf Interactive Dashboard  —  Plotly / Dash
# Our World in Data-inspired style
# ============================================================
# Run with:  python dashboard.py
# Then open  http://127.0.0.1:8050  in your browser.
#
# Required packages:
#   pandas dash plotly
#
# Folder structure expected:
#   dashboard.py
#   books.csv
#   assets/custom.css   <- auto-loaded by Dash
# ============================================================

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, dash_table

# ── 1. Load & clean ─────────────────────────────────────────
df = pd.read_csv("books.csv")
df.columns = df.columns.str.strip()
df = df[df["title"].notna()]
df["pages"]      = pd.to_numeric(df["pages"], errors="coerce")
df["year_pub"]   = pd.to_numeric(df["year of publication"], errors="coerce")
df["sex"]        = df["sex"].str.strip().str.lower()
df["country_clean"]   = df["country"].str.split("-").str[0].str.strip()
df["author_clean"]    = df["author"].str.strip().str.title()
df["publisher_clean"] = df["publisher"].str.strip().str.title()
df["language"]   = df["language"].fillna("unknown").str.strip()

# ── 2. Design tokens (OWID-inspired) ────────────────────────
ACCENT       = "#01696f"
ACCENT_LIGHT = "#4f98a3"
ACCENT_PALE  = "#cedcd8"
BG           = "#f7f6f2"
SURFACE      = "#ffffff"
TEXT_MAIN    = "#28251d"
TEXT_MUTED   = "#7a7974"
BORDER       = "#dcd9d5"

OWID_PALETTE = [
    "#01696f", "#4f98a3", "#a2c4c9",
    "#964219", "#bb653b", "#d19900",
    "#437a22", "#6daa45", "#a12c7b",
    "#006494", "#7a39bb",
]

CHART_LAYOUT = dict(
    font=dict(family="Playfair Display, Georgia, serif",
              color=TEXT_MAIN, size=13),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=16, r=16, t=52, b=16),
    title_font=dict(family="Playfair Display, Georgia, serif",
                    size=15, color=TEXT_MAIN),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=BORDER,
                borderwidth=1, font=dict(size=12)),
    xaxis=dict(showgrid=True, gridcolor="#ede9e3", gridwidth=1,
               zeroline=False, linecolor=BORDER,
               tickfont=dict(size=12, color=TEXT_MUTED),
               title_font=dict(size=12, color=TEXT_MUTED)),
    yaxis=dict(showgrid=True, gridcolor="#ede9e3", gridwidth=1,
               zeroline=False, linecolor=BORDER,
               tickfont=dict(size=12, color=TEXT_MUTED),
               title_font=dict(size=12, color=TEXT_MUTED)),
    hoverlabel=dict(bgcolor=SURFACE, bordercolor=ACCENT,
                    font=dict(family="Lato, Helvetica Neue, sans-serif",
                              size=13, color=TEXT_MAIN)),
    transition=dict(duration=500, easing="cubic-in-out"),
    uirevision="constant",
)

# ── 3. App ──────────────────────────────────────────────────
# CSS is loaded automatically from assets/custom.css
# Fonts are loaded via external_stylesheets
app = Dash(
    __name__,
    title="Bookshelf Dashboard",
    external_stylesheets=[
        "https://fonts.googleapis.com/css2?"
        "family=Playfair+Display:wght@400;600;700"
        "&family=Lato:wght@300;400;700&display=swap"
    ],
)

app.layout = html.Div([

    # ── Header ──────────────────────────────────────────────
    html.Div([
        html.Div([
            # Mini bar-chart logo
            html.Div([
                html.Div(style={"width": "10px", "height": "36px",
                                "background": ACCENT, "borderRadius": "2px",
                                "display": "inline-block", "marginRight": "4px",
                                "verticalAlign": "middle"}),
                html.Div(style={"width": "10px", "height": "28px",
                                "background": ACCENT_LIGHT, "borderRadius": "2px",
                                "display": "inline-block", "marginRight": "4px",
                                "verticalAlign": "middle"}),
                html.Div(style={"width": "10px", "height": "20px",
                                "background": ACCENT_PALE, "borderRadius": "2px",
                                "display": "inline-block", "verticalAlign": "middle"}),
            ], style={"display": "inline-flex", "alignItems": "flex-end",
                      "marginRight": "14px", "verticalAlign": "middle"}),
            html.Span("Bookshelf Dashboard", style={
                "fontFamily": "Playfair Display, Georgia, serif",
                "fontSize": "28px", "fontWeight": "700",
                "color": TEXT_MAIN, "verticalAlign": "middle",
                "letterSpacing": "-.01em",
            }),
        ], style={"display": "flex", "alignItems": "center"}),
        html.P(
            f"Personal reading library · {len(df)} books · interactive explorer",
            style={"fontFamily": "Lato, sans-serif", "fontSize": "14px",
                   "color": TEXT_MUTED, "marginTop": "6px"}
        ),
    ], style={"padding": "32px 40px 20px",
              "borderBottom": f"2px solid {ACCENT}",
              "marginBottom": "28px"}),

    # ── Filters ─────────────────────────────────────────────
    html.Div([
        html.Div([
            html.Span("Language", className="filter-label"),
            dcc.Dropdown(
                id="filter-lang",
                options=[{"label": l.title(), "value": l}
                         for l in sorted(df["language"].unique())],
                multi=True, placeholder="All languages…",
                style={"fontSize": "13px"}),
        ], style={"flex": "1", "minWidth": "180px"}),

        html.Div([
            html.Span("Author sex", className="filter-label"),
            dcc.Dropdown(
                id="filter-sex",
                options=[{"label": "Male", "value": "m"},
                         {"label": "Female", "value": "f"}],
                multi=True, placeholder="All…",
                style={"fontSize": "13px"}),
        ], style={"flex": "1", "minWidth": "140px"}),

        html.Div([
            html.Span("Publication year range", className="filter-label"),
            dcc.RangeSlider(
                id="filter-year",
                min=int(df["year_pub"].dropna().min()),
                max=int(df["year_pub"].dropna().max()),
                value=[1800, int(df["year_pub"].dropna().max())],
                marks=None,
                tooltip={"placement": "bottom", "always_visible": True},
                step=1),
        ], style={"flex": "3", "minWidth": "260px"}),

    ], style={"display": "flex", "alignItems": "flex-end",
              "gap": "20px", "flexWrap": "wrap",
              "padding": "0 40px 28px"}),

    # ── KPI row ─────────────────────────────────────────────
    html.Div(id="kpi-row",
             style={"display": "flex", "gap": "16px",
                    "padding": "0 40px 28px", "flexWrap": "wrap"}),

    html.Hr(className="divider", style={"margin": "0 40px 28px"}),

    # ── Charts ──────────────────────────────────────────────
    html.Div([
        # Row 1
        html.Div([
            html.Div([dcc.Graph(id="hist-pages",
                                config={"displayModeBar": False})],
                     className="chart-card",
                     style={"flex": "1", "minWidth": "320px"}),
            html.Div([dcc.Graph(id="hist-year",
                                config={"displayModeBar": False})],
                     className="chart-card",
                     style={"flex": "1", "minWidth": "320px"}),
        ], style={"display": "flex", "gap": "16px",
                  "marginBottom": "16px", "flexWrap": "wrap"}),

        # Row 2
        html.Div([
            html.Div([dcc.Graph(id="scatter-main",
                                config={"displayModeBar": False})],
                     className="chart-card",
                     style={"flex": "2", "minWidth": "400px"}),
            html.Div([dcc.Graph(id="pie-country",
                                config={"displayModeBar": False})],
                     className="chart-card",
                     style={"flex": "1", "minWidth": "300px"}),
        ], style={"display": "flex", "gap": "16px",
                  "marginBottom": "16px", "flexWrap": "wrap"}),

        # Row 3
        html.Div([
            html.Div([dcc.Graph(id="bar-authors",
                                config={"displayModeBar": False})],
                     className="chart-card",
                     style={"flex": "1", "minWidth": "320px"}),
            html.Div([dcc.Graph(id="bar-lang",
                                config={"displayModeBar": False})],
                     className="chart-card",
                     style={"flex": "1", "minWidth": "320px"}),
        ], style={"display": "flex", "gap": "16px",
                  "marginBottom": "16px", "flexWrap": "wrap"}),

        # Row 4
        html.Div([
            html.Div([dcc.Graph(id="tree-publisher",
                                config={"displayModeBar": False})],
                     className="chart-card",
                     style={"flex": "2", "minWidth": "400px"}),
            html.Div([dcc.Graph(id="donut-sex",
                                config={"displayModeBar": False})],
                     className="chart-card",
                     style={"flex": "1", "minWidth": "260px"}),
        ], style={"display": "flex", "gap": "16px",
                  "marginBottom": "28px", "flexWrap": "wrap"}),

    ], style={"padding": "0 40px"}),

    # ── Book table ───────────────────────────────────────────
    html.Div([
        html.Span("Book list", className="section-title"),
        html.Div(id="table-container"),
    ], style={"padding": "0 40px 48px"}),

], style={"backgroundColor": BG, "minHeight": "100vh"})


# ── 4. Filter helper ─────────────────────────────────────────
def apply_filters(languages, sexes, year_range):
    mask = pd.Series([True] * len(df), index=df.index)
    if languages:
        mask &= df["language"].isin(languages)
    if sexes:
        mask &= df["sex"].isin(sexes)
    if year_range:
        yr = df["year_pub"]
        mask &= (yr.isna() | ((yr >= year_range[0]) & (yr <= year_range[1])))
    return df[mask]


# ── 5. KPI callback ──────────────────────────────────────────
@app.callback(
    Output("kpi-row", "children"),
    Input("filter-lang",  "value"),
    Input("filter-sex",   "value"),
    Input("filter-year",  "value"),
)
def update_kpis(langs, sexes, year_range):
    d = apply_filters(langs, sexes, year_range)
    cards = [
        ("Books",          f"{len(d):,}"),
        ("Total pages",    f"{int(d['pages'].sum(skipna=True)):,}"),
        ("Avg pages/book", f"{int(d['pages'].mean(skipna=True)):,}"),
        ("Unique authors", f"{d['author_clean'].nunique():,}"),
    ]
    return [
        html.Div([
            html.Div(label, className="kpi-label"),
            html.Div(value, className="kpi-value"),
        ], className="kpi-card")
        for label, value in cards
    ]


# ── 6. Charts callback ───────────────────────────────────────
@app.callback(
    Output("hist-pages",      "figure"),
    Output("hist-year",       "figure"),
    Output("scatter-main",    "figure"),
    Output("pie-country",     "figure"),
    Output("bar-authors",     "figure"),
    Output("bar-lang",        "figure"),
    Output("tree-publisher",  "figure"),
    Output("donut-sex",       "figure"),
    Output("table-container", "children"),
    Input("filter-lang",  "value"),
    Input("filter-sex",   "value"),
    Input("filter-year",  "value"),
)
def update_charts(langs, sexes, year_range):
    d = apply_filters(langs, sexes, year_range)

    fig_pages = px.histogram(
        d.dropna(subset=["pages"]), x="pages", nbins=20,
        title="Distribution of pages",
        labels={"pages": "Pages", "count": "Books"},
        color_discrete_sequence=[ACCENT],
    )
    fig_pages.update_traces(marker_line_color="white", marker_line_width=1.5,
                             hovertemplate="<b>%{x} pages</b><br>Books: %{y}<extra></extra>")
    fig_pages.update_layout(**CHART_LAYOUT, bargap=0.06)

    d_yr = d.dropna(subset=["year_pub"])
    d_yr = d_yr[d_yr["year_pub"] >= 1800]
    fig_year = px.histogram(
        d_yr, x="year_pub", nbins=30,
        title="Books by publication year (>= 1800)",
        labels={"year_pub": "Year", "count": "Books"},
        color_discrete_sequence=[ACCENT_LIGHT],
    )
    fig_year.update_traces(marker_line_color="white", marker_line_width=1.5,
                            hovertemplate="<b>%{x}</b><br>Books: %{y}<extra></extra>")
    fig_year.update_layout(**CHART_LAYOUT, bargap=0.06)

    d_sc = d.dropna(subset=["pages", "year_pub"])
    d_sc = d_sc[d_sc["year_pub"] >= 1800]
    fig_scatter = px.scatter(
        d_sc, x="year_pub", y="pages", color="country_clean",
        hover_name="title",
        hover_data={"author_clean": True, "pages": True,
                    "year_pub": True, "country_clean": False},
        size="pages", size_max=26,
        title="Year of publication vs. length",
        labels={"year_pub": "Year", "pages": "Pages",
                "country_clean": "Country", "author_clean": "Author"},
        color_discrete_sequence=OWID_PALETTE, opacity=0.75,
    )
    fig_scatter.update_layout(**CHART_LAYOUT, legend_title_text="Country")

    top_c = d["country_clean"].value_counts().head(10)
    fig_pie = go.Figure(go.Pie(
        values=top_c.values, labels=top_c.index, hole=0.42,
        marker_colors=OWID_PALETTE,
        textinfo="percent+label", textfont_size=12,
        textfont_family="Lato, sans-serif",
        hovertemplate="<b>%{label}</b><br>%{value} books · %{percent}<extra></extra>",
    ))
    fig_pie.update_layout(**CHART_LAYOUT, title_text="Top 10 author nationalities",
                           showlegend=False)

    top_auth = (
        d[d["author_clean"].notna()]
        .groupby("author_clean")
        .agg(books=("title", "count"),
             pages=("pages", lambda x: int(x.sum(skipna=True))))
        .sort_values("books", ascending=False).head(15).reset_index()
    )
    fig_auth = px.bar(
        top_auth, y="author_clean", x="books", orientation="h",
        title="Top 15 authors by number of books",
        labels={"author_clean": "", "books": "Books"},
        color="pages",
        color_continuous_scale=[[0, ACCENT_PALE], [0.5, ACCENT_LIGHT], [1, ACCENT]],
        hover_data={"pages": True},
    )
    fig_auth.update_traces(
        marker_line_color="white", marker_line_width=0.8,
        hovertemplate="<b>%{y}</b><br>Books: %{x}<br>Total pages: %{customdata[0]:,}<extra></extra>")
    fig_auth.update_layout(**CHART_LAYOUT,
                            yaxis=dict(categoryorder="total ascending",
                                       showgrid=False,
                                       tickfont=dict(size=12, color=TEXT_MAIN)),
                            coloraxis_showscale=False)

    lang_counts = d["language"].value_counts().reset_index()
    lang_counts.columns = ["language", "count"]
    fig_lang = px.bar(
        lang_counts, x="language", y="count",
        title="Books by reading language",
        labels={"language": "Language", "count": "Books"},
        color="count",
        color_continuous_scale=[[0, ACCENT_PALE], [1, ACCENT]],
    )
    fig_lang.update_traces(marker_line_color="white", marker_line_width=1,
                            hovertemplate="<b>%{x}</b><br>Books: %{y}<extra></extra>")
    fig_lang.update_layout(**CHART_LAYOUT, coloraxis_showscale=False)

    pub_counts = (
        d[d["publisher_clean"].notna()]
        .groupby("publisher_clean").size()
        .reset_index(name="books")
        .sort_values("books", ascending=False).head(30)
    )
    fig_tree = px.treemap(
        pub_counts, path=["publisher_clean"], values="books",
        title="Top 30 publishers",
        color="books",
        color_continuous_scale=[[0, ACCENT_PALE], [0.5, ACCENT_LIGHT], [1, ACCENT]],
    )
    fig_tree.update_traces(
        textinfo="label+value", textfont_size=12,
        textfont_family="Lato, sans-serif",
        hovertemplate="<b>%{label}</b><br>Books: %{value}<extra></extra>",
        marker_line_color="white", marker_line_width=1.5,
    )
    fig_tree.update_layout(**CHART_LAYOUT, coloraxis_showscale=False)

    sex_map = {"m": "Male", "f": "Female"}
    sex_counts = d["sex"].map(sex_map).value_counts().reset_index()
    sex_counts.columns = ["sex", "count"]
    fig_sex = go.Figure(go.Pie(
        values=sex_counts["count"], labels=sex_counts["sex"], hole=0.55,
        marker_colors=[ACCENT, "#a12c7b"],
        textinfo="percent+label", textfont_size=13,
        textfont_family="Lato, sans-serif",
        hovertemplate="<b>%{label}</b><br>%{value} authors · %{percent}<extra></extra>",
    ))
    fig_sex.update_layout(**CHART_LAYOUT, title_text="Authors by sex",
                           showlegend=False)

    table_df = (
        d[["title", "author_clean", "pages", "year of publication",
           "country_clean", "publisher_clean", "language"]]
        .rename(columns={"author_clean": "author", "country_clean": "country",
                         "publisher_clean": "publisher",
                         "year of publication": "year"})
        .sort_values("title")
    )
    table = dash_table.DataTable(
        data=table_df.to_dict("records"),
        columns=[{"name": c.upper(), "id": c} for c in table_df.columns],
        page_size=15, filter_action="native", sort_action="native",
        style_table={"overflowX": "auto", "borderRadius": "6px",
                     "border": f"1px solid {BORDER}"},
        style_header={
            "backgroundColor": ACCENT, "color": "white",
            "fontWeight": "700", "fontSize": "11px",
            "letterSpacing": ".07em", "textTransform": "uppercase",
            "fontFamily": "Lato, sans-serif",
            "padding": "10px 14px", "border": "none",
        },
        style_cell={
            "fontFamily": "Lato, sans-serif", "fontSize": "13px",
            "color": TEXT_MAIN, "padding": "9px 14px",
            "border": f"1px solid {BORDER}",
            "maxWidth": "260px", "overflow": "hidden",
            "textOverflow": "ellipsis",
        },
        style_data_conditional=[
            {"if": {"row_index": "odd"}, "backgroundColor": "#f7f6f2"},
            {"if": {"state": "selected"},
             "backgroundColor": ACCENT_PALE,
             "border": f"1px solid {ACCENT}"},
        ],
        tooltip_data=[
            {col: {"value": str(row[col]), "type": "markdown"}
             for col in table_df.columns}
            for row in table_df.to_dict("records")
        ],
        tooltip_duration=None,
    )
    return (fig_pages, fig_year, fig_scatter, fig_pie,
            fig_auth, fig_lang, fig_tree, fig_sex, table)


# ── 7. Entry point ───────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)

# ============================================================
# Bookshelf Interactive Dashboard  —  Plotly / Dash
# ============================================================
# Run with:  python dashboard.py
# Then open  http://127.0.0.1:8050  in your browser.
#
# Required packages (add to requirements.txt):
#   pandas dash plotly
# ============================================================

import re
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, dash_table

# ── 1. Load & clean ─────────────────────────────────────────
df = pd.read_csv("books.csv")

# Normalise column names
df.columns = df.columns.str.strip()

# Drop rows with completely empty titles
df = df[df["title"].notna()]

# pages → numeric (drop rows that can't be converted)
df["pages"] = pd.to_numeric(df["pages"], errors="coerce")

# year of publication: keep only numeric years (drop V.Y., negative, etc.)
df["year_pub"] = pd.to_numeric(df["year of publication"], errors="coerce")

# Normalise sex column (strip spaces)
df["sex"] = df["sex"].str.strip().str.lower()

# Normalise country (take the first country when multiple are listed)
df["country_clean"] = df["country"].str.split("-").str[0].str.strip()

# Author title-case
df["author_clean"] = df["author"].str.strip().str.title()

# Publisher title-case
df["publisher_clean"] = df["publisher"].str.strip().str.title()

# Language — fill blanks with "unknown"
df["language"] = df["language"].fillna("unknown").str.strip()

# ── 2. Colour palette ───────────────────────────────────────
PALETTE = px.colors.qualitative.Set2
ACCENT  = "#01696f"   # teal

# ── 3. App shell ────────────────────────────────────────────
app = Dash(__name__, title="Bookshelf Dashboard")

app.layout = html.Div(
    style={"fontFamily": "'Segoe UI', sans-serif",
           "backgroundColor": "#f7f6f2",
           "minHeight": "100vh",
           "padding": "24px 32px"},
    children=[

        # ── Header ──────────────────────────────────────────
        html.Div([
            html.H1("📚 Bookshelf Dashboard",
                    style={"color": ACCENT, "marginBottom": "4px"}),
            html.P(f"{len(df)} books · interactive explorer",
                   style={"color": "#7a7974", "marginTop": 0}),
        ], style={"marginBottom": "24px"}),

        # ── Global filters row ──────────────────────────────
        html.Div([
            html.Div([
                html.Label("Language", style={"fontWeight": "600"}),
                dcc.Dropdown(
                    id="filter-lang",
                    options=[{"label": l.title(), "value": l}
                             for l in sorted(df["language"].unique())],
                    multi=True,
                    placeholder="All languages…",
                    style={"fontSize": "14px"}
                ),
            ], style={"flex": "1", "minWidth": "180px", "marginRight": "16px"}),

            html.Div([
                html.Label("Author sex", style={"fontWeight": "600"}),
                dcc.Dropdown(
                    id="filter-sex",
                    options=[{"label": "Male",    "value": "m"},
                             {"label": "Female",  "value": "f"}],
                    multi=True,
                    placeholder="All…",
                    style={"fontSize": "14px"}
                ),
            ], style={"flex": "1", "minWidth": "140px", "marginRight": "16px"}),

            html.Div([
                html.Label("Publication year range", style={"fontWeight": "600"}),
                dcc.RangeSlider(
                    id="filter-year",
                    min=int(df["year_pub"].dropna().min()),
                    max=int(df["year_pub"].dropna().max()),
                    value=[1800, int(df["year_pub"].dropna().max())],
                    marks=None,
                    tooltip={"placement": "bottom", "always_visible": True},
                    step=1,
                ),
            ], style={"flex": "3", "minWidth": "260px"}),
        ], style={"display": "flex", "alignItems": "flex-end",
                  "marginBottom": "28px", "flexWrap": "wrap", "gap": "8px"}),

        # ── KPI row ─────────────────────────────────────────
        html.Div(id="kpi-row",
                 style={"display": "flex", "gap": "16px",
                        "marginBottom": "28px", "flexWrap": "wrap"}),

        # ── Row 1: pages histogram + year histogram ──────────
        html.Div([
            dcc.Graph(id="hist-pages",   style={"flex": "1", "minWidth": "320px"}),
            dcc.Graph(id="hist-year",    style={"flex": "1", "minWidth": "320px"}),
        ], style={"display": "flex", "gap": "16px",
                  "marginBottom": "16px", "flexWrap": "wrap"}),

        # ── Row 2: scatter year vs pages + nationality pie ───
        html.Div([
            dcc.Graph(id="scatter-main", style={"flex": "2", "minWidth": "400px"}),
            dcc.Graph(id="pie-country",  style={"flex": "1", "minWidth": "300px"}),
        ], style={"display": "flex", "gap": "16px",
                  "marginBottom": "16px", "flexWrap": "wrap"}),

        # ── Row 3: top authors bar + language bar ────────────
        html.Div([
            dcc.Graph(id="bar-authors",   style={"flex": "1", "minWidth": "320px"}),
            dcc.Graph(id="bar-lang",      style={"flex": "1", "minWidth": "320px"}),
        ], style={"display": "flex", "gap": "16px",
                  "marginBottom": "16px", "flexWrap": "wrap"}),

        # ── Row 4: publisher treemap + sex donut ─────────────
        html.Div([
            dcc.Graph(id="tree-publisher", style={"flex": "2", "minWidth": "400px"}),
            dcc.Graph(id="donut-sex",      style={"flex": "1", "minWidth": "260px"}),
        ], style={"display": "flex", "gap": "16px",
                  "marginBottom": "24px", "flexWrap": "wrap"}),

        # ── Row 5: searchable book table ─────────────────────
        html.H3("Book list", style={"color": ACCENT, "marginBottom": "8px"}),
        html.Div(id="table-container"),
    ]
)


# ── 4. Shared filter helper ──────────────────────────────────
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


# ── 5. KPI callback ─────────────────────────────────────────
@app.callback(
    Output("kpi-row", "children"),
    Input("filter-lang",  "value"),
    Input("filter-sex",   "value"),
    Input("filter-year",  "value"),
)
def update_kpis(langs, sexes, year_range):
    d = apply_filters(langs, sexes, year_range)
    total_books  = len(d)
    total_pages  = int(d["pages"].sum(skipna=True))
    avg_pages    = round(d["pages"].mean(skipna=True), 0)
    n_authors    = d["author_clean"].nunique()

    def kpi_card(label, value):
        return html.Div([
            html.P(label,  style={"color": "#7a7974", "fontSize": "13px",
                                  "marginBottom": "2px"}),
            html.H2(f"{value:,}", style={"color": ACCENT, "margin": 0,
                                          "fontVariantNumeric": "tabular-nums"}),
        ], style={"backgroundColor": "white",
                  "borderRadius": "10px",
                  "padding": "16px 24px",
                  "boxShadow": "0 2px 8px rgba(0,0,0,.07)",
                  "minWidth": "140px"})

    return [
        kpi_card("Books",          total_books),
        kpi_card("Total pages",    total_pages),
        kpi_card("Avg pages/book", int(avg_pages)),
        kpi_card("Unique authors", n_authors),
    ]


# ── 6. Main charts callback ──────────────────────────────────
@app.callback(
    Output("hist-pages",     "figure"),
    Output("hist-year",      "figure"),
    Output("scatter-main",   "figure"),
    Output("pie-country",    "figure"),
    Output("bar-authors",    "figure"),
    Output("bar-lang",       "figure"),
    Output("tree-publisher", "figure"),
    Output("donut-sex",      "figure"),
    Output("table-container","children"),
    Input("filter-lang",  "value"),
    Input("filter-sex",   "value"),
    Input("filter-year",  "value"),
)
def update_charts(langs, sexes, year_range):
    d = apply_filters(langs, sexes, year_range)

    common = dict(template="plotly_white",
                  color_discrete_sequence=PALETTE)

    # ── histogram: pages ────────────────────────────────────
    fig_pages = px.histogram(
        d.dropna(subset=["pages"]),
        x="pages", nbins=20,
        title="Distribution of pages",
        labels={"pages": "Pages"},
        color_discrete_sequence=[ACCENT],
        **{k: v for k, v in common.items() if k != "color_discrete_sequence"}
    )
    fig_pages.update_layout(bargap=0.05, title_font_color=ACCENT)

    # ── histogram: year ─────────────────────────────────────
    d_yr = d.dropna(subset=["year_pub"])
    d_yr = d_yr[d_yr["year_pub"] >= 1800]    # focus on modern era
    fig_year = px.histogram(
        d_yr, x="year_pub", nbins=30,
        title="Books by publication year (≥ 1800)",
        labels={"year_pub": "Year"},
        color_discrete_sequence=["#4f98a3"],
        **{k: v for k, v in common.items() if k != "color_discrete_sequence"}
    )
    fig_year.update_layout(bargap=0.05, title_font_color=ACCENT)

    # ── scatter: year vs pages ───────────────────────────────
    d_sc = d.dropna(subset=["pages", "year_pub"])
    d_sc = d_sc[d_sc["year_pub"] >= 1800]
    fig_scatter = px.scatter(
        d_sc,
        x="year_pub", y="pages",
        color="country_clean",
        hover_data={"title": True, "author_clean": True,
                    "pages": True, "year_pub": True,
                    "country_clean": False},
        hover_name="title",
        size="pages", size_max=28,
        title="Year of publication vs pages",
        labels={"year_pub": "Year", "pages": "Pages",
                "country_clean": "Country"},
        **common
    )
    fig_scatter.update_layout(title_font_color=ACCENT,
                               legend_title_text="Country")

    # ── pie: top 10 countries ────────────────────────────────
    top_c = (d["country_clean"].value_counts().head(10))
    fig_pie = px.pie(
        values=top_c.values, names=top_c.index,
        title="Top 10 author nationalities",
        hole=0.35,
        **common
    )
    fig_pie.update_traces(textposition="inside", textinfo="percent+label")
    fig_pie.update_layout(title_font_color=ACCENT,
                           showlegend=False)

    # ── bar: top 15 authors by book count ───────────────────
    top_auth = (
        d[d["author_clean"].notna()]
        .groupby("author_clean")
        .agg(books=("title", "count"),
             pages=("pages",  lambda x: int(x.sum(skipna=True))))
        .sort_values("books", ascending=False)
        .head(15)
        .reset_index()
    )
    fig_auth = px.bar(
        top_auth, y="author_clean", x="books",
        orientation="h",
        title="Top 15 authors by number of books",
        labels={"author_clean": "", "books": "Books"},
        color="pages",
        color_continuous_scale="Teal",
        hover_data={"pages": True},
        **{k: v for k, v in common.items() if k != "color_discrete_sequence"}
    )
    fig_auth.update_layout(yaxis={"categoryorder": "total ascending"},
                            title_font_color=ACCENT,
                            coloraxis_showscale=False)

    # ── bar: language distribution ───────────────────────────
    lang_counts = d["language"].value_counts().reset_index()
    lang_counts.columns = ["language", "count"]
    fig_lang = px.bar(
        lang_counts, x="language", y="count",
        title="Books by reading language",
        labels={"language": "Language", "count": "Books"},
        color_discrete_sequence=[ACCENT],
        **{k: v for k, v in common.items() if k != "color_discrete_sequence"}
    )
    fig_lang.update_layout(title_font_color=ACCENT)

    # ── treemap: publishers ──────────────────────────────────
    pub_counts = (
        d[d["publisher_clean"].notna()]
        .groupby("publisher_clean")
        .size()
        .reset_index(name="books")
        .sort_values("books", ascending=False)
        .head(30)
    )
    fig_tree = px.treemap(
        pub_counts,
        path=["publisher_clean"],
        values="books",
        title="Top 30 publishers (by book count)",
        color="books",
        color_continuous_scale="Teal",
        **{k: v for k, v in common.items() if k != "color_discrete_sequence"}
    )
    fig_tree.update_layout(title_font_color=ACCENT,
                            coloraxis_showscale=False)
    fig_tree.update_traces(textinfo="label+value")

    # ── donut: sex ───────────────────────────────────────────
    sex_map   = {"m": "Male", "f": "Female"}
    sex_counts = (
        d["sex"].map(sex_map).value_counts().reset_index()
    )
    sex_counts.columns = ["sex", "count"]
    fig_sex = px.pie(
        sex_counts, values="count", names="sex",
        title="Authors by sex",
        hole=0.5,
        color="sex",
        color_discrete_map={"Male": ACCENT, "Female": "#d163a7"},
        **{k: v for k, v in common.items() if k != "color_discrete_sequence"}
    )
    fig_sex.update_layout(title_font_color=ACCENT)

    # ── table ────────────────────────────────────────────────
    table_df = (
        d[["title", "author_clean", "pages", "year of publication",
           "country_clean", "publisher_clean", "language"]]
        .rename(columns={"author_clean": "author",
                         "country_clean": "country",
                         "publisher_clean": "publisher",
                         "year of publication": "year"})
        .sort_values("title")
    )
    table = dash_table.DataTable(
        data=table_df.to_dict("records"),
        columns=[{"name": c, "id": c} for c in table_df.columns],
        page_size=15,
        filter_action="native",
        sort_action="native",
        style_table={"overflowX": "auto"},
        style_header={"backgroundColor": ACCENT,
                      "color": "white",
                      "fontWeight": "bold",
                      "fontSize": "13px"},
        style_cell={"fontSize": "13px",
                    "padding": "8px 12px",
                    "backgroundColor": "#fafaf8"},
        style_data_conditional=[
            {"if": {"row_index": "odd"},
             "backgroundColor": "#f3f0ec"}
        ],
    )
    return (fig_pages, fig_year, fig_scatter, fig_pie,
            fig_auth, fig_lang, fig_tree, fig_sex, table)


# ── 7. Entry point ───────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)

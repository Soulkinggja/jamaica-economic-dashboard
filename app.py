"""Jamaica Economic Dashboard

An interactive Streamlit dashboard that tracks Jamaica's main economic
indicators from 2000 to today, plus IMF projections.

Run locally:  streamlit run app.py
"""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DATA_FILE = Path(__file__).parent / "data" / "jamaica_indicators.csv"

# Colors (validated categorical and diverging slots, light mode)
BLUE = "#2a78d6"
RED = "#e34948"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
SURFACE = "#fcfcfb"

INDICATORS = {
    "gdp_growth": {"label": "Real GDP growth", "unit": "%", "fmt": "{:.1f}%", "good": "up",
                   "help": "Annual change in real GDP. Source: IMF World Economic Outlook."},
    "inflation": {"label": "Inflation", "unit": "%", "fmt": "{:.1f}%", "good": "down",
                  "help": "Annual change in consumer prices. Source: World Bank."},
    "unemployment": {"label": "Unemployment", "unit": "%", "fmt": "{:.1f}%", "good": "down",
                     "help": "Share of the labour force without work. Source: IMF World Economic Outlook."},
    "debt_gdp": {"label": "Public debt", "unit": "% of GDP", "fmt": "{:.1f}%", "good": "down",
                 "help": "General government gross debt as a share of GDP. Source: IMF."},
    "fx_rate": {"label": "JMD per US dollar", "unit": "JMD", "fmt": "{:.2f}", "good": "down",
                "help": "Annual average exchange rate. A higher number means a weaker Jamaican dollar."},
    "gdp_per_capita": {"label": "GDP per person", "unit": "US$", "fmt": "${:,.0f}", "good": "up",
                       "help": "GDP divided by population, in current US dollars. Source: World Bank."},
    "current_account": {"label": "Current account balance", "unit": "% of GDP", "fmt": "{:.1f}%", "good": "up",
                        "help": "Trade, income and remittance flows with the rest of the world. Source: IMF."},
    "gdp_usd_bn": {"label": "GDP", "unit": "US$ billions", "fmt": "${:.1f}B", "good": "up",
                   "help": "Size of the economy in current US dollars. Source: World Bank."},
    "population": {"label": "Population", "unit": "people", "fmt": "{:,.0f}", "good": None,
                   "help": "Total population. Source: World Bank."},
}

HOVER = {
    "gdp_growth": "%{x}: %{y:.1f}%<extra></extra>",
    "inflation": "%{x}: %{y:.1f}%<extra></extra>",
    "unemployment": "%{x}: %{y:.1f}%<extra></extra>",
    "debt_gdp": "%{x}: %{y:.1f}% of GDP<extra></extra>",
    "fx_rate": "%{x}: J$%{y:.2f} per US$<extra></extra>",
    "gdp_per_capita": "%{x}: US$%{y:,.0f}<extra></extra>",
    "current_account": "%{x}: %{y:.1f}% of GDP<extra></extra>",
    "gdp_usd_bn": "%{x}: US$%{y:.1f} billion<extra></extra>",
    "population": "%{x}: %{y:,.0f}<extra></extra>",
}

# year -> (short label shown on charts, full description shown on hover)
EVENTS = {
    2008: ("Financial crisis", "2008: Global financial crisis"),
    2013: ("IMF programme", "2013: Four year IMF programme begins"),
    2020: ("COVID 19", "2020: COVID 19 pandemic"),
    2024: ("Beryl", "2024: Hurricane Beryl"),
    2025: ("Melissa", "2025: Hurricane Melissa, the strongest storm on record to hit Jamaica"),
}


# ---------------------------------------------------------------- data
@st.cache_data
def load_data(path: Path = DATA_FILE) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["year"] = df["year"].astype(int)
    df["is_projection"] = df["is_projection"].astype(bool)
    return df


def series(df: pd.DataFrame, key: str, years: tuple[int, int], projections: bool) -> pd.DataFrame:
    s = df[(df["indicator"] == key) & df["year"].between(*years)]
    if not projections:
        s = s[~s["is_projection"]]
    return s.sort_values("year")


def latest_actual(df: pd.DataFrame, key: str):
    s = df[(df["indicator"] == key) & ~df["is_projection"]].sort_values("year")
    last, prev = s.iloc[-1], s.iloc[-2]
    return int(last["year"]), float(last["value"]), float(prev["value"])


# ---------------------------------------------------------------- chart helpers
def base_layout(fig: go.Figure, y_title: str, years: tuple[int, int], height: int = 400) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=8, t=52, b=8),
        plot_bgcolor=SURFACE,
        paper_bgcolor=SURFACE,
        font=dict(family="system-ui, -apple-system, Segoe UI, sans-serif", color=INK_2, size=13),
        hoverlabel=dict(bgcolor="white", bordercolor=AXIS, font=dict(color=INK)),
        legend=dict(orientation="h", yanchor="top", y=-0.12, xanchor="left", x=0, font=dict(color=INK_2)),
        bargap=0.25,
    )
    fig.update_xaxes(showgrid=False, linecolor=AXIS, tickcolor=AXIS, tickfont=dict(color=MUTED), dtick=2,
                     range=[years[0] - 0.7, years[1] + 0.7])
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=AXIS, zerolinewidth=1, tickfont=dict(color=MUTED),
                     title=dict(text=y_title, font=dict(color=MUTED, size=12)))
    return fig


def add_events(fig: go.Figure, years: tuple[int, int]) -> None:
    shown = [(yr, ev) for yr, ev in EVENTS.items() if years[0] <= yr <= years[1]]
    for i, (yr, (label, full)) in enumerate(shown):
        fig.add_vline(x=yr, line=dict(color=AXIS, width=1, dash="dot"), layer="below")
        # labels sit above the plot, on two staggered rows so close years don't collide
        fig.add_annotation(x=yr, y=1, yref="paper", text=label, hovertext=full, showarrow=False,
                           xanchor="center", yanchor="bottom", yshift=4 + (18 if i % 2 else 0),
                           font=dict(size=11, color=MUTED))


def line_chart(df, key, years, projections, events, y_title, ref=None):
    meta = INDICATORS[key]
    s = series(df, key, years, projections)
    actual = s[~s["is_projection"]]
    proj = s[s["is_projection"]]
    hover = HOVER[key]
    fig = go.Figure()
    if ref is not None:
        lo, hi, label = ref
        if hi is None:
            fig.add_hline(y=lo, line=dict(color=MUTED, width=1, dash="dash"),
                          annotation_text=label, annotation_position="top left",
                          annotation_font=dict(size=11, color=MUTED))
        else:
            fig.add_hrect(y0=lo, y1=hi, fillcolor="#cde2fb", opacity=0.45, line_width=0, layer="below",
                          annotation_text=label, annotation_position="top left",
                          annotation_font=dict(size=11, color=INK_2))
    fig.add_trace(go.Scatter(x=actual["year"], y=actual["value"], name="Actual", mode="lines+markers",
                             line=dict(color=BLUE, width=2), marker=dict(size=8, color=BLUE,
                             line=dict(color=SURFACE, width=2)), hovertemplate=hover))
    if len(proj):
        joined = pd.concat([actual.tail(1), proj])
        sizes = [0] * (len(joined) - len(proj)) + [8] * len(proj)  # no marker on the joining actual point
        fig.add_trace(go.Scatter(x=joined["year"], y=joined["value"], name="IMF projection",
                                 mode="lines+markers", line=dict(color=BLUE, width=2, dash="dash"),
                                 marker=dict(size=sizes, color=SURFACE, line=dict(color=BLUE, width=2)),
                                 hovertemplate=hover.replace("<extra>", " (projection)<extra>")))
    fig.update_layout(showlegend=len(proj) > 0)
    span = (int(s["year"].min()), int(s["year"].max()))  # fit the axis to the data shown
    if events:
        add_events(fig, span)
    return base_layout(fig, y_title, span)


def polarity_bars(df, key, years, projections, events, y_title):
    s = series(df, key, years, projections)
    colors = [BLUE if v >= 0 else RED for v in s["value"]]
    fig = go.Figure(go.Bar(
        x=s["year"], y=s["value"],
        marker=dict(color=colors, opacity=[0.45 if p else 1 for p in s["is_projection"]],
                    pattern=dict(shape=["/" if p else "" for p in s["is_projection"]], fgcolor=SURFACE),
                    cornerradius=4, line=dict(width=0)),
        customdata=["IMF projection" if p else "Actual" for p in s["is_projection"]],
        hovertemplate="%{x}: %{y:.1f}%  (%{customdata})<extra></extra>",
    ))
    fig.update_layout(showlegend=False)
    span = (int(s["year"].min()), int(s["year"].max()))  # fit the axis to the data shown
    if events:
        add_events(fig, span)
    return base_layout(fig, y_title, span)


# ---------------------------------------------------------------- page
st.set_page_config(page_title="Jamaica Economic Dashboard", layout="wide")
st.markdown(
    """
    <style>
      .block-container {padding-top: 2rem; max-width: 1200px;}
      [data-testid="stMetricValue"] {font-size: 1.7rem;}
      .takeaway {background:#f0efec; border-radius:8px; padding:0.9rem 1.1rem; margin-bottom:0.5rem;
                 color:#0b0b0b; line-height:1.5;}
      .src {color:#52514e; font-size:0.85rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

df = load_data()
first_year = int(df["year"].min())
last_actual_year = int(df.loc[~df["is_projection"], "year"].max())
last_year = int(df["year"].max())

with st.sidebar:
    st.header("Controls")
    show_proj = st.toggle("Show IMF projections", value=True,
                          help="Dashed lines and striped bars are IMF forecasts, not actual data.")
    show_events = st.toggle("Show key events", value=True)
    max_year = last_year if show_proj else last_actual_year
    years = st.slider("Years", min_value=first_year, max_value=max_year,
                      value=(first_year, max_year), step=1)
    st.divider()
    st.caption("Built by Devin McIntosh with Python, pandas, Plotly and Streamlit.")
    st.caption("[LinkedIn](https://www.linkedin.com/in/devinlerandezmcintosh)")

st.title("Jamaica Economic Dashboard")
st.markdown(
    f"How Jamaica's economy has changed from {first_year} to {last_actual_year}, in one place. "
    "Use the controls on the left to change the years or hide the IMF forecasts."
)

# KPI row
st.caption(f"Latest actual figures ({last_actual_year}), compared with the year before")
kpis = ["gdp_growth", "inflation", "unemployment", "debt_gdp", "fx_rate", "gdp_per_capita"]
cols = st.columns(len(kpis))
for col, key in zip(cols, kpis):
    meta = INDICATORS[key]
    yr, val, prev = latest_actual(df, key)
    diff = val - prev
    if key == "gdp_per_capita":
        delta = f"{diff:+,.0f} vs {yr - 1}"
    elif key == "fx_rate":
        delta = f"{diff:+.2f} vs {yr - 1}"
    else:
        delta = f"{diff:+.1f} pts vs {yr - 1}"
    col.metric(meta["label"], meta["fmt"].format(val), delta,
               delta_color="normal" if meta["good"] == "up" else "inverse", help=meta["help"])

# Key takeaways, computed from the data so they update with it
debt = df[(df["indicator"] == "debt_gdp") & ~df["is_projection"]]
peak = debt.loc[debt["value"].idxmax()]
_, debt_now, _ = latest_actual(df, "debt_gdp")
unemp = df[(df["indicator"] == "unemployment") & ~df["is_projection"]]
_, unemp_now, _ = latest_actual(df, "unemployment")
fx = df[df["indicator"] == "fx_rate"].sort_values("year")
fx_start, fx_end = fx.iloc[0], fx.iloc[-1]
infl = df[(df["indicator"] == "inflation")]
infl_early = infl[infl["year"].between(2000, 2014)]["value"].mean()
infl_late = infl[infl["year"].between(2015, last_actual_year)]["value"].mean()
growth_next = df[(df["indicator"] == "gdp_growth") & (df["year"] == last_actual_year + 1)]

st.subheader("Key takeaways")
t1, t2 = st.columns(2)
with t1:
    st.markdown(
        f"<div class='takeaway'><b>Debt has been cut in half.</b> Public debt peaked at "
        f"{peak['value']:.0f}% of GDP in {int(peak['year'])} and was {debt_now:.0f}% in {last_actual_year}.</div>",
        unsafe_allow_html=True)
    st.markdown(
        f"<div class='takeaway'><b>Unemployment is at its lowest since at least {first_year}.</b> "
        f"It fell to {unemp_now:.1f}% in {last_actual_year}, from a high of "
        f"{unemp['value'].max():.1f}% in {int(unemp.loc[unemp['value'].idxmax(), 'year'])}.</div>",
        unsafe_allow_html=True)
with t2:
    st.markdown(
        f"<div class='takeaway'><b>Prices are steadier.</b> Inflation averaged {infl_early:.1f}% a year "
        f"from 2000 to 2014, and {infl_late:.1f}% a year from 2015 to {last_actual_year}.</div>",
        unsafe_allow_html=True)
    msg = (f"<div class='takeaway'><b>The dollar keeps sliding.</b> One US dollar cost "
           f"J${fx_start['value']:.0f} in {int(fx_start['year'])} and about J${fx_end['value']:.0f} "
           f"in {int(fx_end['year'])}.")
    if len(growth_next):
        g = float(growth_next["value"].iloc[0])
        outlook = "no growth" if abs(g) < 0.05 else f"growth of {g:.1f}%"
        msg += f" After Hurricane Melissa, the IMF expects {outlook} in {last_actual_year + 1}."
    st.markdown(msg + "</div>", unsafe_allow_html=True)

st.write("")
tab_growth, tab_prices, tab_jobs, tab_debt, tab_data = st.tabs(
    ["Growth", "Prices and currency", "Jobs", "Debt and external balance", "Data"])

with tab_growth:
    st.markdown("**Real GDP growth (% per year)**")
    st.plotly_chart(polarity_bars(df, "gdp_growth", years, show_proj, show_events, "% change"),
                    width="stretch")
    st.caption("Red bars are years the economy shrank. Striped bars are IMF projections. "
               "Dotted lines mark key events; hover a label for details.")
    st.markdown("**GDP per person (current US$)**")
    st.plotly_chart(line_chart(df, "gdp_per_capita", years, show_proj, show_events, "US$"),
                    width="stretch")

with tab_prices:
    st.markdown("**Inflation (% per year)**")
    st.plotly_chart(line_chart(df, "inflation", years, show_proj, show_events, "% change",
                               ref=(4, 6, "Bank of Jamaica target range, 4% to 6%")),
                    width="stretch")
    st.markdown("**Jamaican dollars per US dollar (annual average)**")
    st.plotly_chart(line_chart(df, "fx_rate", years, show_proj, show_events, "JMD per USD"),
                    width="stretch")
    st.caption("A higher line means a weaker Jamaican dollar.")

with tab_jobs:
    st.markdown("**Unemployment rate (% of labour force)**")
    st.plotly_chart(line_chart(df, "unemployment", years, show_proj, show_events, "%"),
                    width="stretch")
    st.markdown("**Population**")
    st.plotly_chart(line_chart(df, "population", years, show_proj, False, "People"),
                    width="stretch")

with tab_debt:
    st.markdown("**Public debt (% of GDP)**")
    st.plotly_chart(line_chart(df, "debt_gdp", years, show_proj, show_events, "% of GDP",
                               ref=(60, None, "60% of GDP, fiscal rule target")),
                    width="stretch")
    st.markdown("**Current account balance (% of GDP)**")
    st.plotly_chart(polarity_bars(df, "current_account", years, show_proj, show_events, "% of GDP"),
                    width="stretch")
    st.caption("Below zero means Jamaica spent more abroad than it earned. Striped bars are IMF projections.")

with tab_data:
    view = df[df["year"].between(*years)]
    if not show_proj:
        view = view[~view["is_projection"]]
    wide = view.pivot_table(index="year", columns="indicator", values="value").reset_index()
    decimals = {"fx_rate": 2, "gdp_per_capita": 0, "population": 0}
    wide = wide.round({k: decimals.get(k, 1) for k in INDICATORS if k in wide.columns})
    order = ["year"] + [k for k in INDICATORS if k in wide.columns]
    wide = wide[order].rename(columns={k: f"{v['label']} ({v['unit']})" for k, v in INDICATORS.items()})
    st.dataframe(wide, hide_index=True, width="stretch",
                 column_config={"year": st.column_config.NumberColumn("Year", format="%d")})
    st.download_button("Download the data (CSV)", view.to_csv(index=False).encode(),
                       "jamaica_economic_indicators.csv", "text/csv")

st.divider()
st.markdown(
    "<p class='src'><b>Sources:</b> "
    "<a href='https://www.imf.org/external/datamapper'>IMF World Economic Outlook</a> (GDP growth, unemployment, "
    "debt, current account), "
    "<a href='https://data.worldbank.org/country/jamaica'>World Bank</a> via "
    "<a href='https://fred.stlouisfed.org'>FRED</a> (inflation, GDP, GDP per person, population), "
    "Penn World Table via FRED (exchange rate to 2023; later years are averages of daily market rates). "
    f"IMF figures from {last_actual_year + 1} onward are projections.</p>",
    unsafe_allow_html=True,
)

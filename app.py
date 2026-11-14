"""
Netflix Data Dashboard
Streamlit version of the charts from shreya_project3.ipynb

Run:  streamlit run app.py
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# ----------------------------------------------------------------------------
# Page setup + Netflix theme
# ----------------------------------------------------------------------------
HERE = Path(__file__).parent
ICON = HERE / "netflix_icon.png"

st.set_page_config(
    page_title="Netflix Dashboard",
    page_icon=str(ICON) if ICON.exists() else "🎬",
    layout="wide",
)

RED, DARK_RED, BLACK, CHARCOAL, GREY = "#E50914", "#B9090B", "#141414", "#221F1F", "#B3B3B3"
RED_SCALE = ["#5C0408", "#8B0A0F", "#B9090B", "#E50914", "#F6121D", "#FF5A60", "#FF9A9E"]

LOGO_SVG = """
<svg width="30" height="52" viewBox="0 0 24 40" xmlns="http://www.w3.org/2000/svg">
  <rect x="0" y="0" width="7" height="40" fill="#B9090B"/>
  <rect x="17" y="0" width="7" height="40" fill="#B9090B"/>
  <polygon points="0,0 7,0 24,40 17,40" fill="#E50914"/>
</svg>
"""

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;600&display=swap');

    html, body, [class*="css"], .stApp {{ font-family: 'Inter', 'Helvetica Neue', Arial, sans-serif; }}
    .stApp {{ background: linear-gradient(180deg, #000000 0%, {BLACK} 260px); }}
    header[data-testid="stHeader"] {{ background: transparent; }}

    .nf-header {{ display:flex; align-items:center; gap:14px; padding:4px 0 14px;
                  border-bottom:3px solid {RED}; margin-bottom:18px; }}
    .nf-wordmark {{ font-family:'Bebas Neue', Impact, sans-serif; font-size:46px;
                    letter-spacing:4px; color:{RED}; line-height:1; }}
    .nf-sub {{ font-family:'Bebas Neue', Impact, sans-serif; font-size:26px;
               letter-spacing:3px; color:#fff; opacity:.85; margin-left:6px; }}

    h1, h2, h3 {{ font-family:'Bebas Neue', Impact, sans-serif !important;
                  letter-spacing:2px; font-weight:400 !important; }}
    h3 {{ color:#fff; border-left:4px solid {RED}; padding-left:10px; }}

    div[data-testid="stMetric"] {{ background:{CHARCOAL}; border-left:4px solid {RED};
                                   padding:14px 16px; border-radius:4px; }}
    div[data-testid="stMetricValue"] {{ font-family:'Bebas Neue', Impact, sans-serif;
                                        font-size:38px; letter-spacing:1px; }}
    div[data-testid="stMetricLabel"] p {{ color:{GREY}; }}

    section[data-testid="stSidebar"] {{ background:#000; border-right:1px solid #2b2b2b; }}

    button[data-baseweb="tab"] {{ font-family:'Bebas Neue', Impact, sans-serif;
                                  font-size:20px; letter-spacing:2px; }}
    div[data-baseweb="tab-highlight"] {{ background-color:{RED} !important; }}
    span[data-baseweb="tag"] {{ background-color:{RED} !important; }}
    </style>
    <div class="nf-header">{LOGO_SVG}<span class="nf-wordmark">NETFLIX</span>
    <span class="nf-sub">DATA DASHBOARD</span></div>
    """,
    unsafe_allow_html=True,
)


def style(fig, height=420):
    """Apply the Netflix look to a Plotly figure."""
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#FFFFFF", family="Inter, Helvetica, Arial"),
        title_font=dict(family="Bebas Neue, Impact", size=24, color="#FFFFFF"),
        margin=dict(l=10, r=10, t=60, b=10),
        legend=dict(font=dict(color=GREY)),
    )
    fig.update_xaxes(gridcolor="#2b2b2b", zeroline=False)
    fig.update_yaxes(gridcolor="#2b2b2b", zeroline=False)
    return fig


# ----------------------------------------------------------------------------
# Data loading (same cleaning steps as the notebook)
# ----------------------------------------------------------------------------
DEFAULT_FILES = ["netflix_titles_nov_2019.csv.zip", "netflix_titles_nov_2019.csv"]


@st.cache_data(show_spinner="Loading Netflix data...")
def load_data(source, name: str) -> pd.DataFrame:
    compression = "zip" if name.lower().endswith(".zip") else "infer"
    df = pd.read_csv(source, encoding="ISO-8859-1", compression=compression)

    df["director"] = df["director"].fillna("Unknown")
    df["cast"] = df["cast"].fillna("No Cast Listed").str.strip()
    df["country"] = df["country"].fillna("Unknown")
    df["release_year"] = df["release_year"].fillna(df["release_year"].median()).astype(int)
    df["year_added"] = pd.to_datetime(df["date_added"].str.strip(), errors="coerce").dt.year.astype("Int64")

    # duration: minutes for movies, seasons for TV shows
    df["duration_num"] = pd.to_numeric(df["duration"].str.extract(r"(\d+)")[0], errors="coerce")
    return df


def explode_counts(series: pd.Series, drop=("Unknown", "No Cast Listed")) -> pd.Series:
    s = series.str.split(",").explode().str.strip()
    s = s[~s.isin(drop) & (s != "")]
    return s.value_counts()


with st.sidebar:
    st.markdown("### Data")
    uploaded = st.file_uploader("Upload netflix_titles CSV or ZIP", type=["csv", "zip"])

df = None
if uploaded is not None:
    df = load_data(uploaded, uploaded.name)
else:
    for fname in DEFAULT_FILES:
        path = HERE / fname
        if path.exists():
            df = load_data(str(path), fname)
            break

if df is None:
    st.info(
        "Upload `netflix_titles_nov_2019.csv.zip` in the sidebar, or place it in the same "
        "folder as `app.py` and refresh."
    )
    st.stop()

# ----------------------------------------------------------------------------
# Sidebar filters
# ----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### Filters")
    types = st.multiselect("Type", sorted(df["type"].dropna().unique()), default=sorted(df["type"].dropna().unique()))
    yr_min, yr_max = int(df["release_year"].min()), int(df["release_year"].max())
    years = st.slider("Release year", yr_min, yr_max, (yr_min, yr_max))
    ratings = st.multiselect("Rating", sorted(df["rating"].dropna().unique()), placeholder="All ratings")
    top_n = st.slider("Top N (genres, actors, directors)", 5, 20, 10)

f = df[df["type"].isin(types) & df["release_year"].between(*years)]
if ratings:
    f = f[f["rating"].isin(ratings)]

if f.empty:
    st.warning("No titles match the current filters.")
    st.stop()

# ----------------------------------------------------------------------------
# KPIs
# ----------------------------------------------------------------------------
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total titles", f"{len(f):,}")
c2.metric("Movies", f"{(f['type'] == 'Movie').sum():,}")
c3.metric("TV shows", f"{(f['type'] == 'TV Show').sum():,}")
c4.metric("Most common rating", f["rating"].mode().iat[0] if f["rating"].notna().any() else "-")
c5.metric("Peak release year", int(f["release_year"].mode().iat[0]))

st.write("")
tab_over, tab_genre, tab_time, tab_people, tab_dur = st.tabs(
    ["Overview", "Genres & Countries", "Timeline", "Cast & Directors", "Duration"]
)

# ----------------------------------------------------------------------------
# Overview: Movies vs TV, rating share
# ----------------------------------------------------------------------------
with tab_over:
    a, b = st.columns(2)
    with a:
        t = f["type"].value_counts().reset_index()
        t.columns = ["type", "count"]
        fig = px.pie(t, names="type", values="count", hole=0.5, title="Movies vs TV Shows",
                     color="type", color_discrete_map={"Movie": RED, "TV Show": "#F5F5F1"})
        fig.update_traces(textinfo="percent+label", marker=dict(line=dict(color=BLACK, width=3)))
        st.plotly_chart(style(fig), use_container_width=True)
    with b:
        r = f["rating"].value_counts().head(5).reset_index()
        r.columns = ["rating", "count"]
        fig = px.pie(r, names="rating", values="count", hole=0.5, title="Top 5 Ratings",
                     color_discrete_sequence=RED_SCALE[::-1])
        fig.update_traces(textinfo="percent+label", marker=dict(line=dict(color=BLACK, width=3)))
        st.plotly_chart(style(fig), use_container_width=True)

# ----------------------------------------------------------------------------
# Genres & countries
# ----------------------------------------------------------------------------
with tab_genre:
    a, b = st.columns(2)
    with a:
        g = explode_counts(f["listed_in"]).head(top_n).reset_index()
        g.columns = ["genre", "count"]
        fig = px.bar(g, x="count", y="genre", orientation="h", title=f"Top {top_n} Genres",
                     color="count", color_continuous_scale=["#5C0408", RED])
        fig.update_layout(yaxis=dict(autorange="reversed"), coloraxis_showscale=False)
        st.plotly_chart(style(fig, 460), use_container_width=True)
    with b:
        cat = f["listed_in"].value_counts().head(top_n).reset_index()
        cat.columns = ["category", "count"]
        fig = px.pie(cat, names="category", values="count", hole=0.45,
                     title="Category Share (listed_in combinations)",
                     color_discrete_sequence=RED_SCALE + ["#F5F5F1", "#808080", "#404040"])
        fig.update_traces(textinfo="percent", marker=dict(line=dict(color=BLACK, width=2)))
        st.plotly_chart(style(fig, 460), use_container_width=True)

    co = explode_counts(f["country"]).head(top_n).reset_index()
    co.columns = ["country", "count"]
    fig = px.bar(co, x="country", y="count", title=f"Top {top_n} Producing Countries",
                 color="count", color_continuous_scale=["#5C0408", RED])
    fig.update_layout(coloraxis_showscale=False)
    st.plotly_chart(style(fig, 380), use_container_width=True)

# ----------------------------------------------------------------------------
# Timeline
# ----------------------------------------------------------------------------
with tab_time:
    a, b = st.columns(2)
    with a:
        ya = f["year_added"].dropna().astype(int).value_counts().sort_index().reset_index()
        ya.columns = ["year_added", "count"]
        fig = px.bar(ya, x="year_added", y="count", title="Titles Added Per Year")
        fig.update_traces(marker_color=RED)
        st.plotly_chart(style(fig), use_container_width=True)
    with b:
        ry = f["release_year"].value_counts().sort_index().reset_index()
        ry.columns = ["release_year", "count"]
        fig = px.line(ry, x="release_year", y="count", markers=True,
                      title="Trend of Content Release Years")
        fig.update_traces(line=dict(color=RED, width=3), marker=dict(color="#FFFFFF", size=6))
        st.plotly_chart(style(fig), use_container_width=True)

    by_type = f.groupby(["release_year", "type"]).size().reset_index(name="count")
    fig = px.area(by_type, x="release_year", y="count", color="type", title="Releases by Type Over Time",
                  color_discrete_map={"Movie": RED, "TV Show": "#F5F5F1"})
    st.plotly_chart(style(fig, 360), use_container_width=True)

# ----------------------------------------------------------------------------
# Cast & directors
# ----------------------------------------------------------------------------
with tab_people:
    a, b = st.columns(2)
    with a:
        ac = explode_counts(f["cast"]).head(top_n).reset_index()
        ac.columns = ["actor", "titles"]
        fig = px.bar(ac, x="actor", y="titles", title=f"Top {top_n} Actors on Netflix",
                     color="titles", color_continuous_scale=["#5C0408", RED])
        fig.update_layout(coloraxis_showscale=False, xaxis_tickangle=-40)
        st.plotly_chart(style(fig, 460), use_container_width=True)
    with b:
        dr = explode_counts(f["director"]).head(top_n).reset_index()
        dr.columns = ["director", "titles"]
        fig = px.bar(dr, x="director", y="titles", title=f"Top {top_n} Directors on Netflix",
                     color="titles", color_continuous_scale=["#5C0408", RED])
        fig.update_layout(coloraxis_showscale=False, xaxis_tickangle=-40)
        st.plotly_chart(style(fig, 460), use_container_width=True)

# ----------------------------------------------------------------------------
# Duration
# ----------------------------------------------------------------------------
with tab_dur:
    movies = f.loc[f["type"] == "Movie", "duration_num"].dropna()
    shows = f.loc[f["type"] == "TV Show", "duration_num"].dropna()

    a, b = st.columns(2)
    with a:
        st.markdown("### Movie runtime (min)")
        if movies.empty:
            st.caption("No movies in the current selection.")
        else:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Mean", f"{movies.mean():.0f}")
            m2.metric("Median", f"{movies.median():.0f}")
            m3.metric("Min", f"{movies.min():.0f}")
            m4.metric("Max", f"{movies.max():.0f}")
            fig = px.histogram(movies, nbins=40, title="Movie Duration Distribution")
            fig.update_traces(marker_color=RED)
            fig.update_layout(showlegend=False, xaxis_title="Minutes", yaxis_title="Titles")
            st.plotly_chart(style(fig, 380), use_container_width=True)
    with b:
        st.markdown("### TV seasons")
        if shows.empty:
            st.caption("No TV shows in the current selection.")
        else:
            s1, s2, s3, s4 = st.columns(4)
            s1.metric("Mean", f"{shows.mean():.1f}")
            s2.metric("Median", f"{shows.median():.0f}")
            s3.metric("Min", f"{shows.min():.0f}")
            s4.metric("Max", f"{shows.max():.0f}")
            sc = shows.astype(int).value_counts().sort_index().reset_index()
            sc.columns = ["seasons", "count"]
            fig = px.bar(sc, x="seasons", y="count", title="Number of Seasons per Show")
            fig.update_traces(marker_color=RED)
            fig.update_xaxes(type="category")
            st.plotly_chart(style(fig, 380), use_container_width=True)

with st.expander("Browse the data"):
    st.dataframe(
        f[["title", "type", "director", "country", "release_year", "rating", "duration", "listed_in"]],
        use_container_width=True, hide_index=True,
    )

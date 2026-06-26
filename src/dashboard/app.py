import os
import sys
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy.orm import Session

root_path = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_path))

from src.database import SessionLocal
from src.models import Product, PriceHistory

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Price Tracker",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Personal / project links — configurables per entorn (veure .env.prod.example)
PORTFOLIO_URL = os.getenv("PORTFOLIO_URL", "https://ericfolch.com")
GITHUB_URL = os.getenv("GITHUB_URL", "https://github.com/EricFolchMartinez")
LINKEDIN_URL = os.getenv("LINKEDIN_URL", "https://www.linkedin.com/in/eric-folch/")

# When true, show a small badge clarifying this is a static, read-only showcase.
DEMO_MODE = os.getenv("DEMO_MODE", "true").strip().lower() in {"1", "true", "yes", "on"}

# Palette
BG = "#0d0f14"
SURFACE = "#14171f"
BORDER = "#232733"
TEXT = "#dfe3ea"
MUTED = "#8a909e"
ACCENT = "#4f7cff"
GOOD = "#34d399"
WARN = "#e0a64a"

# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------
st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}

    #MainMenu, footer {{ visibility: hidden; }}

    /* Keep the header transparent but functional so the sidebar toggle stays visible */
    header[data-testid="stHeader"] {{ background: transparent; }}
    [data-testid="stToolbar"] {{ display: none; }}
    [data-testid="stSidebarCollapsedControl"] {{ visibility: visible; }}

    .stApp {{ background: {BG}; }}

    .block-container {{
        padding-top: 2.6rem;
        padding-bottom: 4rem;
        max-width: 1180px;
    }}

    /* Masthead */
    .masthead {{
        border-bottom: 1px solid {BORDER};
        padding-bottom: 1.4rem;
        margin-bottom: 2rem;
    }}
    .masthead .eyebrow {{
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        color: {MUTED};
        margin-bottom: 0.5rem;
    }}
    .masthead h1 {{
        font-size: 1.7rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        color: {TEXT};
        margin: 0;
    }}
    .masthead p {{
        color: {MUTED};
        margin: 0.4rem 0 0 0;
        font-size: 0.95rem;
        max-width: 620px;
    }}

    /* Metric cards */
    div[data-testid="stMetric"] {{
        background: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: 10px;
        padding: 1rem 1.2rem;
    }}
    div[data-testid="stMetricLabel"] p {{
        color: {MUTED} !important;
        font-weight: 500;
        font-size: 0.78rem;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }}
    div[data-testid="stMetricValue"] {{
        font-weight: 700;
        font-size: 1.65rem;
        color: {TEXT};
    }}

    /* Section label */
    .section-label {{
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: {MUTED};
        margin: 2.4rem 0 0.9rem 0;
    }}

    div[data-testid="stDataFrame"] {{
        border: 1px solid {BORDER};
        border-radius: 10px;
        overflow: hidden;
    }}

    /* Sidebar */
    section[data-testid="stSidebar"] {{
        background: {BG};
        border-right: 1px solid {BORDER};
    }}
    section[data-testid="stSidebar"] .block-container {{ padding-top: 2rem; }}

    .sb-brand {{ font-size: 1.05rem; font-weight: 700; color: {TEXT}; letter-spacing: -0.01em; }}
    .sb-tagline {{ color: {MUTED}; font-size: 0.85rem; margin-top: 0.25rem; line-height: 1.45; }}
    .sb-heading {{
        font-size: 0.7rem; font-weight: 600; letter-spacing: 0.12em;
        text-transform: uppercase; color: {MUTED};
        margin: 1.8rem 0 0.7rem 0;
    }}
    .sb-link a {{
        display: block; text-decoration: none;
        color: {TEXT} !important; font-size: 0.9rem; font-weight: 500;
        padding: 0.5rem 0; border-bottom: 1px solid {BORDER};
        transition: color 0.15s ease, padding-left 0.15s ease;
    }}
    .sb-link a:hover {{ color: {ACCENT} !important; padding-left: 4px; }}
    .sb-stack {{ color: {MUTED}; font-size: 0.82rem; line-height: 1.7; }}
    .sb-credit {{ color: #5a606e; font-size: 0.78rem; margin-top: 2rem; }}

    hr {{ border-color: {BORDER}; }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Data access
# ---------------------------------------------------------------------------
def get_data() -> pd.DataFrame:
    db: Session = SessionLocal()
    try:
        products = db.query(Product).all()
        rows = []
        for p in products:
            latest_price = p.prices[-1].price if p.prices else 0.0
            rows.append(
                {
                    "ID": p.id,
                    "Name": p.name,
                    "Current Price": latest_price,
                    "Target Price": p.target_price,
                    "URL": p.url,
                }
            )
        return pd.DataFrame(rows)
    finally:
        db.close()


def get_history(product_id: int) -> pd.DataFrame:
    db: Session = SessionLocal()
    try:
        history = (
            db.query(PriceHistory)
            .filter(PriceHistory.product_id == product_id)
            .order_by(PriceHistory.scraped_at.asc())
            .all()
        )
        return pd.DataFrame([{"Date": h.scraped_at, "Price": h.price} for h in history])
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="sb-brand">Price Tracker</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sb-tagline">Monitorització de preus a plataformes e-commerce.</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="sb-heading">Enllaços</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="sb-link">
            <a href="{PORTFOLIO_URL}" target="_blank">Portfolio</a>
            <a href="{GITHUB_URL}" target="_blank">Codi font</a>
            <a href="{LINKEDIN_URL}" target="_blank">LinkedIn</a>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="sb-heading">Stack</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sb-stack">Python · FastAPI<br>SQLAlchemy · BeautifulSoup<br>Streamlit · Plotly</div>',
        unsafe_allow_html=True,
    )
    if DEMO_MODE:
        st.markdown(
            '<div class="sb-tagline" style="margin-top:1.8rem;">'
            "Mode demo · dades de mostra, només lectura."
            "</div>",
            unsafe_allow_html=True,
        )
    st.markdown('<div class="sb-credit">Eric Folch</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Masthead
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="masthead">
        <div class="eyebrow">Dashboard</div>
        <h1>Price Tracker</h1>
        <p>Seguiment automàtic de preus a plataformes e-commerce, amb històric d'evolució i detecció d'ofertes segons un preu objectiu.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------
df_products = get_data()

n_products = len(df_products)
avg_price = 0.0
deals = 0
cheapest = "—"

if not df_products.empty:
    avg_price = df_products["Current Price"].mean()
    cheapest = f"{df_products['Current Price'].min():.2f} €"

    # Only rows with a target price set are eligible to be "deals".
    with_target = df_products.dropna(subset=["Target Price"])
    if not with_target.empty:
        deals = int((with_target["Current Price"] <= with_target["Target Price"]).sum())

c1, c2, c3, c4 = st.columns(4)
c1.metric("Productes", n_products)
c2.metric("Preu mitjà", f"{avg_price:.2f} €")
c3.metric("Ofertes actives", deals)
c4.metric("Preu més baix", cheapest)


# ---------------------------------------------------------------------------
# Products table
# ---------------------------------------------------------------------------
st.markdown('<div class="section-label">Productes rastrejats</div>', unsafe_allow_html=True)

if not df_products.empty:
    st.dataframe(
        df_products,
        column_config={
            "ID": st.column_config.NumberColumn("ID", width="small"),
            "Name": st.column_config.TextColumn("Producte"),
            "URL": st.column_config.LinkColumn("Enllaç", display_text="Obrir"),
            "Current Price": st.column_config.NumberColumn("Preu actual", format="%.2f €"),
            "Target Price": st.column_config.NumberColumn("Objectiu", format="%.2f €"),
        },
        hide_index=True,
        use_container_width=True,
    )
else:
    st.info("Encara no hi ha cap producte rastrejat. Afegeix-ne un des de la CLI o l'API.")


# ---------------------------------------------------------------------------
# Price evolution
# ---------------------------------------------------------------------------
st.markdown('<div class="section-label">Evolució de preus</div>', unsafe_allow_html=True)

if not df_products.empty:
    selected_name = st.selectbox(
        "Producte",
        df_products["Name"].tolist(),
        label_visibility="collapsed",
    )

    selected_row = df_products[df_products["Name"] == selected_name].iloc[0]
    product_id = int(selected_row["ID"])
    current_price = selected_row["Current Price"]
    target_price = selected_row["Target Price"]

    if pd.notna(target_price):
        if current_price <= target_price:
            st.success(
                f"Preu per sota de l'objectiu: {current_price:.2f} € (objectiu {target_price:.2f} €)."
            )
        else:
            diff = current_price - target_price
            st.warning(
                f"Per sobre de l'objectiu en {diff:.2f} € (objectiu {target_price:.2f} €)."
            )

    df_history = get_history(product_id)

    if not df_history.empty:
        fig = px.area(df_history, x="Date", y="Price")
        fig.update_traces(
            line=dict(color=ACCENT, width=2),
            fillcolor="rgba(79,124,255,0.10)",
            hovertemplate="%{y:.2f} €<extra></extra>",
        )

        if pd.notna(target_price):
            fig.add_hline(
                y=target_price,
                line_dash="dot",
                line_color=GOOD,
                line_width=1.5,
                annotation_text=f"Objectiu {target_price:.2f} €",
                annotation_position="top left",
                annotation_font_color=GOOD,
                annotation_font_size=11,
            )

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif", color=MUTED, size=12),
            margin=dict(l=0, r=0, t=10, b=0),
            yaxis=dict(title=None, gridcolor=BORDER, zeroline=False, ticksuffix=" €"),
            xaxis=dict(title=None, gridcolor="rgba(35,39,51,0.5)"),
            hovermode="x unified",
            height=380,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Encara no hi ha prou historial per a aquest producte.")

import sys
import os
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy.orm import Session
from src.database import SessionLocal
from src.models import Product, PriceHistory

st.set_page_config(page_title="Price Tracker Pro", layout="wide")
root_path = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_path))

# Fetches all products and its history from the database
def get_data():
    db: Session = SessionLocal()
    products = db.query(Product).all()
    
    data = []
    for p in products:
        latest_price = p.prices[-1].price if p.prices else 0.0
        
        # Add product information to db
        data.append({
            "ID": p.id,
            "Name": p.name,
            "Current Price": latest_price,
            "Target Price": p.target_price,
            "URL": p.url
        })
    db.close()
    return pd.DataFrame(data)

def get_history(product_id):
    db: Session = SessionLocal()
    history = db.query(PriceHistory).filter(PriceHistory.product_id == product_id).all()
    db.close()
    
    return pd.DataFrame([{
        "Date": h.scraped_at,
        "Price": h.price
    } for h in history])


st.title("Price Tracker")
st.markdown("Monitorització de preus en temps real per a Amazon.")

# Variables
df_products = get_data()
col1, col2, col3 = st.columns(3)
col1.metric("Productes Rastrejats", len(df_products))
if not df_products.empty:
    avg_price = df_products["Current Price"].mean()
    col2.metric("Preu Mitjà", f"{avg_price:.2f} €")

st.divider()
st.subheader("Els teus Productes")
if not df_products.empty:
    st.dataframe(
        df_products, 
        column_config={
            "URL": st.column_config.LinkColumn("Product Link"),
            "Current Price": st.column_config.NumberColumn("Preu Actual", format="%.2f €"),
        },
        hide_index=True
    )
else:
    st.info("Encara no has afegit cap producte. Fes servir el terminal o la barra lateral.")

# Graphics
st.divider()
st.subheader("Evolució de Preus")

if not df_products.empty:
    product_names = df_products["Name"].tolist()
    selected_name = st.selectbox("Selecciona un producte per veure l'historial:", product_names)
    
    selected_row = df_products[df_products["Name"] == selected_name].iloc[0]
    product_id = int(selected_row["ID"])
    
    df_history = get_history(product_id)
    
    if not df_history.empty:
        fig = px.line(df_history, x="Date", y="Price", title=f"Historial: {selected_name}", markers=True)
        fig.update_layout(yaxis_title="Preu (€)", xaxis_title="Data")
        st.plotly_chart(fig, use_container_width=True)
        
        # Alert if there is a better price
        current_price = selected_row["Current Price"]
        target_price = selected_row["Target Price"]
        
        if target_price and current_price <= target_price:
            st.success(f"ALERTA D'OFERTA! El preu actual ({current_price}€) està per sota del teu objectiu ({target_price}€)!")
        elif target_price:
            st.warning(f"Encara no hi ha oferta. Objectiu: {target_price}€")
    else:
        st.write("No hi ha historial suficient per mostrar gràfica.")
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(page_title="Gold Volatility Terminal", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    h1 { color: #f1c40f; font-family: 'Segoe UI', sans-serif; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("GC=F GOLD FUTURES: LIVE VOLATILITY SURFACE")

@st.cache_data(ttl=60)
def fetch_market_data():
    try:
        gold = yf.Ticker("GC=F")
        expirations = gold.options[:5] # පළමු මාස 5 ක දත්ත
        data_list = []
        
        for expiry in expirations:
            chain = gold.option_chain(expiry).calls
            for _, row in chain.iterrows():
                data_list.append({
                    'strike': row['strike'],
                    'expiry': expiry,
                    'iv': row['impliedVolatility']
                })
        return pd.DataFrame(data_list)
    except Exception:
        return pd.DataFrame()

df = fetch_market_data()

if not df.empty:
    df['dte'] = (pd.to_datetime(df['expiry']) - datetime.now()).dt.days
    
    # 3D Mesh Plot (Interpolation නැතිව කෙලින්ම අඳින නිසා වේගවත්)
    fig = go.Figure(data=[go.Mesh3d(
        x=df['strike'],
        y=df['dte'],
        z=df['iv'],
        intensity=df['iv'],
        colorscale='YlOrRd',
        opacity=0.8
    )])

    fig.update_layout(
        scene=dict(
            xaxis_title='Strike Price ($)',
            yaxis_title='Days to Expiry (DTE)',
            zaxis_title='Implied Volatility (IV)',
        ),
        width=1100, height=800,
        template="plotly_dark"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Last Update: " + datetime.now().strftime("%H:%M:%S"))
else:
    st.error("Market data currently unavailable. Please try refreshing in a few seconds.")

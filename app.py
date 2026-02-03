import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime
import time

st.set_page_config(page_title="Gold Volatility Terminal", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    h1 { color: #f1c40f; font-family: 'Segoe UI', sans-serif; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("GC=F GOLD FUTURES: LIVE VOLATILITY SURFACE")

@st.cache_data(ttl=300)
def fetch_market_data():
    gold = yf.Ticker("GC=F")
    # දත්ත ලැබෙන තෙක් 3 වතාවක් උත්සාහ කරයි
    for i in range(3):
        try:
            expirations = gold.options[:5]
            if not expirations:
                time.sleep(1)
                continue
                
            data_list = []
            for expiry in expirations:
                chain = gold.option_chain(expiry).calls
                for _, row in chain.iterrows():
                    data_list.append({
                        'strike': row['strike'],
                        'expiry': expiry,
                        'iv': row['impliedVolatility']
                    })
            if data_list:
                return pd.DataFrame(data_list)
        except Exception:
            time.sleep(1)
    return pd.DataFrame()

df = fetch_market_data()

if not df.empty:
    df['dte'] = (pd.to_datetime(df['expiry']) - datetime.now()).dt.days
    
    # පෘෂ්ඨය ලස්සනට පෙන්වීමට scatter3d භාවිතය (වැඩි වේගයක් සඳහා)
    fig = go.Figure(data=[go.Scatter3d(
        x=df['strike'],
        y=df['dte'],
        z=df['iv'],
        mode='markers',
        marker=dict(
            size=4,
            color=df['iv'],
            colorscale='YlOrRd',
            opacity=0.8
        )
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
    st.success("Market Data Synchronized Successfully!")
else:
    st.warning("Yahoo Finance is currently rate-limiting requests. Please wait 1-2 minutes and refresh your browser.")
    st.info("Tip: If you keep seeing this, try checking if 'GC=F' is active on Yahoo Finance website.")

import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime
from scipy.interpolate import griddata

# Page Configuration
st.set_page_config(page_title="Gold Volatility Terminal", layout="wide")

# Dark Theme CSS
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    h1 { color: #f1c40f; font-family: 'Segoe UI', sans-serif; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("GC=F GOLD FUTURES: LIVE VOLATILITY SURFACE")

@st.cache_data(ttl=60)
def fetch_market_data():
    gold = yf.Ticker("GC=F")
    expirations = gold.options[:8]
    data_list = []
    
    for expiry in expirations:
        try:
            chain = gold.option_chain(expiry).calls
            for _, row in chain.iterrows():
                if row['impliedVolatility'] > 0.01: 
                    data_list.append({
                        'strike': row['strike'],
                        'expiry': expiry,
                        'iv': row['impliedVolatility']
                    })
        except:
            continue
    return pd.DataFrame(data_list)

try:
    df = fetch_market_data()
    
    if not df.empty:
        df['dte'] = (pd.to_datetime(df['expiry']) - datetime.now()).dt.days
        
        # Grid Generation
        strike_grid = np.linspace(df['strike'].min(), df['strike'].max(), 100)
        dte_grid = np.linspace(df['dte'].min(), df['dte'].max(), 100)
        strike_grid, dte_grid = np.meshgrid(strike_grid, dte_grid)
        
        iv_grid = griddata(
            (df['strike'], df['dte']), 
            df['iv'], 
            (strike_grid, dte_grid), 
            method='linear'
        )

        fig = go.Figure(data=[go.Surface(
            x=strike_grid, 
            y=dte_grid, 
            z=iv_grid, 
            colorscale='YlOrRd'
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
        st.caption("System Status: Active | Last Sync: " + datetime.now().strftime("%H:%M:%S"))
        
    else:
        st.info("Synchronizing with Market Data... Please wait.")
except Exception as e:
    st.error(f"Operational Error: {e}")

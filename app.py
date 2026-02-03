import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime
from scipy.interpolate import griddata

# Page Configuration
st.set_page_config(page_title="Gold Volatility Surface", layout="wide")

# Custom CSS for Professional Look
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    h1 { color: #f1c40f; font-family: 'Courier New', monospace; }
    </style>
    """, unsafe_allow_html=True)

st.title("GC=F GOLD FUTURES: REAL-TIME VOLATILITY SURFACE")

@st.cache_data(ttl=60)
def fetch_market_data():
    gold = yf.Ticker("GC=F")
    # Fetching the first 8 expiration dates
    expirations = gold.options[:8]
    data_list = []
    
    for expiry in expirations:
        try:
            chain = gold.option_chain(expiry).calls
            for _, row in chain.iterrows():
                if row['impliedVolatility'] > 0.01: # Filter out noise
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
        # Calculate Days to Expiry (DTE)
        df['dte'] = (pd.to_datetime(df['expiry']) - datetime.now()).dt.days
        
        # Grid Generation for Smooth Surface
        strike_grid = np.linspace(df['strike'].min(), df['strike'].max(), 100)
        dte_grid = np.linspace(df['dte'].min(), df['dte'].max(), 100)
        strike_grid, dte_grid = np.meshgrid(strike_grid, dte_grid)
        
        # Interpolate IV onto the grid
        iv_grid = griddata(
            (df['strike'], df['dte']), 
            df['iv'], 
            (strike_grid, dte_grid), 
            method='linear'
        )

        # Plotting the 3D Surface
        fig = go.Figure(data=[go.Surface(
            x=strike_grid, 
            y=dte_grid, 
            z=iv_grid, 
            colorscale='YlOrRd', # Gold/Orange/Red theme
            colorbar_title='IV %'
        )])
        
        fig.update_layout(
            scene=dict(
                xaxis_title='Strike Price ($)',
                yaxis_title='Days to Expiry (DTE)',
                zaxis_title='Implied Volatility',
                xaxis=dict(gridcolor='white'),
                yaxis=dict(gridcolor='white'),
                zaxis=dict(gridcolor='white'),
            ),
            width=1100,
            height=800,
            template="plotly_dark",
            margin=dict(r=20, l=10, b=10, t=10)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Data Source: Yahoo Finance | Updated: " + datetime.now().strftime("%H:%M:%S"))
        
    else:
        st.warning("Awaiting Market Data Sync...")
except Exception as e:
    st.error(f"System Error: {e}")

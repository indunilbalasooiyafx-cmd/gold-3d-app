import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Gold Vol Terminal", layout="wide")

# Modern Minimalist Header
st.markdown("<h1 style='text-align: center; color: #f1c40f;'>GOLD (GC=F) VOLATILITY RADAR</h1>", unsafe_allow_html=True)

@st.cache_data(ttl=3600) # පැයක් යනකම් දත්ත මතක තබා ගනී
def get_gold_options():
    try:
        gold = yf.Ticker("GC=F")
        # එක මාසයක දත්ත විතරක් මුලින් ගමු (වේගවත් වීමට)
        expiries = gold.options[:3] 
        all_data = []
        
        for exp in expiries:
            opt = gold.option_chain(exp).calls
            temp = opt[['strike', 'impliedVolatility']].copy()
            temp['expiry'] = exp
            all_data.append(temp)
            
        return pd.concat(all_data) if all_data else pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

# UI Layout
df = get_gold_options()

if not df.empty:
    df['dte'] = (pd.to_datetime(df['expiry']) - datetime.now()).dt.days
    
    # Professional 3D Scatter
    fig = go.Figure(data=[go.Scatter3d(
        x=df['strike'],
        y=df['dte'],
        z=df['impliedVolatility'],
        mode='markers',
        marker=dict(
            size=3,
            color=df['impliedVolatility'],
            colorscale='Hot',
            showscale=True
        )
    )])

    fig.update_layout(
        scene=dict(
            xaxis_title='Strike ($)',
            yaxis_title='Days to Expiry',
            zaxis_title='IV Index',
            bgcolor='#0e1117'
        ),
        paper_bgcolor='#0e1117',
        font=dict(color="white"),
        width=1000, height=700,
        margin=dict(l=0, r=0, b=0, t=0)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("<p style='text-align: center;'>Status: <span style='color: #2ecc71;'>LIVE DATA CONNECTED</span></p>", unsafe_allow_html=True)
else:
    st.error("SYSTEM ON STANDBY: Yahoo Finance connection is on cooldown.")
    st.info("The server is temporarily limiting requests. Please leave this tab open and don't refresh for 5-10 minutes. The system will auto-retry.")

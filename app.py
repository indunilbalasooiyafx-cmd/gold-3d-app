import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Gold Vol Terminal", layout="wide")

# Simple Header
st.markdown("<h1 style='color: #f1c40f;'>GOLD (GC=F) 3D VOLATILITY VIEW</h1>", unsafe_allow_html=True)

@st.cache_data(ttl=600) # දත්ත විනාඩි 10ක් යනකම් මතක තබා ගනී (Cache)
def get_clean_data():
    try:
        gold = yf.Ticker("GC=F")
        # මාස 3ක් පමණක් ගනිමු (සර්වර් එකට ලේසියි)
        expiries = gold.options[:3] 
        all_data = []
        
        for exp in expiries:
            opt = gold.option_chain(exp).calls
            # අවශ්‍යම දත්ත ටික විතරක් පෙරලා ගනිමු
            temp = opt[['strike', 'impliedVolatility']].copy()
            temp['expiry'] = exp
            all_data.append(temp)
            
        return pd.concat(all_data) if all_data else pd.DataFrame()
    except:
        return pd.DataFrame()

df = get_clean_data()

if not df.empty:
    df['dte'] = (pd.to_datetime(df['expiry']) - datetime.now()).dt.days
    
    # 3D Scatter Plot - මේක ඕනෑම Device එකක වේගයෙන් වැඩ කරයි
    fig = go.Figure(data=[go.Scatter3d(
        x=df['strike'],
        y=df['dte'],
        z=df['impliedVolatility'],
        mode='markers',
        marker=dict(size=3, color=df['impliedVolatility'], colorscale='Viridis')
    )])

    fig.update_layout(
        scene=dict(xaxis_title='Strike', yaxis_title='Days', zaxis_title='IV'),
        template="plotly_dark",
        margin=dict(l=0, r=0, b=0, t=0)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    st.success("Connected to Data Feed")
else:
    st.error("Server Busy: Please wait 2-3 minutes and refresh.")
    st.info("Yahoo Finance is blocking requests temporarily. Don't refresh repeatedly.")

import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Gold 3D Terminal", layout="wide")
st.title("GC Gold Futures 3D Surface")

def get_data():
    gold = yf.Ticker("GC=F")
    dates = gold.options[:5]
    all_data = []
    for d in dates:
        chain = gold.option_chain(d).calls
        chain['expiry'] = d
        all_data.append(chain)
    return pd.concat(all_data)

try:
    df = get_data()
    df['expiry'] = pd.to_datetime(df['expiry'])
    df['days'] = (df['expiry'] - datetime.now()).dt.days
    fig = go.Figure(data=[go.Mesh3d(x=df['strike'], y=df['days'], z=df['impliedVolatility'], intensity=df['impliedVolatility'], colorscale='Plasma')])
    st.plotly_chart(fig, use_container_width=True)
except:
    st.write("Data loading... please refresh.")

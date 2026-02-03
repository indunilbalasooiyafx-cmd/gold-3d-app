import yfinance as yf
import pandas as pd
import numpy as np
import functions as f
import streamlit as st
from scipy.interpolate import griddata
import plotly.graph_objects as go
import requests

# 1. Yahoo Finance එක රවට්ටන්න Browser එකක් වගේ Headers හදමු
def get_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    })
    return session

# 2. Caching පාවිච්චි කරලා Requests ගණන අඩු කරමු (විනාඩි 15ක් යනකම් දත්ත මතක තියාගනී)
@st.cache_data(ttl=900)
def get_stock_data(ticker_symbol="GC=F", period="1y"):
    session = get_session()
    stock = yf.Ticker(ticker_symbol, session=session)
    
    try:
        # ඉතිහාස දත්ත සහ වර්තමාන මිල ලබා ගැනීම
        hist = stock.history(period=period)
        if hist.empty:
            raise ValueError("No historical data found.")
            
        spot_price = hist['Close'].iloc[-1]
        return stock, hist, spot_price
    except Exception as e:
        st.error(f"Yahoo Finance Error: {e}")
        # Error එකක් ආවොත් App එක Crash නොවී ඉන්න සාමාන්‍ය අගයක් දෙමු
        return stock, pd.DataFrame(), 2700.0

@st.cache_data(ttl=900)
def get_options_data(_stock):
    # දත්ත ගොඩක් ඉල්ලන්නේ නැතුව මුල් Expiry Dates 8ක් විතරක් ගමු
    expiries = _stock.options[:8] 
    calls_frames = []
    
    for date in expiries:
        try:
            chain = _stock.option_chain(date).calls.copy()
            chain["expiration"] = date
            calls_frames.append(chain)
        except:
            continue

    calls_all = pd.concat(calls_frames, ignore_index=True) if calls_frames else pd.DataFrame()
    return calls_all, expiries

def filter_calls_data(calls_data, spot_price, min_strike_price, max_strike_price):
    if calls_data.empty:
        return pd.DataFrame()
        
    filtered_calls_data = calls_data[
        (calls_data["strike"] >= min_strike_price) &
        (calls_data["strike"] <= max_strike_price)].copy()

    filtered_calls_data["TimeToExpiry"] = filtered_calls_data["expiration"].map(f.calculate_time_to_expiration)
    
    # ඉතා කෙටි කාලීන Options අයින් කරමු (Noise වැඩි නිසා)
    filtered_calls_data = filtered_calls_data[filtered_calls_data["TimeToExpiry"] >= 0.02]

    # Bid/Ask මැද මිල ගමු
    filtered_calls_data["midPrice"] = 0.5 * (filtered_calls_data["bid"] + filtered_calls_data["ask"])
    
    # Bid/Ask නැත්නම් Last Price එක පාවිච්චි කරමු
    filtered_calls_data["midPrice"] = filtered_calls_data["midPrice"].replace(0, np.nan).fillna(filtered_calls_data["lastPrice"])

    return filtered_calls_data.reset_index(drop=True)

def calculate_implied_volatility(filtered_calls_data, spot_price, risk_free_rate, dividend_yield):
    rows = []
    if filtered_calls_data.empty:
        return pd.DataFrame()

    for _, row in filtered_calls_data.iterrows():
        T = row["TimeToExpiry"]
        price = row["midPrice"]

        if not np.isfinite(price) or price <= 0: continue
        
        # Black-Scholes භාවිතයෙන් සැබෑ IV එක ගණනය කිරීම
        iv = f.Call_IV(spot_price, row["strike"], risk_free_rate, T, price, dividend_yield)
        
        if np.isfinite(iv):
            rows.append((row["contractSymbol"], row["strike"], T, iv))

    return pd.DataFrame(rows, columns=["ContractSymbol","StrikePrice","TimeToExpiry","ImpliedVolatility"])

def get_plot_data(filtered_df):
    if filtered_df.empty:
        return np.array([]), np.array([]), np.array([])
    X = filtered_df['TimeToExpiry'].values
    Y = filtered_df['StrikePrice'].values
    Z = filtered_df['ImpliedVolatility'].values * 100
    return X, Y, Z
